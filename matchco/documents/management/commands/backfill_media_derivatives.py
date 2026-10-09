from django.core.management.base import BaseCommand
from django_tenants.utils import get_tenant_model, schema_context

from documents.models import MediaAsset
from documents.services import generate_media_derivatives


class Command(BaseCommand):
    help = 'Gera miniaturas WebP/AVIF e dimensões para imagens existentes.'

    def handle(self, *args, **options):
        generated = skipped = 0
        for tenant in get_tenant_model().objects.exclude(schema_name='public'):
            with schema_context(tenant.schema_name):
                for asset in MediaAsset.objects.filter(kind=MediaAsset.IMAGE).exclude(file='').iterator():
                    if asset.preview_file and asset.webp_file and asset.avif_file:
                        skipped += 1
                        continue
                    if generate_media_derivatives(asset):
                        generated += 1
        self.stdout.write(self.style.SUCCESS(f'{generated} imagem(ns) processada(s); {skipped} já possuíam derivados.'))
