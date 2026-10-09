import hashlib
import hmac
import json
import urllib.request

from django.utils import timezone

from configuration.models import Organization, WebhookDelivery, WebhookSubscription


def enqueue_webhook_event(*, organization, event_type, payload):
    """Create durable outbound deliveries; network I/O is performed by a worker/command."""
    # Learning events live in the tenant schema and carry a TenantOrganization,
    # while webhook configuration lives in the public schema.
    organization_id = getattr(organization, 'organization_id', getattr(organization, 'pk', None))
    public_organization = Organization.objects.filter(pk=organization_id).first()
    if not public_organization:
        return []

    deliveries = []
    for subscription in WebhookSubscription.objects.filter(organization=public_organization, active=True):
        if subscription.events and event_type not in subscription.events and '*' not in subscription.events:
            continue
        deliveries.append(WebhookDelivery.objects.create(
            subscription=subscription,
            event_type=event_type,
            payload=payload,
        ))
    return deliveries


def deliver_webhook(delivery, *, timeout=10):
    """Deliver one signed webhook without coupling the domain code to a task queue."""
    subscription = delivery.subscription
    body = json.dumps({
        'id': delivery.pk,
        'event': delivery.event_type,
        'created_at': delivery.created_at.isoformat(),
        'data': delivery.payload,
    }, default=str).encode('utf-8')
    signature = hmac.new(subscription.secret.encode('utf-8'), body, hashlib.sha256).hexdigest() if subscription.secret else ''
    request = urllib.request.Request(
        subscription.endpoint,
        data=body,
        headers={'Content-Type': 'application/json', 'User-Agent': 'MatchCo-Webhooks/1.0', 'X-MatchCo-Event': delivery.event_type, 'X-MatchCo-Signature': signature},
        method='POST',
    )
    delivery.attempts += 1
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            delivery.response_code = response.status
            delivery.status = WebhookDelivery.SENT if 200 <= response.status < 300 else WebhookDelivery.FAILED
            delivery.error_message = '' if delivery.status == WebhookDelivery.SENT else f'HTTP {response.status}'
            if delivery.status == WebhookDelivery.SENT:
                delivery.delivered_at = timezone.now()
                subscription.last_delivered_at = delivery.delivered_at
                subscription.save(update_fields=('last_delivered_at',))
    except Exception as exc:
        delivery.status = WebhookDelivery.FAILED
        delivery.error_message = str(exc)[:2000]
    delivery.save(update_fields=('attempts', 'response_code', 'status', 'error_message', 'delivered_at'))
    return delivery
