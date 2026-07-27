"""
DEPRECATED: This command is replaced by Phase 3.3B generic hierarchy system.

Instead of using this command, configure alumni auto-creation via Django admin:

1. Create GroupHierarchyType with code='alumni'
2. Set auto_create_on='graduation' (or trigger via signal)
3. Configure GroupHierarchyTerminology with labels

Or create alumni groups manually via Django admin:
  Configuration > Group Hierarchy Types > Create new type

See PHASE_3_3B_GENERIC_GROUPS_ARCHITECTURE.md for details.
"""

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'DEPRECATED: Use Phase 3.3B generic hierarchy system instead. See docs/PHASE_3_3B_GENERIC_GROUPS_ARCHITECTURE.md'

    def add_arguments(self, parser):
        parser.add_argument('graduation_date', type=str, help='Graduation date (YYYY-MM-DD)')
        parser.add_argument('--org', type=str, help='Organization slug')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be converted')

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                '❌ DEPRECATED: convert_alumni command is no longer supported.\n\n'
                'Phase 3.3B replaces this with a generic hierarchy system managed via Django admin.\n\n'
                'To create alumni groups:\n'
                '  1. Go to Django Admin > Configuration > Group Hierarchy Types\n'
                '  2. Create a new type with code="alumni", name="Alumni"\n'
                '  3. Set auto_create_on="graduation" to auto-trigger on graduation signal\n'
                '  4. Configure labels via Group Hierarchy Terminology\n\n'
                'See: docs/PHASE_3_3B_GENERIC_GROUPS_ARCHITECTURE.md\n'
            )
        )
        raise CommandError('This command is deprecated. Use Phase 3.3B generic system.')
