"""Processa prazos do recrutamento Match sem reabrir o fluxo de CV."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Expira convites e decisões Match e abre novas rodadas quando necessário.'

    def handle(self, *args, **options):
        from django.core.management import call_command

        # Mantemos um nome operacional estável para o worker, mas a execução
        # é exclusivamente a jornada atual de convite/Match sem currículo.
        call_command('process_match_invitation_rounds', verbosity=options.get('verbosity', 1))
        self.stdout.write(self.style.SUCCESS('Prazos do recrutamento Match processados.'))
