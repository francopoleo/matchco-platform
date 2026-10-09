"""
Performance Tests: Concurrent User Simulation

Simulates multiple users performing real-world operations simultaneously.

Goals:
- 100+ concurrent users without degradation
- Memory stability (no leaks)
- Database connection pool doesn't exhaust
- Error rate <2% under load
"""

import pytest
import time
import asyncio
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


class TestConcurrentUserScenarios:
    """Test realistic concurrent user scenarios"""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_50_concurrent_candidate_signups(self, django_db_blocker):
        """Test: 50 candidates signing up simultaneously"""

        results = self._simulate_candidate_signups(50, django_db_blocker)

        print(f"\n50 Concurrent Signups:")
        print(f"  Completed: {results['completed']}/50")
        print(f"  Success rate: {results['success_rate']:.2%}")
        print(f"  Mean time: {results['mean_time']:.2f}s")
        print(f"  Errors: {results['error_count']}")

        assert results['success_rate'] > 0.95, \
            f"Success rate {results['success_rate']:.2%} too low"
        assert results['error_count'] < 3, \
            f"Too many errors: {results['error_count']}"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_100_concurrent_candidate_signups(self, django_db_blocker):
        """Test: 100 candidates signing up simultaneously (production load)"""

        results = self._simulate_candidate_signups(100, django_db_blocker)

        print(f"\n100 Concurrent Signups (Production Load):")
        print(f"  Completed: {results['completed']}/100")
        print(f"  Success rate: {results['success_rate']:.2%}")
        print(f"  Mean time: {results['mean_time']:.2f}s")
        print(f"  Peak concurrent: {results['peak_concurrent']}")
        print(f"  Total duration: {results['total_duration']:.2f}s")
        print(f"  Throughput: {results['throughput']:.1f} signups/sec")

        assert results['success_rate'] > 0.98, \
            f"Success rate {results['success_rate']:.2%} below 98% target"
        assert results['error_count'] < 2, \
            f"Too many errors: {results['error_count']}"

    def _simulate_candidate_signups(self, user_count, django_db_blocker):
        """Simulate candidate signup flow"""

        with django_db_blocker.unblock():
            from matchco.recruitment.models import CandidateProfile

            completed = 0
            success_count = 0
            error_count = 0
            durations = []
            concurrent_count = 0
            peak_concurrent = 0
            lock = threading.Lock()

            start_time = time.time()

            def candidate_signup(user_id):
                nonlocal completed, success_count, error_count, concurrent_count, peak_concurrent

                try:
                    with lock:
                        concurrent_count += 1
                        peak_concurrent = max(peak_concurrent, concurrent_count)

                    signup_start = time.time()

                    # Simulate profile creation
                    profile = CandidateProfile.objects.create(
                        mobile=f"+551198765{user_id:05d}",
                        email=f"signup{user_id}@test.com",
                        name=f"User {user_id}",
                    )

                    signup_duration = time.time() - signup_start

                    with lock:
                        completed += 1
                        success_count += 1
                        durations.append(signup_duration)

                    return True

                except Exception as e:
                    with lock:
                        completed += 1
                        error_count += 1
                    return False
                finally:
                    with lock:
                        concurrent_count -= 1

            # Execute signups concurrently
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [
                    executor.submit(candidate_signup, i)
                    for i in range(user_count)
                ]

                for future in as_completed(futures):
                    pass

            total_duration = time.time() - start_time

        return {
            'completed': completed,
            'success_count': success_count,
            'error_count': error_count,
            'success_rate': success_count / user_count if user_count > 0 else 0,
            'mean_time': sum(durations) / len(durations) if durations else 0,
            'peak_concurrent': peak_concurrent,
            'total_duration': total_duration,
            'throughput': user_count / total_duration,
        }


class TestConcurrentEmployerActions:
    """Test concurrent employer actions"""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_50_employers_view_candidates(self, django_db_blocker):
        """Test: 50 employers viewing candidates simultaneously"""

        results = self._simulate_employer_views(50, django_db_blocker)

        print(f"\n50 Concurrent Employer Views:")
        print(f"  Successful views: {results['successful_views']}/50")
        print(f"  Mean view time: {results['mean_view_time']:.2f}ms")
        print(f"  Access errors: {results['access_errors']}")

        assert results['successful_views'] >= 48, \
            f"Only {results['successful_views']}/50 successful views"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_100_concurrent_interest_declarations(self, django_db_blocker):
        """Test: 100 employers declaring interest simultaneously"""

        results = self._simulate_interest_declarations(100, django_db_blocker)

        print(f"\n100 Concurrent Interest Declarations:")
        print(f"  Successful: {results['successful_declarations']}/100")
        print(f"  Success rate: {results['success_rate']:.2%}")
        print(f"  State transitions: {results['state_transitions']}")
        print(f"  Errors: {results['errors']}")

        assert results['success_rate'] > 0.95, \
            "Interest declaration success rate too low under load"

    def _simulate_employer_views(self, employer_count, django_db_blocker):
        """Simulate employers viewing candidates"""

        with django_db_blocker.unblock():
            from matchco.recruitment.models import (
                Relation, CandidateProfile
            )

            # Create candidate pool
            candidates = []
            for i in range(20):
                c = CandidateProfile.objects.create(
                    mobile=f"+551198765{i:04d}",
                    email=f"candidate{i}@test.com",
                )
                candidates.append(c)

            # Create relations in viewable states
            relations = []
            for candidate in candidates:
                r = Relation.objects.create(
                    candidate_profile=candidate,
                    state=Relation.STATE_EMPLOYER_INTEREST_VIEW,
                )
                relations.append(r)

            successful_views = 0
            access_errors = 0
            view_times = []
            lock = threading.Lock()

            def employer_view_candidate(employer_id):
                nonlocal successful_views, access_errors

                try:
                    # Pick random relation
                    relation = random.choice(relations)

                    view_start = time.time()

                    # Retrieve relation
                    retrieved = Relation.objects.get(id=relation.id)
                    candidate = retrieved.candidate_profile

                    view_time = time.time() - view_start

                    with lock:
                        successful_views += 1
                        view_times.append(view_time * 1000)  # Convert to ms

                except Exception as e:
                    with lock:
                        access_errors += 1

            # Simulate concurrent views
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [
                    executor.submit(employer_view_candidate, i)
                    for i in range(employer_count)
                ]

                for future in as_completed(futures):
                    pass

        return {
            'successful_views': successful_views,
            'access_errors': access_errors,
            'mean_view_time': sum(view_times) / len(view_times) if view_times else 0,
            'max_view_time': max(view_times) if view_times else 0,
        }

    def _simulate_interest_declarations(self, employer_count, django_db_blocker):
        """Simulate employers declaring interest"""

        with django_db_blocker.unblock():
            from matchco.recruitment.models import (
                Relation, CandidateProfile
            )

            # Create relation pool
            relations = []
            for i in range(50):
                c = CandidateProfile.objects.create(
                    mobile=f"+551198765{i:05d}",
                    email=f"candidate{i}@test.com",
                )
                r = Relation.objects.create(
                    candidate_profile=c,
                    state=Relation.STATE_EMPLOYER_INTEREST_VIEW,
                )
                relations.append(r)

            successful_declarations = 0
            state_transitions = 0
            errors = 0
            lock = threading.Lock()

            def declare_interest(employer_id):
                nonlocal successful_declarations, state_transitions, errors

                try:
                    # Pick unique relation
                    if employer_id < len(relations):
                        relation = relations[employer_id]

                        # Simulate state transition
                        relation.state = Relation.STATE_EMPLOYER_INTERESTED
                        relation.save()

                        with lock:
                            successful_declarations += 1
                            state_transitions += 1

                except Exception as e:
                    with lock:
                        errors += 1

            # Simulate concurrent declarations
            with ThreadPoolExecutor(max_workers=25) as executor:
                futures = [
                    executor.submit(declare_interest, i)
                    for i in range(min(employer_count, len(relations)))
                ]

                for future in as_completed(futures):
                    pass

        return {
            'successful_declarations': successful_declarations,
            'success_rate': successful_declarations / employer_count,
            'state_transitions': state_transitions,
            'errors': errors,
        }


class TestDatabaseConnectionPool:
    """Test database connection pool under load"""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_connection_pool_stability_100_concurrent(self, django_db_blocker):
        """Test: Database connections don't get exhausted"""

        with django_db_blocker.unblock():
            from django.db import connections
            from matchco.recruitment.models import CandidateProfile

            connection_peaks = []
            lock = threading.Lock()

            def database_operation(op_id):
                try:
                    # Get connection info
                    with lock:
                        active_connections = len([
                            c for c in connections.all()
                            if c.connection is not None
                        ])
                        connection_peaks.append(active_connections)

                    # Do database operation
                    profile = CandidateProfile.objects.create(
                        mobile=f"+551198765{op_id:05d}",
                        email=f"pool{op_id}@test.com",
                    )

                    return True

                except Exception:
                    return False

            # Execute 100 concurrent operations
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [
                    executor.submit(database_operation, i)
                    for i in range(100)
                ]

                for future in as_completed(futures):
                    pass

            max_connections = max(connection_peaks) if connection_peaks else 0

            print(f"\nDatabase Connection Pool:")
            print(f"  Peak connections: {max_connections}")
            print(f"  Pool stable: {max_connections < 20}")

            # Should stay well below pool limit
            assert max_connections < 30, \
                f"Connection pool peaked at {max_connections} (should be <30)"


class TestMemoryStability:
    """Test memory stability under load"""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_no_memory_leak_on_profile_creation(self, django_db_blocker):
        """Test: Profile creation doesn't leak memory"""

        import gc
        import sys

        with django_db_blocker.unblock():
            from matchco.recruitment.models import CandidateProfile

            gc.collect()
            initial_objects = len(gc.get_objects())

            # Create many profiles
            for i in range(100):
                CandidateProfile.objects.create(
                    mobile=f"+551198765{i:05d}",
                    email=f"memory{i}@test.com",
                    name=f"User {i}",
                )

            gc.collect()
            final_objects = len(gc.get_objects())

            object_growth = final_objects - initial_objects

            print(f"\nMemory Stability (100 profiles):")
            print(f"  Initial objects: {initial_objects}")
            print(f"  Final objects: {final_objects}")
            print(f"  Growth: {object_growth}")
            print(f"  Growth per profile: {object_growth / 100:.1f}")

            # Object growth should be reasonable (~10 per profile)
            assert object_growth / 100 < 50, \
                f"Object growth {object_growth / 100:.1f} per profile too high"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_no_memory_leak_on_queries(self, django_db_blocker):
        """Test: Repeated queries don't leak memory"""

        import gc

        with django_db_blocker.unblock():
            from matchco.recruitment.models import CandidateProfile

            # Create test data
            for i in range(10):
                CandidateProfile.objects.create(
                    mobile=f"+551198765{i:04d}",
                    email=f"query{i}@test.com",
                )

            gc.collect()
            initial_objects = len(gc.get_objects())

            # Perform many queries
            for _ in range(100):
                list(CandidateProfile.objects.all())
                list(CandidateProfile.objects.filter(mobile__contains="551"))

            gc.collect()
            final_objects = len(gc.get_objects())

            object_growth = final_objects - initial_objects

            print(f"\nMemory Stability (200 queries):")
            print(f"  Growth: {object_growth} objects")

            # Growth should be minimal
            assert object_growth < 1000, \
                f"Object growth {object_growth} too high"
