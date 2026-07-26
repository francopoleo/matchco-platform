from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from configuration.models import Organization, Company, Membership
from learning.models import ContentTrail, TrailAssignment

User = get_user_model()


class MembershipComplianceFieldsTestCase(TestCase):
    """Test Membership model compliance fields."""

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org', slug='test-org')
        self.company = Company.objects.create(organization=self.org, name='Test Company')
        self.user = User.objects.create_user(
            email=f'user-{timezone.now().timestamp()}@test.com',
            username=f'user_{timezone.now().timestamp()}',
            password='testpass123'
        )

    def test_membership_compliance_status_default(self):
        """Test that compliance_status defaults to 'pending'."""
        membership = Membership.objects.create(
            user=self.user,
            organization=self.org,
            company=self.company,
            role='member'
        )
        self.assertEqual(membership.compliance_status, 'pending')

    def test_membership_compliance_status_choices(self):
        """Test all compliance status choices are valid."""
        status_choices = ['pending', 'in_progress', 'completed', 'overdue', 'failed']

        for idx, status in enumerate(status_choices):
            user = User.objects.create_user(
                email=f'user-{idx}-{timezone.now().timestamp()}@test.com',
                username=f'user_{idx}_{timezone.now().timestamp()}',
                password='testpass123'
            )
            membership = Membership.objects.create(
                user=user,
                organization=self.org,
                company=self.company,
                role='member',
                compliance_status=status
            )
            self.assertEqual(membership.compliance_status, status)

    def test_membership_compliance_due_date(self):
        """Test setting compliance_due_date."""
        due_date = timezone.now() + timedelta(days=30)
        membership = Membership.objects.create(
            user=self.user,
            organization=self.org,
            company=self.company,
            role='member',
            compliance_due_date=due_date
        )
        self.assertEqual(membership.compliance_due_date, due_date)

    def test_membership_compliance_completed_at(self):
        """Test setting compliance_completed_at."""
        now = timezone.now()
        membership = Membership.objects.create(
            user=self.user,
            organization=self.org,
            company=self.company,
            role='member',
            compliance_status='completed',
            compliance_completed_at=now
        )
        self.assertEqual(membership.compliance_completed_at, now)

    def test_membership_compliance_workflow(self):
        """Test a complete compliance workflow: pending -> in_progress -> completed."""
        due_date = timezone.now() + timedelta(days=30)
        membership = Membership.objects.create(
            user=self.user,
            organization=self.org,
            company=self.company,
            role='member',
            compliance_status='pending',
            compliance_due_date=due_date
        )

        # User starts training
        membership.compliance_status = 'in_progress'
        membership.save()
        self.assertEqual(membership.compliance_status, 'in_progress')

        # User completes training
        now = timezone.now()
        membership.compliance_status = 'completed'
        membership.compliance_completed_at = now
        membership.save()
        self.assertEqual(membership.compliance_status, 'completed')
        self.assertIsNotNone(membership.compliance_completed_at)

    def test_membership_compliance_overdue(self):
        """Test overdue compliance status."""
        due_date = timezone.now() - timedelta(days=1)  # Past date
        membership = Membership.objects.create(
            user=self.user,
            organization=self.org,
            company=self.company,
            role='member',
            compliance_status='overdue',
            compliance_due_date=due_date
        )
        self.assertEqual(membership.compliance_status, 'overdue')
        self.assertLess(membership.compliance_due_date, timezone.now())

    def test_membership_compliance_failed(self):
        """Test failed compliance status."""
        due_date = timezone.now() + timedelta(days=30)
        membership = Membership.objects.create(
            user=self.user,
            organization=self.org,
            company=self.company,
            role='member',
            compliance_status='failed',
            compliance_due_date=due_date
        )
        self.assertEqual(membership.compliance_status, 'failed')


class TrailAssignmentComplianceFieldsTestCase(TestCase):
    """Test TrailAssignment model compliance fields."""

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org', slug='test-org')
        self.company = Company.objects.create(organization=self.org, name='Test Company')
        self.user = User.objects.create_user(
            email=f'user-{timezone.now().timestamp()}@test.com',
            username=f'user_{timezone.now().timestamp()}',
            password='testpass123'
        )
        self.trail = ContentTrail.objects.create(
            organization=self.org,
            title='Compliance Trail',
            slug='compliance-trail',
            trail_type='required',
            status='published',
            owner=self.user
        )

    def test_trail_assignment_is_mandatory_default(self):
        """Test that is_mandatory defaults to False."""
        assignment = TrailAssignment.objects.create(
            trail=self.trail,
            user=self.user
        )
        self.assertFalse(assignment.is_mandatory)

    def test_trail_assignment_is_mandatory_true(self):
        """Test setting is_mandatory to True."""
        assignment = TrailAssignment.objects.create(
            trail=self.trail,
            user=self.user,
            is_mandatory=True
        )
        self.assertTrue(assignment.is_mandatory)

    def test_trail_assignment_compliance_type_default(self):
        """Test that compliance_type defaults to 'general'."""
        assignment = TrailAssignment.objects.create(
            trail=self.trail,
            user=self.user
        )
        self.assertEqual(assignment.compliance_type, 'general')

    def test_trail_assignment_compliance_type_choices(self):
        """Test all compliance_type choices are valid."""
        compliance_types = ['general', 'internal', 'external', 'stakeholder']

        for idx, comp_type in enumerate(compliance_types):
            user = User.objects.create_user(
                email=f'user-{idx}-{timezone.now().timestamp()}@test.com',
                username=f'user_{idx}_{timezone.now().timestamp()}',
                password='testpass123'
            )
            assignment = TrailAssignment.objects.create(
                trail=self.trail,
                user=user,
                compliance_type=comp_type
            )
            self.assertEqual(assignment.compliance_type, comp_type)

    def test_trail_assignment_internal_employee_compliance(self):
        """Test internal employee compliance assignment."""
        assignment = TrailAssignment.objects.create(
            trail=self.trail,
            user=self.user,
            is_mandatory=True,
            compliance_type='internal',
            due_at=timezone.now() + timedelta(days=7)
        )
        self.assertTrue(assignment.is_mandatory)
        self.assertEqual(assignment.compliance_type, 'internal')

    def test_trail_assignment_external_partner_compliance(self):
        """Test external partner compliance assignment."""
        assignment = TrailAssignment.objects.create(
            trail=self.trail,
            user=self.user,
            is_mandatory=True,
            compliance_type='external',
            due_at=timezone.now() + timedelta(days=14)
        )
        self.assertTrue(assignment.is_mandatory)
        self.assertEqual(assignment.compliance_type, 'external')

    def test_trail_assignment_stakeholder_compliance(self):
        """Test stakeholder/manager compliance assignment."""
        assignment = TrailAssignment.objects.create(
            trail=self.trail,
            user=self.user,
            is_mandatory=True,
            compliance_type='stakeholder',
            due_at=timezone.now() + timedelta(days=3)
        )
        self.assertTrue(assignment.is_mandatory)
        self.assertEqual(assignment.compliance_type, 'stakeholder')

    def test_trail_assignment_compliance_completion(self):
        """Test completing a mandatory compliance trail."""
        now = timezone.now()
        assignment = TrailAssignment.objects.create(
            trail=self.trail,
            user=self.user,
            is_mandatory=True,
            compliance_type='internal',
            assigned_at=now,
            due_at=now + timedelta(days=7)
        )

        # User starts
        assignment.started_at = now + timedelta(hours=1)
        assignment.save()
        self.assertIsNotNone(assignment.started_at)

        # User completes
        assignment.completed_at = now + timedelta(hours=2)
        assignment.save()
        self.assertIsNotNone(assignment.completed_at)
        self.assertEqual((assignment.completed_at - assignment.started_at).total_seconds(), 3600)

    def test_trail_assignment_mandatory_with_revocation(self):
        """Test that mandatory assignments can be revoked with reason."""
        assignment = TrailAssignment.objects.create(
            trail=self.trail,
            user=self.user,
            is_mandatory=True,
            compliance_type='internal'
        )

        # Revoke assignment
        assignment.revoked_at = timezone.now()
        assignment.revocation_reason = 'User left company'
        assignment.save()

        self.assertIsNotNone(assignment.revoked_at)
        self.assertEqual(assignment.revocation_reason, 'User left company')


class ComplianceIntegrationTestCase(TestCase):
    """Test integration of Membership and TrailAssignment compliance."""

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org', slug='test-org')
        self.company = Company.objects.create(organization=self.org, name='Test Company')
        self.user = User.objects.create_user(
            email=f'user-{timezone.now().timestamp()}@test.com',
            username=f'user_{timezone.now().timestamp()}',
            password='testpass123'
        )
        self.trail = ContentTrail.objects.create(
            organization=self.org,
            title='Compliance Trail',
            slug='compliance-trail',
            trail_type='required',
            status='published',
            owner=self.user
        )

    def test_membership_and_trail_assignment_sync(self):
        """Test that membership compliance status reflects trail assignments."""
        # Create membership with pending compliance
        membership = Membership.objects.create(
            user=self.user,
            organization=self.org,
            company=self.company,
            role='member',
            compliance_status='pending',
            compliance_due_date=timezone.now() + timedelta(days=30)
        )

        # Create mandatory trail assignment
        assignment = TrailAssignment.objects.create(
            trail=self.trail,
            user=self.user,
            is_mandatory=True,
            compliance_type='internal',
            due_at=membership.compliance_due_date
        )

        # Start the trail
        assignment.started_at = timezone.now()
        assignment.save()

        # Update membership to in_progress
        membership.compliance_status = 'in_progress'
        membership.save()

        # Complete the trail
        assignment.completed_at = timezone.now()
        assignment.save()

        # Update membership to completed
        membership.compliance_status = 'completed'
        membership.compliance_completed_at = timezone.now()
        membership.save()

        # Verify both are in sync
        self.assertEqual(membership.compliance_status, 'completed')
        self.assertIsNotNone(assignment.completed_at)

    def test_multiple_memberships_same_user_different_orgs(self):
        """Test user with multiple memberships in different organizations."""
        org2 = Organization.objects.create(name='Test Org 2', slug='test-org-2')
        company2 = Company.objects.create(organization=org2, name='Test Company 2')

        # Membership in org1
        mem1 = Membership.objects.create(
            user=self.user,
            organization=self.org,
            company=self.company,
            role='member',
            compliance_status='pending'
        )

        # Membership in org2
        mem2 = Membership.objects.create(
            user=self.user,
            organization=org2,
            company=company2,
            role='admin',
            compliance_status='completed',
            compliance_completed_at=timezone.now()
        )

        # Verify both memberships have correct compliance status
        self.assertEqual(mem1.compliance_status, 'pending')
        self.assertEqual(mem2.compliance_status, 'completed')

        # Verify user has both memberships
        user_memberships = self.user.memberships.all()
        self.assertEqual(user_memberships.count(), 2)

    def test_compliance_metrics_query(self):
        """Test querying compliance metrics."""
        # Create multiple users with different compliance statuses
        users = []
        statuses = ['pending', 'in_progress', 'completed', 'overdue']

        for idx, status in enumerate(statuses):
            user = User.objects.create_user(
                email=f'user-{idx}-{timezone.now().timestamp()}@test.com',
                username=f'user_{idx}_{timezone.now().timestamp()}',
                password='testpass123'
            )
            Membership.objects.create(
                user=user,
                organization=self.org,
                company=self.company,
                role='member',
                compliance_status=status,
                compliance_due_date=timezone.now() + timedelta(days=30)
            )
            users.append(user)

        # Query compliance metrics
        pending_count = Membership.objects.filter(
            organization=self.org,
            compliance_status='pending'
        ).count()

        completed_count = Membership.objects.filter(
            organization=self.org,
            compliance_status='completed'
        ).count()

        self.assertEqual(pending_count, 1)
        self.assertEqual(completed_count, 1)
