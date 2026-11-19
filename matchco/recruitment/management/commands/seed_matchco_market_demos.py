"""Seed realistic, multi-market MatchCo demonstrations.

The command is additive by default. It creates or updates the scenarios used
by the development environment: Bourbon Shopping, RD Saúde and
ElectraTech Eletrônicos.
"""

from datetime import date, timedelta
import random

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from django_tenants.utils import schema_context

from configuration.models import (
    Membership,
    Organization as ConfigOrganization,
    Company as ConfigCompany,
    BusinessUnit as ConfigBusinessUnit,
    BusinessChannel as ConfigBusinessChannel,
    JobFunction as ConfigJobFunction,
    OperationalUnit as ConfigOperationalUnit,
    PhysicalLocation,
    OrganizationServiceSubscription,
)
from recruitment.domain_models import (
    RecruitmentChannel, RecruitmentCompany, RecruitmentJobFunction,
    RecruitmentOrganization, RecruitmentStore, RecruitmentPhysicalUnit,
    RecruitmentOrganizationRelation, RecruitmentPlatformBinding,
)
from recruitment.models import (
    AuthorityScope, CandidateConsent, CandidateIdentity, CandidateProfile,
    CandidateCanonicalResponse, CanonicalCatalog, CanonicalFunctionMapping, CanonicalTerm,
    CandidateProfileSurveyResponse, EntryPoint, OpportunityCanonicalRequirement,
    OpportunityCriterion, Position, EmployerActor, Relation,
)
from recruitment.questionnaire_builder import create_questionnaire_draft
from recruitment.models import QuestionnaireQuestion, QuestionnaireTemplate, Relation
from recruitment.services import (
    candidate_is_eligible_for_position, deliver_opportunity_notice,
    employer_interested, person_interested, record_canonical_response,
    record_candidate_context,
)
from recruitment.questionnaires import resolve_questionnaire


User = get_user_model()

SCENARIOS = [
    {
        'slug': 'bourbon-shopping', 'name': 'Bourbon Shopping', 'market': 'shopping',
        'brand': 'Bourbon Shopping', 'company': 'Bourbon Shopping',
        'administration_units': (
            ('Administração do empreendimento', 'ADMINISTRACAO', 'administracao'),
            ('Atendimento ao lojista', 'SERVICO', 'servicos'),
            ('Operações e facilities', 'SERVICO', 'operacoes'),
            ('Marketing e eventos', 'SERVICO', 'marketing'),
        ),
        'additional_companies': [
            {
                'name': 'Renner', 'legacy_unit_names': {'Renner': 'Renner · Bourbon Shopping'},
                'services': ('content', 'talk', 'training', 'recruitment', 'analytics'),
                'units': (('Renner · Bourbon Shopping', 'LOJA', 'moda'),),
            },
            {
                'name': 'C&A', 'legacy_unit_names': {'C&A': 'C&A · Bourbon Shopping'},
                'services': ('content', 'talk', 'training', 'recruitment', 'analytics'),
                'units': (('C&A · Bourbon Shopping', 'LOJA', 'moda'),),
            },
            {
                'name': 'Riachuelo', 'legacy_unit_names': {'Riachuelo': 'Riachuelo · Bourbon Shopping'},
                'services': ('content', 'talk', 'training', 'recruitment', 'analytics'),
                'units': (('Riachuelo · Bourbon Shopping', 'LOJA', 'moda'),),
            },
            {
                'name': 'Zara', 'legacy_unit_names': {'Zara': 'Zara · Bourbon Shopping'},
                'services': ('content', 'talk', 'training', 'recruitment', 'analytics'),
                'units': (('Zara · Bourbon Shopping', 'LOJA', 'moda'),),
            },
            {
                'name': 'Fast Shop', 'legacy_unit_names': {'Fast Shop': 'Fast Shop · Bourbon Shopping'},
                'services': ('content', 'talk', 'training', 'recruitment', 'analytics'),
                'units': (('Fast Shop · Bourbon Shopping', 'LOJA', 'eletronicos'),),
            },
            {
                'name': 'Centauro', 'legacy_unit_names': {'Centauro': 'Centauro · Bourbon Shopping'},
                'services': ('content', 'talk', 'training', 'recruitment', 'analytics'),
                'units': (('Centauro · Bourbon Shopping', 'LOJA', 'esportes'),),
            },
            {
                'name': 'Tok&Stok', 'legacy_unit_names': {'Tok&Stok': 'Tok&Stok · Bourbon Shopping'},
                'services': ('content', 'talk', 'training', 'recruitment', 'analytics'),
                'units': (('Tok&Stok · Bourbon Shopping', 'LOJA', 'casa'),),
            },
            {
                'name': 'O Boticário', 'legacy_unit_names': {'O Boticário': 'O Boticário · Bourbon Shopping'},
                'services': ('content', 'talk', 'training', 'recruitment', 'analytics'),
                'units': (('O Boticário · Bourbon Shopping', 'LOJA', 'beleza'),),
            },
            {
                'name': 'Zaffari', 'legacy_unit_names': {'Zaffari': 'Zaffari · Bourbon Shopping'},
                'services': ('content', 'talk', 'training', 'recruitment', 'analytics'),
                'units': (('Zaffari · Bourbon Shopping', 'LOJA', 'supermercado'),),
            },
            {
                'name': 'Drogasil', 'legacy_unit_names': {'Drogasil · Bourbon': 'Drogasil · Bourbon Shopping'},
                'services': ('content', 'talk', 'training', 'certification', 'recruitment', 'analytics'),
                'units': (('Drogasil · Bourbon Shopping', 'LOJA', 'farmacia'),),
            },
            {
                'name': '5àsec', 'legacy_unit_names': {'5àsec': '5àsec · Bourbon Shopping'},
                'services': ('content', 'talk', 'training', 'recruitment', 'analytics'),
                'units': (('5àsec · Bourbon Shopping', 'SERVICO', 'servicos'),),
            },
            {
                'name': 'A Medicina Diagnóstica', 'legacy_unit_names': {'A Medicina Diagnóstica': 'A Medicina Diagnóstica · Bourbon Shopping'},
                'services': ('content', 'talk', 'training', 'recruitment', 'analytics'),
                'units': (('A Medicina Diagnóstica · Bourbon Shopping', 'SERVICO', 'saude'),),
            },
            {
                'name': 'Espaço Itaú de Cinema', 'legacy_unit_names': {'Espaço Itaú de Cinema': 'Espaço Itaú de Cinema · Bourbon Shopping'},
                'services': ('content', 'talk', 'training', 'recruitment', 'analytics'),
                'units': (('Espaço Itaú de Cinema · Bourbon Shopping', 'SERVICO', 'entretenimento'),),
            },
            {
                'name': 'Teatro Bradesco', 'legacy_unit_names': {'Teatro Bradesco': 'Teatro Bradesco · Bourbon Shopping'},
                'services': ('content', 'talk', 'training', 'recruitment', 'analytics'),
                'units': (('Teatro Bradesco · Bourbon Shopping', 'SERVICO', 'entretenimento'),),
            },
            {
                'name': 'Chilli Beans', 'legacy_unit_names': {'Quiosque Chilli Beans': 'Quiosque Chilli Beans · Bourbon Shopping'},
                'services': ('content', 'talk', 'training', 'recruitment', 'analytics'),
                'units': (('Quiosque Chilli Beans · Bourbon Shopping', 'QUIOSQUE', 'acessorios'),),
            },
            {
                'name': 'Kopenhagen', 'legacy_unit_names': {'Quiosque Kopenhagen': 'Quiosque Kopenhagen · Bourbon Shopping'},
                'services': ('content', 'talk', 'training', 'recruitment', 'analytics'),
                'units': (('Quiosque Kopenhagen · Bourbon Shopping', 'QUIOSQUE', 'alimentacao'),),
            },
        ],
        'units': [
            ('Renner', 'LOJA', 'moda'), ('C&A', 'LOJA', 'moda'),
            ('Riachuelo', 'LOJA', 'moda'), ('Zara', 'LOJA', 'moda'),
            ('Fast Shop', 'LOJA', 'eletronicos'), ('Centauro', 'LOJA', 'esportes'),
            ('Tok&Stok', 'LOJA', 'casa'), ('O Boticário', 'LOJA', 'beleza'),
            ('Drogasil · Bourbon', 'LOJA', 'farmacia'),
            ('Zaffari', 'LOJA', 'supermercado'), ('5àsec', 'SERVICO', 'servicos'),
            ('Teatro Bradesco', 'SERVICO', 'entretenimento'),
            ('Espaço Itaú de Cinema', 'SERVICO', 'entretenimento'),
            ('Quiosque Chilli Beans', 'QUIOSQUE', 'acessorios'),
            ('Quiosque Kopenhagen', 'QUIOSQUE', 'alimentacao'),
            ('A Medicina Diagnóstica', 'SERVICO', 'saude'),
        ],
        'functions': ['Atendente de loja', 'Vendedor(a)', 'Caixa', 'Estoquista', 'Atendente de farmácia', 'Farmacêutico(a)', 'Gerente de loja', 'Supervisor(a)', 'Operador(a) de cinema', 'Atendente de serviços'],
        'content_prefix': 'Bourbon',
    },
    {
        'slug': 'drogasil-rede', 'name': 'RD Saúde', 'market': 'retail',
        'brand': 'RD Saúde', 'company': 'Drogasil',
        'additional_companies': [
            {
                'name': 'Raia',
                'services': ('content', 'talk', 'training', 'recruitment', 'analytics'),
                'units': (
                    ('Raia · Lapa', 'LOJA', 'farmacia'),
                    ('Raia · Perdizes', 'LOJA', 'farmacia'),
                ),
            },
        ],
        'units': [
            ('Drogasil · Bourbon Shopping', 'LOJA', 'farmacia'),
            ('Drogasil · Perdizes', 'LOJA', 'farmacia'),
            ('Drogasil · Lapa', 'LOJA', 'farmacia'),
            ('Drogasil · Centro de Distribuição', 'DISTRIBUICAO', 'logistica'),
        ],
        'functions': ['Atendente de farmácia', 'Balconista de farmácia', 'Farmacêutico(a)', 'Caixa', 'Estoquista', 'Gerente de loja', 'Supervisor(a)'],
        'content_prefix': 'Drogasil',
    },
    {
        'slug': 'electratech-demo', 'name': 'ElectraTech Eletrônicos', 'market': 'manufacturer',
        'brand': 'ElectraTech', 'company': 'ElectraTech Brasil',
        'units': [
            ('Fábrica · Campinas', 'FABRICA', 'industria'),
            ('Centro de Distribuição · Jundiaí', 'DISTRIBUICAO', 'logistica'),
            ('Rede Tech Center · São Paulo', 'REVENDA', 'revenda'),
            ('Revenda Parceira · Campinas', 'REVENDA', 'revenda'),
            ('Assistência Técnica Autorizada', 'SERVICO', 'assistencia'),
        ],
        'functions': ['Representante comercial', 'Consultor(a) de tecnologia', 'Técnico(a) de suporte', 'Especialista de produto', 'Gerente de canal', 'Analista de qualidade'],
        'content_prefix': 'ElectraTech',
    },
]

SHOPPING_SCOPES = [AuthorityScope.AA1_DECLARE_NEED, AuthorityScope.AA2_STRUCTURE_OPPORTUNITY, AuthorityScope.AA3_ACTIVATE_OPPORTUNITY, AuthorityScope.AA4_MODIFY_OPPORTUNITY, AuthorityScope.AA5_CLOSE_OPPORTUNITY, AuthorityScope.AA6_VIEW_EMPLOYER_INTEREST_VIEW, AuthorityScope.AA7_DECLARE_EMPLOYER_INTEREST, AuthorityScope.AA8_RECEIVE_CONTACT_CHANNEL]

OPERATIONAL_AREAS_BY_UNIT = {
    'Fábrica · Campinas': ['Produção', 'Qualidade', 'Manutenção', 'Segurança do trabalho'],
    'Centro de Distribuição · Jundiaí': ['Recebimento', 'Armazenagem', 'Expedição', 'Transportes'],
    'Rede Tech Center · São Paulo': ['Vendas', 'Atendimento técnico', 'Estoque', 'Gerência'],
    'Revenda Parceira · Campinas': ['Vendas', 'Atendimento', 'Pós-venda'],
    'Assistência Técnica Autorizada': ['Recepção', 'Diagnóstico', 'Reparos', 'Peças e garantia'],
}

# O Bourbon Shopping informa o endereço do empreendimento como Rua Palestra
# Itália, 500, São Paulo/SP, CEP 05005-030. As unidades abaixo representam
# lojas dentro do mesmo shopping e, portanto, usam o CEP do empreendimento;
# não inventamos um CEP diferente para cada lojista.
BOURBON_POSTAL_CODE = '05005-030'

# Valores de referência exclusivamente para os candidatos fictícios da demo.
# Eles representam regiões de São Paulo para permitir a evolução da leitura de
# proximidade, mas não identificam o endereço de nenhuma pessoa.
SAO_PAULO_DEMO_CEPS = [
    '05005-030', '05007-000', '05015-000', '05025-000', '05300-000', '05406-000',
    '05508-000', '04001-000', '04538-000', '04101-000', '01234-000', '01451-000',
]

# Coordenadas aproximadas das regiões representadas acima. São dados de demo,
# não uma geolocalização residencial real. Em produção, a origem deve ser um
# provedor de geocodificação aprovado, com cache e controles de privacidade.
SAO_PAULO_DEMO_COORDINATES = [
    (-23.5265, -46.6815), (-23.5300, -46.6900), (-23.5300, -46.6700),
    (-23.5400, -46.6900), (-23.5200, -46.7200), (-23.5500, -46.6900),
    (-23.5600, -46.7200), (-23.5700, -46.6400), (-23.5900, -46.6800),
    (-23.5900, -46.6300), (-23.5400, -46.6500), (-23.5700, -46.6700),
]

BOURBON_COORDINATES = (-23.526455, -46.681507)

CANONICAL_BY_FUNCTION = {
    'Atendente de loja': ['atendimento-de-loja'],
    'Vendedor(a)': ['vendedor-de-loja', 'consultor-de-vendas'],
    'Caixa': ['caixa-de-loja', 'operador-de-caixa'],
    'Estoquista': ['estoquista-de-loja', 'repositor-de-loja'],
    'Gerente de loja': ['gerente-de-loja', 'lider-de-loja'],
    'Supervisor(a)': ['supervisor-de-loja'],
    'Operador(a) de cinema': ['atendimento-de-loja'],
    'Atendente de serviços': ['atendimento-de-loja', 'recepcionista'],
    'Representante comercial': ['promotor-de-vendas', 'consultor-de-vendas'],
    'Farmacêutico(a)': ['farmaceutico-responsavel-tecnico'],
    'Atendente de farmácia': ['atendente-de-farmacia', 'balconista-de-farmacia'],
    'Balconista de farmácia': ['balconista-de-farmacia', 'atendente-de-farmacia'],
    'Analista de qualidade': ['analista-de-qualidade'],
    'Especialista de produto': ['especialista-de-produto'],
    'Coordenador(a) de canal': ['gerente-de-canal'],
    'Consultor(a) de tecnologia': ['consultor-de-vendas', 'especialista-de-produto'],
    'Técnico(a) de suporte': ['tecnico-de-suporte'],
    'Gerente de canal': ['gerente-de-canal'],
}

# Catálogo operacional inicial do shopping. As funções existem no catálogo
# da organização para permitir evolução, mas só ficam vinculadas às unidades
# onde fazem sentido. Isso impede, por exemplo, que Farmacêutico(a) apareça
# em Centauro apenas porque a função também existe para a Drogasil.
SHOPPING_FUNCTIONS_BY_CATEGORY = {
    'moda': {'Atendente de loja', 'Vendedor(a)', 'Caixa', 'Estoquista', 'Gerente de loja', 'Supervisor(a)'},
    'esportes': {'Atendente de loja', 'Vendedor(a)', 'Caixa', 'Estoquista', 'Gerente de loja', 'Supervisor(a)'},
    'eletronicos': {'Atendente de loja', 'Vendedor(a)', 'Caixa', 'Estoquista', 'Gerente de loja', 'Supervisor(a)'},
    'casa': {'Atendente de loja', 'Vendedor(a)', 'Caixa', 'Estoquista', 'Gerente de loja', 'Supervisor(a)'},
    'beleza': {'Atendente de loja', 'Vendedor(a)', 'Caixa', 'Estoquista', 'Gerente de loja', 'Supervisor(a)'},
    'acessorios': {'Atendente de loja', 'Vendedor(a)', 'Caixa', 'Estoquista', 'Gerente de loja', 'Supervisor(a)'},
    'supermercado': {'Atendente de loja', 'Vendedor(a)', 'Caixa', 'Estoquista', 'Gerente de loja', 'Supervisor(a)'},
    'farmacia': {'Atendente de farmácia', 'Farmacêutico(a)', 'Caixa', 'Estoquista', 'Gerente de loja', 'Supervisor(a)'},
    'servicos': {'Atendente de serviços', 'Gerente de loja', 'Supervisor(a)'},
    'saude': {'Atendente de serviços', 'Gerente de loja', 'Supervisor(a)'},
    'alimentacao': {'Atendente de serviços', 'Caixa', 'Estoquista', 'Supervisor(a)'},
    'entretenimento': {'Atendente de serviços', 'Operador(a) de cinema', 'Caixa', 'Supervisor(a)'},
}

# A ElectraTech usa o mesmo catálogo canônico, mas a oferta válida depende do
# tipo de operação. Assim o candidato pode ter um perfil único e a empresa
# pode publicar necessidades diferentes para fábrica, logística, revenda e
# assistência, sem transformar todo cargo em opção de toda unidade.
ELECTRATECH_FUNCTIONS_BY_CHANNEL = {
    'industria': {'Especialista de produto', 'Técnico(a) de suporte', 'Analista de qualidade'},
    'logistica': {'Técnico(a) de suporte', 'Analista de qualidade'},
    'revenda': {'Representante comercial', 'Consultor(a) de tecnologia', 'Especialista de produto', 'Gerente de canal'},
    'assistencia': {'Técnico(a) de suporte', 'Especialista de produto', 'Analista de qualidade'},
}


class Command(BaseCommand):
    help = 'Cria cenários demo isolados de Bourbon Shopping, RD Saúde e ElectraTech.'

    def add_arguments(self, parser):
        parser.add_argument('--only', choices=[item['slug'] for item in SCENARIOS], help='Executa apenas um cenário.')
        parser.add_argument('--reset-demo', action='store_true', help='Apaga somente os três slugs de demonstração antes de recriar.')
        parser.add_argument('--with-bourbon-content', action='store_true', help='Executa o conteúdo tenant de todas as demos ao final.')

    def handle(self, *args, **options):
        scenarios = [item for item in SCENARIOS if not options.get('only') or item['slug'] == options['only']]
        if options.get('reset_demo'):
            RecruitmentOrganization.objects.filter(slug__in=[item['slug'] for item in scenarios]).delete()
            ConfigOrganization.objects.filter(slug__in=[item['slug'] for item in scenarios if item['slug'] != 'bourbon-shopping']).delete()

        for scenario in scenarios:
            try:
                config_org = self.ensure_config_org(scenario)
                self.ensure_configuration_structure(config_org, scenario)
                recruitment_org = self.ensure_recruitment_org(config_org, scenario)
                company = RecruitmentCompany.objects.get_or_create(organization=recruitment_org, name=scenario['company'])[0]
                canonical_company = ConfigCompany.objects.filter(
                    organization=config_org, name=scenario['company'],
                ).first()
                if canonical_company and company.legacy_id != canonical_company.pk:
                    company.legacy_id = canonical_company.pk
                    company.save(update_fields=['legacy_id'])
                channels = self.ensure_channels(company, scenario)
                stores = self.ensure_stores(
                    recruitment_org, company, channels, scenario, config_org=config_org,
                )
                functions = self.ensure_functions(recruitment_org, company, channels, scenario)
                self.ensure_canonical_mappings(recruitment_org, stores, functions, scenario)
                manager = self.ensure_user_and_actor(recruitment_org, config_org, stores[0], scenario)
                entry_points = self.ensure_entry_points(recruitment_org, stores, scenario)
                self.ensure_templates(recruitment_org, functions, scenario)
                candidates = self.ensure_candidates(recruitment_org, stores, functions, entry_points, scenario)
                positions = self.ensure_positions(recruitment_org, stores, functions, scenario)
                self.ensure_candidate_activity(candidates, positions, manager)
                self.ensure_platform_binding(recruitment_org, config_org)
                self.stdout.write(self.style.SUCCESS(
                    f"{scenario['name']}: {len(stores)} unidades · {len(functions)} funções · "
                    f"{len(entry_points)} QR · {len(candidates)} candidatos · {len(positions)} necessidades"
                ))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"{scenario['name']}: falhou sem cancelar os outros cenários: {exc}"))

        bourbon = RecruitmentOrganization.objects.filter(slug='bourbon-shopping').first()
        drogasil = RecruitmentOrganization.objects.filter(slug='drogasil-rede').first()
        if bourbon and drogasil:
            RecruitmentOrganizationRelation.objects.update_or_create(
                organization=bourbon,
                related_organization=drogasil,
                relation_type=RecruitmentOrganizationRelation.RELATION_SPONSOR,
                defaults={'active': True, 'metadata': {'purpose': 'shopping_network_overlap'}},
            )

        if options.get('with_bourbon_content'):
            try:
                call_command('seed_bourbon_tenant_content', tenant='bourbon-shopping')
                call_command('seed_market_tenant_content', tenant='drogasil-rede', market='pharma')
                call_command('seed_certification_demo')
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f'Parte do conteúdo tenant não foi executada: {exc}'))

        self.stdout.write(self.style.SUCCESS('Demos de mercado prontas. Conteúdo e templates existentes foram preservados.'))

    def ensure_config_org(self, scenario):
        org = ConfigOrganization.objects.filter(slug=scenario['slug']).first()
        if not org and scenario.get('schema_name'):
            org = ConfigOrganization.objects.filter(schema_name=scenario['schema_name']).first()
            if org:
                org.slug = scenario['slug']
                org.save(update_fields=['slug'])
        if not org:
            org = ConfigOrganization.objects.create(
                schema_name=scenario['slug'], name=scenario['name'], slug=scenario['slug'],
                description=f'Demo MatchCo · {scenario["name"]}', active=True, is_public=False,
                market=scenario['market'], onboarding_status=ConfigOrganization.ONBOARDING_READY,
                brand_name=scenario['brand'], primary_color='#f97316',
                default_entry_template={'shopping': 'shopping', 'pharma': 'manufacturer', 'manufacturer': 'manufacturer'}.get(scenario['market'], 'generic'),
            )
        else:
            changed = []
            for field, value in (
                ('name', scenario['name']),
                ('market', scenario['market']),
                ('brand_name', scenario['brand']),
                ('active', True),
                ('onboarding_status', ConfigOrganization.ONBOARDING_READY),
            ):
                if getattr(org, field) != value:
                    setattr(org, field, value); changed.append(field)
            if changed:
                org.save(update_fields=changed)
        OrganizationServiceSubscription.objects.update_or_create(
            organization=org,
            company=None,
            service_code=OrganizationServiceSubscription.SERVICE_RECRUITMENT,
            defaults={'status': OrganizationServiceSubscription.STATUS_ACTIVE, 'plan_code': 'demo-match-high-turnover'},
        )
        # The Console is organization-scoped when no company has been chosen
        # yet (for example immediately after switching from Bourbon to
        # Drogasil). Keep the shared demo capabilities active at that level;
        # company rows below remain explicit overrides for each package.
        common_service_codes = [
            OrganizationServiceSubscription.SERVICE_CONTENT,
            OrganizationServiceSubscription.SERVICE_TALK,
            OrganizationServiceSubscription.SERVICE_TRAINING,
            OrganizationServiceSubscription.SERVICE_ANALYTICS,
        ]
        if scenario.get('slug') in {'drogasil-rede', 'electratech-demo'}:
            common_service_codes.append(OrganizationServiceSubscription.SERVICE_CERTIFICATION)
        for service_code in common_service_codes:
            OrganizationServiceSubscription.objects.update_or_create(
                organization=org,
                company=None,
                service_code=service_code,
                defaults={'status': OrganizationServiceSubscription.STATUS_ACTIVE, 'plan_code': 'demo-common-services'},
            )
        from tenants_core.models import TenantOrganization
        with schema_context(org.schema_name):
            TenantOrganization.objects.update_or_create(
                organization_id=org.pk,
                defaults={'name': org.name, 'slug': org.slug},
            )
        return org

    def ensure_configuration_structure(self, config_org, scenario):
        """Popula a mesma estrutura exibida no Console, não só o domínio Match."""
        structure_units = scenario.get('administration_units') or scenario['units']
        company, _ = ConfigCompany.objects.get_or_create(
            organization=config_org,
            name=scenario['company'],
            defaults={'active': True},
        )
        company.active = True
        company.save(update_fields=['active'])

        # O catálogo de serviços é explícito no seed para demonstrar que a
        # mesma organização pode ter empresas com pacotes diferentes. A linha
        # da organização continua sendo o padrão; estas linhas são exceções
        # comerciais da empresa e não criam outra hierarquia.
        service_codes = {
            'bourbon-shopping': (
                OrganizationServiceSubscription.SERVICE_CONTENT,
                OrganizationServiceSubscription.SERVICE_TALK,
                OrganizationServiceSubscription.SERVICE_TRAINING,
                OrganizationServiceSubscription.SERVICE_RECRUITMENT,
                OrganizationServiceSubscription.SERVICE_OPERATIONS,
                OrganizationServiceSubscription.SERVICE_ANALYTICS,
            ),
            'drogasil-rede': (
                OrganizationServiceSubscription.SERVICE_CONTENT,
                OrganizationServiceSubscription.SERVICE_TALK,
                OrganizationServiceSubscription.SERVICE_TRAINING,
                OrganizationServiceSubscription.SERVICE_CERTIFICATION,
                OrganizationServiceSubscription.SERVICE_RECRUITMENT,
                OrganizationServiceSubscription.SERVICE_ANALYTICS,
            ),
            'electratech-demo': (
                OrganizationServiceSubscription.SERVICE_CONTENT,
                OrganizationServiceSubscription.SERVICE_TALK,
                OrganizationServiceSubscription.SERVICE_TRAINING,
                OrganizationServiceSubscription.SERVICE_CERTIFICATION,
                OrganizationServiceSubscription.SERVICE_OPERATIONS,
                OrganizationServiceSubscription.SERVICE_PARTNERS,
                OrganizationServiceSubscription.SERVICE_ANALYTICS,
            ),
        }.get(config_org.slug, ())
        for code in service_codes:
            OrganizationServiceSubscription.objects.update_or_create(
                organization=config_org,
                company=company,
                service_code=code,
                defaults={'status': OrganizationServiceSubscription.STATUS_ACTIVE, 'plan_code': f'demo-{config_org.slug}'},
            )

        channel_by_key = {}
        for channel_key in sorted({item[2] for item in structure_units}):
            channel, _ = ConfigBusinessChannel.objects.get_or_create(
                company=company,
                name=channel_key.replace('_', ' ').title(),
                defaults={'active': True},
            )
            channel.active = True
            channel.save(update_fields=['active'])
            channel_by_key[channel_key] = channel

        for name in scenario['functions']:
            function, _ = ConfigJobFunction.objects.get_or_create(
                company=company,
                name=name,
                defaults={'active': True},
            )
            applicable_channels = []
            for _, _, channel_key in structure_units:
                allowed = SHOPPING_FUNCTIONS_BY_CATEGORY.get(channel_key, set(scenario['functions']))
                if scenario['slug'] == 'electratech-demo':
                    allowed = ELECTRATECH_FUNCTIONS_BY_CHANNEL.get(channel_key, set())
                elif scenario['slug'] == 'drogasil-rede':
                    allowed = ({'Estoquista', 'Supervisor(a)'} if channel_key == 'logistica' else {
                        'Atendente de farmácia', 'Balconista de farmácia', 'Farmacêutico(a)',
                        'Caixa', 'Estoquista', 'Gerente de loja', 'Supervisor(a)',
                    })
                if name in allowed and channel_by_key[channel_key] not in applicable_channels:
                    applicable_channels.append(channel_by_key[channel_key])
            function.active = True
            function.save(update_fields=['active'])
            function.channels.set(applicable_channels)

        for name, kind, channel_key in structure_units:
            physical_location = None
            if name in {'Drogasil · Bourbon', 'Drogasil · Bourbon Shopping'}:
                physical_location, _ = PhysicalLocation.objects.get_or_create(
                    external_key='shopping-bourbon-drogasil',
                    defaults={
                        'name': 'Drogasil · Bourbon Shopping', 'cep': BOURBON_POSTAL_CODE,
                        'city': 'São Paulo', 'state': 'SP',
                        'latitude': BOURBON_COORDINATES[0], 'longitude': BOURBON_COORDINATES[1],
                    },
                )
            elif scenario['slug'] == 'bourbon-shopping':
                physical_location, _ = PhysicalLocation.objects.get_or_create(
                    external_key='shopping-bourbon',
                    defaults={
                        'name': 'Bourbon Shopping', 'cep': BOURBON_POSTAL_CODE,
                        'city': 'São Paulo', 'state': 'SP',
                        'latitude': BOURBON_COORDINATES[0], 'longitude': BOURBON_COORDINATES[1],
                    },
                )
            unit_kind = {
                'LOJA': ConfigBusinessUnit.UNIT_STORE,
                'QUIOSQUE': ConfigBusinessUnit.UNIT_KIOSK,
                'SERVICO': ConfigBusinessUnit.UNIT_SERVICE,
                'DISTRIBUICAO': ConfigBusinessUnit.UNIT_DISTRIBUTION,
                'FABRICA': ConfigBusinessUnit.UNIT_FACTORY,
                'REVENDA': ConfigBusinessUnit.UNIT_PARTNER,
            }.get(kind, ConfigBusinessUnit.UNIT_OTHER)
            is_shopping = physical_location is not None
            if is_shopping:
                location_type = ConfigBusinessUnit.LOCATION_SHOPPING
            elif kind in {'FABRICA', 'DISTRIBUICAO'}:
                location_type = ConfigBusinessUnit.LOCATION_INDUSTRIAL
            else:
                location_type = ConfigBusinessUnit.LOCATION_STREET
            demo_cep = BOURBON_POSTAL_CODE if is_shopping else ''
            unit, _ = ConfigBusinessUnit.objects.get_or_create(
                company=company,
                name=name,
                defaults={
                    'code': slugify(name)[:80],
                    'trade_name': name,
                    'external_reference': slugify(f'{scenario["slug"]}-{name}')[:120],
                    'unit_kind': unit_kind,
                    'location_type': location_type,
                    'active': True,
                    'channel': channel_by_key[channel_key],
                    'shopping_name': 'Bourbon Shopping' if is_shopping else '',
                    'cep': demo_cep,
                    'city': 'São Paulo',
                    'state': 'SP',
                    'physical_location': physical_location,
                    'opening_hours': {'mon-sat': '09:00-22:00'} if is_shopping else {},
                },
            )
            unit.channel = channel_by_key[channel_key]
            unit.physical_location = physical_location
            unit.active = True
            if not unit.code:
                unit.code = slugify(name)[:80]
            unit.trade_name = unit.trade_name or name
            unit.external_reference = unit.external_reference or slugify(f'{scenario["slug"]}-{name}')[:120]
            unit.unit_kind = unit_kind
            unit.location_type = location_type
            unit.shopping_name = 'Bourbon Shopping' if is_shopping else ''
            if is_shopping:
                unit.cep = BOURBON_POSTAL_CODE
                unit.city = 'São Paulo'
                unit.state = 'SP'
                unit.opening_hours = {'mon-sat': '09:00-22:00'}
            unit.save(update_fields=['channel', 'active', 'code', 'physical_location', 'trade_name',
                                     'external_reference', 'unit_kind', 'location_type', 'shopping_name',
                                     'cep', 'city', 'state', 'opening_hours'])

            # O terceiro nível é exercitado no cenário ElectraTech para
            # validar áreas/equipes sem obrigar shopping e farmácia a criá-lo.
            for area_name in OPERATIONAL_AREAS_BY_UNIT.get(name, []):
                ConfigOperationalUnit.objects.get_or_create(
                    business_unit=unit,
                    code=slugify(area_name)[:80],
                    defaults={'name': area_name, 'active': True},
                )

        self.ensure_administration_units(config_org, company, scenario)
        self.ensure_additional_config_companies(config_org, scenario)

    def ensure_administration_units(self, config_org, company, scenario):
        """Keep the shopping operator visible alongside its tenant companies."""
        for name, kind, channel_key in scenario.get('administration_units', ()):
            channel, _ = ConfigBusinessChannel.objects.get_or_create(
                company=company,
                name=channel_key.replace('_', ' ').title(),
                defaults={'active': True},
            )
            channel.active = True
            channel.save(update_fields=['active'])
            unit_kind = {
                'ADMINISTRACAO': ConfigBusinessUnit.UNIT_OTHER,
                'SERVICO': ConfigBusinessUnit.UNIT_SERVICE,
            }.get(kind, ConfigBusinessUnit.UNIT_OTHER)
            ConfigBusinessUnit.objects.update_or_create(
                company=company,
                name=name,
                defaults={
                    'code': slugify(name)[:80],
                    'trade_name': name,
                    'external_reference': slugify(f'{config_org.slug}-{name}')[:120],
                    'unit_kind': unit_kind,
                    'location_type': ConfigBusinessUnit.LOCATION_SHOPPING,
                    'active': True,
                    'channel': channel,
                    'shopping_name': 'Bourbon Shopping',
                    'cep': BOURBON_POSTAL_CODE,
                    'city': 'São Paulo',
                    'state': 'SP',
                    'opening_hours': {'mon-sat': '09:00-22:00'},
                },
            )

    def ensure_additional_config_companies(self, config_org, scenario):
        """Populate extra companies without creating parallel recruitment trees."""
        administration_company = ConfigCompany.objects.filter(
            organization=config_org, name=scenario['company'],
        ).first()
        for specification in scenario.get('additional_companies', ()):
            company, _ = ConfigCompany.objects.get_or_create(
                organization=config_org,
                name=specification['name'],
                defaults={'active': True},
            )
            company.active = True
            company.save(update_fields=['active'])

            channels = {}
            for _, _, channel_key in specification.get('units', ()):
                channel, _ = ConfigBusinessChannel.objects.get_or_create(
                    company=company,
                    name=channel_key.replace('_', ' ').title(),
                    defaults={'active': True},
                )
                channel.active = True
                channel.save(update_fields=['active'])
                channels[channel_key] = channel

            for service_code in specification.get('services', ()):
                OrganizationServiceSubscription.objects.update_or_create(
                    organization=config_org,
                    company=company,
                    service_code=service_code,
                    defaults={'status': OrganizationServiceSubscription.STATUS_ACTIVE, 'plan_code': f'demo-{config_org.slug}'},
                )

            unit_kinds = {
                'LOJA': ConfigBusinessUnit.UNIT_STORE,
                'QUIOSQUE': ConfigBusinessUnit.UNIT_KIOSK,
                'SERVICO': ConfigBusinessUnit.UNIT_SERVICE,
                'DISTRIBUICAO': ConfigBusinessUnit.UNIT_DISTRIBUTION,
            }
            for name, kind, channel_key in specification.get('units', ()):
                legacy_name = next(
                    (old_name for old_name, new_name in specification.get('legacy_unit_names', {}).items() if new_name == name),
                    None,
                )
                if administration_company and legacy_name:
                    legacy_unit = ConfigBusinessUnit.objects.filter(
                        company=administration_company, name=legacy_name,
                    ).first()
                    target_unit = ConfigBusinessUnit.objects.filter(company=company, name=name).first()
                    if legacy_unit and not target_unit:
                        legacy_unit.company = company
                        legacy_unit.name = name
                        legacy_unit.trade_name = name
                        legacy_unit.save(update_fields=['company', 'name', 'trade_name'])
                    elif legacy_unit and target_unit and legacy_unit.pk != target_unit.pk:
                        # Earlier additive runs created the target before the
                        # old unit could be rehomed. Preserve canonical links
                        # and remove only that duplicate demo row.
                        RecruitmentStore.objects.filter(legacy_id=legacy_unit.pk).update(legacy_id=target_unit.pk)
                        legacy_unit.delete()
                ConfigBusinessUnit.objects.update_or_create(
                    company=company,
                    name=name,
                    defaults={
                        'code': slugify(name)[:80],
                        'trade_name': name,
                        'external_reference': slugify(f'{config_org.slug}-{name}')[:120],
                        'unit_kind': unit_kinds.get(kind, ConfigBusinessUnit.UNIT_OTHER),
                        'location_type': ConfigBusinessUnit.LOCATION_INDUSTRIAL if kind == 'DISTRIBUICAO' else ConfigBusinessUnit.LOCATION_SHOPPING,
                        'active': True,
                        'channel': channels.get(channel_key),
                        'city': 'São Paulo',
                        'state': 'SP',
                    },
                )

    def ensure_recruitment_org(self, config_org, scenario):
        org, _ = RecruitmentOrganization.objects.get_or_create(
            slug=scenario['slug'],
            defaults={'external_id': scenario['slug'], 'name': scenario['name'], 'legacy_id': config_org.pk, 'active': True},
        )
        if org.legacy_id != config_org.pk or org.name != scenario['name']:
            org.legacy_id = config_org.pk; org.name = scenario['name']; org.active = True
            org.save(update_fields=['legacy_id', 'name', 'active'])
        return org

    def ensure_channels(self, company, scenario):
        names = sorted(set(item[2] for item in scenario['units']))
        return [RecruitmentChannel.objects.get_or_create(company=company, name=name.replace('_', ' ').title())[0] for name in names]

    def ensure_stores(self, org, company, channels, scenario, *, config_org=None):
        by_name = {channel.name.lower().replace(' ', '_'): channel for channel in channels}
        stores = []
        for index, (name, kind, channel_key) in enumerate(scenario['units']):
            canonical_unit = ConfigBusinessUnit.objects.filter(
                company__organization=config_org, name=name,
            ).first() if config_org else None
            channel = by_name.get(channel_key)
            is_bourbon_location = 'Bourbon' in name or scenario['slug'] == 'bourbon-shopping'
            postal_code = BOURBON_POSTAL_CODE if is_bourbon_location else f'013{10 + index:03d}00'
            latitude, longitude = BOURBON_COORDINATES if is_bourbon_location else (None, None)
            physical_unit = None
            if 'Drogasil' in name and 'Bourbon' in name:
                physical_unit, _ = RecruitmentPhysicalUnit.objects.get_or_create(
                    external_key='shopping-bourbon-drogasil',
                    defaults={
                        'name': 'Drogasil · Bourbon Shopping',
                        'postal_code': BOURBON_POSTAL_CODE,
                        'city': 'São Paulo',
                        'state': 'SP',
                    },
                )
            store, _ = RecruitmentStore.objects.get_or_create(
                organization=org, company=company, name=name,
                defaults={
                    'legacy_id': canonical_unit.pk if canonical_unit else None,
                    'code': f'{kind}-{slugify(name)[:35]}', 'channel': channel,
                    'physical_unit': physical_unit, 'active': True,
                    'postal_code': postal_code, 'latitude': latitude, 'longitude': longitude,
                },
            )
            if canonical_unit and store.legacy_id != canonical_unit.pk:
                store.legacy_id = canonical_unit.pk
                store.save(update_fields=['legacy_id'])
            if (store.channel_id != getattr(channel, 'pk', None) or store.postal_code != postal_code
                    or store.latitude != latitude or store.longitude != longitude
                    or store.physical_unit_id != getattr(physical_unit, 'pk', None) or not store.active):
                store.channel = channel; store.physical_unit = physical_unit; store.active = True; store.postal_code = postal_code
                store.latitude = latitude; store.longitude = longitude
                store.save(update_fields=['channel', 'physical_unit', 'active', 'postal_code', 'latitude', 'longitude'])
            stores.append(store)
        return stores

    def ensure_functions(self, org, company, channels, scenario):
        functions = []
        for name in scenario['functions']:
            func, _ = RecruitmentJobFunction.objects.get_or_create(organization=org, company=company, name=name, defaults={'active': True})
            func.channels.set(channels)
            functions.append(func)
        return functions

    def allowed_functions_for_store(self, store, scenario):
        """Retorna o catálogo local aplicável à unidade, não o catálogo global."""
        if scenario['slug'] == 'drogasil-rede':
            return (
                {'Estoquista', 'Supervisor(a)'}
                if 'Distribuição' in (store.channel.name if store.channel else '')
                else {'Atendente de farmácia', 'Balconista de farmácia', 'Farmacêutico(a)', 'Caixa', 'Estoquista', 'Gerente de loja', 'Supervisor(a)'}
            )
        if scenario['slug'] == 'bourbon-shopping':
            category = (store.channel.name or '').lower().replace(' ', '_') if store.channel else ''
            return SHOPPING_FUNCTIONS_BY_CATEGORY.get(category, {'Atendente de loja', 'Vendedor(a)', 'Caixa', 'Estoquista', 'Gerente de loja', 'Supervisor(a)'})
        if scenario['slug'] == 'electratech-demo':
            channel_key = (store.channel.name or '').lower().replace(' ', '_') if store.channel else ''
            return ELECTRATECH_FUNCTIONS_BY_CHANNEL.get(channel_key, set())
        return set(scenario.get('functions', []))

    def ensure_canonical_mappings(self, org, stores, functions, scenario):
        """Garante que todo cargo demo use termos do catálogo do candidato."""
        catalog, _ = CanonicalCatalog.objects.get_or_create(
            code='market-default', version=1,
            defaults={
                'name': 'Funções canônicas de mercado',
                'status': CanonicalCatalog.STATUS_PUBLISHED,
                'source': 'system_default',
            },
        )
        for store in stores:
            allowed_names = self.allowed_functions_for_store(store, scenario)
            allowed_ids = [function.pk for function in functions if function.name in allowed_names]
            # Corrige seeds anteriores sem apagar o cargo da empresa: apenas
            # desativa o vínculo canônico que não pertence a esta unidade.
            CanonicalFunctionMapping.objects.filter(
                organization=org, business_unit=store,
            ).exclude(job_function_id__in=allowed_ids).update(active=False)

        for function in functions:
            codes = CANONICAL_BY_FUNCTION.get(function.name, [slugify(function.name)])
            for code in codes:
                label = code.replace('-', ' ').title()
                term, _ = CanonicalTerm.objects.get_or_create(
                    catalog=catalog, code=code,
                    defaults={
                        'term_type': CanonicalTerm.TYPE_FUNCTION,
                        'label': label,
                        'active': True,
                    },
                )
                for store in stores:
                    if function.name not in self.allowed_functions_for_store(store, scenario):
                        continue
                    CanonicalFunctionMapping.objects.update_or_create(
                        term=term, job_function=function, organization=org,
                        business_unit=store,
                        defaults={
                            'local_label': function.name,
                            'source': 'demo_store_catalog',
                            'active': True,
                        },
                    )

    def ensure_user_and_actor(self, org, config_org, store, scenario):
        username = f"gestor_{scenario['slug']}"
        user, _ = User.objects.get_or_create(username=username, defaults={'email': f'{username}@matchco.demo', 'is_active': True})
        user.set_password('demo123'); user.is_staff = True; user.is_active = True; user.save()
        Membership.objects.get_or_create(user=user, organization=config_org, defaults={'role': 'admin', 'active': True, 'is_primary': False})
        EmployerActor.objects.update_or_create(user=user, organization=org, business_unit=None, defaults={'authority_scopes': SHOPPING_SCOPES, 'human_verified_at': timezone.now(), 'active': True})
        return user

    def ensure_platform_binding(self, recruitment_org, config_org):
        RecruitmentPlatformBinding.objects.update_or_create(
            recruitment_organization=recruitment_org,
            platform_organization_id=config_org.pk,
            defaults={
                'capabilities': ['talk', 'courses', 'certifications', 'audiences'],
                'active': True,
            },
        )

    def ensure_entry_points(self, org, stores, scenario):
        result = []
        for store in stores:
            ep, _ = EntryPoint.objects.get_or_create(organization=org, label=f'QR Match · {store.name}', defaults={'kind': EntryPoint.KIND_STORE, 'scope_store': store, 'mode': EntryPoint.MODE_MATCH, 'experience_template': scenario['market'] if scenario['market'] in dict(EntryPoint.EXPERIENCE_CHOICES) else 'generic', 'purpose': EntryPoint.PURPOSE_RECRUITMENT, 'audience': EntryPoint.AUDIENCE_CANDIDATE, 'audience_role': EntryPoint.AUDIENCE_ROLE_CANDIDATE, 'canonical_destination_url': 'https://direct.ddns.net/qr/pending/', 'state': EntryPoint.STATE_ACTIVE})
            ep.scope_store = store
            ep.scope_shopping_id = 'bourbon-shopping' if scenario['slug'] == 'bourbon-shopping' or 'Bourbon' in store.name else ''
            ep.scope_network_id = scenario['slug']
            ep.mode = EntryPoint.MODE_MATCH
            ep.state = EntryPoint.STATE_ACTIVE
            ep.brand_name = scenario['brand']
            ep.canonical_destination_url = f'https://direct.ddns.net/qr/{ep.pk}/'
            ep.save(update_fields=[
                'scope_store', 'scope_shopping_id', 'scope_network_id', 'mode',
                'state', 'brand_name', 'canonical_destination_url', 'updated_at',
            ])
            result.append(ep)
        return result

    def ensure_templates(self, org, functions, scenario):
        call_command('seed_questionnaire_templates', organization=org.slug)
        function_map = {function.name: function for function in functions}
        if scenario['market'] == 'shopping':
            specs = [('Vendedor(a)', 'vendedor', 'salesperson', [('customer_scenario', 'Como você atenderia uma pessoa indecisa?', 'textarea', [], True)]), ('Gerente de loja', 'gerente', 'manager', [('leadership_case', 'Conte uma situação em que liderou uma equipe em um dia de alta demanda.', 'textarea', [], True)])]
        elif scenario['market'] == 'pharma':
            specs = [('Farmacêutico(a)', 'farmaceutico', 'technician', [('regulatory_training', 'Quais registros e treinamentos profissionais você possui?', 'textarea', [], True)]), ('Representante comercial', 'representante', 'salesperson', [('product_education', 'Como você explicaria um produto técnico para uma farmácia parceira?', 'textarea', [], True)])]
        else:
            specs = [('Técnico(a) de suporte', 'suporte', 'technician', [('technical_case', 'Descreva um diagnóstico técnico que você realizou.', 'textarea', [], True)]), ('Gerente de canal', 'canal', 'manager', [('partner_case', 'Como você desenvolveria uma revenda com baixa ativação?', 'textarea', [], True)])]
        for function_name, code, role, questions in specs:
            function = function_map.get(function_name)
            if not function:
                continue
            template, _ = QuestionnaireTemplate.objects.get_or_create(organization=org, code=f'role-{code}', version=1, defaults={'name': f'{function_name} · perguntas específicas', 'description': 'Variação curta aplicada somente a esta função.', 'status': QuestionnaireTemplate.STATUS_PUBLISHED, 'scope_job_function': function, 'audience_role': role, 'is_default': False, 'source': 'seed'})
            if not template.scope_job_function_id:
                template.scope_job_function = function; template.status = QuestionnaireTemplate.STATUS_PUBLISHED; template.save(update_fields=['scope_job_function', 'status'])
            for order, (key, label, field_type, options, required) in enumerate(questions, 20):
                QuestionnaireQuestion.objects.get_or_create(template=template, key=key, defaults={'label': label, 'field_type': field_type, 'options': options, 'required': required, 'order': order})

    def demo_answer(self, question, index, scenario, function_name):
        """Return a useful, deterministic answer for the demo form."""
        answers = {
            'experience': f'{index + 1} anos em atendimento e operação de {scenario["name"]}.',
            'skills': 'Atendimento, organização de rotina, comunicação e trabalho em equipe.',
            'availability': 'Disponibilidade para escala comercial, inclusive alguns finais de semana.',
            'routine': 'Organizo prioridades, acompanho as metas do turno e peço apoio quando a demanda aumenta.',
            'sales_experience': 'Experiência com atendimento consultivo, demonstração de produtos e acompanhamento de clientes.',
            'customer_scenario': 'Faço perguntas para entender a necessidade, apresento opções com clareza e acompanho a decisão sem pressionar.',
            'leadership_case': 'Redistribuí a equipe por prioridade, mantive a comunicação objetiva e acompanhei o atendimento até normalizar o fluxo.',
            'technical_case': 'Recolhi os sintomas, reproduzi o problema, isolei a causa e registrei a solução para evitar recorrência.',
            'partner_case': 'Mapeio o motivo da baixa ativação, combino uma meta de curto prazo e acompanho a revenda com treinamento e materiais.',
            'product_education': 'Traduzo a característica técnica em benefício para o cliente e confirmo se a equipe da farmácia consegue explicar o uso corretamente.',
            'regulatory_training': 'Treinamentos de boas práticas, atendimento seguro e atualização dos procedimentos exigidos para a função.',
            'certifications': 'Treinamentos de produto, segurança operacional e atendimento ao cliente.',
            'specialty': f'{function_name} e operação orientada ao cliente.',
            'health_role': 'Atendimento e operação de serviços de saúde.',
            'patient_customer_care': 'Confirmo a necessidade, explico os próximos passos em linguagem simples e preservo a privacidade da pessoa.',
        }
        if question.field_type in ('single_choice', 'boolean', 'scale') and question.options:
            return question.options[index % len(question.options)]
        if question.field_type == 'multiple_choice' and question.options:
            start = index % len(question.options)
            return [question.options[start], question.options[(start + 1) % len(question.options)]] if len(question.options) > 1 else [question.options[0]]
        return answers.get(question.key, f'Resposta demonstrativa de {function_name} para o cenário {scenario["name"]}.')

    def ensure_candidates(self, org, stores, functions, entry_points, scenario):
        rnd = random.Random(scenario['slug'])
        candidates = []
        for index in range(12):
            first = ['Ana', 'Bruno', 'Carla', 'Diego', 'Elisa', 'Fábio', 'Gabi', 'Henrique', 'Íris', 'João', 'Karen', 'Lucas'][index]
            email = f'{first.lower()}.{slugify(scenario["slug"])}@matchco.demo'
            identity, _ = CandidateIdentity.objects.get_or_create(email_normalized=email, defaults={'phone_normalized': f'1198{index:07d}'})
            ep = entry_points[index % len(entry_points)]
            profile, _ = CandidateProfile.objects.get_or_create(organization=org, email=email, defaults={'identity': identity, 'first_name': first, 'last_name': 'Demo', 'phone': f'1198{index:07d}', 'city': 'São Paulo', 'state': 'SP', 'experience_years': rnd.choice([0, 1, 2, 4, 7]), 'preferred_store': ep.scope_store, 'qr_id': str(ep.pk), 'visibility_match': True, 'interest_categories': [scenario['market'], 'atendimento']})
            function = functions[index % len(functions)]
            profile.job_functions.set([function])
            profile.identity = identity
            profile.cep = (SAO_PAULO_DEMO_CEPS[index % len(SAO_PAULO_DEMO_CEPS)]
                           if scenario['slug'] == 'bourbon-shopping'
                           else f'013{10 + index % 5:03d}00')
            if scenario['slug'] == 'bourbon-shopping':
                profile.latitude, profile.longitude = SAO_PAULO_DEMO_COORDINATES[index % len(SAO_PAULO_DEMO_COORDINATES)]
            profile.availability_days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat'] if index % 3 else ['thu', 'fri', 'sat', 'sun']
            profile.availability_period = ['morning', 'afternoon', 'evening'][index % 3]
            profile.preferred_work_format = Position.FORMAT_TEMPORARIO if index % 4 == 0 else Position.FORMAT_FIXO
            profile.available_from = date.today() + timedelta(days=index % 5)
            profile.circulation_state = CandidateProfile.CIRCULATION_ALLOWED
            profile.visibility_match = True
            profile.save(update_fields=['identity', 'cep', 'latitude', 'longitude', 'availability_days', 'availability_period', 'preferred_work_format', 'available_from', 'circulation_state', 'visibility_match', 'updated_at'])
            record_candidate_context(
                candidate=profile, entry_point=ep,
                metadata={'via': 'market_demo_seed', 'qr_id': str(ep.pk)},
            )
            mapped_terms = CanonicalTerm.objects.filter(
                function_mappings__job_function=function,
                function_mappings__business_unit=ep.scope_store,
                function_mappings__active=True,
                active=True,
            ).distinct()
            for term in mapped_terms:
                if CandidateCanonicalResponse.objects.filter(
                    candidate=profile, term=term,
                    purpose=CandidateCanonicalResponse.PURPOSE_DISTRIBUTION,
                    source_reference=f'demo:{ep.pk}', revoked_at__isnull=True,
                ).exists():
                    continue
                record_canonical_response(
                    candidate=profile, term=term,
                    scope=CandidateCanonicalResponse.SCOPE_UNIT,
                    purpose=CandidateCanonicalResponse.PURPOSE_DISTRIBUTION,
                    origin=CandidateCanonicalResponse.ORIGIN_QR,
                    organization=org, business_unit=ep.scope_store,
                    value={
                        'interest_mode': 'want' if index % 3 else 'learn',
                        'experience': 'first_job' if profile.experience_years == 0 else 'experienced',
                        'work_format': profile.preferred_work_format,
                    }, consented_at=timezone.now(),
                    source_reference=f'demo:{ep.pk}',
                )
            questionnaire = resolve_questionnaire(profile)
            if questionnaire:
                answers = {}
                for question in questionnaire.questions.filter(active=True):
                    answers[question.key] = self.demo_answer(question, index, scenario, function.name)
                CandidateProfileSurveyResponse.objects.update_or_create(
                    candidate=profile,
                    defaults={'organization': org, 'questionnaire_template': questionnaire, 'responses': answers},
                )
                profile.onboarding_completed = True
                profile.save(update_fields=['onboarding_completed', 'updated_at'])
            purposes = [CandidateConsent.PURPOSE_CIRCULATION_STORE]
            if index % 2 == 0 and ep.scope_shopping_id:
                purposes.append(CandidateConsent.PURPOSE_CIRCULATION_SHOPPING)
            if index % 3 == 0:
                purposes.append(CandidateConsent.PURPOSE_CIRCULATION_NETWORK)
            purposes.append(CandidateConsent.PURPOSE_TRANSACTIONAL_MESSAGING)
            for purpose in purposes:
                CandidateConsent.objects.update_or_create(
                    identity=identity, organization=org, purpose=purpose,
                    source=f'entry_point:{ep.pk}',
                    defaults={
                        'granted': True, 'revoked_at': None,
                        'policy_version': 'demo-v1',
                        'legal_basis': CandidateConsent.BASIS_CONSENT,
                    },
                )
            candidates.append(profile)
        return candidates

    def ensure_positions(self, org, stores, functions, scenario):
        positions = []
        for index, function in enumerate(functions[:6]):
            store = stores[index % len(stores)]
            is_classic = any(term in function.name.lower() for term in ('gerente', 'supervisor', 'técnico', 'analista', 'especialista', 'coordenador'))
            mode = Position.MODE_MATCH
            title = f'{function.name} · {store.name}'
            position, _ = Position.objects.get_or_create(organization=org, business_unit=store, job_function=function, title=title, defaults={'description': f'Oportunidade demonstrativa para {scenario["name"]}.', 'requirements': 'Disponibilidade e interesse pela função.', 'workplace': store.name, 'schedule': 'Segunda a sábado · escala da unidade', 'work_format': Position.FORMAT_TEMPORARIO if index % 3 == 0 else Position.FORMAT_FIXO, 'starts_at': date.today() + timedelta(days=7 + index), 'city': 'São Paulo', 'state': 'SP', 'mode': mode, 'tag': Position.TAG_PRECISA, 'state': Position.STATE_ACTIVATED, 'pre_interest_set_complete': True, 'activated_at': timezone.now()})
            OpportunityCriterion.objects.get_or_create(opportunity=position, label='Disponibilidade compatível', defaults={'weight': OpportunityCriterion.WEIGHT_REQUIRED})
            position.mode = mode; position.state = Position.STATE_ACTIVATED; position.pre_interest_set_complete = True; position.active = True
            position.required_days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
            position.required_period = ['morning', 'afternoon', 'evening'][index % 3]
            position.required_experience = Position.EXPERIENCE_ANY if index % 2 else Position.EXPERIENCE_SIMILAR
            position.requested_slots = 2; position.invite_batch_size = 4
            position.negotiable_fields = ['period', 'start_date', 'work_format']
            position.save(update_fields=['mode', 'state', 'pre_interest_set_complete', 'active', 'required_days', 'required_period', 'required_experience', 'requested_slots', 'invite_batch_size', 'negotiable_fields', 'updated_at'])
            terms = CanonicalTerm.objects.filter(function_mappings__job_function=function, function_mappings__business_unit=store, function_mappings__active=True, active=True).distinct()
            for term in terms:
                OpportunityCanonicalRequirement.objects.get_or_create(position=position, term=term, defaults={'requirement': OpportunityCanonicalRequirement.REQUIRED, 'source': 'demo_store_catalog'})
            positions.append(position)
        return positions

    def ensure_candidate_activity(self, candidates, positions, manager):
        """Populate only Match relations for high-turnover opportunities."""
        for position in positions:
            eligible = [candidate for candidate in candidates if candidate.preferred_store_id == position.business_unit_id and candidate_is_eligible_for_position(candidate=candidate, position=position)]
            if not eligible:
                eligible = [candidate for candidate in candidates if candidate_is_eligible_for_position(candidate=candidate, position=position)]
            for candidate in eligible[:2]:
                relation = deliver_opportunity_notice(candidate=candidate, opportunity=position)
                if relation.state == Relation.STATE_NOTICE_DELIVERED:
                    person_interested(relation=relation)
                    relation.refresh_from_db()
                if relation.state == Relation.STATE_EMPLOYER_INTEREST_VIEW:
                    try:
                        employer_interested(relation=relation, actor=manager)
                    except Exception:
                        # The data remains useful even if a demo actor has a
                        # different authority configuration in an old install.
                        pass
