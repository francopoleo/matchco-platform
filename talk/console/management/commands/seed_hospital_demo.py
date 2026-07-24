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
from publishing.models import Publication, Tag


class Command(BaseCommand):
    help = 'Create the repeatable Hospital Generative enterprise demonstration.'

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
            self.stdout.write('Seed: 1 organização, 1 grupo, 4 unidades, 20 departamentos, 7 tipos de pessoa, 20 funções, 36 usuários, 12 cursos, 12 publicações e políticas de audiência.')
            return
        if options['reset'] and not options['yes']:
            raise CommandError('O reset é destrutivo. Execute novamente com --reset --yes.')
        if options['reset']:
            self.reset_database()
            self.stdout.write(self.style.WARNING('Base limpa. Criando o administrador protegido.'))
        with transaction.atomic():
            admin = self.ensure_admin(options)
            self.seed(admin)
        self.stdout.write(self.style.SUCCESS('Demonstração Hospital Generative criada/atualizada com sucesso.'))

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
        users = self.create_users(admin, org, group, units, channels, person_types, functions)
        self.create_managers(admin, org, group, units)
        self.create_content(admin, org, group, units, channels, person_types, functions)
        self.stdout.write(f'{len(users)} usuários de demonstração preparados.')

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
        policy, _ = AudiencePolicy.objects.update_or_create(name=name, organization=org, defaults={'description': 'Política da demonstração Hospital Generative.', 'match_mode': AudiencePolicy.ALL, 'active': True})
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
            course, _ = Course.objects.update_or_create(slug=slug, defaults={'title': title, 'type': 'course', 'state': 'published', 'published_date': timezone.now(), 'author': admin, 'owner': admin, 'organization': org, 'subject': subjects[subject_name], 'overview': f'Conteúdo demonstrativo para o ambiente hospitalar. Este material não substitui protocolos oficiais aprovados.', 'audience_policy': policy, 'points_per_completation': 20})
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
            publication, _ = Publication.objects.update_or_create(slug=slugify(title), defaults={'kind': kind, 'organization': org, 'title': title, 'excerpt': excerpt, 'body': f'{excerpt}\n\nMaterial fictício de demonstração do Talk Learning para o ambiente hospitalar.', 'author': admin, 'audience_policy': policy, 'status': Publication.PUBLISHED, 'published_at': timezone.now()})
            publication.tags.set([tags[name] for name in tag_names])
