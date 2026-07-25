from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.management.color import no_style
from django.core.management import CommandError
from django.core.management.base import BaseCommand
from django.core.management.sql import sql_flush
from django.db import connection, transaction
from django.utils import timezone
from django.utils.text import slugify

from audience.models import AudiencePolicy, AudienceRule
from configuration.models import (
    BusinessChannel, BusinessUnit, Company, JobFunction, ManagementAssignment,
    Membership, OperationalUnit, Organization, OrganizationTerminology, PersonType,
)
from courses.models import Answer, Content, Course, Module, Question, Quiz, Subject, Text, Video
from documents.models import Document, DocumentEvent, DocumentPermission, DocumentVersion
from gamification.models import GamificationSettings
from learning.models import ContentEvent, ContentTrail, TrailStep, TrailAssignment
from publishing.models import ContentFeedback, Publication, Tag
from user_management.models import InvitationCode


class Command(BaseCommand):
    help = 'Create the repeatable Hospital Generative + Seguradora Generative enterprise demonstration with Documents, Progressive Growth, and Analytics.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Flush all application data before seeding.')
        parser.add_argument('--yes', action='store_true', help='Confirm the destructive reset.')
        parser.add_argument('--dry-run', action='store_true', help='Show the plan without changing the database.')
        parser.add_argument('--admin-username', default='admin')
        parser.add_argument('--admin-email', default='admin@talk.local')
        parser.add_argument('--admin-password', default='Admin@Talk123!')

    def handle(self, *args, **options):
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY-RUN: nenhuma alteração será feita.'))
            self.stdout.write('Reset: todos os dados seriam removidos, exceto o administrador recriado.')
            self.stdout.write('Seed: Hospital Generative + Seguradora Generative com Documents, Progressive Growth, Feedback, e Analytics simulado.')
            return
        if options['reset'] and not options['yes']:
            raise CommandError('O reset é destrutivo. Execute novamente com --reset --yes.')
        if options['reset']:
            self.reset_database()
            self.stdout.write(self.style.WARNING('Base limpa. Criando o administrador protegido.'))
        with transaction.atomic():
            admin = self.ensure_admin(options)
            self.seed(admin)
        self.stdout.write(self.style.SUCCESS('Demonstrações Hospital Generative e Seguradora Generative criadas com sucesso!'))

    def reset_database(self):
        """Flush application tables with PostgreSQL cascade, preserving the schema/migrations."""
        statements = sql_flush(no_style(), connection, reset_sequences=True, allow_cascade=True)
        connection.ops.execute_sql_flush(statements)

    def ensure_admin(self, options):
        User = get_user_model()
        admin = User.objects.filter(is_superuser=True).order_by('id').first()
        if admin:
            return admin
        admin = User.objects.create_superuser(
            username=options['admin_username'],
            email=options['admin_email'],
            password=options['admin_password'],
        )
        return admin

    def seed(self, admin):
        org, _ = Organization.objects.update_or_create(
            slug='hospital-generative', defaults={'name': 'Hospital Generative', 'active': True}
        )
        OrganizationTerminology.objects.update_or_create(
            organization=org,
            defaults={
                'level_1_label': 'Grupo',
                'level_1_description': 'Grupo hospitalar e sua governança corporativa.',
                'level_2_label': 'Hospital ou operação',
                'level_2_description': 'Hospital, centro de consultas ou instituto especializado.',
                'level_3_label': 'Unidade ou departamento',
                'level_3_description': 'Serviço, departamento, especialidade ou equipe local.',
            },
        )
        group, _ = Company.objects.update_or_create(
            organization=org, name='Grupo Hospital Generative', defaults={'code': 'GHG', 'active': True}
        )
        units = self.create_units(group)
        channels = self.create_channels(group)
        person_types = self.create_person_types(org)
        functions = self.create_functions(group, channels)
        GamificationSettings.objects.update_or_create(
            description='Hospital Generative Demo',
            defaults={
                'ap_first_login': True,
                'dp_first_login': 1,
                'ap_feed_post_view': True,
                'dp_feed_post_view': 1,
                'ap_course_enrollment': True,
                'dp_course_enrollment': 5,
                'ap_course_completation': True,
                'dp_course_completation': 20,
                'ap_passed_tests': True,
                'dp_passed_tests': 10,
            },
        )
        users = self.create_users(admin, org, group, units, channels, person_types, functions)
        self.create_managers(admin, org, group, units)
        self.create_content(admin, org, group, units, channels, person_types, functions)
        self.create_trails(admin, org, group, 'hospital')
        self.create_hospital_documents(admin, org, group, units, users)
        self.create_analytics_and_feedback(admin, org)
        InvitationCode.objects.update_or_create(
            code='HOSPITAL-GENERATIVE-2026',
            defaults={'organization': org, 'company': group, 'business_unit': None, 'operational_unit': None, 'person_type': person_types.get('colaborador'), 'issued_by': admin, 'max_uses': 100, 'active': True},
        )
        self.stdout.write(f'✅ {len(users)} usuários Hospital Generative preparados.')
        self.seed_insurance(admin)

    def seed_insurance(self, admin):
        """Seed a second tenant using the same configurable enterprise model."""
        org, _ = Organization.objects.update_or_create(
            slug='seguradora-generative', defaults={'name': 'Seguradora Generative', 'active': True}
        )
        OrganizationTerminology.objects.update_or_create(
            organization=org,
            defaults={
                'level_1_label': 'Grupo segurador',
                'level_1_description': 'Grupo econômico e suas empresas de seguros e serviços financeiros.',
                'level_2_label': 'Operação ou regional',
                'level_2_description': 'Ramo de negócio, regional, unidade administrativa ou canal próprio.',
                'level_3_label': 'Unidade ou equipe',
                'level_3_description': 'Departamento, célula, carteira ou equipe responsável pela operação.',
            },
        )
        company, _ = Company.objects.update_or_create(
            organization=org, name='Seguradora Generative', defaults={'code': 'SG', 'active': True}
        )
        units = self.create_insurance_units(company)
        channels = self.create_insurance_channels(company)
        person_types = self.create_insurance_person_types(org)
        functions = self.create_insurance_functions(company, channels)
        users = self.create_insurance_users(admin, org, company, units, channels, person_types, functions)
        self.create_insurance_manager(admin, org, company, units)
        self.create_insurance_content(admin, org, company, units)
        self.create_trails(admin, org, company, 'insurance')
        self.create_insurance_documents(admin, org, company, units, users)
        self.create_analytics_and_feedback(admin, org)
        InvitationCode.objects.update_or_create(
            code='SEGURADORA-GENERATIVE-2026',
            defaults={'organization': org, 'company': company, 'business_unit': None, 'operational_unit': None, 'person_type': person_types.get('colaborador'), 'issued_by': admin, 'max_uses': 100, 'active': True},
        )
        self.stdout.write(f'✅ {len(users)} usuários Seguradora Generative preparados.')
        self.create_demo_account()

    def create_demo_account(self):
        User = get_user_model()
        demo, created = User.objects.get_or_create(username='demo', defaults={'email': 'demo@talk.local', 'first_name': 'Conta', 'last_name': 'Demo', 'is_demo': True, 'is_active': True})
        demo.email = 'demo@talk.local'
        demo.first_name, demo.last_name, demo.is_demo, demo.is_active = 'Conta', 'Demo', True, True
        if created or not demo.has_usable_password():
            demo.set_password('TalkDemo123!')
        demo.save()
        hospital = Organization.objects.filter(slug='hospital-generative').first()
        hospital_company = hospital.companies.order_by('id').first() if hospital else None
        hospital_unit = hospital_company.business_units.order_by('id').first() if hospital_company else None
        hospital_operational = hospital_unit.operational_units.order_by('id').first() if hospital_unit else None
        insurance = Organization.objects.get(slug='seguradora-generative')
        insurance_company = insurance.companies.order_by('id').first()
        insurance_unit = insurance_company.business_units.order_by('id').first()
        insurance_operational = insurance_unit.operational_units.order_by('id').first()
        if hospital_company and hospital_unit and hospital_operational:
            Membership.objects.update_or_create(user=demo, company=hospital_company, business_unit=hospital_unit, operational_unit=hospital_operational, defaults={'organization': hospital, 'active': True, 'is_primary': True})
        Membership.objects.update_or_create(user=demo, company=insurance_company, business_unit=insurance_unit, operational_unit=insurance_operational, defaults={'organization': insurance, 'active': True, 'is_primary': False})

    def create_insurance_units(self, company):
        structure = {
            'corporativo': ('Operação Corporativa', ['Governança e riscos', 'Compliance e controles', 'Produtos e subscrição', 'Tecnologia e dados']),
            'sao-paulo': ('Regional São Paulo', ['Comercial e corretores', 'Sinistros Auto', 'Sinistros Patrimoniais', 'Atendimento']),
            'rio-de-janeiro': ('Regional Rio de Janeiro', ['Comercial e corretores', 'Sinistros Auto', 'Assistência 24 horas', 'Atendimento']),
            'minas-gerais': ('Regional Minas Gerais', ['Comercial e corretores', 'Regulação de sinistros', 'Atendimento']),
            'central-relacionamento': ('Central de Relacionamento', ['Call center', 'Ouvidoria', 'Retenção e qualidade']),
            'operacao-digital': ('Operação Digital', ['Vendas digitais', 'Portal do cliente', 'Jornada e analytics']),
        }
        result = {}
        for code, (name, teams) in structure.items():
            unit, _ = BusinessUnit.objects.update_or_create(company=company, code=f'sg-{code}', defaults={'name': name, 'active': True})
            result[code] = (unit, {})
            for team in teams:
                operational, _ = OperationalUnit.objects.update_or_create(
                    business_unit=unit, name=team, defaults={'code': slugify(f'sg-{code}-{team}'), 'active': True}
                )
                result[code][1][team] = operational
        return result

    def create_insurance_channels(self, company):
        names = ['Corretores', 'Assessorias e brokers', 'Bancos e parceiros', 'Afinidades e varejo', 'Vendas digitais', 'Central de atendimento', 'Prestadores credenciados', 'Clientes e empresas', 'Gestão corporativa']
        return {name: BusinessChannel.objects.update_or_create(company=company, name=name, defaults={'active': True})[0] for name in names}

    def create_insurance_person_types(self, org):
        values = {
            'colaborador': ('Colaborador', 'Profissional contratado pela seguradora.'),
            'gestor': ('Gestor', 'Responsável por pessoas, operação ou carteira.'),
            'corretor': ('Corretor', 'Profissional ou representante de distribuição de seguros.'),
            'parceiro': ('Parceiro comercial', 'Banco, assessoria, afinidade ou parceiro de distribuição.'),
            'prestador': ('Prestador credenciado', 'Oficina, assistência, clínica, vistoriador ou regulador.'),
            'cliente': ('Cliente', 'Pessoa física ou representante de empresa segurada.'),
            'auditor': ('Auditor', 'Profissional de auditoria, controles ou conformidade.'),
        }
        return {code: PersonType.objects.update_or_create(organization=org, code=code, defaults={'name': name, 'description': description, 'active': True})[0] for code, (name, description) in values.items()}

    def create_insurance_functions(self, company, channels):
        names = ['Diretor de operações', 'Gerente regional', 'Gerente de canais', 'Corretor de seguros', 'Executivo de contas', 'Analista de produtos', 'Subscritor', 'Analista de riscos', 'Regulador de sinistros', 'Analista de sinistros', 'Atendente de relacionamento', 'Ouvidor', 'Analista de compliance', 'Analista de dados', 'Prestador de assistência', 'Vistoriador', 'Auditor interno']
        result = {}
        for name in names:
            function, _ = JobFunction.objects.update_or_create(company=company, name=name, defaults={'active': True})
            if 'corretor' in name.lower() or 'canal' in name.lower() or 'contas' in name.lower():
                function.channels.set([channels['Corretores'], channels['Assessorias e brokers']])
            elif 'prestador' in name.lower() or 'vistoriador' in name.lower() or 'regulador' in name.lower():
                function.channels.set([channels['Prestadores credenciados']])
            else:
                function.channels.set([channels['Gestão corporativa']])
            result[name] = function
        return result

    def _insurance_operational(self, units, unit_code, team):
        return units[unit_code][1][team]

    def create_insurance_users(self, admin, org, company, units, channels, person_types, functions):
        User = get_user_model()
        profiles = [
            ('sg.gestor', 'Helena', 'Martins', 'gestor', 'Gerente regional', 'sao-paulo', 'Comercial e corretores', 'Corretores'),
            ('sg.corretor', 'André', 'Barbosa', 'corretor', 'Corretor de seguros', 'sao-paulo', 'Comercial e corretores', 'Corretores'),
            ('sg.subscritor', 'Beatriz', 'Moura', 'colaborador', 'Subscritor', 'corporativo', 'Produtos e subscrição', 'Gestão corporativa'),
            ('sg.sinistros', 'Carlos', 'Pires', 'colaborador', 'Analista de sinistros', 'rio-de-janeiro', 'Sinistros Auto', 'Gestão corporativa'),
            ('sg.atendimento', 'Daniela', 'Ramos', 'colaborador', 'Atendente de relacionamento', 'central-relacionamento', 'Call center', 'Central de atendimento'),
            ('sg.prestador', 'Eduardo', 'Nunes', 'prestador', 'Prestador de assistência', 'rio-de-janeiro', 'Assistência 24 horas', 'Prestadores credenciados'),
            ('sg.cliente', 'Fátima', 'Demo', 'cliente', None, 'operacao-digital', 'Portal do cliente', 'Clientes e empresas'),
        ]
        users = []
        for index in range(1, 4):
            for prefix, first, last, person_code, function_name, unit_code, team, channel_name in profiles:
                username = f'{prefix}.{index:02d}'
                user, created = User.objects.get_or_create(username=username, defaults={'email': f'{username}@seguradora-generative.demo', 'first_name': first, 'last_name': last})
                user.email, user.first_name, user.last_name = f'{username}@seguradora-generative.demo', first, last
                if created:
                    user.set_password('TalkDemo123!')
                user.save()
                unit = units[unit_code][0]
                operational = self._insurance_operational(units, unit_code, team)
                membership, _ = Membership.objects.update_or_create(user=user, company=company, business_unit=unit, operational_unit=operational, defaults={'organization': org, 'person_type': person_types[person_code], 'active': True, 'is_primary': True})
                membership.channels.set([channels[channel_name]])
                if function_name:
                    membership.functions.set([functions[function_name]])
                users.append(user)

        multi, created = User.objects.get_or_create(username='sg.executivo.multi', defaults={'email': 'sg.executivo.multi@demo.local', 'first_name': 'Rafael', 'last_name': 'Multiempresa'})
        if created:
            multi.set_password('TalkDemo123!')
        multi.save()
        hospital = Organization.objects.filter(slug='hospital-generative').first()
        hospital_company = hospital.companies.order_by('id').first() if hospital else None
        hospital_unit = hospital_company.business_units.order_by('id').first() if hospital_company else None
        hospital_operational = hospital_unit.operational_units.order_by('id').first() if hospital_unit else None
        if hospital_company and hospital_unit and hospital_operational:
            Membership.objects.update_or_create(user=multi, company=hospital_company, business_unit=hospital_unit, operational_unit=hospital_operational, defaults={'organization': hospital, 'active': True, 'is_primary': True})
        membership, _ = Membership.objects.update_or_create(user=multi, company=company, business_unit=units['corporativo'][0], operational_unit=self._insurance_operational(units, 'corporativo', 'Governança e riscos'), defaults={'organization': org, 'active': True, 'is_primary': False, 'person_type': person_types['gestor']})
        membership.channels.set([channels['Gestão corporativa']])
        membership.functions.set([functions['Diretor de operações']])
        return users

    def create_insurance_manager(self, admin, org, company, units):
        ManagementAssignment.objects.update_or_create(user=admin, organization=org, company=None, business_unit=None, operational_unit=None, role='people_admin', defaults={'active': True})
        manager = get_user_model().objects.filter(username='sg.gestor.01').first()
        if manager:
            ManagementAssignment.objects.update_or_create(user=manager, organization=org, company=company, business_unit=units['sao-paulo'][0], operational_unit=None, role='people_admin', defaults={'active': True})

    def create_insurance_content(self, admin, org, company, units):
        subjects = {name: Subject.objects.update_or_create(slug=slugify(f'sg-{name}'), defaults={'title': name})[0] for name in ['Produtos e coberturas', 'Distribuição', 'Subscrição e riscos', 'Sinistros', 'Atendimento e experiência', 'Compliance e controles']}
        course_data = [
            ('sg-produtos', 'Portfólio de seguros e coberturas', 'Produtos e coberturas'),
            ('sg-corretor', 'Jornada do corretor Generative', 'Distribuição'),
            ('sg-subscricao', 'Fundamentos de subscrição e risco', 'Subscrição e riscos'),
            ('sg-sinistros', 'Regulação e atendimento de sinistros', 'Sinistros'),
            ('sg-atendimento', 'Atendimento humanizado ao segurado', 'Atendimento e experiência'),
            ('sg-compliance', 'Compliance, controles e prevenção a fraudes', 'Compliance e controles'),
            ('sg-digital', 'Canais digitais e autosserviço', 'Atendimento e experiência'),
            ('sg-prestadores', 'Rede de prestadores e assistência', 'Sinistros'),
        ]
        text_type, video_type, quiz_type = (ContentType.objects.get_for_model(model) for model in (Text, Video, Quiz))
        for slug, title, subject_name in course_data:
            policy = self.policy(f'Seguradora · Curso · {title}', org, [(AudienceRule.COMPANY, [company.pk])])
            course, _ = Course.objects.update_or_create(slug=slug, defaults={'title': title, 'type': 'course', 'state': 'published', 'published_date': timezone.now(), 'author': admin, 'owner': admin, 'organization': org, 'subject': subjects[subject_name], 'overview': f'Conteúdo demonstrativo da Seguradora Generative sobre {title.lower()}.', 'audience_policy': policy, 'points_per_completation': 20, 'banner': self.demo_asset('insurance', self.insurance_image(slug))})
            for order, module_title in enumerate(['Visão geral', 'Aplicação prática', 'Verificação de conhecimento']):
                module, _ = Module.objects.update_or_create(course=course, title=module_title, defaults={'description': f'Módulo demonstrativo de {title}.', 'order': order})
                text, _ = Text.objects.update_or_create(owner=admin, title=f'{title} · {module_title}', defaults={'content': f'{module_title}\n\nMaterial fictício para demonstrar a comunicação e capacitação de uma seguradora multicanal.'})
                content, _ = Content.objects.get_or_create(module=module, content_type=text_type, object_id=text.pk, defaults={'order': 0})
                text.content_type_id = content.pk
                text.save(update_fields=['content_type'])
                video, _ = Video.objects.update_or_create(owner=admin, title=f'{title} · vídeo', defaults={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'content': 'Vídeo demonstrativo.'})
                Content.objects.get_or_create(module=module, content_type=video_type, object_id=video.pk, defaults={'order': 1})
                if order == 2:
                    quiz, _ = Quiz.objects.update_or_create(owner=admin, title=f'{title} · Quiz', defaults={'overview': 'Quiz demonstrativo.', 'number_of_questions': 1, 'required_score_to_pass': 70, 'time': 5})
                    question, _ = Question.objects.get_or_create(quiz=quiz, order=1, defaults={'text': 'Qual é o objetivo principal deste conteúdo?'})
                    Answer.objects.get_or_create(question=question, text='Atender o segurado com segurança, clareza e conformidade.', defaults={'correct': True})
                    Answer.objects.get_or_create(question=question, text='Ignorar regras e protocolos da operação.', defaults={'correct': False})
                    Content.objects.get_or_create(module=module, content_type=quiz_type, object_id=quiz.pk, defaults={'order': 2})
        tags = {name: Tag.objects.update_or_create(slug=slugify(f'sg-{name}'), defaults={'name': name})[0] for name in ['Produtos', 'Corretores', 'Sinistros', 'Atendimento', 'Riscos', 'Compliance', 'Prestadores']}
        items = [
            ('feed', 'Nova jornada de cotação para corretores', 'A Seguradora Generative disponibilizou uma atualização rápida para apoiar corretores na cotação.', ['Corretores', 'Produtos']),
            ('feed', 'Rede de assistência 24 horas atualizada', 'Confira os prestadores ativos e o novo fluxo para abertura de solicitações.', ['Prestadores', 'Atendimento']),
            ('feed', 'Semana de prevenção a fraudes', 'Conteúdos e orientações para identificar sinais de fraude durante a análise de propostas e sinistros.', ['Riscos', 'Compliance']),
            ('feed', 'Novo painel de sinistros', 'A operação passa a acompanhar os principais indicadores de regulação em um único painel.', ['Sinistros', 'Atendimento']),
            ('wiki', 'Guia do corretor e canais de distribuição', 'Referência permanente para produtos, propostas, documentos e suporte ao corretor.', ['Corretores', 'Produtos']),
            ('wiki', 'Fluxo de abertura e regulação de sinistros', 'Passo a passo para registrar, analisar, regular e comunicar um sinistro.', ['Sinistros', 'Atendimento']),
            ('wiki', 'Manual de credenciamento de prestadores', 'Critérios, documentos e responsabilidades da rede de oficinas e assistência.', ['Prestadores', 'Compliance']),
            ('wiki', 'Matriz de controles e prevenção a fraudes', 'Referência para controles de subscrição, pagamentos e investigação.', ['Riscos', 'Compliance']),
        ]
        for kind, title, excerpt, tag_names in items:
            policy = self.policy(f'Seguradora · {kind.title()} · {title}', org, [(AudienceRule.COMPANY, [company.pk])])
            defaults = {'kind': kind, 'organization': org, 'title': title, 'excerpt': excerpt, 'body': f'{excerpt}\n\nMaterial fictício de demonstração da Seguradora Generative.', 'author': admin, 'audience_policy': policy, 'status': Publication.PUBLISHED, 'published_at': timezone.now(), 'image': self.insurance_publication_image(title)}
            defaults.update(self.publication_classification(title, kind))
            publication, _ = Publication.objects.update_or_create(slug=slugify(f'sg-{title}'), defaults=defaults)
            publication.tags.set([tags[name] for name in tag_names])

    def create_units(self, group):
        structure = {
            'hospital-generative-ipiranga-sp': ('Hospital Generative Ipiranga - SP', ['Pronto Socorro', 'UTI Adulto', 'UTI Pediátrica', 'Centro Cirúrgico', 'Ortopedia', 'Laboratório', 'Diagnóstico por Imagem']),
            'hospital-generative-pompeia-sp': ('Hospital Generative Pompeia - SP', ['Pronto Socorro', 'UTI Adulto', 'Centro Cirúrgico', 'Ortopedia', 'Laboratório']),
            'centro-consultas-pompeia-sp': ('Centro de Consultas Pompeia - SP', ['Consultórios', 'Cardiologia', 'Ortopedia', 'Exames']),
            'instituto-diagnostico-sp': ('Instituto Generative de Diagnóstico - SP', ['Ressonância Magnética', 'Tomografia', 'Ultrassonografia', 'Laboratório de Análises']),
        }
        result = {}
        for code, (name, departments) in structure.items():
            unit, _ = BusinessUnit.objects.update_or_create(company=group, code=code, defaults={'name': name, 'active': True})
            result[code] = (unit, {})
            for department in departments:
                operational, _ = OperationalUnit.objects.update_or_create(
                    business_unit=unit, name=department, defaults={'code': slugify(department), 'active': True}
                )
                result[code][1][department] = operational
        return result

    def create_channels(self, group):
        names = ['Colaborador interno', 'Corpo clínico', 'Enfermagem e assistência', 'Prestador credenciado', 'Fornecedor', 'Laboratório parceiro', 'Paciente / Portal', 'Gestão corporativa']
        return {name: BusinessChannel.objects.update_or_create(company=group, name=name, defaults={'active': True})[0] for name in names}

    def create_person_types(self, org):
        names = {
            'colaborador': ('Colaborador', 'Profissional contratado diretamente pelo grupo.'),
            'corpo-clinico': ('Corpo clínico', 'Médico ou profissional assistencial credenciado.'),
            'enfermagem': ('Enfermagem', 'Profissional de enfermagem e assistência.'),
            'prestador': ('Prestador de serviços', 'Pessoa vinculada a uma empresa prestadora.'),
            'fornecedor': ('Fornecedor', 'Pessoa vinculada a fornecedor de produtos ou equipamentos.'),
            'paciente': ('Paciente', 'Usuário externo do portal do paciente.'),
            'gestor': ('Gestor', 'Responsável por pessoas, operação ou conteúdo.'),
        }
        return {code: PersonType.objects.update_or_create(organization=org, code=code, defaults={'name': name, 'description': description, 'active': True})[0] for code, (name, description) in names.items()}

    def create_functions(self, group, channels):
        names = ['Médico cirurgião', 'Médico ortopedista', 'Médico cardiologista', 'Médico pediatra', 'Enfermeiro', 'Enfermeiro responsável técnico', 'Técnico de enfermagem', 'Fisioterapeuta', 'Farmacêutico', 'Biomédico', 'Técnico de laboratório', 'Técnico de radiologia', 'Coordenador de unidade', 'Coordenador médico', 'Coordenador de enfermagem', 'Segurança do paciente', 'Recepcionista', 'Tecnologia da informação', 'Compras e suprimentos', 'Manutenção predial']
        result = {}
        for name in names:
            function, _ = JobFunction.objects.update_or_create(company=group, name=name, defaults={'active': True})
            function.channels.set([channels['Corpo clínico']] if name.startswith('Médico') else [channels['Enfermagem e assistência']] if 'enferm' in name.lower() or 'Técnico de enfermagem' in name else [channels['Colaborador interno']])
            result[name] = function
        return result

    def create_users(self, admin, org, group, units, channels, person_types, functions):
        User = get_user_model()
        profiles = [
            ('medico', 'Mariana', 'Silva', 'corpo-clinico', 'Médico cirurgião', 'Hospital Generative Ipiranga - SP', 'Centro Cirúrgico'),
            ('ortopedista', 'Ricardo', 'Oliveira', 'corpo-clinico', 'Médico ortopedista', 'Hospital Generative Pompeia - SP', 'Ortopedia'),
            ('cardiologista', 'Fernanda', 'Costa', 'corpo-clinico', 'Médico cardiologista', 'Centro de Consultas Pompeia - SP', 'Cardiologia'),
            ('pediatra', 'Lucas', 'Almeida', 'corpo-clinico', 'Médico pediatra', 'Hospital Generative Ipiranga - SP', 'UTI Pediátrica'),
            ('enfermeira', 'Camila', 'Santos', 'enfermagem', 'Enfermeiro', 'Hospital Generative Ipiranga - SP', 'UTI Adulto'),
            ('tecnico', 'João', 'Souza', 'enfermagem', 'Técnico de enfermagem', 'Hospital Generative Pompeia - SP', 'Pronto Socorro'),
            ('radiologia', 'Paulo', 'Mendes', 'colaborador', 'Técnico de radiologia', 'Instituto Generative de Diagnóstico - SP', 'Ressonância Magnética'),
            ('laboratorio', 'Aline', 'Ferreira', 'colaborador', 'Técnico de laboratório', 'Hospital Generative Ipiranga - SP', 'Laboratório'),
            ('coordenadora', 'Juliana', 'Ramos', 'gestor', 'Coordenador de unidade', 'Hospital Generative Ipiranga - SP', 'Pronto Socorro'),
            ('fornecedor', 'Bruno', 'Nogueira', 'fornecedor', 'Compras e suprimentos', 'Hospital Generative Pompeia - SP', 'Laboratório'),
            ('prestador', 'Patricia', 'Lima', 'prestador', 'Fisioterapeuta', 'Hospital Generative Ipiranga - SP', 'UTI Adulto'),
            ('paciente', 'Ana', 'Demo', 'paciente', None, 'Centro de Consultas Pompeia - SP', 'Consultórios'),
        ]
        users = []
        for index in range(1, 4):
            for prefix, first, last, person_code, function_name, unit_name, department_name in profiles:
                username = f'{prefix}.{index:02d}'
                user, created = User.objects.get_or_create(username=username, defaults={'email': f'{username}@hospital-generative.demo', 'first_name': first, 'last_name': last})
                user.email = f'{username}@hospital-generative.demo'
                user.first_name, user.last_name = first, last
                if created:
                    user.set_password('TalkDemo123!')
                user.save()
                unit = next(item for item, departments in units.values() if item.name == unit_name)
                operational = next(value for item, departments in units.values() if item.name == unit_name for name, value in departments.items() if name == department_name)
                membership, _ = Membership.objects.update_or_create(user=user, company=group, business_unit=unit, operational_unit=operational, defaults={'organization': org, 'person_type': person_types[person_code], 'active': True, 'is_primary': True})
                membership.channels.set([channels['Paciente / Portal']] if person_code == 'paciente' else [channels['Fornecedor']] if person_code == 'fornecedor' else [channels['Prestador credenciado']] if person_code == 'prestador' else [channels['Corpo clínico']] if person_code == 'corpo-clinico' else [channels['Enfermagem e assistência']] if person_code == 'enfermagem' else [channels['Colaborador interno']])
                if function_name:
                    membership.functions.set([functions[function_name]])
                users.append(user)
        return users

    def create_managers(self, admin, org, group, units):
        ManagementAssignment.objects.update_or_create(user=admin, organization=org, company=None, business_unit=None, operational_unit=None, role='people_admin', defaults={'active': True})
        coordinator = get_user_model().objects.filter(username='coordenadora.01').first()
        if coordinator:
            unit = next(item for item, _ in units.values() if 'Ipiranga' in item.name)
            ManagementAssignment.objects.update_or_create(user=coordinator, organization=org, company=group, business_unit=unit, operational_unit=None, role='people_admin', defaults={'active': True})

    def policy(self, name, org, rules):
        policy, _ = AudiencePolicy.objects.update_or_create(name=name, organization=org, defaults={'description': 'Política da demonstração.', 'match_mode': AudiencePolicy.ALL, 'active': True})
        policy.rules.all().delete()
        for position, (dimension, values) in enumerate(rules):
            AudienceRule.objects.create(policy=policy, dimension=dimension, values=[str(value) for value in values], position=position)
        return policy

    def create_content(self, admin, org, group, units, channels, person_types, functions):
        subjects = {}
        for name in ['Segurança do paciente', 'Assistência', 'Operações hospitalares', 'Tecnologia e dados', 'Compliance e LGPD']:
            subjects[name] = Subject.objects.update_or_create(slug=slugify(name), defaults={'title': name})[0]
        ipiranga = next(item for item, _ in units.values() if 'Ipiranga' in item.name)
        ipiranga_ps = next(value for item, departments in units.values() if item == ipiranga for name, value in departments.items() if name == 'Pronto Socorro')
        cirurgia = next(value for item, departments in units.values() for name, value in departments.items() if name == 'Centro Cirúrgico')
        course_data = [
            ('seguranca-paciente', 'Segurança do paciente', 'Segurança do paciente', None),
            ('cirurgia-segura', 'Protocolo de cirurgia segura', 'Assistência', cirurgia),
            ('higienizacao-maos', 'Higienização das mãos', 'Assistência', None),
            ('pronto-socorro', 'Atendimento inicial no pronto socorro', 'Assistência', ipiranga_ps),
            ('uti-adulto', 'Rotina da UTI adulto', 'Assistência', None),
            ('uti-pediatrica', 'Rotina da UTI pediátrica', 'Assistência', None),
            ('equipamentos-imagem', 'Uso seguro de equipamentos de imagem', 'Operações hospitalares', None),
            ('exames-laboratoriais', 'Coleta e transporte de exames', 'Operações hospitalares', None),
            ('lgpd-saude', 'LGPD e sigilo de informações de saúde', 'Compliance e LGPD', None),
            ('comunicacao-paciente', 'Comunicação com pacientes e familiares', 'Assistência', None),
            ('integracao-prestadores', 'Integração de prestadores', 'Operações hospitalares', None),
            ('gestao-unidade', 'Gestão de unidade hospitalar', 'Operações hospitalares', None),
        ]
        text_type, video_type, quiz_type = (ContentType.objects.get_for_model(model) for model in (Text, Video, Quiz))
        for slug, title, subject_name, operational in course_data:
            rules = [(AudienceRule.COMPANY, [group.pk])]
            if operational:
                rules.append((AudienceRule.OPERATIONAL_UNIT, [operational.pk]))
            policy = self.policy(f'Curso · {title}', org, rules)
            course, _ = Course.objects.update_or_create(slug=slug, defaults={'title': title, 'type': 'course', 'state': 'published', 'published_date': timezone.now(), 'author': admin, 'owner': admin, 'organization': org, 'subject': subjects[subject_name], 'overview': f'Conteúdo demonstrativo para o ambiente hospitalar. Este material não substitui protocolos oficiais aprovados.', 'audience_policy': policy, 'points_per_completation': 20, 'banner': self.hospital_image(slug)})
            for order, module_title in enumerate(['Contexto e objetivos', 'Rotina prática', 'Verificação de conhecimento']):
                module, _ = Module.objects.update_or_create(course=course, title=module_title, defaults={'description': f'Módulo demonstrativo de {title}.', 'order': order})
                text, _ = Text.objects.update_or_create(owner=admin, title=f'{title} · {module_title}', defaults={'content': f'{module_title}\n\nEste conteúdo é fictício e serve para demonstrar a experiência do Talk em ambientes hospitalares.'})
                content, _ = Content.objects.get_or_create(module=module, content_type=text_type, object_id=text.pk, defaults={'order': 0})
                text.content_type_id = content.pk
                text.save(update_fields=['content_type'])
                video, _ = Video.objects.update_or_create(owner=admin, title=f'{title} · vídeo', defaults={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'content': 'Vídeo demonstrativo.'})
                Content.objects.get_or_create(module=module, content_type=video_type, object_id=video.pk, defaults={'order': 1})
                if order == 2:
                    quiz, _ = Quiz.objects.update_or_create(owner=admin, title=f'{title} · Quiz', defaults={'overview': 'Quiz demonstrativo.', 'number_of_questions': 1, 'required_score_to_pass': 70, 'time': 5})
                    question, _ = Question.objects.get_or_create(quiz=quiz, order=1, defaults={'text': 'Qual é a finalidade principal deste conteúdo?'})
                    Answer.objects.get_or_create(question=question, text='Apoiar a rotina com segurança e padronização.', defaults={'correct': True})
                    Answer.objects.get_or_create(question=question, text='Substituir protocolos oficiais sem validação.', defaults={'correct': False})
                    Content.objects.get_or_create(module=module, content_type=quiz_type, object_id=quiz.pk, defaults={'order': 2})
        self.create_publications(admin, org, group, units)

    def create_publications(self, admin, org, group, units):
        tags = {name: Tag.objects.update_or_create(slug=slugify(name), defaults={'name': name})[0] for name in ['Segurança', 'Assistência', 'Cirurgia', 'Laboratório', 'Imagem', 'LGPD', 'Operações']}
        items = [
            ('feed', 'Atualização do protocolo de identificação', 'A equipe de Segurança do Paciente publicou uma atualização rápida para a identificação segura.', ['Segurança']),
            ('feed', 'Janela de manutenção da ressonância', 'O equipamento terá manutenção programada. Consulte a agenda da unidade.', ['Imagem', 'Operações']),
            ('feed', 'Treinamento obrigatório de cirurgia segura', 'O novo curso está disponível para o Centro Cirúrgico.', ['Cirurgia', 'Assistência']),
            ('feed', 'Novo fluxo para coleta de exames', 'Confira o treinamento e a referência da Wiki antes do próximo plantão.', ['Laboratório']),
            ('feed', 'Boas-vindas aos novos prestadores', 'O material de integração está disponível para o canal de prestadores.', ['Operações']),
            ('wiki', 'Checklist de cirurgia segura', 'Referência permanente para a conferência pré-operatória.', ['Cirurgia', 'Segurança']),
            ('wiki', 'Fluxo de acionamento da UTI', 'Guia de referência para comunicação e escalonamento.', ['Assistência']),
            ('wiki', 'Manual de coleta e transporte de exames', 'Orientações demonstrativas para coleta, identificação e transporte.', ['Laboratório']),
            ('wiki', 'Uso e limpeza de equipamentos de imagem', 'Referência para operação segura e abertura de chamados.', ['Imagem']),
            ('wiki', 'Guia de integração de prestadores', 'Informações para prestadores credenciados no grupo.', ['Operações']),
            ('wiki', 'LGPD e sigilo de informações de saúde', 'Princípios básicos para uso responsável de informações.', ['LGPD']),
            ('wiki', 'Matriz de responsabilidades por departamento', 'Quem acionar em cada cenário operacional.', ['Operações']),
        ]
        for index, (kind, title, excerpt, tag_names) in enumerate(items):
            policy = self.policy(f'{kind.title()} · {title}', org, [(AudienceRule.COMPANY, [group.pk])])
            defaults = {'kind': kind, 'organization': org, 'title': title, 'excerpt': excerpt, 'body': f'{excerpt}\n\nMaterial fictício de demonstração do Talk para o ambiente hospitalar.', 'author': admin, 'audience_policy': policy, 'status': Publication.PUBLISHED, 'published_at': timezone.now(), 'image': self.hospital_publication_image(title)}
            defaults.update(self.publication_classification(title, kind))
            publication, _ = Publication.objects.update_or_create(slug=slugify(title), defaults=defaults)
            publication.tags.set([tags[name] for name in tag_names])

    def create_hospital_documents(self, admin, org, group, units, users):
        """Seed realistic hospital documents with versioning and permissions."""
        now = timezone.now()
        document_specs = [
            {'slug': 'protocolo-cirurgia-segura', 'title': 'Protocolo de Cirurgia Segura', 'category': 'procedure', 'description': 'Passo a passo para cirurgias seguras com checklist pré/intra/pós-operatório.', 'cirurgia': True},
            {'slug': 'manual-higienizacao', 'title': 'Manual de Higienização das Mãos', 'category': 'manual', 'description': 'Técnicas e frequência de higienização conforme protocolo ANVISA.', 'enfermagem': True},
            {'slug': 'rotina-uti-adulto', 'title': 'Rotina da UTI Adulto', 'category': 'procedure', 'description': 'Procedimentos, cuidados e monitoramento em UTI adulto.', 'uti': True},
            {'slug': 'rotina-uti-pediatrica', 'title': 'Rotina da UTI Pediátrica', 'category': 'procedure', 'description': 'Procedimentos pediátricos, dosagens e protocolos especiais.', 'uti': True},
            {'slug': 'formulario-admissao', 'title': 'Formulário de Admissão Hospitalar', 'category': 'form', 'description': 'Documento para preenchimento de dados do paciente na admissão.'},
            {'slug': 'lgpd-saude', 'title': 'LGPD e Sigilo de Informações de Saúde', 'category': 'policy', 'description': 'Obrigações legais e responsabilidades no tratamento de dados em saúde.'},
            {'slug': 'guia-integracao-prestadores', 'title': 'Guia de Integração de Prestadores', 'category': 'manual', 'description': 'Informações e requisitos para credenciamento de prestadores terceirizados.'},
        ]

        # Get organizational units for audience targeting
        ipiranga = next(item for item, _ in units.values() if 'Ipiranga' in item.name)
        cirurgia_unit = next((value for _, departments in units.values() for name, value in departments.items() if name == 'Centro Cirúrgico'), None)

        docs_created = []
        for spec in document_specs:
            slug, title, category, description = spec['slug'], spec['title'], spec['category'], spec['description']
            # Create audience policy
            rules = [(AudienceRule.COMPANY, [group.pk])]
            if spec.get('cirurgia') and cirurgia_unit:
                rules.append((AudienceRule.OPERATIONAL_UNIT, [cirurgia_unit.pk]))
            if spec.get('uti'):
                # Target both UTI Adulto and Pediátrica
                uti_units = [value for _, departments in units.values() for name, value in departments.items() if 'UTI' in name]
                if uti_units:
                    rules.append((AudienceRule.OPERATIONAL_UNIT, [u.pk for u in uti_units]))
            if spec.get('enfermagem'):
                rules.append((AudienceRule.COMPANY, [group.pk]))  # All staff but published

            policy = self.policy(f'Documento Hospital · {title}', org, rules)

            # Create document
            doc, _ = Document.objects.update_or_create(
                slug=slug,
                defaults={
                    'organization': org,
                    'title': title,
                    'code': f'HG-{slug.upper()[:20]}',
                    'category': category,
                    'description': description,
                    'status': Document.PUBLISHED,
                    'owner': admin,
                    'audience_policy': policy,
                    'announce_changes': True,
                    'published_at': now,
                }
            )

            # Create first version
            version, _ = DocumentVersion.objects.get_or_create(
                document=doc,
                version_number=1,
                defaults={
                    'body': f'{title}\n\n{description}\n\n[Conteúdo fictício para demonstração do Talk em ambiente hospitalar]',
                    'mime_type': 'text/plain',
                    'file_size': len(description),
                    'change_summary': 'Versão inicial',
                    'created_by': admin,
                    'effective_at': now - timedelta(days=30),
                    'expires_at': now + timedelta(days=365),
                }
            )
            doc.current_version = version
            doc.save()
            docs_created.append(doc)

            # Create permissions for relevant users
            for user in users:
                if category == 'policy' or (spec.get('cirurgia') and user.username.startswith('medico')):
                    DocumentPermission.objects.get_or_create(
                        document=doc, user=user,
                        defaults={'can_view': True, 'can_download': True, 'granted_by': admin}
                    )
                elif category in ('procedure', 'manual') and (spec.get('enfermagem') or spec.get('uti')):
                    if user.username.startswith(('enfermeira', 'tecnico', 'pediatra')):
                        DocumentPermission.objects.get_or_create(
                            document=doc, user=user,
                            defaults={'can_view': True, 'can_download': True, 'granted_by': admin}
                        )

            # Simulate some views
            for i, user in enumerate(users[:3]):
                if DocumentPermission.objects.filter(document=doc, user=user).exists():
                    DocumentEvent.objects.create(
                        document=doc, version=version, user=user,
                        event_name=DocumentEvent.OPENED,
                        occurred_at=now - timedelta(days=30-i)
                    )
                    if i < 2:
                        DocumentEvent.objects.create(
                            document=doc, version=version, user=user,
                            event_name=DocumentEvent.DOWNLOADED,
                            occurred_at=now - timedelta(days=29-i)
                        )

        self.stdout.write(f'✅ {len(docs_created)} documentos Hospital Generative criados com versioning e permissões.')

    def create_insurance_documents(self, admin, org, company, units, users):
        """Seed realistic insurance documents with versioning and permissions."""
        now = timezone.now()
        document_specs = [
            ('guia-produtos', 'Guia de Produtos e Coberturas', 'manual', 'Catálogo completo de produtos, limites e exclusões de cobertura.'),
            ('processo-subscricao', 'Processo de Subscrição e Análise de Risco', 'procedure', 'Etapas para avaliação de propostas e cálculo de prêmios.'),
            ('fluxo-sinistros', 'Fluxo de Abertura e Regulação de Sinistros', 'procedure', 'Passo a passo desde abertura até análise e pagamento de sinistro.'),
            ('manual-prestadores', 'Manual de Credenciamento de Prestadores', 'manual', 'Critérios, documentos necessários e responsabilidades da rede.'),
            ('politica-adesao-corretor', 'Política de Adesão de Corretores', 'policy', 'Requisitos, comissões e obrigações de corretores parceiros.'),
            ('compliance-fraude', 'Matriz de Controles e Prevenção a Fraudes', 'policy', 'Procedimentos e indicadores para detecção de fraudes em subscrição e sinistros.'),
            ('formulario-proposta', 'Formulário Padrão de Proposta', 'form', 'Documento para preenchimento de dados da proposta do cliente.'),
            ('relatorio-sinistro', 'Modelo de Relatório de Sinistro', 'form', 'Template para documentação e análise de sinistros.'),
        ]

        docs_created = []
        for slug, title, category, description in document_specs:
            # Create audience policy targeting the insurance company
            policy = self.policy(f'Documento Seguradora · {title}', org, [(AudienceRule.COMPANY, [company.pk])])

            # Create document
            doc, _ = Document.objects.update_or_create(
                slug=f'sg-{slug}',
                defaults={
                    'organization': org,
                    'title': title,
                    'code': f'SG-{slug.upper()[:20]}',
                    'category': category,
                    'description': description,
                    'status': Document.PUBLISHED,
                    'owner': admin,
                    'audience_policy': policy,
                    'announce_changes': True,
                    'published_at': now,
                }
            )

            # Create first version
            version, _ = DocumentVersion.objects.get_or_create(
                document=doc,
                version_number=1,
                defaults={
                    'body': f'{title}\n\n{description}\n\n[Conteúdo fictício para demonstração do Talk em ambiente de seguros]',
                    'mime_type': 'text/plain',
                    'file_size': len(description),
                    'change_summary': 'Versão inicial',
                    'created_by': admin,
                    'effective_at': now - timedelta(days=60),
                    'expires_at': now + timedelta(days=730),
                }
            )
            doc.current_version = version
            doc.save()
            docs_created.append(doc)

            # Create permissions based on document type and user role
            for user in users:
                username = user.username
                # All employees get access to policies and procedures
                if category in ('policy', 'procedure', 'manual'):
                    DocumentPermission.objects.get_or_create(
                        document=doc, user=user,
                        defaults={'can_view': True, 'can_download': True, 'granted_by': admin}
                    )
                # Corretores get special access to produto and adesão docs
                elif category == 'manual' and username.startswith('sg.corretor'):
                    DocumentPermission.objects.get_or_create(
                        document=doc, user=user,
                        defaults={'can_view': True, 'can_download': True, 'granted_by': admin}
                    )

            # Simulate some views
            for i, user in enumerate(users[:4]):
                if DocumentPermission.objects.filter(document=doc, user=user).exists():
                    DocumentEvent.objects.create(
                        document=doc, version=version, user=user,
                        event_name=DocumentEvent.OPENED,
                        occurred_at=now - timedelta(days=60-i*2)
                    )
                    if i < 3:
                        DocumentEvent.objects.create(
                            document=doc, version=version, user=user,
                            event_name=DocumentEvent.ACTIVE,
                            active_seconds=300 + (i * 100),
                            occurred_at=now - timedelta(days=59-i*2)
                        )

        self.stdout.write(f'✅ {len(docs_created)} documentos Seguradora Generative criados com versioning e permissões.')

    def create_trails(self, admin, org, company, org_type='hospital'):
        """Create learning paths (trails) that sequence courses for organizational onboarding."""
        if org_type == 'hospital':
            trails_data = [
                ('onboarding-equipe', 'Onboarding da equipe', ContentTrail.REQUIRED, ['seguranca-paciente', 'higienizacao-maos', 'comunicacao-paciente']),
                ('assistencia-clinica', 'Trilha de assistência clínica', ContentTrail.RECOMMENDED, ['cirurgia-segura', 'uti-adulto', 'uti-pediatrica']),
                ('operacoes', 'Trilha de operações', ContentTrail.RECOMMENDED, ['equipamentos-imagem', 'exames-laboratoriais', 'gestao-unidade']),
                ('conformidade', 'Trilha de conformidade', ContentTrail.REQUIRED, ['lgpd-saude', 'integracao-prestadores']),
            ]
            policy_name_prefix = 'Hospital · Trilha'
        else:  # insurance
            trails_data = [
                ('sg-onboarding', 'Onboarding da seguradora', ContentTrail.REQUIRED, ['sg-produtos', 'sg-atendimento', 'sg-compliance']),
                ('sg-vendas', 'Trilha de vendas e corretores', ContentTrail.RECOMMENDED, ['sg-produtos', 'sg-corretor', 'sg-subscricao']),
                ('sg-sinistros-path', 'Trilha de sinistros e prestadores', ContentTrail.RECOMMENDED, ['sg-sinistros', 'sg-prestadores', 'sg-atendimento']),
                ('sg-digital-path', 'Trilha digital e autosserviço', ContentTrail.RECOMMENDED, ['sg-digital', 'sg-atendimento', 'sg-produtos']),
            ]
            policy_name_prefix = 'Seguradora · Trilha'

        courses = Course.objects.filter(organization=org)
        trails_created = 0

        for slug, title, trail_type, course_slugs in trails_data:
            policy = self.policy(f'{policy_name_prefix} · {title}', org, [(AudienceRule.COMPANY, [company.pk])])
            trail, created = ContentTrail.objects.update_or_create(
                slug=slug,
                defaults={
                    'title': title,
                    'objective': f'Trilha de aprendizado sequenciada para {title.lower()} na {org.name}.',
                    'trail_type': trail_type,
                    'status': ContentTrail.PUBLISHED,
                    'organization': org,
                    'audience_policy': policy,
                    'owner': admin,
                    'version': 1,
                }
            )

            if created:
                # Create trail steps from courses
                trail.steps.all().delete()
                for position, course_slug in enumerate(course_slugs):
                    course = courses.filter(slug=course_slug).first()
                    if course:
                        TrailStep.objects.create(
                            trail=trail,
                            position=position,
                            title=course.title,
                            content_type=ContentType.objects.get_for_model(Course),
                            object_id=course.pk,
                            required=(trail_type == ContentTrail.REQUIRED),
                            completion_event=ContentEvent.CONTENT_COMPLETED,
                        )
                trails_created += 1

        org_name = 'Hospital Generative' if org_type == 'hospital' else 'Seguradora Generative'
        self.stdout.write(f'✅ {trails_created} trilhas de aprendizado {org_name} criadas.')

    def create_analytics_and_feedback(self, admin, org):
        """Create realistic analytics events and feedback data for 30-day demo period."""
        now = timezone.now()
        publications = Publication.objects.filter(organization=org)
        courses = Course.objects.filter(organization=org)
        documents = Document.objects.filter(organization=org)
        User = get_user_model()
        org_users = User.objects.filter(memberships__organization=org).distinct()

        events_created = 0
        feedback_created = 0

        # Get ContentType for Publications and Courses
        pub_ct = ContentType.objects.get_for_model(Publication)
        course_ct = ContentType.objects.get_for_model(Course)

        # Create 30 days of realistic analytics events
        for days_ago in range(30):
            event_date = now - timedelta(days=days_ago)
            # 2-5 random events per day per user
            for user in org_users[:max(1, len(org_users)//2)]:
                num_events = [2, 3, 4, 5][days_ago % 4]
                for _ in range(num_events):
                    # Random content engagement
                    if publications.exists() and days_ago % 3 == 0:
                        pub = publications.order_by('?').first()
                        ContentEvent.objects.create(
                            event_name=ContentEvent.CONTENT_OPENED,
                            user=user, organization=org,
                            content_type=pub_ct, object_id=pub.pk,
                            active_seconds=30 + (days_ago % 60),
                            metadata={'source': 'demo', 'publication_kind': pub.kind}
                        )
                        events_created += 1
                    elif courses.exists() and days_ago % 2 == 0:
                        course = courses.order_by('?').first()
                        progress = min(100, 20 + days_ago * 2)
                        ContentEvent.objects.create(
                            event_name=ContentEvent.COURSE_ENROLLED if days_ago > 20 else ContentEvent.CONTENT_ACTIVE,
                            user=user, organization=org,
                            content_type=course_ct, object_id=course.pk,
                            progress_percent=progress,
                            metadata={'source': 'demo', 'progress': progress}
                        )
                        events_created += 1

        # Create feedback for publications (5-10% of users per publication)
        feedback_ratings = [
            (ContentFeedback.HELPFUL, 'Helpful'),
            (ContentFeedback.PARTIAL, 'Partially Helpful'),
            (ContentFeedback.NOT_HELPFUL, 'Not Helpful'),
        ]

        for publication in publications:
            feedback_count = max(1, len(org_users) // 20)  # ~5% of users
            for idx, user in enumerate(org_users.order_by('?')[:feedback_count]):
                rating, rating_display = feedback_ratings[idx % 3]
                ContentFeedback.objects.get_or_create(
                    content_type=pub_ct, object_id=publication.pk, user=user,
                    defaults={
                        'rating': rating,
                        'reason': ContentFeedback.REASON_CHOICES[idx % len(ContentFeedback.REASON_CHOICES)][0] if rating != ContentFeedback.HELPFUL else '',
                        'comment': f'Demo feedback: {rating_display}',
                    }
                )
                feedback_created += 1

        self.stdout.write(f'✅ {events_created} eventos de analytics criados.')
        self.stdout.write(f'✅ {feedback_created} feedbacks de conteúdo criados.')

    @staticmethod
    def demo_asset(domain, filename):
        return f'demo_assets/{domain}/{filename}'

    def hospital_image(self, slug):
        mapping = {
            'seguranca-paciente': 'patient-safety.png',
            'cirurgia-segura': 'surgical-safety.png',
            'higienizacao-maos': 'patient-safety.png',
            'pronto-socorro': 'hospital-ecosystem.png',
            'uti-adulto': 'hospital-ecosystem.png',
            'uti-pediatrica': 'hospital-ecosystem.png',
            'equipamentos-imagem': 'imaging-lab.png',
            'exames-laboratoriais': 'imaging-lab.png',
            'lgpd-saude': 'imaging-lab.png',
            'comunicacao-paciente': 'hospital-ecosystem.png',
            'integracao-prestadores': 'hospital-ecosystem.png',
            'gestao-unidade': 'hospital-ecosystem.png',
        }
        return self.demo_asset('hospital', mapping.get(slug, 'hospital-ecosystem.png'))

    def hospital_publication_image(self, title):
        title = title.lower()
        if 'cirurgia' in title or 'identificação' in title:
            filename = 'surgical-safety.png' if 'cirurgia' in title else 'patient-safety.png'
        elif any(word in title for word in ('ressonância', 'imagem', 'exames')):
            filename = 'imaging-lab.png'
        else:
            filename = 'hospital-ecosystem.png'
        return self.demo_asset('hospital', filename)

    def insurance_image(self, slug):
        mapping = {
            'sg-produtos': 'portfolio-coverage.png',
            'sg-corretor': 'digital-channels.png',
            'sg-subscricao': 'risk-compliance.png',
            'sg-sinistros': 'claims-network.png',
            'sg-atendimento': 'digital-channels.png',
            'sg-compliance': 'risk-compliance.png',
            'sg-digital': 'digital-channels.png',
            'sg-prestadores': 'claims-network.png',
        }
        return mapping.get(slug, 'portfolio-coverage.png')

    def insurance_publication_image(self, title):
        title = title.lower()
        if any(word in title for word in ('fraude', 'controles')):
            filename = 'risk-compliance.png'
        elif any(word in title for word in ('sinistros', 'assistência', 'prestadores')):
            filename = 'claims-network.png'
        elif any(word in title for word in ('corretor', 'cotação')):
            filename = 'digital-channels.png'
        else:
            filename = 'portfolio-coverage.png'
        return self.demo_asset('insurance', filename)

    @staticmethod
    def publication_classification(title, kind):
        title = title.lower()
        if any(word in title for word in ('manutenção', 'fraudes', 'identificação', 'obrigatório', 'prevenção')):
            return {'importance': Publication.CRITICAL, 'content_category': 'incident' if 'manutenção' in title else 'required_document', 'requires_acknowledgement': True, 'reminder_hours': 12}
        if any(word in title for word in ('novo fluxo', 'nova jornada', 'atualização', 'mudança', 'regulação', 'checklist')):
            return {'importance': Publication.IMPORTANT, 'content_category': 'procedure_change' if any(word in title for word in ('fluxo', 'jornada', 'regulação', 'checklist')) else 'document_update', 'requires_acknowledgement': kind == 'wiki', 'reminder_hours': 24}
        return {'importance': Publication.ROUTINE, 'content_category': 'announcement' if kind == 'feed' else 'update', 'requires_acknowledgement': False, 'reminder_hours': 48}
