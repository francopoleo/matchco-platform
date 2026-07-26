from django.core.management.base import BaseCommand
from configuration.models import Organization


class Command(BaseCommand):
    help = 'Create virtual public organizations for external users'

    def handle(self, *args, **options):
        orgs = [
            ('Public - Candidates', 'public-candidates', 'Job applicants & hiring process'),
            ('Public - Doctors', 'public-doctors', 'Medical professionals learning'),
            ('Public - Partners', 'public-partners', 'Integration partners & resellers'),
            ('Public - Students', 'public-students', 'Public course learners'),
        ]

        for name, slug, description in orgs:
            org, created = Organization.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'description': description,
                    'is_public': True,
                }
            )
            if not created and not org.description:
                org.description = description
                org.save()
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f'✅ {status}: {name}')

        self.stdout.write(self.style.SUCCESS('✓ Public organizations ready!'))
