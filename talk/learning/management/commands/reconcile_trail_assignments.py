from django.core.management.base import BaseCommand

from audience.models import AudiencePolicy
from learning.services import reconcile_policy_assignments


class Command(BaseCommand):
    help = 'Reavalia atribuições materializadas após alterações de audiência.'

    def add_arguments(self, parser):
        parser.add_argument('--policy', type=int, help='Recalcula somente uma política.')

    def handle(self, *args, **options):
        policies = AudiencePolicy.objects.filter(pk=options['policy']) if options.get('policy') else AudiencePolicy.objects.filter(active=True)
        totals = {'created': 0, 'restored': 0, 'revoked': 0, 'checked': 0}
        for policy in policies:
            stats = reconcile_policy_assignments(policy)
            for key in totals:
                totals[key] += stats[key]
        self.stdout.write(self.style.SUCCESS(f"Atribuições reavaliadas: {totals}"))
