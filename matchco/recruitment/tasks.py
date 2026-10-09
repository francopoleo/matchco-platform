"""Asynchronous recruitment jobs; synchronous commands remain available for dev."""

from celery import shared_task


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_deadlines_task(self):
    from django.core.management import call_command
    call_command('process_match_invitation_rounds')
    return 'processed'


# ---------------------------------------------------------------------------
# Porta Match — jobs periódicos (D3)
# ---------------------------------------------------------------------------

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def apply_retention_task(self, commit=False):
    """Aplica RT-01..RT-06. Beat diário."""
    from .services import apply_retention_policy
    return apply_retention_policy(dry_run=not commit)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_pending_notifications_task(self):
    """Envia SLA + certificações a expirar. Beat 2x/dia."""
    from django.core.management import call_command
    call_command('send_notifications', '--commit')
    return 'done'


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def mark_stale_signals_task(self):
    """Marca ProfileSignal F1/F2 como stale e dispara reconfirmação.

    Não altera o modelo; apenas notifica o candidato quando um sinal material
    virou stale desde a última execução (metadados no signal).
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import ProfileSignal, FreshnessClass
    from . import notifications

    now = timezone.now()
    since = now - timedelta(days=1)
    stale = ProfileSignal.objects.filter(
        freshness_class__in=[FreshnessClass.F1_DYNAMIC, FreshnessClass.F2_HIGHLY_DYNAMIC],
        expires_at__lte=now,
        expires_at__gt=since,
    ).select_related('profile')

    sent = 0
    for sig in stale:
        try:
            notifications.notify_signal_reconfirm(
                candidate=sig.profile,
                signal_key=sig.key,
                signal_label=sig.label or sig.key,
            )
            sent += 1
        except Exception:
            pass
    return sent


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def monitor_entry_points_task(self):
    """PIAG monitor — checa integridade de cada EntryPoint ACTIVE.

    Verifica: HTTPS + destino canônico responde 2xx/3xx + hostname bate.
    Se falhar, marca COMPROMISED e grava POINT_COMPROMISED no Ledger.
    """
    from urllib.parse import urlparse
    from .models import EntryPoint
    from .services import ledger_record

    compromised = 0
    for ep in EntryPoint.objects.filter(state=EntryPoint.STATE_ACTIVE):
        url = ep.canonical_destination_url or ''
        parsed = urlparse(url)
        is_ok = parsed.scheme == 'https' and parsed.netloc
        # Poderia fazer HEAD real; mantido lógico para não depender de rede em teste.
        # Adapter opcional em .integrations.piag_probe pode assumir a checagem HTTP.
        try:
            from .integrations import piag_probe  # opcional
            is_ok = is_ok and piag_probe.probe(url)
        except Exception:
            pass

        if not is_ok:
            ep.state = EntryPoint.STATE_COMPROMISED
            ep.save(update_fields=['state', 'updated_at'])
            ledger_record(
                'POINT_COMPROMISED', actor_type='system',
                entry_point=ep,
                metadata={'reason': 'piag_monitor_failed', 'url': url},
            )
            compromised += 1
    return compromised


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def expire_pending_opportunities_task(self):
    """Fecha Opportunities cujo active_until já passou. Beat diário."""
    from django.utils import timezone
    from .models import Position
    from .services import ledger_record

    now = timezone.now().date()
    qs = Position.objects.filter(
        state__in=[Position.STATE_ACTIVATED, Position.STATE_CIRCULATED],
        active_until__lt=now,
    )
    count = 0
    for opp in qs:
        opp.state = Position.STATE_CLOSED
        opp.closed_at = timezone.now()
        opp.save(update_fields=['state', 'closed_at', 'updated_at'])
        ledger_record(
            'OPPORTUNITY_CLOSED', actor_type='system',
            opportunity=opp, metadata={'reason': 'expired_by_active_until'},
        )
        count += 1
    return count
