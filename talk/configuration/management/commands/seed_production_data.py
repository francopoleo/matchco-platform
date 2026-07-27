"""
Production seed data with comprehensive content, images, trails and assignments.
Creates complete organizational data with feeds, wikis, documents, and learning trails.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from django.db import transaction
from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

from configuration.models import (
    Organization, Membership,
    GroupHierarchyType, GroupNode, UserGroupMembership,
)
from courses.models import Course, Subject, Content
from publishing.models import Publication
from documents.models import Document
from learning.models import ContentTrail, TrailStep, TrailAssignment

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed production data with comprehensive content, trails and assignments'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data first')

    @transaction.atomic
    def handle(self, *args, **options):
        if options['clear']:
            self.clear_existing_data()

        self.stdout.write(self.style.SUCCESS('🚀 Starting comprehensive seed...'))

        # Get organizations (assuming seed_complete_system was run first)
        orgs = self.get_or_create_basic_orgs()
        self.stdout.write(self.style.SUCCESS(f'✅ Working with {len(orgs)} organizations'))

        users_by_org = self.get_org_users(orgs)
        subjects = self.get_subjects()

        # Create comprehensive content
        self.create_rich_publications(orgs, users_by_org)
        self.stdout.write(self.style.SUCCESS('✅ Created rich publications'))

        self.create_rich_documents(orgs, users_by_org)
        self.stdout.write(self.style.SUCCESS('✅ Created rich documents'))

        self.create_learning_trails(orgs, users_by_org, subjects)
        self.stdout.write(self.style.SUCCESS('✅ Created learning trails'))

        self.create_trail_assignments(orgs, users_by_org)
        self.stdout.write(self.style.SUCCESS('✅ Created trail assignments'))

        self.stdout.write(self.style.SUCCESS('\n✨ Production seed complete!'))

    def clear_existing_data(self):
        """Clear production data"""
        self.stdout.write('Clearing existing production data...')
        TrailAssignment.objects.all().delete()
        TrailStep.objects.all().delete()
        ContentTrail.objects.filter(slug__contains='-trail-').delete()
        Publication.objects.all().delete()
        Document.objects.all().delete()
        self.stdout.write('✅ Cleared')

    def get_or_create_basic_orgs(self):
        """Get existing organizations"""
        return {org.slug: org for org in Organization.objects.filter(is_public=False)}

    def get_org_users(self, orgs):
        """Get users for each organization"""
        users_by_org = {}
        for org_slug, org in orgs.items():
            users_by_org[org_slug] = {}
            memberships = Membership.objects.filter(organization=org, active=True)
            for membership in memberships:
                if membership.role == 'admin':
                    users_by_org[org_slug]['admin'] = membership.user
                elif membership.role == 'manager':
                    if 'managers' not in users_by_org[org_slug]:
                        users_by_org[org_slug]['managers'] = []
                    users_by_org[org_slug]['managers'].append(membership.user)
                elif membership.role == 'member':
                    if 'members' not in users_by_org[org_slug]:
                        users_by_org[org_slug]['members'] = []
                    users_by_org[org_slug]['members'].append(membership.user)
        return users_by_org

    def get_subjects(self):
        """Get existing subjects"""
        subjects = {}
        for subject in Subject.objects.all():
            subjects[subject.title] = subject
        return subjects

    def get_demo_image_path(self, org_slug, index=0):
        """Get path to demo image if available"""
        demo_assets = Path('/Users/franco/Dev/talk/talk/media/demo_assets')
        if org_slug == 'hospital-generative':
            images = list((demo_assets / 'hospital').glob('*.png'))
            if images:
                return images[index % len(images)]
        elif org_slug == 'seguradora-generative':
            images = list((demo_assets / 'insurance').glob('*.png'))
            if images:
                return images[index % len(images)]
        return None

    def create_rich_publications(self, orgs, users_by_org):
        """Create comprehensive publications for each organization"""

        publications_by_org = {
            'hospital-generative': [
                {
                    'title': 'Protocolo de Segurança do Paciente - Atualização Q3',
                    'body': 'Novos protocolos de segurança implementados em todas as unidades. Todos os funcionários devem completar a certificação até o final do mês.',
                    'kind': Publication.FEED,
                    'importance': Publication.CRITICAL,
                },
                {
                    'title': 'Guia Completo de HIPAA',
                    'body': 'Documentação completa sobre conformidade HIPAA com exemplos práticos e casos de uso.',
                    'kind': Publication.WIKI,
                    'importance': Publication.CRITICAL,
                },
                {
                    'title': 'Procedimentos de Emergência - Atualizado',
                    'body': 'Procedimentos passo a passo para situações de emergência médica em diferentes departamentos.',
                    'kind': Publication.WIKI,
                    'importance': Publication.CRITICAL,
                },
                {
                    'title': 'Laboratório de Imagem - Novo Equipamento',
                    'body': 'Guia de uso do novo equipamento de ressonância magnética instalado no laboratório.',
                    'kind': Publication.WIKI,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Comunicado: Mudança no Sistema de Agendamento',
                    'body': 'A partir de próxima segunda, usaremos novo sistema de agendamento. Treinamento disponível online.',
                    'kind': Publication.FEED,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Boas Práticas em Atendimento ao Paciente',
                    'body': 'Guia de melhores práticas para melhorar a experiência do paciente em todas as interações.',
                    'kind': Publication.WIKI,
                    'importance': Publication.ROUTINE,
                },
            ],
            'seguradora-generative': [
                {
                    'title': 'Novo Produto: Cobertura Integral para PMEs',
                    'body': 'Apresentamos nosso novo produto de seguro abrangente para pequenas e médias empresas.',
                    'kind': Publication.FEED,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Guia Completo de Processamento de Sinistros',
                    'body': 'Procedimentos detalhados para processar sinistros de forma rápida e eficiente.',
                    'kind': Publication.WIKI,
                    'importance': Publication.CRITICAL,
                },
                {
                    'title': 'Regulações Q3 2024',
                    'body': 'Atualizações regulatórias importantes que afetam nossas operações.',
                    'kind': Publication.FEED,
                    'importance': Publication.CRITICAL,
                },
                {
                    'title': 'Rede de Prestadores - Atualização',
                    'body': 'Lista atualizada de prestadores de serviços e procedimentos cobertos.',
                    'kind': Publication.WIKI,
                    'importance': Publication.ROUTINE,
                },
                {
                    'title': 'Canais Digitais para Clientes',
                    'body': 'Guia completo sobre como utilizar nossos canais digitais para consultas e solicitações.',
                    'kind': Publication.WIKI,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Comunicado: Nova Política de Cobertura',
                    'body': 'Alterações na política de cobertura para melhor atender nossos clientes.',
                    'kind': Publication.FEED,
                    'importance': Publication.IMPORTANT,
                },
            ],
            'escola-generative': [
                {
                    'title': 'Calendário Acadêmico 2024',
                    'body': 'Datas importantes, períodos de aula e férias para o ano letivo de 2024.',
                    'kind': Publication.FEED,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Código de Conduta Estudantil',
                    'body': 'Políticas e expectativas de comportamento para todos os alunos.',
                    'kind': Publication.WIKI,
                    'importance': Publication.ROUTINE,
                },
                {
                    'title': 'Procedimentos de Inscrição',
                    'body': 'Guia passo a passo para inscrição em cursos e programas especiais.',
                    'kind': Publication.WIKI,
                    'importance': Publication.ROUTINE,
                },
                {
                    'title': 'Aviso: Mudanças no Sistema de Notas',
                    'body': 'Novo sistema de registro de notas disponível a partir de próximo semestre.',
                    'kind': Publication.FEED,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Recursos de Suporte ao Estudante',
                    'body': 'Lista completa de serviços de apoio disponíveis para ajudar no sucesso acadêmico.',
                    'kind': Publication.WIKI,
                    'importance': Publication.ROUTINE,
                },
            ],
            'manufatura-xyz': [
                {
                    'title': 'Alerta de Segurança: Novo Equipamento',
                    'body': 'Informações críticas de segurança sobre os novos equipamentos instalados na linha de produção.',
                    'kind': Publication.FEED,
                    'importance': Publication.CRITICAL,
                },
                {
                    'title': 'Procedimentos de Controle de Qualidade',
                    'body': 'Detalhes completos sobre os procedimentos de controle de qualidade para atingir <1% de taxa de erro.',
                    'kind': Publication.WIKI,
                    'importance': Publication.CRITICAL,
                },
                {
                    'title': 'Guia de Operação de Máquinas',
                    'body': 'Manual completo de operação e manutenção de todas as máquinas na fábrica.',
                    'kind': Publication.WIKI,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Comunicado: Novo Turno de Produção',
                    'body': 'A partir do próximo mês, implementaremos novo turno para aumentar a produção.',
                    'kind': Publication.FEED,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Boas Práticas de Segurança',
                    'body': 'Guia de segurança e prevenção de acidentes na fábrica.',
                    'kind': Publication.WIKI,
                    'importance': Publication.CRITICAL,
                },
            ],
            'retail-800': [
                {
                    'title': 'Atualização de Padrões de Marca',
                    'body': 'Novos padrões de marca e identidade visual para todas as 800 lojas.',
                    'kind': Publication.FEED,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Guia Completo de Atendimento ao Cliente',
                    'body': 'Melhores práticas para proporcionar excelente atendimento em todas as lojas.',
                    'kind': Publication.WIKI,
                    'importance': Publication.ROUTINE,
                },
                {
                    'title': 'Procedimentos de Caixa e Pagamento',
                    'body': 'Instruções detalhadas sobre operações de caixa e métodos de pagamento.',
                    'kind': Publication.WIKI,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Lançamento de Novo Produto',
                    'body': 'Informações sobre o novo produto sendo lançado em todas as lojas.',
                    'kind': Publication.FEED,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Política de Devoluções e Trocas',
                    'body': 'Política completa de devoluções e trocas para todos os clientes.',
                    'kind': Publication.WIKI,
                    'importance': Publication.ROUTINE,
                },
            ],
            'fintech-rapido': [
                {
                    'title': 'Conformidade Regulatória Q3',
                    'body': 'Últimos requisitos regulatórios e lista de verificação de conformidade.',
                    'kind': Publication.FEED,
                    'importance': Publication.CRITICAL,
                },
                {
                    'title': 'Diretrizes de Segurança de Produtos',
                    'body': 'Protocolos de segurança e melhores práticas para produtos fintech.',
                    'kind': Publication.WIKI,
                    'importance': Publication.CRITICAL,
                },
                {
                    'title': 'Documentação da API',
                    'body': 'Especificações técnicas completas da API para integrações.',
                    'kind': Publication.WIKI,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Atualização de Segurança Crítica',
                    'body': 'Atualização de segurança importante que deve ser implementada imediatamente.',
                    'kind': Publication.FEED,
                    'importance': Publication.CRITICAL,
                },
                {
                    'title': 'Guia de Experiência do Usuário',
                    'body': 'Padrões de UX e melhores práticas para produtos fintech.',
                    'kind': Publication.WIKI,
                    'importance': Publication.ROUTINE,
                },
            ],
            'farmalab-biotech': [
                {
                    'title': 'Atualização de Territórios de Representantes',
                    'body': 'Novas atribuições de territórios para representantes médicos.',
                    'kind': Publication.FEED,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Base de Dados de Informações de Produtos',
                    'body': 'Informações completas de produtos, dosagens e dados clínicos.',
                    'kind': Publication.WIKI,
                    'importance': Publication.CRITICAL,
                },
                {
                    'title': 'Relatório de Visita a Médicos',
                    'body': 'Template e guia para preenchimento de relatórios de visita.',
                    'kind': Publication.WIKI,
                    'importance': Publication.ROUTINE,
                },
                {
                    'title': 'Conformidade Regulatória FDA',
                    'body': 'Última documentação e conformidade regulatória FDA.',
                    'kind': Publication.FEED,
                    'importance': Publication.CRITICAL,
                },
                {
                    'title': 'Dados de Ensaios Clínicos',
                    'body': 'Resumo dos dados dos ensaios clínicos mais recentes.',
                    'kind': Publication.WIKI,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Boas Práticas de Farmacovigilância',
                    'body': 'Diretrizes completas de farmacovigilância e segurança de medicamentos.',
                    'kind': Publication.WIKI,
                    'importance': Publication.CRITICAL,
                },
            ],
        }

        for org_slug, org in orgs.items():
            pubs = publications_by_org.get(org_slug, [])
            org_admin = users_by_org[org_slug].get('admin')
            if not org_admin:
                continue

            for idx, pub_config in enumerate(pubs):
                slug = slugify(f"{pub_config['title']}-{org_slug}-{idx}")

                # Try to get demo image
                image_path = self.get_demo_image_path(org_slug, idx)
                image_content = None
                if image_path and image_path.exists():
                    with open(image_path, 'rb') as f:
                        image_content = ContentFile(f.read(), name=image_path.name)

                publication, _ = Publication.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'organization': org,
                        'title': pub_config['title'],
                        'kind': pub_config['kind'],
                        'status': Publication.PUBLISHED,
                        'importance': pub_config['importance'],
                        'body': pub_config['body'],
                        'excerpt': pub_config['body'][:150],
                        'author': org_admin,
                        'published_at': timezone.now(),
                        'image': image_content if image_content else None,
                    }
                )

            self.stdout.write(f'  Publications created for {org.name}')

    def create_rich_documents(self, orgs, users_by_org):
        """Create comprehensive documents for each organization"""

        documents_by_org = {
            'hospital-generative': [
                {'title': 'Manual de Segurança do Paciente', 'category': 'manual', 'description': 'Guia abrangente de segurança'},
                {'title': 'Conformidade HIPAA', 'category': 'policy', 'description': 'Documentação legal de conformidade'},
                {'title': 'Protocolos de Emergência', 'category': 'procedure', 'description': 'Procedimentos de resposta a emergências'},
                {'title': 'Guia de Equipamentos Médicos', 'category': 'manual', 'description': 'Manual de operação de equipamentos'},
                {'title': 'Política de Privacidade de Pacientes', 'category': 'policy', 'description': 'Políticas de privacidade completas'},
                {'title': 'Procedimentos de Esterilização', 'category': 'procedure', 'description': 'Processo de esterilização de instrumentos'},
            ],
            'seguradora-generative': [
                {'title': 'Modelos de Política de Seguro', 'category': 'form', 'description': 'Documentos padrão de política'},
                {'title': 'Manual de Processamento de Sinistros', 'category': 'manual', 'description': 'Guia de procedimentos de sinistros'},
                {'title': 'Guia de Conformidade Regulatória', 'category': 'policy', 'description': 'Requisitos regulatórios completos'},
                {'title': 'Rede de Prestadores', 'category': 'evidence', 'description': 'Lista de prestadores de serviços'},
                {'title': 'Cobertura de Produtos', 'category': 'manual', 'description': 'Detalhes completos de cobertura'},
                {'title': 'Processo de Aprovação de Sinistros', 'category': 'procedure', 'description': 'Fluxo de aprovação de sinistros'},
            ],
            'escola-generative': [
                {'title': 'Manual do Aluno', 'category': 'manual', 'description': 'Handbook para estudantes'},
                {'title': 'Documentação de Currículo', 'category': 'evidence', 'description': 'Descrições e requisitos de cursos'},
                {'title': 'Código de Conduta', 'category': 'policy', 'description': 'Políticas de conduta estudantil'},
                {'title': 'Procedimentos de Inscrição', 'category': 'procedure', 'description': 'Processo de inscrição em cursos'},
                {'title': 'Política Acadêmica', 'category': 'policy', 'description': 'Políticas e procedimentos acadêmicos'},
            ],
            'manufatura-xyz': [
                {'title': 'Manual de Segurança', 'category': 'manual', 'description': 'Guia completo de segurança'},
                {'title': 'Documento de Padrões de Qualidade', 'category': 'evidence', 'description': 'Procedimentos de controle de qualidade'},
                {'title': 'Guia de Operação de Equipamentos', 'category': 'manual', 'description': 'Manual de máquinas'},
                {'title': 'Certificação de Máquinas', 'category': 'evidence', 'description': 'Certificados de equipamentos'},
                {'title': 'Procedimentos de Manutenção', 'category': 'procedure', 'description': 'Cronograma e procedimentos de manutenção'},
                {'title': 'Política de Segurança Industrial', 'category': 'policy', 'description': 'Políticas de segurança completas'},
            ],
            'retail-800': [
                {'title': 'Manual de Diretrizes de Marca', 'category': 'manual', 'description': 'Guia de identidade de marca'},
                {'title': 'Manual de Operações de Loja', 'category': 'manual', 'description': 'Procedimentos operacionais padrão'},
                {'title': 'Guia de Atendimento ao Cliente', 'category': 'manual', 'description': 'Padrões de serviço ao cliente'},
                {'title': 'Política de Devoluções', 'category': 'policy', 'description': 'Política de devoluções e trocas'},
                {'title': 'Procedimentos de Ponto de Venda', 'category': 'procedure', 'description': 'Operações de caixa e PDV'},
                {'title': 'Guia de Produtos Especiais', 'category': 'manual', 'description': 'Informações sobre produtos especiais'},
            ],
            'fintech-rapido': [
                {'title': 'Documento de Conformidade de Segurança', 'category': 'policy', 'description': 'Protocolos de segurança'},
                {'title': 'Documentação da API', 'category': 'evidence', 'description': 'Especificações técnicas de API'},
                {'title': 'Marco Regulatório', 'category': 'policy', 'description': 'Requisitos regulatórios completos'},
                {'title': 'Guia de Segurança do Produto', 'category': 'procedure', 'description': 'Procedimentos de segurança do produto'},
                {'title': 'Evidência de Conformidade', 'category': 'evidence', 'description': 'Documentação de conformidade'},
                {'title': 'Diretivas de Privacidade de Dados', 'category': 'policy', 'description': 'Políticas de privacidade de dados'},
            ],
            'farmalab-biotech': [
                {'title': 'Catálogo de Produtos', 'category': 'evidence', 'description': 'Informações completas de produtos e especificações'},
                {'title': 'Manual do Representante Médico', 'category': 'manual', 'description': 'Diretrizes para representantes médicos'},
                {'title': 'Dados de Ensaios Clínicos', 'category': 'evidence', 'description': 'Pesquisa e resultados de ensaios'},
                {'title': 'Documentação Regulatória', 'category': 'policy', 'description': 'Aprovações de FDA e regulatory'},
                {'title': 'Procedimento de Farmacovigilância', 'category': 'procedure', 'description': 'Processo de farmacovigilância'},
                {'title': 'Conformidade de Boas Práticas', 'category': 'policy', 'description': 'Políticas de boas práticas farmacêuticas'},
            ],
        }

        for org_slug, org in orgs.items():
            docs = documents_by_org.get(org_slug, [])
            org_admin = users_by_org[org_slug].get('admin')
            if not org_admin:
                continue

            for idx, doc_config in enumerate(docs):
                slug = slugify(f"{doc_config['title']}-{org_slug}-{idx}")
                document, _ = Document.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'organization': org,
                        'title': doc_config['title'],
                        'category': doc_config['category'],
                        'description': doc_config['description'],
                        'status': Document.PUBLISHED,
                        'owner': org_admin,
                    }
                )

            self.stdout.write(f'  Documents created for {org.name}')

    def create_learning_trails(self, orgs, users_by_org, subjects):
        """Create learning trails for organizations"""

        trails_by_org = {
            'hospital-generative': [
                {
                    'title': 'Segurança do Paciente 101',
                    'objective': 'Aprender princípios fundamentais de segurança do paciente',
                    'trail_type': ContentTrail.REQUIRED,
                },
                {
                    'title': 'Conformidade HIPAA',
                    'objective': 'Entender e aplicar regulações HIPAA',
                    'trail_type': ContentTrail.REQUIRED,
                },
                {
                    'title': 'Procedimentos de Emergência',
                    'objective': 'Preparação para resposta a emergências médicas',
                    'trail_type': ContentTrail.REQUIRED,
                },
                {
                    'title': 'Novo Equipamento Médico',
                    'objective': 'Treinamento prático no novo equipamento de ressonância',
                    'trail_type': ContentTrail.RECOMMENDED,
                },
            ],
            'seguradora-generative': [
                {
                    'title': 'Processamento de Sinistros Avançado',
                    'objective': 'Dominar técnicas de processamento eficiente de sinistros',
                    'trail_type': ContentTrail.REQUIRED,
                },
                {
                    'title': 'Produtos de Seguro',
                    'objective': 'Conhecer linha completa de produtos de seguros',
                    'trail_type': ContentTrail.RECOMMENDED,
                },
                {
                    'title': 'Conformidade Regulatória',
                    'objective': 'Estar em dia com regulações vigentes',
                    'trail_type': ContentTrail.REQUIRED,
                },
                {
                    'title': 'Atendimento ao Cliente',
                    'objective': 'Melhorar habilidades de atendimento e negociação',
                    'trail_type': ContentTrail.RECOMMENDED,
                },
            ],
            'escola-generative': [
                {
                    'title': 'Orientação para Novos Alunos',
                    'objective': 'Conhecer campus, recursos e oportunidades',
                    'trail_type': ContentTrail.REQUIRED,
                },
                {
                    'title': 'Ferramentas Acadêmicas Online',
                    'objective': 'Aprender a usar plataformas e ferramentas acadêmicas',
                    'trail_type': ContentTrail.RECOMMENDED,
                },
                {
                    'title': 'Desenvolvimento Acadêmico',
                    'objective': 'Estratégias para sucesso acadêmico',
                    'trail_type': ContentTrail.RECOMMENDED,
                },
            ],
            'manufatura-xyz': [
                {
                    'title': 'Segurança na Fábrica',
                    'objective': 'Certificação em segurança industrial',
                    'trail_type': ContentTrail.REQUIRED,
                },
                {
                    'title': 'Operação de Máquinas',
                    'objective': 'Treinamento hands-on em operação de máquinas',
                    'trail_type': ContentTrail.REQUIRED,
                },
                {
                    'title': 'Controle de Qualidade',
                    'objective': 'Aprender procedimentos de controle de qualidade',
                    'trail_type': ContentTrail.REQUIRED,
                },
                {
                    'title': 'Liderança na Produção',
                    'objective': 'Desenvolvimento de habilidades de liderança',
                    'trail_type': ContentTrail.RECOMMENDED,
                },
            ],
            'retail-800': [
                {
                    'title': 'Orientação de Vendedor',
                    'objective': 'Primeiros passos para novos vendedores',
                    'trail_type': ContentTrail.REQUIRED,
                },
                {
                    'title': 'Atendimento de Excelência',
                    'objective': 'Técnicas de atendimento ao cliente de alto nível',
                    'trail_type': ContentTrail.RECOMMENDED,
                },
                {
                    'title': 'Conhecimento de Produtos',
                    'objective': 'Aprofundar conhecimento em linhas de produtos',
                    'trail_type': ContentTrail.RECOMMENDED,
                },
                {
                    'title': 'Gerenciamento de Loja',
                    'objective': 'Preparação para posição de gerência',
                    'trail_type': ContentTrail.RECOMMENDED,
                },
            ],
            'fintech-rapido': [
                {
                    'title': 'Segurança Fintech 101',
                    'objective': 'Fundamentos de segurança para produtos fintech',
                    'trail_type': ContentTrail.REQUIRED,
                },
                {
                    'title': 'Conformidade Regulatória Fintech',
                    'objective': 'Entender landscape regulatório fintech',
                    'trail_type': ContentTrail.REQUIRED,
                },
                {
                    'title': 'Desenvolvimento de Produto',
                    'objective': 'Metodologias de desenvolvimento de produtos fintech',
                    'trail_type': ContentTrail.RECOMMENDED,
                },
                {
                    'title': 'Arquitetura de Sistemas',
                    'objective': 'Padrões e arquiteturas de sistemas fintech',
                    'trail_type': ContentTrail.RECOMMENDED,
                },
            ],
            'farmalab-biotech': [
                {
                    'title': 'Treinamento de Representante Médico',
                    'objective': 'Certificação completa para representantes médicos',
                    'trail_type': ContentTrail.REQUIRED,
                },
                {
                    'title': 'Conhecimento de Produtos Farmacêuticos',
                    'objective': 'Domínio completo de linha de produtos',
                    'trail_type': ContentTrail.REQUIRED,
                },
                {
                    'title': 'Conformidade Regulatória FDA',
                    'objective': 'Entender conformidade FDA e regulatória',
                    'trail_type': ContentTrail.REQUIRED,
                },
                {
                    'title': 'Venda e Negociação Médica',
                    'objective': 'Habilidades avançadas de venda para médicos',
                    'trail_type': ContentTrail.RECOMMENDED,
                },
            ],
        }

        for org_slug, org in orgs.items():
            trails_config = trails_by_org.get(org_slug, [])
            org_admin = users_by_org[org_slug].get('admin')
            if not org_admin:
                continue

            for idx, trail_config in enumerate(trails_config):
                slug = slugify(f"{trail_config['title']}-{org_slug}-{idx}")
                trail, _ = ContentTrail.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'organization': org,
                        'title': trail_config['title'],
                        'objective': trail_config['objective'],
                        'trail_type': trail_config['trail_type'],
                        'status': ContentTrail.PUBLISHED,
                        'owner': org_admin,
                    }
                )

            self.stdout.write(f'  Learning trails created for {org.name}')

    def create_trail_assignments(self, orgs, users_by_org):
        """Assign trails to users"""

        for org_slug, org in orgs.items():
            org_users = users_by_org[org_slug]
            trails = ContentTrail.objects.filter(organization=org, status=ContentTrail.PUBLISHED)

            # Assign required trails to all members
            for trail in trails.filter(trail_type=ContentTrail.REQUIRED):
                for user_list in [org_users.get('managers', []), org_users.get('members', [])]:
                    for user in user_list[:5]:  # Limit to first 5
                        TrailAssignment.objects.get_or_create(
                            user=user,
                            trail=trail,
                            defaults={'is_mandatory': True}
                        )

            # Assign recommended trails to managers
            for trail in trails.filter(trail_type=ContentTrail.RECOMMENDED):
                for user in org_users.get('managers', []):
                    TrailAssignment.objects.get_or_create(
                        user=user,
                        trail=trail,
                        defaults={'is_mandatory': False}
                    )

            self.stdout.write(f'  Trail assignments created for {org.name}')
