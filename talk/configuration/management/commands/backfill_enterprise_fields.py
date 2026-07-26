from django.core.management.base import BaseCommand
from django.db import transaction
from configuration.models import Membership, MembershipAudit


class Command(BaseCommand):
    help = 'Backfill enterprise user fields (created_by, is_primary constraint, audit trail)'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting backfill...'))

        # Step 1: Set created_by for memberships without one
        self.stdout.write('Step 1: Setting created_by for existing memberships...')
        memberships_updated = 0
        for membership in Membership.objects.filter(created_by__isnull=True):
            membership.created_by = membership.user
            membership.save(update_fields=['created_by'])
            memberships_updated += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Updated {memberships_updated} memberships'))

        # Step 2: Ensure each user has exactly 1 is_primary=True
        self.stdout.write('Step 2: Enforcing single primary membership per user...')
        fixed_count = 0

        # Get all users with memberships
        from django.contrib.auth import get_user_model
        User = get_user_model()

        for user in User.objects.filter(memberships__isnull=False).distinct():
            active_memberships = user.memberships.filter(active=True).order_by('-created_at')

            if not active_memberships.exists():
                continue

            # Check if user has a primary membership
            primary = active_memberships.filter(is_primary=True).first()

            if not primary:
                # No primary - set the first active (or oldest)
                first = active_memberships.order_by('created_at').first()
                first.is_primary = True
                first.save(update_fields=['is_primary'])
                fixed_count += 1
                self.stdout.write(f'  ✓ Set {user} primary membership to {first.organization}')
            else:
                # Has primary - remove is_primary from others
                other_primaries = active_memberships.filter(is_primary=True).exclude(id=primary.id)
                for other in other_primaries:
                    other.is_primary = False
                    other.save(update_fields=['is_primary'])
                    fixed_count += 1
                    self.stdout.write(f'  ✓ Removed primary flag from {user} in {other.organization}')

        self.stdout.write(self.style.SUCCESS(f'  ✓ Fixed {fixed_count} users'))

        # Step 3: Create audit logs for initial state
        self.stdout.write('Step 3: Creating initial audit logs...')
        audit_count = 0

        for membership in Membership.objects.all():
            if not MembershipAudit.objects.filter(membership=membership, action='created').exists():
                MembershipAudit.objects.create(
                    membership=membership,
                    user=membership.created_by or membership.user,
                    action='created',
                    new_values={
                        'role': membership.role,
                        'is_primary': membership.is_primary,
                        'active': membership.active,
                    },
                    reason='Initial backfill from migration',
                )
                audit_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {audit_count} audit logs'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n✓ Backfill complete!'))
        self.stdout.write(f'  • Memberships updated: {memberships_updated}')
        self.stdout.write(f'  • Users fixed: {fixed_count}')
        self.stdout.write(f'  • Audit logs created: {audit_count}')
