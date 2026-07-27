from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from configuration.models import Organization, Company, UserGroup, GroupMembership, GroupAccess

User = get_user_model()


class UserGroupTestCase(TestCase):
    """Test UserGroup model."""

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org', slug='test-org')
        self.user = User.objects.create_user(
            email='test@test.com',
            username='testuser',
            password='testpass123'
        )

    def test_create_parents_group(self):
        """Test creating a parents/guardians group."""
        group = UserGroup.objects.create(
            organization=self.org,
            name='School Parents',
            slug='school-parents',
            group_type='parents',
            description='Parents of students at School A',
            metadata={'school_name': 'School A'}
        )

        self.assertEqual(group.name, 'School Parents')
        self.assertEqual(group.group_type, 'parents')
        self.assertEqual(group.organization, self.org)
        self.assertEqual(group.metadata['school_name'], 'School A')

    def test_create_alumni_group(self):
        """Test creating an alumni group."""
        group = UserGroup.objects.create(
            organization=self.org,
            name='Class of 2020',
            slug='class-2020',
            group_type='alumni',
            metadata={'graduation_year': 2020}
        )

        self.assertEqual(group.group_type, 'alumni')
        self.assertEqual(group.metadata['graduation_year'], 2020)

    def test_create_department_group(self):
        """Test creating a department group."""
        group = UserGroup.objects.create(
            organization=self.org,
            name='Engineering',
            slug='engineering',
            group_type='department',
            description='Engineering Department'
        )

        self.assertEqual(group.group_type, 'department')
        self.assertEqual(group.get_group_type_display(), 'Department')

    def test_custom_group(self):
        """Test creating a custom group."""
        group = UserGroup.objects.create(
            organization=self.org,
            name='Custom Audience',
            slug='custom-group',
            group_type='custom'
        )

        self.assertEqual(group.group_type, 'custom')

    def test_unique_slug_per_organization(self):
        """Test that slug must be unique per organization."""
        UserGroup.objects.create(
            organization=self.org,
            name='Group 1',
            slug='group-slug',
            group_type='custom'
        )

        with self.assertRaises(Exception):
            UserGroup.objects.create(
                organization=self.org,
                name='Group 2',
                slug='group-slug',
                group_type='custom'
            )

    def test_different_orgs_can_have_same_slug(self):
        """Test that different orgs can use the same slug."""
        org2 = Organization.objects.create(name='Test Org 2', slug='test-org-2')

        group1 = UserGroup.objects.create(
            organization=self.org,
            name='Group 1',
            slug='same-slug',
            group_type='custom'
        )

        group2 = UserGroup.objects.create(
            organization=org2,
            name='Group 1',
            slug='same-slug',
            group_type='custom'
        )

        self.assertNotEqual(group1.organization, group2.organization)


class GroupMembershipTestCase(TestCase):
    """Test GroupMembership model."""

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org', slug='test-org')
        self.group = UserGroup.objects.create(
            organization=self.org,
            name='Test Group',
            slug='test-group',
            group_type='custom'
        )
        self.user1 = User.objects.create_user(email='user1@test.com', username='user1', password='pass')
        self.user2 = User.objects.create_user(email='user2@test.com', username='user2', password='pass')
        self.admin = User.objects.create_user(email='admin@test.com', username='admin', password='pass')

    def test_add_member_to_group(self):
        """Test adding a member to a group."""
        membership = GroupMembership.objects.create(
            user=self.user1,
            group=self.group,
            role='member',
            status='active',
            created_by=self.admin
        )

        self.assertEqual(membership.user, self.user1)
        self.assertEqual(membership.group, self.group)
        self.assertEqual(membership.role, 'member')
        self.assertEqual(membership.status, 'active')

    def test_group_admin_role(self):
        """Test group admin role."""
        membership = GroupMembership.objects.create(
            user=self.user1,
            group=self.group,
            role='admin',
            created_by=self.admin
        )

        self.assertEqual(membership.role, 'admin')
        self.assertEqual(membership.get_role_display(), 'Group Admin')

    def test_viewer_role(self):
        """Test viewer-only role."""
        membership = GroupMembership.objects.create(
            user=self.user1,
            group=self.group,
            role='viewer',
            created_by=self.admin
        )

        self.assertEqual(membership.role, 'viewer')

    def test_pending_approval_status(self):
        """Test pending approval status."""
        membership = GroupMembership.objects.create(
            user=self.user1,
            group=self.group,
            status='pending',
            created_by=self.admin
        )

        self.assertEqual(membership.status, 'pending')

    def test_inactive_membership(self):
        """Test inactive membership status."""
        membership = GroupMembership.objects.create(
            user=self.user1,
            group=self.group,
            status='inactive',
            created_by=self.admin
        )

        self.assertEqual(membership.status, 'inactive')

    def test_linked_user_for_parents(self):
        """Test linking a student user for parent groups."""
        student = User.objects.create_user(email='student@test.com', username='student', password='pass')

        membership = GroupMembership.objects.create(
            user=self.user1,
            group=self.group,
            linked_user=student,
            created_by=self.admin
        )

        self.assertEqual(membership.linked_user, student)

    def test_unique_user_per_group(self):
        """Test that a user can only join a group once."""
        GroupMembership.objects.create(
            user=self.user1,
            group=self.group,
            created_by=self.admin
        )

        with self.assertRaises(Exception):
            GroupMembership.objects.create(
                user=self.user1,
                group=self.group,
                created_by=self.admin
            )

    def test_multiple_users_in_group(self):
        """Test adding multiple users to the same group."""
        GroupMembership.objects.create(user=self.user1, group=self.group, created_by=self.admin)
        GroupMembership.objects.create(user=self.user2, group=self.group, created_by=self.admin)

        members = self.group.members.filter(status='active')
        self.assertEqual(members.count(), 2)

    def test_member_count_by_status(self):
        """Test counting active members."""
        GroupMembership.objects.create(
            user=self.user1,
            group=self.group,
            status='active',
            created_by=self.admin
        )
        GroupMembership.objects.create(
            user=self.user2,
            group=self.group,
            status='inactive',
            created_by=self.admin
        )

        active_members = self.group.members.filter(status='active').count()
        self.assertEqual(active_members, 1)


class GroupAccessTestCase(TestCase):
    """Test GroupAccess model."""

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org', slug='test-org')
        self.group = UserGroup.objects.create(
            organization=self.org,
            name='Test Group',
            slug='test-group',
            group_type='custom'
        )
        self.user = User.objects.create_user(email='user@test.com', username='user', password='pass')

    def test_view_only_access_to_trail(self):
        """Test granting view-only access to a trail."""
        access = GroupAccess.objects.create(
            group=self.group,
            content_type='trail',
            object_id=1,
            access_level='view',
            created_by=self.user
        )

        self.assertEqual(access.content_type, 'trail')
        self.assertEqual(access.object_id, 1)
        self.assertEqual(access.access_level, 'view')

    def test_full_access_to_organization_content(self):
        """Test granting full access to all organization content."""
        access = GroupAccess.objects.create(
            group=self.group,
            content_type='organization',
            object_id=None,
            access_level='manage',
            created_by=self.user
        )

        self.assertEqual(access.content_type, 'organization')
        self.assertIsNone(access.object_id)
        self.assertEqual(access.access_level, 'manage')

    def test_download_access_to_course(self):
        """Test granting download access to a course."""
        access = GroupAccess.objects.create(
            group=self.group,
            content_type='course',
            object_id=5,
            access_level='download',
            created_by=self.user
        )

        self.assertEqual(access.access_level, 'download')

    def test_view_progress_access(self):
        """Test view progress access level."""
        access = GroupAccess.objects.create(
            group=self.group,
            content_type='publication',
            object_id=10,
            access_level='view_progress',
            created_by=self.user
        )

        self.assertEqual(access.get_access_level_display(), 'View Progress')

    def test_no_access_level(self):
        """Test no access level."""
        access = GroupAccess.objects.create(
            group=self.group,
            content_type='trail',
            object_id=1,
            access_level='none',
            created_by=self.user
        )

        self.assertEqual(access.access_level, 'none')

    def test_unique_access_per_content(self):
        """Test that access rule is unique per content."""
        GroupAccess.objects.create(
            group=self.group,
            content_type='trail',
            object_id=1,
            access_level='view',
            created_by=self.user
        )

        with self.assertRaises(Exception):
            GroupAccess.objects.create(
                group=self.group,
                content_type='trail',
                object_id=1,
                access_level='manage',
                created_by=self.user
            )

    def test_all_access_levels(self):
        """Test all access level choices."""
        levels = ['none', 'view', 'view_progress', 'download', 'manage']

        for idx, level in enumerate(levels):
            access = GroupAccess.objects.create(
                group=self.group,
                content_type='trail',
                object_id=idx + 100,
                access_level=level,
                created_by=self.user
            )
            self.assertEqual(access.access_level, level)

    def test_all_content_types(self):
        """Test all content type choices."""
        types = ['trail', 'course', 'publication', 'organization']

        for idx, ctype in enumerate(types):
            access = GroupAccess.objects.create(
                group=self.group,
                content_type=ctype,
                object_id=idx + 1,
                access_level='view',
                created_by=self.user
            )
            self.assertEqual(access.content_type, ctype)


class GroupIntegrationTestCase(TestCase):
    """Test integration scenarios with groups."""

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org', slug='test-org')
        self.parents_group = UserGroup.objects.create(
            organization=self.org,
            name='School Parents',
            slug='parents',
            group_type='parents',
            metadata={'school_name': 'Primary School'}
        )
        self.user = User.objects.create_user(email='user@test.com', username='user', password='pass')
        self.student = User.objects.create_user(email='student@test.com', username='student', password='pass')

    def test_parent_student_relationship(self):
        """Test parent-student linking via group membership."""
        membership = GroupMembership.objects.create(
            user=self.user,  # Parent
            group=self.parents_group,
            linked_user=self.student,  # Student
            created_by=self.user
        )

        # Verify relationship
        self.assertEqual(membership.user.email, 'user@test.com')
        self.assertEqual(membership.linked_user.email, 'student@test.com')

    def test_group_with_access_rules(self):
        """Test group with multiple access rules."""
        # Create 2 access rules
        GroupAccess.objects.create(
            group=self.parents_group,
            content_type='trail',
            object_id=1,
            access_level='view_progress',
            created_by=self.user
        )

        GroupAccess.objects.create(
            group=self.parents_group,
            content_type='course',
            object_id=1,
            access_level='view',
            created_by=self.user
        )

        # Verify rules
        rules = self.parents_group.access_rules.all()
        self.assertEqual(rules.count(), 2)

    def test_group_member_and_access_combination(self):
        """Test complete group setup with members and access."""
        # Add member
        GroupMembership.objects.create(
            user=self.user,
            group=self.parents_group,
            linked_user=self.student,
            created_by=self.user
        )

        # Grant access
        GroupAccess.objects.create(
            group=self.parents_group,
            content_type='organization',
            access_level='view_progress',
            created_by=self.user
        )

        # Verify
        group = UserGroup.objects.get(slug='parents')
        self.assertEqual(group.members.count(), 1)
        self.assertEqual(group.access_rules.count(), 1)
