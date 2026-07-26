from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from django.contrib.auth import get_user_model
from io import StringIO

from configuration.models import Organization, Company, Membership
from learning.models import ContentTrail, TrailAssignment

User = get_user_model()


class ComplianceAutoAssignmentTestCase(TestCase):
    """Test compliance trail auto-assignment functionality."""

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org', slug='test-org', is_public=False)
        self.company = Company.objects.create(organization=self.org, name='Test Company')

        # Create compliance trails
        self.internal_trail = ContentTrail.objects.create(
            organization=self.org,
            title='Internal Employee Compliance',
            slug='compliance-internal-employee',
            trail_type='required',
            status='published',
            owner=self._create_user('admin@test.com')
        )

        self.external_trail = ContentTrail.objects.create(
            organization=self.org,
            title='External Partner Compliance',
            slug='compliance-external-partner',
            trail_type='required',
            status='published',
            owner=self._create_user('admin2@test.com')
        )

        self.stakeholder_trail = ContentTrail.objects.create(
            organization=self.org,
            title='Stakeholder Compliance',
            slug='compliance-stakeholder',
            trail_type='required',
            status='published',
            owner=self._create_user('admin3@test.com')
        )

    def _create_user(self, email):
        """Helper to create a unique user."""
        username = email.split('@')[0]
        # Add timestamp if needed to avoid duplicates
        counter = 0
        base_username = username
        while User.objects.filter(username=username).exists():
            counter += 1
            username = f'{base_username}{counter}'

        return User.objects.create_user(
            email=email,
            username=username,
            password='testpass123'
        )

    def test_assign_internal_employee_compliance(self):
        """Test assigning internal employee compliance trail."""
        user = self._create_user('employee@test.com')
        membership = Membership.objects.create(
            user=user,
            organization=self.org,
            company=self.company,
            role='member',
            active=True
        )

        # Run command
        out = StringIO()
        call_command('assign_compliance_trails', '--org=test-org', stdout=out)

        # Verify assignment
        assignment = TrailAssignment.objects.get(user=user, trail=self.internal_trail)
        self.assertTrue(assignment.is_mandatory)
        self.assertEqual(assignment.compliance_type, 'internal')

        # Verify membership update
        membership.refresh_from_db()
        self.assertEqual(membership.compliance_status, 'pending')
        self.assertIsNotNone(membership.compliance_due_date)

    def test_assign_stakeholder_compliance(self):
        """Test assigning stakeholder compliance trail to admin."""
        user = self._create_user('admin@test.com')
        membership = Membership.objects.create(
            user=user,
            organization=self.org,
            company=self.company,
            role='admin',
            active=True
        )

        # Run command
        out = StringIO()
        call_command('assign_compliance_trails', '--org=test-org', stdout=out)

        # Verify assignment
        assignment = TrailAssignment.objects.get(user=user, trail=self.stakeholder_trail)
        self.assertTrue(assignment.is_mandatory)
        self.assertEqual(assignment.compliance_type, 'stakeholder')

    def test_skip_inactive_memberships(self):
        """Test that inactive memberships are not assigned."""
        user = self._create_user('inactive@test.com')
        membership = Membership.objects.create(
            user=user,
            organization=self.org,
            company=self.company,
            role='member',
            active=False
        )

        # Run command
        out = StringIO()
        call_command('assign_compliance_trails', '--org=test-org', stdout=out)

        # Verify no assignment
        self.assertFalse(TrailAssignment.objects.filter(user=user).exists())

    def test_skip_already_assigned(self):
        """Test that already assigned trails are not duplicated."""
        user = self._create_user('user@test.com')
        membership = Membership.objects.create(
            user=user,
            organization=self.org,
            company=self.company,
            role='member',
            active=True
        )

        # Pre-assign
        TrailAssignment.objects.create(
            user=user,
            trail=self.internal_trail,
            is_mandatory=True,
            compliance_type='internal'
        )

        # Run command
        out = StringIO()
        call_command('assign_compliance_trails', '--org=test-org', stdout=out)

        # Verify only one assignment
        assignments = TrailAssignment.objects.filter(user=user, trail=self.internal_trail)
        self.assertEqual(assignments.count(), 1)

    def test_dry_run_mode(self):
        """Test dry-run mode doesn't make changes."""
        user = self._create_user('dryrun@test.com')
        membership = Membership.objects.create(
            user=user,
            organization=self.org,
            company=self.company,
            role='member',
            active=True
        )

        # Run command with dry-run
        out = StringIO()
        call_command('assign_compliance_trails', '--org=test-org', '--dry-run', stdout=out)

        # Verify no actual assignment
        self.assertFalse(TrailAssignment.objects.filter(user=user).exists())

        # Verify membership not updated
        membership.refresh_from_db()
        self.assertEqual(membership.compliance_status, 'pending')
        self.assertIsNone(membership.compliance_due_date)

    def test_multiple_users_assignment(self):
        """Test assigning compliance to multiple users."""
        users = [
            self._create_user(f'user1@test.com'),
            self._create_user(f'user2@test.com'),
            self._create_user(f'user3@test.com'),
        ]

        for user in users:
            Membership.objects.create(
                user=user,
                organization=self.org,
                company=self.company,
                role='member',
                active=True
            )

        # Run command
        out = StringIO()
        call_command('assign_compliance_trails', '--org=test-org', stdout=out)

        # Verify all assigned
        for user in users:
            assignment = TrailAssignment.objects.get(user=user, trail=self.internal_trail)
            self.assertTrue(assignment.is_mandatory)

    def test_missing_trail_skips_user(self):
        """Test that users are skipped if their compliance trail is missing."""
        user = self._create_user('skip@test.com')
        Membership.objects.create(
            user=user,
            organization=self.org,
            company=self.company,
            role='member',
            active=True
        )

        # Delete the internal trail
        self.internal_trail.delete()

        # Run command
        out = StringIO()
        call_command('assign_compliance_trails', '--org=test-org', stdout=out)

        # Verify no assignment
        self.assertFalse(TrailAssignment.objects.filter(user=user).exists())

    def test_external_org_gets_external_compliance(self):
        """Test that external/public org users get external compliance type."""
        public_org = Organization.objects.create(
            name='Public Org',
            slug='public-org',
            is_public=True
        )
        company = Company.objects.create(organization=public_org, name='Test Company')

        user = self._create_user('external@test.com')
        Membership.objects.create(
            user=user,
            organization=public_org,
            company=company,
            role='member',
            active=True
        )

        # Run command
        out = StringIO()
        call_command('assign_compliance_trails', '--org=public-org', stdout=out)

        # Verify external compliance assigned
        assignment = TrailAssignment.objects.get(user=user, trail=self.external_trail)
        self.assertEqual(assignment.compliance_type, 'external')

    def test_nonexistent_org_slug(self):
        """Test command with non-existent organization slug."""
        out = StringIO()
        call_command('assign_compliance_trails', '--org=nonexistent', stdout=out)

        # Should complete without error but print error message
        output = out.getvalue()
        self.assertIn('not found', output)
