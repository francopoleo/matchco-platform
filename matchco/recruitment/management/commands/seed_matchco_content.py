"""Canonical development seed for tenant content, independent of recruitment."""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Cria somente conteúdo do tenant (cursos, feed, wiki e documentos).'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', default='bourbon-shopping', help='Schema do tenant que receberá o conteúdo.')

    def handle(self, *args, **options):
        call_command('seed_bourbon_tenant_content', tenant=options['tenant'])
        self.stdout.write(self.style.SUCCESS('Seed de conteúdo concluído. Recrutamento não foi criado.'))
