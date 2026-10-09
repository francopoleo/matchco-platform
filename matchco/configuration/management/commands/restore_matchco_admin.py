from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from configuration.models import Membership, Organization


class Command(BaseCommand):
    help = 'Restaura o usuário admin de desenvolvimento sem limpar dados.'

    def add_arguments(self, parser):
        parser.add_argument('--password', default='admin', help='Senha do admin de desenvolvimento.')

    def handle(self, *args, **options):
        User = get_user_model()
        admin, _ = User.objects.update_or_create(
            username='admin',
            defaults={
                'email': 'admin@matchco.local',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            },
        )
        admin.set_password(options['password'])
        admin.save(update_fields=['password', 'email', 'is_staff', 'is_superuser', 'is_active'])
        organization = Organization.objects.filter(slug='bourbon-shopping').first()
        if organization:
            Membership.objects.update_or_create(
                user=admin,
                organization=organization,
                defaults={'role': 'admin', 'active': True, 'is_primary': True},
            )
        self.stdout.write(self.style.SUCCESS('Usuário admin restaurado: admin'))
