from django.core.management.base import BaseCommand

from learning.integrations import deliver_webhook
from configuration.models import WebhookDelivery


class Command(BaseCommand):
    help = 'Entrega webhooks pendentes de integrações externas.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100)

    def handle(self, *args, **options):
        deliveries = WebhookDelivery.objects.filter(status=WebhookDelivery.PENDING).select_related('subscription')[:max(1, min(options['limit'], 1000))]
        sent = failed = 0
        for delivery in deliveries:
            if deliver_webhook(delivery).status == WebhookDelivery.SENT:
                sent += 1
            else:
                failed += 1
        self.stdout.write(self.style.SUCCESS(f'Webhooks processados: {sent} enviados, {failed} falhos.'))
