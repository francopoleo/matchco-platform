"""
Performance Tests: API Latency Under Load

Measures API endpoint response times and throughput under various loads.

Goals:
- Profile creation latency <500ms p99
- API response consistency
- Throughput: 100+ profiles/second
- No database connection pool exhaustion
"""

import pytest
import time
import asyncio
import statistics
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestAPILatencyBaseline:
    """Baseline latency for common operations"""

    @pytest.mark.performance
    def test_candidate_profile_creation_latency(self, client, django_db_blocker):
        """Test: Profile creation latency baseline"""

        latencies = []

        with django_db_blocker.unblock():
            from matchco.recruitment.models import CandidateProfile

            for i in range(10):
                start = time.time()

                profile = CandidateProfile.objects.create(
                    mobile=f"+551198765{i:04d}",
                    email=f"candidate{i}@test.com",
                    name=f"Candidate {i}",
                )

                duration_ms = (time.time() - start) * 1000
                latencies.append(duration_ms)

        # Calculate statistics
        p50 = np.percentile(latencies, 50)
        p99 = np.percentile(latencies, 99)
        mean = statistics.mean(latencies)
        max_latency = max(latencies)

        print(f"\nProfile Creation Latency:")
        print(f"  p50: {p50:.2f}ms")
        print(f"  p99: {p99:.2f}ms")
        print(f"  mean: {mean:.2f}ms")
        print(f"  max: {max_latency:.2f}ms")

        # Assert baselines
        assert p99 < 500, f"p99 latency {p99}ms exceeds 500ms target"
        assert mean < 200, f"Mean latency {mean}ms exceeds 200ms target"

    @pytest.mark.performance
    def test_relation_creation_latency(self, django_db_blocker):
        """Test: Relation creation latency"""

        latencies = []

        with django_db_blocker.unblock():
            from matchco.recruitment.models import Relation, CandidateProfile

            candidate = CandidateProfile.objects.create(
                mobile="+5511987654321",
                email="candidate@test.com",
            )

            for i in range(10):
                start = time.time()

                relation = Relation.objects.create(
                    candidate_profile=candidate,
                    state=Relation.STATE_NOTICE_DELIVERED,
                )

                duration_ms = (time.time() - start) * 1000
                latencies.append(duration_ms)

        p99 = np.percentile(latencies, 99)
        mean = statistics.mean(latencies)

        print(f"\nRelation Creation Latency:")
        print(f"  p99: {p99:.2f}ms")
        print(f"  mean: {mean:.2f}ms")

        assert p99 < 300, f"Relation creation p99 {p99}ms exceeds target"

    @pytest.mark.performance
    def test_question_creation_latency(self, django_db_blocker, store_with_questionnaire):
        """Test: Question creation with compliance checking"""

        latencies = []

        with django_db_blocker.unblock():
            template = store_with_questionnaire["template"]

            for i in range(10):
                start = time.time()

                from matchco.recruitment.models import QuestionnaireQuestion

                question = QuestionnaireQuestion.objects.create(
                    template=template,
                    label=f"Question {i}",
                    field_type="text",
                    position=i + 100,
                )

                duration_ms = (time.time() - start) * 1000
                latencies.append(duration_ms)

        p99 = np.percentile(latencies, 99)

        print(f"\nQuestion Creation Latency:")
        print(f"  p99: {p99:.2f}ms")

        # Question creation includes compliance check (~15-20ms)
        assert p99 < 200, f"Question creation p99 {p99}ms exceeds target"


class TestConcurrentProfileCreation:
    """Test profile creation under concurrent load"""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_10_concurrent_profiles(self, django_db_blocker):
        """Test: Create 10 profiles concurrently"""

        results = self._create_concurrent_profiles(10, django_db_blocker)

        assert results['success_count'] >= 9, \
            f"Only {results['success_count']}/10 succeeded"
        assert results['p99_latency'] < 500, \
            f"p99 latency {results['p99_latency']}ms exceeds 500ms"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_50_concurrent_profiles(self, django_db_blocker):
        """Test: Create 50 profiles concurrently"""

        results = self._create_concurrent_profiles(50, django_db_blocker)

        assert results['success_count'] >= 48, \
            f"Only {results['success_count']}/50 succeeded"
        assert results['success_rate'] > 0.95, \
            f"Success rate {results['success_rate']:.2%} too low"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_100_concurrent_profiles(self, django_db_blocker):
        """Test: Create 100 profiles concurrently (production load)"""

        results = self._create_concurrent_profiles(100, django_db_blocker)

        print(f"\n100 Concurrent Profiles:")
        print(f"  Success: {results['success_count']}/100")
        print(f"  Success rate: {results['success_rate']:.2%}")
        print(f"  Mean latency: {results['mean_latency']:.2f}ms")
        print(f"  p50 latency: {results['p50_latency']:.2f}ms")
        print(f"  p99 latency: {results['p99_latency']:.2f}ms")
        print(f"  Throughput: {results['throughput']:.0f} profiles/sec")

        assert results['success_count'] >= 95, \
            f"Only {results['success_count']}/100 succeeded"
        assert results['success_rate'] > 0.95, \
            f"Success rate {results['success_rate']:.2%} too low"
        assert results['p99_latency'] < 1000, \
            f"p99 latency {results['p99_latency']}ms exceeds 1000ms under load"

    def _create_concurrent_profiles(self, count, django_db_blocker):
        """Helper: Create profiles concurrently"""

        with django_db_blocker.unblock():
            from matchco.recruitment.models import CandidateProfile

            latencies = []
            errors = []
            start_time = time.time()

            def create_profile(i):
                try:
                    profile_start = time.time()

                    profile = CandidateProfile.objects.create(
                        mobile=f"+551198765{i:05d}",
                        email=f"concurrent{i}@test.com",
                        name=f"Concurrent {i}",
                    )

                    duration_ms = (time.time() - profile_start) * 1000
                    return {
                        'success': True,
                        'latency': duration_ms,
                        'profile_id': profile.id,
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'error': str(e),
                    }

            # Execute concurrently with thread pool
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(create_profile, i)
                    for i in range(count)
                ]

                for future in as_completed(futures):
                    result = future.result()
                    if result['success']:
                        latencies.append(result['latency'])
                    else:
                        errors.append(result['error'])

            total_duration = time.time() - start_time

        # Calculate statistics
        success_count = len(latencies)
        success_rate = success_count / count

        return {
            'success_count': success_count,
            'success_rate': success_rate,
            'error_count': len(errors),
            'mean_latency': statistics.mean(latencies) if latencies else 0,
            'p50_latency': np.percentile(latencies, 50) if latencies else 0,
            'p99_latency': np.percentile(latencies, 99) if latencies else 0,
            'max_latency': max(latencies) if latencies else 0,
            'throughput': count / total_duration,
            'total_duration': total_duration,
            'latencies': latencies,
        }


class TestDatabasePerformance:
    """Test database query performance under load"""

    @pytest.mark.performance
    def test_no_n_plus_one_on_profile_list(self, django_db_blocker):
        """Test: Profile listing doesn't have N+1 queries"""

        with django_db_blocker.unblock():
            from django.db import connection
            from django.test.utils import CaptureQueriesContext
            from matchco.recruitment.models import CandidateProfile

            # Create profiles
            for i in range(5):
                CandidateProfile.objects.create(
                    mobile=f"+551198765{i:04d}",
                    email=f"list{i}@test.com",
                )

            # Measure queries on list()
            with CaptureQueriesContext(connection) as ctx:
                profiles = list(CandidateProfile.objects.all())

            # Should be 1 query (SELECT *), not 1 + N queries
            query_count = len(ctx.captured_queries)

            print(f"\nProfile List Queries:")
            print(f"  Count: {query_count}")
            print(f"  N+1 detected: {query_count > 2}")

            assert query_count <= 2, \
                f"Got {query_count} queries for listing {len(profiles)} profiles"

    @pytest.mark.performance
    def test_profile_with_answers_query_count(self, django_db_blocker):
        """Test: Profile with answers doesn't overflow query limit"""

        with django_db_blocker.unblock():
            from django.db import connection
            from django.test.utils import CaptureQueriesContext
            from matchco.recruitment.models import (
                CandidateProfile, CandidateSignupAnswer,
                QuestionnaireTemplate, QuestionnaireQuestion
            )

            # Create template with questions
            template = QuestionnaireTemplate.objects.create(
                name="Test",
                slug="test",
            )

            for i in range(5):
                QuestionnaireQuestion.objects.create(
                    template=template,
                    label=f"Q{i}",
                    field_type="text",
                    position=i,
                )

            # Create profile with answers
            profile = CandidateProfile.objects.create(
                mobile="+5511987654321",
                email="test@test.com",
            )

            for q in template.questions.all():
                CandidateSignupAnswer.objects.create(
                    candidate_profile=profile,
                    question=q,
                    response_text="answer",
                )

            # Measure queries
            with CaptureQueriesContext(connection) as ctx:
                retrieved = CandidateProfile.objects.get(id=profile.id)
                answers = list(retrieved.answers.all())

            query_count = len(ctx.captured_queries)

            print(f"\nProfile + Answers Queries: {query_count}")

            # Should be minimal (1-2 queries)
            assert query_count <= 3, \
                f"Got {query_count} queries (expected ≤3)"

    @pytest.mark.performance
    def test_relation_state_filtering_performance(self, django_db_blocker):
        """Test: Filtering relations by state is efficient"""

        with django_db_blocker.unblock():
            from django.db import connection
            from django.test.utils import CaptureQueriesContext
            from matchco.recruitment.models import Relation, CandidateProfile

            # Create relations in different states
            candidate = CandidateProfile.objects.create(
                mobile="+5511987654321",
                email="candidate@test.com",
            )

            for i in range(20):
                state = [
                    Relation.STATE_NOTICE_DELIVERED,
                    Relation.STATE_EMPLOYER_INTEREST_VIEW,
                    Relation.STATE_EMPLOYER_INTERESTED,
                    Relation.STATE_MATCHED,
                ][i % 4]

                Relation.objects.create(
                    candidate_profile=candidate,
                    state=state,
                )

            # Measure filter query
            with CaptureQueriesContext(connection) as ctx:
                viewable = Relation.objects.filter(
                    state__in=[
                        Relation.STATE_EMPLOYER_INTEREST_VIEW,
                        Relation.STATE_EMPLOYER_INTERESTED,
                        Relation.STATE_MATCHED,
                    ]
                )
                count = viewable.count()

            query_count = len(ctx.captured_queries)

            print(f"\nRelation State Filter: {query_count} queries, {count} results")

            assert query_count <= 2, \
                f"State filtering used {query_count} queries"


class TestThroughputMeasurement:
    """Measure operations per second"""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_profile_creation_throughput(self, django_db_blocker):
        """Test: Measure profile creation throughput"""

        with django_db_blocker.unblock():
            from matchco.recruitment.models import CandidateProfile

            start = time.time()
            created = 0

            # Create profiles for 5 seconds
            while time.time() - start < 5:
                try:
                    CandidateProfile.objects.create(
                        mobile=f"+551198765{created:05d}",
                        email=f"throughput{created}@test.com",
                        name=f"Throughput {created}",
                    )
                    created += 1
                except Exception:
                    break

            duration = time.time() - start
            throughput = created / duration

            print(f"\nProfile Creation Throughput:")
            print(f"  Created: {created}")
            print(f"  Duration: {duration:.2f}s")
            print(f"  Throughput: {throughput:.0f} profiles/sec")

            # Should achieve at least 100 profiles/second
            assert throughput >= 100, \
                f"Throughput {throughput:.0f}/sec below 100 target"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_relation_state_transition_throughput(self, django_db_blocker):
        """Test: Measure relation state transition throughput"""

        with django_db_blocker.unblock():
            from matchco.recruitment.models import Relation, CandidateProfile

            candidate = CandidateProfile.objects.create(
                mobile="+5511987654321",
                email="candidate@test.com",
            )

            # Create base relations
            relations = []
            for i in range(20):
                r = Relation.objects.create(
                    candidate_profile=candidate,
                    state=Relation.STATE_EMPLOYER_INTEREST_VIEW,
                )
                relations.append(r)

            start = time.time()
            transitions = 0

            # Transition states rapidly
            while time.time() - start < 5:
                for relation in relations:
                    relation.state = Relation.STATE_EMPLOYER_INTERESTED
                    relation.save()
                    transitions += 1

                    if time.time() - start >= 5:
                        break

            duration = time.time() - start
            throughput = transitions / duration

            print(f"\nRelation Transitions Throughput:")
            print(f"  Transitions: {transitions}")
            print(f"  Throughput: {throughput:.0f} transitions/sec")

            assert throughput >= 50, \
                f"Transition throughput {throughput:.0f}/sec too low"
