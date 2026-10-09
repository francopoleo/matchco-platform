"""Concede certificação a um candidato (bridge manual).

Uso:
    python manage.py grant_certification --email a@ex.com \
        --key nr35 --name "NR-35" --valid-until 2027-12-31
"""
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from recruitment.integrations.signals import on_certification_granted
from recruitment.models import CandidateProfile
from recruitment.services import resolve_platform_context


class Command(BaseCommand):
    help = 'Concede certificação a um candidato.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True)
        parser.add_argument('--key', required=True, help='Ex: nr35, mopp, anvisa_haccp')
        parser.add_argument('--name', required=True)
        parser.add_argument('--valid-until', help='YYYY-MM-DD (opcional)')

    def handle(self, *args, **opts):
        profile = CandidateProfile.objects.filter(email=opts['email']).first()
        if profile is None:
            raise CommandError(f'Candidato não encontrado: {opts["email"]}')

        valid = None
        if opts['valid_until']:
            valid = timezone.make_aware(
                datetime.strptime(opts['valid_until'], '%Y-%m-%d')
            )

        sig = on_certification_granted(
            candidate_id=profile.pk,
            cert_key=opts['key'], cert_name=opts['name'],
            valid_until=valid,
            platform_context=(
                resolve_platform_context(organization=profile.organization)
                if profile.organization.platform_bindings.filter(active=True).exists()
                else None
            ),
        )
        if sig is None:
            self.stdout.write(self.style.WARNING(
                'Candidato não deu consent INTEGRATION_CERTIFICATIONS. Nada foi feito.'
            ))
            return
        self.stdout.write(self.style.SUCCESS(
            f'Concedida: {sig.label} · freshness {sig.freshness_class}'
        ))
