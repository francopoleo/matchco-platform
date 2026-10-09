"""Create the starter questionnaire library for recruitment organizations.

This command is intentionally idempotent. It creates published starter
versions only when they do not exist, so an organization's edited templates
are never overwritten by a routine deploy.
"""

from django.core.management.base import BaseCommand

from recruitment.domain_models import RecruitmentOrganization
from recruitment.models import QuestionnaireQuestion, QuestionnaireTemplate


QUESTION_SETS = {
    'generic_v1': {
        'name': 'MatchCo essencial',
        'description': 'Base curta para qualquer organização e função.',
        'default': True,
        'questions': [
            ('experience', 'Qual é sua experiência profissional?', 'textarea', [], True),
            ('interests', 'Em que tipo de oportunidade você tem interesse?', 'single_choice',
             ['Operação', 'Vendas', 'Atendimento', 'Administrativo', 'Técnico', 'Aberto a oportunidades'], False),
            ('skills', 'Quais são suas principais habilidades?', 'textarea', [], True),
            ('availability', 'Qual é sua disponibilidade de dias e horários?', 'textarea', [], False),
            ('start_date', 'Quando você poderia começar?', 'single_choice',
             ['Imediatamente', 'Em até 15 dias', 'Em até 30 dias', 'A combinar'], False),
        ],
    },
    'high_turnover_v1': {
        'name': 'Operação de alto giro',
        'description': 'Fluxo rápido para atendimento, loja, estoque e operação.',
        'market': 'retail',
        'questions': [
            ('customer_experience', 'Você já trabalhou com atendimento ao público?', 'single_choice', ['Sim', 'Não'], True),
            ('shift', 'Quais turnos você consegue cumprir?', 'multiple_choice', ['Manhã', 'Tarde', 'Noite', 'Fins de semana'], True),
            ('routine', 'Como você lida com uma rotina dinâmica e com metas?', 'textarea', [], True),
            ('location', 'Você consegue trabalhar presencialmente na unidade indicada?', 'boolean', ['Sim', 'Não'], True),
            ('start_date', 'Quando você poderia começar?', 'single_choice', ['Imediatamente', 'Em até 15 dias', 'Em até 30 dias'], False),
        ],
    },
    'sales_v1': {
        'name': 'Vendas e relacionamento',
        'description': 'Para vendedores, representantes, parceiros e equipes comerciais.',
        'audience_role': 'salesperson',
        'questions': [
            ('sales_experience', 'Conte brevemente sua experiência comercial.', 'textarea', [], True),
            ('customer_scenario', 'Como você atenderia uma pessoa indecisa ou insatisfeita?', 'textarea', [], True),
            ('products', 'Com quais categorias de produto você já trabalhou?', 'multiple_choice', ['Consumo', 'Tecnologia', 'Saúde', 'Serviços', 'Outro'], False),
            ('mobility', 'Você tem disponibilidade para visitar clientes ou unidades?', 'boolean', ['Sim', 'Não'], False),
        ],
    },
    'technical_v1': {
        'name': 'Técnico e especialista',
        'description': 'Para funções técnicas, suporte, instalação e especialistas.',
        'audience_role': 'technician',
        'questions': [
            ('specialty', 'Qual é sua principal especialidade?', 'text', [], True),
            ('certifications', 'Quais certificações ou treinamentos você possui?', 'textarea', [], False),
            ('field_work', 'Você tem disponibilidade para atendimento em campo?', 'boolean', ['Sim', 'Não'], True),
            ('technical_case', 'Descreva uma situação técnica que você resolveu.', 'textarea', [], True),
        ],
    },
    'healthcare_v1': {
        'name': 'Saúde e ciências da vida',
        'description': 'Base para farmácias, hospitais, indústria e rede de saúde.',
        'market': 'pharma',
        'questions': [
            ('health_role', 'Qual é sua função ou área de atuação em saúde?', 'single_choice', ['Farmácia', 'Enfermagem', 'Representação', 'Atendimento', 'Operação', 'Outra'], True),
            ('regulatory_training', 'Você possui treinamentos ou registros profissionais relevantes?', 'textarea', [], False),
            ('patient_customer_care', 'Como você garante cuidado e clareza no atendimento?', 'textarea', [], True),
            ('availability', 'Qual é sua disponibilidade de escala ou visitas?', 'textarea', [], False),
        ],
    },
}


class Command(BaseCommand):
    help = 'Cria versões iniciais de questionários configuráveis por organização.'

    def add_arguments(self, parser):
        parser.add_argument('--organization', help='Slug da organização de recrutamento.')

    def handle(self, *args, **options):
        organizations = RecruitmentOrganization.objects.filter(active=True)
        if options.get('organization'):
            organizations = organizations.filter(slug=options['organization'])

        created_templates = 0
        created_questions = 0
        for organization in organizations:
            for code, definition in QUESTION_SETS.items():
                template, created = QuestionnaireTemplate.objects.get_or_create(
                    organization=organization,
                    code=code,
                    version=1,
                    defaults={
                        'name': definition['name'],
                        'description': definition['description'],
                        'status': QuestionnaireTemplate.STATUS_PUBLISHED,
                        'audience_role': definition.get('audience_role', ''),
                        'market': definition.get('market', ''),
                        'is_default': definition.get('default', False),
                    },
                )
                if created:
                    created_templates += 1
                for order, (key, label, field_type, options_list, required) in enumerate(definition['questions']):
                    _, question_created = QuestionnaireQuestion.objects.get_or_create(
                        template=template,
                        key=key,
                        defaults={
                            'label': label,
                            'field_type': field_type,
                            'options': options_list,
                            'required': required,
                            'order': order,
                        },
                    )
                    created_questions += int(question_created)

        self.stdout.write(self.style.SUCCESS(
            f'{created_templates} templates e {created_questions} perguntas criados; '
            'templates existentes foram preservados.'
        ))
