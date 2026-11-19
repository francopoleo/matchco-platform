"""Move QR canonical URLs between public domains without changing QR identity.

Usage:
    python manage.py repoint_qr_codes
    python manage.py repoint_qr_codes --apply
"""

from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from recruitment.models import EntryPoint


class Command(BaseCommand):
    help = 'Atualiza URLs canônicas de QR de um domínio público antigo para o atual.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-host',
            default='esx.ddns.net',
            help='Domínio antigo a ser localizado (padrão: esx.ddns.net).',
        )
        parser.add_argument(
            '--to-base',
            default=getattr(settings, 'QR_CODE_BASE_URL', ''),
            help='Base HTTPS do novo domínio (padrão: QR_CODE_BASE_URL).',
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Grava as alterações. Sem esta opção, apenas exibe a prévia.',
        )

    def handle(self, *args, **options):
        old_host = options['from_host'].strip().lower().rstrip('/')
        target = urlparse(options['to_base'].strip().rstrip('/'))
        if target.scheme != 'https' or not target.netloc:
            raise CommandError('--to-base precisa ser uma URL HTTPS completa.')

        changes = []
        for entry_point in EntryPoint.objects.all().order_by('pk'):
            current = urlparse(entry_point.canonical_destination_url or '')
            if current.hostname != old_host or not current.path.startswith('/qr/'):
                continue
            replacement = urlunparse((
                target.scheme,
                target.netloc,
                current.path,
                current.params,
                current.query,
                current.fragment,
            ))
            if replacement != entry_point.canonical_destination_url:
                changes.append((entry_point, replacement))

        if not changes:
            self.stdout.write(self.style.SUCCESS('Nenhum QR com domínio antigo foi encontrado.'))
            return

        mode = 'APLICANDO' if options['apply'] else 'PRÉVIA'
        self.stdout.write(f'{mode}: {len(changes)} QR(s) serão atualizados.')
        with transaction.atomic():
            for entry_point, replacement in changes:
                self.stdout.write(
                    f'{entry_point.pk} | {entry_point.canonical_destination_url} -> {replacement}'
                )
                if options['apply']:
                    entry_point.canonical_destination_url = replacement
                    entry_point.save(update_fields=['canonical_destination_url', 'updated_at'])

        if not options['apply']:
            self.stdout.write('Nada foi gravado. Rode novamente com --apply para confirmar.')
        else:
            self.stdout.write(self.style.SUCCESS('URLs canônicas atualizadas; gere os PNGs/cartazes no Console.'))
