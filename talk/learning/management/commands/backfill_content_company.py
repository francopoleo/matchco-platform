from django.core.management.base import BaseCommand
from learning.models import ContentTrail
from courses.models import Course
from publishing.models import Publication
from configuration.models import Company


class Command(BaseCommand):
    help = 'Backfill company_id for ContentTrail, Course, and Publication objects based on organization'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        self.stdout.write('Starting content company backfill...\n')

        # Backfill ContentTrail
        self.backfill_trails(dry_run)

        # Backfill Courses
        self.backfill_courses(dry_run)

        # Backfill Publications
        self.backfill_publications(dry_run)

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('✓ Backfill completed successfully!'))
        else:
            self.stdout.write(self.style.WARNING('✓ Dry-run completed - no changes made'))

    def backfill_trails(self, dry_run):
        self.stdout.write('\n📚 ContentTrail:')

        # Find trails without company_id
        trails_without_company = ContentTrail.objects.filter(
            company_id__isnull=True,
            organization_id__isnull=False
        )

        count = 0
        for trail in trails_without_company:
            # Get first company in this organization
            company = Company.objects.filter(
                organization_id=trail.organization_id,
                active=True
            ).first()

            if company:
                if not dry_run:
                    trail.company_id = company.id
                    trail.save()
                self.stdout.write(f'  ✓ {trail.title} → {company.name}')
                count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ {trail.title} - no active company found in org {trail.organization_id}'
                    )
                )

        self.stdout.write(f'  Total updated: {count}')

    def backfill_courses(self, dry_run):
        self.stdout.write('\n🎓 Course:')

        # Find courses without company_id
        courses_without_company = Course.objects.filter(
            company_id__isnull=True,
            organization_id__isnull=False
        )

        count = 0
        for course in courses_without_company:
            # Get first company in this organization
            company = Company.objects.filter(
                organization_id=course.organization_id,
                active=True
            ).first()

            if company:
                if not dry_run:
                    course.company_id = company.id
                    course.save()
                self.stdout.write(f'  ✓ {course.title} → {company.name}')
                count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ {course.title} - no active company found in org {course.organization_id}'
                    )
                )

        self.stdout.write(f'  Total updated: {count}')

    def backfill_publications(self, dry_run):
        self.stdout.write('\n📄 Publication:')

        # Find publications without company_id
        publications_without_company = Publication.objects.filter(
            company_id__isnull=True,
            organization_id__isnull=False
        )

        count = 0
        for pub in publications_without_company:
            # Get first company in this organization
            company = Company.objects.filter(
                organization_id=pub.organization_id,
                active=True
            ).first()

            if company:
                if not dry_run:
                    pub.company_id = company.id
                    pub.save()
                self.stdout.write(f'  ✓ {pub.title} → {company.name}')
                count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ {pub.title} - no active company found in org {pub.organization_id}'
                    )
                )

        self.stdout.write(f'  Total updated: {count}')
