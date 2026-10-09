from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from learning.models import UserNotification
from learning.services import create_notification


class Command(BaseCommand):
    help = 'Reenvia uma lembrança controlada para alertas críticos ainda não lidos.'

    def add_arguments(self, parser):
        parser.add_argument('--hours', type=int, default=24, help='Idade mínima do alerta original.')
        parser.add_argument('--limit', type=int, default=500)

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=max(1, options['hours']))
        alerts = UserNotification.objects.filter(
            priority=UserNotification.CRITICAL,
            read_at__isnull=True,
            created_at__lte=cutoff,
        ).select_related('user', 'organization')[:max(1, options['limit'])]
        created = 0
        for alert in alerts:
            reminder = create_notification(
                alert.user,
                title=f'Lembrete: {alert.title}',
                message='Este alerta crítico ainda não foi lido. Verifique a orientação para sua operação.',
                url=alert.url,
                priority=UserNotification.CRITICAL,
                dedupe_key=f'critical-reminder:{alert.pk}:{alert.created_at.date().isoformat()}',
                organization=alert.organization,
            )
            created += bool(reminder)
        self.stdout.write(self.style.SUCCESS(f'{created} lembrete(s) criado(s).'))
