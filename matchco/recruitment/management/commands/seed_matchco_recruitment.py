"""Canonical development seed for Bourbon, Drogasil and ElectraTech."""

from django.core.management import call_command
from django.core.management.base import BaseCommand
from recruitment.domain_models import RecruitmentOrganization


class Command(BaseCommand):
    help = 'Cria somente os dados de recrutamento do MatchCo (Perfil, unidades, QR, necessidades e relações).'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Recria o cenário de recrutamento antes do seed.')

    def handle(self, *args, **options):
        if options['reset']:
            RecruitmentOrganization.objects.filter(slug__in=['bourbon-shopping', 'drogasil-rede', 'electratech-demo']).delete()
        call_command('seed_matchco_market_demos', only='bourbon-shopping', reset_demo=options['reset'])
        call_command('seed_matchco_market_demos', only='drogasil-rede', reset_demo=options['reset'])
        call_command('seed_matchco_market_demos', only='electratech-demo', reset_demo=options['reset'])
        self.stdout.write(self.style.SUCCESS('Seed de recrutamento Bourbon + Drogasil + ElectraTech concluído. Conteúdo não foi criado.'))
