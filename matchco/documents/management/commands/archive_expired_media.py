from django.core.management.base import BaseCommand
from django.utils import timezone
from django_tenants.utils import get_tenant_model, schema_context

from documents.models import MediaAsset, MediaAssetAuditEvent


class Command(BaseCommand):
    help = 'Identifica mídias vencidas e, com --apply, arquiva as que passaram da retenção.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Aplica o arquivamento; sem esta opção apenas simula.')

    def handle(self, *args, **options):
        now = timezone.now()
        apply_changes = options['apply']
        found = archived = 0
        tenants = get_tenant_model().objects.exclude(schema_name='public')
        for tenant in tenants:
            with schema_context(tenant.schema_name):
                queryset = MediaAsset.objects.filter(
                    retention_until__isnull=False,
                    retention_until__lte=now,
                ).exclude(workflow_status='archived')
                for asset in queryset.iterator():
                    found += 1
                    if not apply_changes:
                        continue
                    asset.active = False
                    asset.workflow_status = 'archived'
                    asset.save(update_fields=('active', 'workflow_status', 'updated_at'))
                    MediaAssetAuditEvent.objects.create(
                        asset=asset,
                        organization=asset.organization,
                        event_name=MediaAssetAuditEvent.UPDATED,
                        metadata={'action': 'retention_archived', 'retention_until': asset.retention_until.isoformat()},
                    )
                    archived += 1
        mode = 'arquivada(s)' if apply_changes else 'encontrada(s) para arquivamento'
        self.stdout.write(self.style.SUCCESS(f'{archived if apply_changes else found} mídia(s) {mode}.'))
