from django.utils import timezone

try:
    from celery import shared_task
except ImportError:  # local development can use the management commands only
    def shared_task(*args, **kwargs):
        def decorator(function):
            return function
        return decorator

from configuration.models import WebhookDelivery
from .integrations import deliver_webhook
from .models import NotificationDelivery
from .services import deliver_notification


@shared_task(name='learning.deliver_webhooks')
def deliver_webhooks(limit=100):
    deliveries = WebhookDelivery.objects.filter(
        status=WebhookDelivery.PENDING,
    ).select_related('subscription')[:max(1, min(int(limit), 1000))]
    sent = failed = 0
    for delivery in deliveries:
        if deliver_webhook(delivery).status == WebhookDelivery.SENT:
            sent += 1
        else:
            failed += 1
    return {'sent': sent, 'failed': failed}


@shared_task(name='learning.retry_notification_deliveries')
def retry_notification_deliveries(limit=100):
    deliveries = NotificationDelivery.objects.filter(
        status=NotificationDelivery.FAILED,
    ).select_related('notification')[:max(1, min(int(limit), 1000))]
    retried = sent = failed = 0
    for delivery in deliveries:
        delivery.status = NotificationDelivery.PENDING
        delivery.error_message = ''
        delivery.save(update_fields=('status', 'error_message'))
        result = deliver_notification(delivery.notification, channel=delivery.channel)
        retried += 1
        sent += result.status == NotificationDelivery.SENT
        failed += result.status == NotificationDelivery.FAILED
    return {'retried': retried, 'sent': sent, 'failed': failed, 'at': timezone.now().isoformat()}
