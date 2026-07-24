from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from audience.models import AudiencePolicy, AudienceRule
from publishing.models import Publication
from user_management.models import User


class Command(BaseCommand):
    help = 'Creates idempotent Feed/Wiki records for console and audience testing.'

    def add_arguments(self, parser):
        parser.add_argument('--email', help='Author email; defaults to the first staff user.')

    def handle(self, *args, **options):
        email = options.get('email')
        author = User.objects.filter(email=email).first() if email else None
        author = author or User.objects.filter(is_staff=True).order_by('id').first()
        if not author:
            raise CommandError('Create a staff user first or pass --email.')

        manager_policy, _ = AudiencePolicy.objects.update_or_create(
            name='Demo - gestores',
            defaults={
                'description': 'Conteúdo de demonstração exclusivo para gestores.',
                'match_mode': AudiencePolicy.ALL,
                'active': True,
            },
        )
        AudienceRule.objects.update_or_create(
            policy=manager_policy,
            dimension='is_staff',
            defaults={'operator': 'in', 'values': [True], 'negate': False, 'position': 0},
        )

        now = timezone.now()
        records = [
            {
                'kind': Publication.FEED,
                'slug': 'demo-novidades-da-plataforma',
                'title': 'Novidades da plataforma',
                'excerpt': 'Um exemplo de comunicado distribuído pelo novo console.',
                'body': 'Este registro demonstra a publicação de um comunicado no Feed.',
                'audience_policy': None,
            },
            {
                'kind': Publication.WIKI,
                'slug': 'demo-guia-para-gestores',
                'title': 'Guia para gestores',
                'excerpt': 'Um exemplo de conteúdo restrito por política de audiência.',
                'body': 'Este registro só deve aparecer para usuários gestores.',
                'audience_policy': manager_policy,
            },
        ]
        for data in records:
            policy = data.pop('audience_policy')
            Publication.objects.update_or_create(
                slug=data['slug'],
                defaults={
                    **data,
                    'author': author,
                    'audience_policy': policy,
                    'status': Publication.PUBLISHED,
                    'published_at': now,
                },
            )
        self.stdout.write(self.style.SUCCESS('Console demo data created/updated.'))
