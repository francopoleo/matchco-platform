from django.core.management.base import BaseCommand
from django_tenants.utils import get_tenant_model, schema_context

from documents.models import DocumentVersion
from documents.services import generate_document_thumbnail


class Command(BaseCommand):
    help = 'Gera miniaturas para PDFs, imagens e conteúdos HTML das versões documentais.'

    def handle(self, *args, **options):
        generated = skipped = 0
        for tenant in get_tenant_model().objects.exclude(schema_name='public'):
            with schema_context(tenant.schema_name):
                for version in DocumentVersion.objects.all().iterator():
                    if version.thumbnail_file:
                        skipped += 1
                        continue
                    if generate_document_thumbnail(version):
                        generated += 1
        self.stdout.write(self.style.SUCCESS(f'{generated} documento(s) processado(s); {skipped} já possuíam miniatura.'))
