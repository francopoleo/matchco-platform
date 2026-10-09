import hashlib

from django.core.management.base import BaseCommand
from django_tenants.utils import get_tenant_model, schema_context

from documents.models import MediaAsset


class Command(BaseCommand):
    help = 'Preenche MIME, tamanho e checksum das mídias existentes.'

    def handle(self, *args, **options):
        updated = 0
        missing = 0
        tenants = get_tenant_model().objects.exclude(schema_name='public')
        for tenant in tenants:
            with schema_context(tenant.schema_name):
                for asset in MediaAsset.objects.exclude(file='').iterator():
                    try:
                        digest = hashlib.sha256()
                        with asset.file.open('rb') as stream:
                            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                                digest.update(chunk)
                        changed = asset.checksum != digest.hexdigest() or asset.file_size != asset.file.size
                        asset.checksum = digest.hexdigest()
                        asset.file_size = asset.file.size or 0
                        if changed:
                            asset.save(update_fields=('checksum', 'file_size', 'updated_at'))
                            updated += 1
                    except (FileNotFoundError, OSError, ValueError):
                        missing += 1
        self.stdout.write(self.style.SUCCESS(f'{updated} mídia(s) atualizada(s); {missing} sem arquivo acessível.'))
