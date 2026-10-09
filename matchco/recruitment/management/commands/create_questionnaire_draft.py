"""Create an auditable questionnaire draft from an organization brief JSON."""

import json

from django.core.management.base import BaseCommand, CommandError

from recruitment.domain_models import RecruitmentOrganization
from recruitment.questionnaire_builder import create_questionnaire_draft


class Command(BaseCommand):
    help = 'Cria um rascunho de questionário a partir de um briefing JSON; nunca publica automaticamente.'

    def add_arguments(self, parser):
        parser.add_argument('--organization', required=True, help='Slug da organização de recrutamento.')
        parser.add_argument('--brief', required=True, help='JSON do briefing ou caminho para um arquivo JSON.')
        parser.add_argument('--code', help='Código da família de templates.')
        parser.add_argument('--name', help='Nome do rascunho.')

    def handle(self, *args, **options):
        organization = RecruitmentOrganization.objects.filter(slug=options['organization']).first()
        if not organization:
            raise CommandError('Organização não encontrada.')
        raw = options['brief']
        try:
            try:
                with open(raw, 'r', encoding='utf-8') as stream:
                    raw = stream.read()
            except (OSError, TypeError):
                pass
            brief = json.loads(raw)
        except (TypeError, ValueError, OSError) as exc:
            raise CommandError(f'Brief inválido: {exc}')
        if not isinstance(brief, dict):
            raise CommandError('O brief precisa ser um objeto JSON.')

        template = create_questionnaire_draft(
            organization,
            brief,
            code=options.get('code'),
            name=options.get('name'),
        )
        self.stdout.write(self.style.SUCCESS(
            f'Rascunho criado: {template.name} · {template.code} · v{template.version}. '
            'Revise no admin antes de publicar.'
        ))
