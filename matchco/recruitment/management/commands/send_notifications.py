"""Envia notificações periódicas: SLA de resposta e certificações a expirar.

Uso:
    python manage.py send_notifications              # dry-run
    python manage.py send_notifications --commit
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from recruitment.models import ProfileSignal, RecruitmentOrganization
from recruitment.services import pending_response_relations
from recruitment import notifications


class Command(BaseCommand):
    help = 'Envia notificações de SLA pendente e certificações a expirar.'

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true')

    def handle(self, *args, **opts):
        commit = opts['commit']
        now = timezone.now()
        sent = 0

        # SLA por org
        for org in RecruitmentOrganization.objects.filter(active=True):
            pending = pending_response_relations(organization=org)
            count = pending.count()
            if count == 0:
                continue
            # Empregadores da org
            for actor in org.employer_actors.filter(active=True).select_related('user'):
                self.stdout.write(f'  → SLA: {actor.user.email} · {count} pendências')
                if commit and actor.user.email:
                    notifications.notify_response_sla_pending(
                        employer_email=actor.user.email, count=count,
                    )
                    sent += 1

        # Certificações a expirar em 30 dias
        cutoff = now + timedelta(days=30)
        signals = ProfileSignal.objects.filter(
            key__startswith='cert:',
            expires_at__lte=cutoff,
            expires_at__gt=now,
        ).select_related('profile')
        for sig in signals:
            self.stdout.write(f'  → CERT: {sig.profile.email} · {sig.label}')
            if commit:
                notifications.notify_certification_expiring(
                    candidate=sig.profile,
                    cert_name=sig.value.get('cert_name', 'certificação'),
                    valid_until=sig.expires_at,
                )
                sent += 1

        self.stdout.write(self.style.SUCCESS(
            f'{"Enviados" if commit else "DRY-RUN"}: {sent}'
        ))
