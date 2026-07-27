"""
Generic command to synchronize group hierarchies based on auto_create_on triggers.

Examples:
  # Sync all hierarchies with auto_create_on='graduation'
  python manage.py sync_group_hierarchies --trigger graduation

  # Sync for specific organization
  python manage.py sync_group_hierarchies --trigger graduation --org hospital-generative

  # Dry run (show what would happen)
  python manage.py sync_group_hierarchies --trigger graduation --dry-run
"""

from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from configuration.models import Organization, GroupHierarchyType, GroupNode, UserGroupMembership
from learning.models import TrailProgress

User = get_user_model()


class Command(BaseCommand):
    help = 'Synchronize group hierarchies based on auto_create_on triggers (generic replacement for convert_alumni)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--trigger',
            type=str,
            required=True,
            help='Auto-create trigger to process (e.g., "graduation")'
        )
        parser.add_argument(
            '--org',
            type=str,
            help='Organization slug (process all if not specified)'
        )
        parser.add_argument(
            '--graduation-date',
            type=str,
            default=None,
            help='Graduation date for graduation trigger (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would happen without making changes'
        )

    def handle(self, *args, **options):
        trigger = options.get('trigger')
        org_slug = options.get('org')
        graduation_date_str = options.get('graduation_date')
        dry_run = options.get('dry_run', False)

        self.stdout.write(self.style.SUCCESS(f'\n🔄 Syncing hierarchies with trigger: {trigger}'))
        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY-RUN MODE]'))
        self.stdout.write('')

        # Get hierarchy types with this trigger
        hierarchy_types = GroupHierarchyType.objects.filter(auto_create_on=trigger, active=True)

        if org_slug:
            hierarchy_types = hierarchy_types.filter(organization__slug=org_slug)

        if not hierarchy_types.exists():
            self.stdout.write(self.style.WARNING(f'⚠️  No hierarchy types found with trigger: {trigger}'))
            return

        self.stdout.write(f'Found {hierarchy_types.count()} hierarchy type(s) with trigger "{trigger}"')
        self.stdout.write('')

        total_processed = 0
        total_created = 0

        for ht in hierarchy_types:
            self.stdout.write(f'Processing: {ht.name} (org: {ht.organization.name})')

            if trigger == 'graduation':
                self._handle_graduation_trigger(ht, graduation_date_str, dry_run)
            elif trigger == 'none':
                self.stdout.write('  ℹ️  Trigger set to "none" - skipping auto-creation')
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠️  Unknown trigger: {trigger}'))

            self.stdout.write('')

        self.stdout.write(self.style.SUCCESS('✅ Synchronization complete!\n'))

    def _handle_graduation_trigger(self, hierarchy_type, graduation_date_str, dry_run):
        """Handle graduation trigger: create alumni groups by year."""

        if not graduation_date_str:
            self.stdout.write(self.style.ERROR('  ❌ --graduation-date required for graduation trigger (YYYY-MM-DD)'))
            return

        try:
            graduation_date = datetime.strptime(graduation_date_str, '%Y-%m-%d').date()
        except ValueError:
            self.stdout.write(self.style.ERROR(f'  ❌ Invalid date format: {graduation_date_str} (use YYYY-MM-DD)'))
            return

        # Find users who completed trails by graduation date
        completed_users = User.objects.filter(
            trail_assignments__completed_at__isnull=False,
            trail_assignments__completed_at__date__lte=graduation_date
        ).distinct()

        self.stdout.write(f'  Found {completed_users.count()} user(s) with completed trails')

        if not completed_users.exists():
            self.stdout.write('  ℹ️  No users to process')
            return

        # Process each user
        created_count = 0
        for user in completed_users:
            # Create or get node for graduation year
            year = graduation_date.year
            node_code = f'alumni-{year}'
            node_name = f'Alumni {year}'

            if not dry_run:
                node, created = GroupNode.objects.get_or_create(
                    hierarchy_type=hierarchy_type,
                    code=node_code,
                    defaults={
                        'parent_node': None,
                        'name': node_name,
                        'level': 1,
                        'metadata': {'graduation_year': year},
                        'active': True
                    }
                )

                # Add user to alumni group
                membership, member_created = UserGroupMembership.objects.get_or_create(
                    user=user,
                    group_node=node,
                    defaults={
                        'role': 'member',
                        'status': 'active',
                        'created_by': user
                    }
                )

                if member_created:
                    self.stdout.write(f'    ✓ {user.email} → {node_name}')
                    created_count += 1
                else:
                    self.stdout.write(f'    ℹ️  {user.email} already in {node_name}')
            else:
                self.stdout.write(f'    [DRY-RUN] Would add {user.email} → Alumni {year}')
                created_count += 1

        self.stdout.write(f'  ✅ Processed {created_count} membership(s)')
