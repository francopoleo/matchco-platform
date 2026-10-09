from django.core.management.base import BaseCommand
from django.utils import timezone
from django_tenants.utils import get_tenant_model, schema_context

from documents.models import DocumentShareLink, MediaAssetShareLink


class Command(BaseCommand):
    help = 'Revoga tokens de compartilhamento que já passaram da validade.'

    def handle(self, *args, **options):
        total = 0
        now = timezone.now()
        for tenant in get_tenant_model().objects.exclude(schema_name='public'):
            with schema_context(tenant.schema_name):
                total += MediaAssetShareLink.objects.filter(active=True, expires_at__lte=now).update(active=False)
                total += DocumentShareLink.objects.filter(active=True, expires_at__lte=now).update(active=False)
        self.stdout.write(self.style.SUCCESS(f'{total} link(s) temporário(s) revogado(s).'))
