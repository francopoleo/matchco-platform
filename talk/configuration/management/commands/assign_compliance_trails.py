from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from configuration.models import Organization, Membership
from learning.models import ContentTrail, TrailAssignment


class Command(BaseCommand):
    help = 'Auto-assign compliance trails based on membership type'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org',
            type=str,
            help='Organization slug (if empty, run for all private orgs)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be assigned without making changes'
        )

    def handle(self, *args, **options):
        org_slug = options.get('org')
        dry_run = options.get('dry_run', False)

        if org_slug:
            orgs = Organization.objects.filter(slug=org_slug)
            if not orgs.exists():
                self.stdout.write(self.style.ERROR(f'Organization "{org_slug}" not found'))
                return
        else:
            orgs = Organization.objects.filter(is_public=False)

        for org in orgs:
            self.assign_compliance_trails(org, dry_run)

    def assign_compliance_trails(self, org, dry_run):
        """Assign compliance trails to all active memberships"""

        # Get compliance trail templates
        compliance_trails = {}
        trail_slugs = {
            'internal': 'compliance-internal-employee',
            'external': 'compliance-external-partner',
            'stakeholder': 'compliance-stakeholder',
        }

        for comp_type, slug in trail_slugs.items():
            try:
                trail = ContentTrail.objects.get(slug=slug, status='published')
                compliance_trails[comp_type] = trail
            except ContentTrail.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Trail not found for {comp_type} (slug: {slug})')
                )

        memberships = org.memberships.filter(active=True).select_related('user')

        assigned_count = 0
        skipped_count = 0

        for membership in memberships:
            # Determine compliance type based on role and organization
            if org.is_public:
                compliance_type = 'external'
            elif membership.role in ['admin', 'owner']:
                compliance_type = 'stakeholder'
            else:
                compliance_type = 'internal'

            trail = compliance_trails.get(compliance_type)

            if not trail:
                skipped_count += 1
                continue

            # Check if already assigned
            if TrailAssignment.objects.filter(
                user=membership.user,
                trail=trail
            ).exists():
                continue

            if not dry_run:
                due_at = timezone.now() + timedelta(days=30)

                # Assign trail
                assignment = TrailAssignment.objects.create(
                    user=membership.user,
                    trail=trail,
                    is_mandatory=True,
                    compliance_type=compliance_type,
                    due_at=due_at,
                )

                # Update membership
                membership.compliance_status = 'pending'
                membership.compliance_due_date = due_at
                membership.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Assigned {trail.title} to {membership.user.email} '
                        f'({compliance_type}, due {due_at.strftime("%d/%m/%Y")})'
                    )
                )

                assigned_count += 1
            else:
                self.stdout.write(
                    f'[DRY-RUN] Would assign {trail.title} to {membership.user.email} '
                    f'({compliance_type})'
                )

                assigned_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Summary for {org.name}:\n'
                f'  • Assigned: {assigned_count}\n'
                f'  • Skipped (no trail): {skipped_count}'
            )
        )
