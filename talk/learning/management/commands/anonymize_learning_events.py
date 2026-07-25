from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from documents.models import DocumentEvent
from learning.models import ContentEvent


class Command(BaseCommand):
    help = 'Anonimiza eventos antigos, preservando agregados sem manter identidade.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=730)

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=max(30, options['days']))
        content_count = ContentEvent.objects.filter(occurred_at__lt=cutoff, user__isnull=False).update(user=None, session_id='')
        document_count = DocumentEvent.objects.filter(occurred_at__lt=cutoff, user__isnull=False).update(user=None)
        self.stdout.write(self.style.SUCCESS(f'Eventos anonimizados: conteúdo={content_count}, documentos={document_count}.'))
