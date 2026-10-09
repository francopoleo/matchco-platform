from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Expira convites/decisões e abre novas rodadas de oportunidades Match.'

    def handle(self, *args, **options):
        from recruitment.models import Position
        from recruitment.services import expire_invitation_rounds, open_invitation_round, recruitment_sla

        now = timezone.now()
        expired = expire_invitation_rounds(now=now)
        opened = 0
        created = 0
        for opportunity in Position.objects.filter(
            state__in=[Position.STATE_ACTIVATED, Position.STATE_CIRCULATED],
            pre_interest_set_complete=True,
            mode=Position.MODE_MATCH,
        ).select_related('organization', 'business_unit'):
            result = open_invitation_round(opportunity=opportunity, now=now)
            if result['created']:
                opened += 1
                created += result['created']
        self.stdout.write(self.style.SUCCESS(
            f"Convites expirados: {expired['expired_notices']}; "
            f"decisões expiradas: {expired['expired_decisions']}; "
            f"novas rodadas: {opened}; convites criados: {created}."
        ))
