"""Aplica política de retenção RT-01..RT-06 (SISTEMA_MATCHCO_CANONICO §6.2).

Uso:
    python manage.py apply_retention               # dry-run
    python manage.py apply_retention --commit      # aplica
"""
from django.core.management.base import BaseCommand

from recruitment.services import apply_retention_policy


class Command(BaseCommand):
    help = 'Aplica classes de retenção RT-01..RT-06.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--commit', action='store_true',
            help='Executa; sem essa flag, apenas relata (dry-run).',
        )

    def handle(self, *args, **options):
        commit = options['commit']
        report = apply_retention_policy(dry_run=not commit)
        self.stdout.write(self.style.SUCCESS(
            f"Retenção {'aplicada' if commit else 'DRY-RUN'} em {report['now']}"
        ))
        for cls, action in report['actions'].items():
            self.stdout.write(f'  {cls}: {action}')