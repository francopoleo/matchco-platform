from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone

from configuration.models import UserGroup, GroupMembership, Membership
from learning.models import TrailProgress

User = get_user_model()


class Command(BaseCommand):
    help = 'Convert graduated students to alumni status'

    def add_arguments(self, parser):
        parser.add_argument(
            'graduation_date',
            type=str,
            help='Graduation date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--org',
            type=str,
            help='Organization slug (if empty, run for all)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be converted without making changes'
        )

    def handle(self, *args, **options):
        graduation_date_str = options['graduation_date']
        org_slug = options.get('org')
        dry_run = options.get('dry_run', False)

        # Parse graduation date
        try:
            graduation_date = datetime.strptime(graduation_date_str, '%Y-%m-%d').date()
        except ValueError:
            raise CommandError(f'Invalid date format: {graduation_date_str}. Use YYYY-MM-DD')

        # Get memberships to convert
        memberships = Membership.objects.filter(
            active=True,
        ).select_related('user', 'organization')

        if org_slug:
            memberships = memberships.filter(organization__slug=org_slug)

        # Find users who completed trails before graduation date
        converted_count = 0
        skipped_count = 0

        for membership in memberships:
            user = membership.user

            # Check if user completed any trails before graduation date
            completed_trails = TrailProgress.objects.filter(
                assignment__user=user,
                completed_at__isnull=False,
                completed_at__date__lte=graduation_date
            ).exists()

            if not completed_trails:
                skipped_count += 1
                continue

            if not dry_run:
                # Downgrade membership role to viewer
                if membership.role != 'viewer':
                    old_role = membership.get_role_display()
                    membership.role = 'viewer'
                    membership.save()
                    self.stdout.write(
                        f'  Role changed: {old_role} → Viewer'
                    )

                # Create or get alumni group for graduation year
                graduation_year = graduation_date.year
                alumni_group, created = UserGroup.objects.get_or_create(
                    organization=membership.organization,
                    slug=f'alumni-{graduation_year}',
                    defaults={
                        'name': f'Alumni {graduation_year}',
                        'group_type': 'alumni',
                        'description': f'Graduates from {graduation_year}',
                        'metadata': {'graduation_year': graduation_year}
                    }
                )

                # Add user to alumni group
                group_membership, _ = GroupMembership.objects.get_or_create(
                    user=user,
                    group=alumni_group,
                    defaults={'role': 'member', 'status': 'active', 'created_by': user}
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Converted {user.email} to alumni '
                        f'({graduation_year}, {membership.organization.name})'
                    )
                )

                converted_count += 1
            else:
                self.stdout.write(
                    f'[DRY-RUN] Would convert {user.email} to alumni '
                    f'({graduation_date.year})'
                )
                converted_count += 1

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Summary:\n'
                f'  • Converted: {converted_count}\n'
                f'  • Skipped (no completed trails): {skipped_count}\n'
                f'  • Graduation date: {graduation_date_str}'
            )
        )
