from django.core.management.base import BaseCommand
from django.utils import timezone
from django_tenants.utils import schema_context, get_tenant_model
from configuration.models import Organization
from courses.models import Course, Module, Text
from publishing.models import Publication
from documents.models import Document
from recruitment.models import CandidateOnboardingTrail


class Command(BaseCommand):
    help = 'Seed content (courses, feeds, wikis, documents) for Bourbon Shopping inside tenant schema'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', type=str, default='bourbon-shopping', help='Tenant schema name')

    def handle(self, *args, **options):
        tenant_name = options['tenant']

        # Get tenant model and find matching one
        TenantModel = get_tenant_model()
        try:
            tenant = TenantModel.objects.get(schema_name=tenant_name)
            self.seed_for_tenant(tenant)
        except TenantModel.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Tenant {tenant_name} not found'))
            return

    def seed_for_tenant(self, tenant):
        """Seed content for a specific tenant using schema_context."""
        with schema_context(tenant.schema_name):
            try:
                org_name = tenant.name if hasattr(tenant, 'name') else tenant.schema_name
                self.stdout.write(f"📚 Criando conteúdo para {org_name} (dentro do tenant)...\n")

                # Criar cursos de varejo
                courses = self.create_retail_courses()
                self.stdout.write(self.style.SUCCESS(f"✓ {len(courses)} cursos criados"))

                self.stdout.write(self.style.SUCCESS("\n✅ Seed de cursos concluído com sucesso! (Publicações e documentos podem ser criados manualmente)"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Erro ao criar conteúdo: {str(e)}"))
                raise

    def create_retail_courses(self):
        """Criar cursos de varejo e treinamento (versão simplificada)"""
        from tenants_core.models import TenantUser

        # Get or create default owner
        owner = TenantUser.objects.first()
        if not owner:
            self.stdout.write(self.style.ERROR("No TenantUser found to assign as course owner"))
            return []

        # Get or create default subject
        from courses.models import Subject
        subject, _ = Subject.objects.get_or_create(
            title='Retail Training'
        )

        courses_data = [
            {
                'title': 'Fundamentos de Atendimento ao Cliente',
                'overview': 'Aprenda as melhores práticas para atender clientes com excelência no varejo',
                'modules': [
                    {'title': 'Comunicação Efetiva', 'description': 'Como se comunicar de forma clara e profissional com clientes'},
                    {'title': 'Empatia e Escuta Ativa', 'description': 'Entenda as necessidades do cliente e ofereça soluções'},
                    {'title': 'Resolução de Conflitos', 'description': 'Como lidar com clientes insatisfeitos de forma profissional'},
                ]
            },
            {
                'title': 'Técnicas de Vendas para Varejo',
                'overview': 'Domine as técnicas essenciais para aumentar suas vendas',
                'modules': [
                    {'title': 'Abordagem do Cliente', 'description': 'Como iniciar uma conversa com potencial de venda'},
                    {'title': 'Apresentação de Produtos', 'description': 'Destaque benefícios e características dos produtos'},
                    {'title': 'Fechamento de Vendas', 'description': 'Estratégias para concluir vendas com sucesso'},
                    {'title': 'Venda Cruzada e Upsell', 'description': 'Técnicas para aumentar o ticket médio'},
                ]
            },
            {
                'title': 'Organização e Visual Merchandising',
                'overview': 'Mantenha a loja atraente e bem organizada para potencializar vendas',
                'modules': [
                    {'title': 'Princípios de Visual Merchandising', 'description': 'Como dispor produtos para atrair clientes'},
                    {'title': 'Controle de Estoque', 'description': 'Gerenciamento eficiente de inventário'},
                    {'title': 'Manutenção da Loja', 'description': 'Limpeza, organização e segurança do espaço'},
                ]
            },
            {
                'title': 'Sistemas de PDV e Formas de Pagamento',
                'overview': 'Trabalhe com sistemas modernos de caixa',
                'modules': [
                    {'title': 'Operação do Sistema PDV', 'description': 'Como usar corretamente o sistema de ponto de venda'},
                    {'title': 'Formas de Pagamento', 'description': 'Dinheiro, cartão, PIX, crediário e outras modalidades'},
                    {'title': 'Segurança Financeira', 'description': 'Procedimentos seguros e conformidade na caixa'},
                ]
            },
            {
                'title': 'Políticas e Código de Conduta',
                'overview': 'Conheça as políticas da empresa e nossos valores',
                'modules': [
                    {'title': 'Código de Conduta', 'description': 'Valores, ética e comportamento esperado'},
                    {'title': 'Direitos e Deveres', 'description': 'Direitos e deveres dos colaboradores'},
                    {'title': 'Segurança e Saúde', 'description': 'Ambientes seguros, higiene e prevenção'},
                ]
            },
        ]

        courses = []
        for course_data in courses_data:
            try:
                course, created = Course.objects.get_or_create(
                    title=course_data['title'],
                    defaults={
                        'overview': course_data['overview'],
                        'state': 'published',
                        'owner': owner,
                        'subject': subject,
                    }
                )
                if created or course not in courses:
                    courses.append(course)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠ Erro ao criar/atualizar curso '{course_data['title']}': {str(e)}"))

        return courses

    def create_publications_feed(self):
        """Criar feed de publicações/notícias"""
        feeds_data = [
            {
                'title': 'Bem-vindo ao Bourbon Shopping!',
                'subtitle': 'Estamos felizes em ter você no nosso time. Aqui você encontrará todas as informações que precisa.',
                'content': '<p>Bem-vindo ao Bourbon Shopping! Somos um centro de compras com mais de 100 lojas e milhares de oportunidades. Nossa missão é oferecer a melhor experiência de compra e trabalho.</p><p>Nesta plataforma, você poderá acessar treinamentos, políticas, notícias e recursos que te ajudarão a ter sucesso em sua carreira.</p>',
            },
            {
                'title': 'Dicas de Atendimento para Aumentar Vendas',
                'subtitle': 'Conheça as melhores práticas que nossos vendedores top utilizam',
                'content': '<p>Nossos melhores vendedores têm algo em comum: eles entendem seus clientes. Aqui estão 5 dicas que fazem diferença:</p><ul><li>Aborde com genuíno interesse</li><li>Escute mais do que fale</li><li>Personalize o atendimento</li><li>Demonstre expertise sobre produtos</li><li>Sempre tente agregar valor</li></ul>',
            },
            {
                'title': 'Campanha de Vendas Julho - Desafio de Metas',
                'subtitle': 'Participe do desafio mensal e ganhe prêmios incríveis',
                'content': '<p>Este mês, estamos lançando um desafio especial! Os 10 melhores vendedores de cada categoria ganham prêmios em dinheiro.</p><p>Saiba mais com seu gerente de loja ou acesse a intranet para ver o regulamento completo.</p>',
            },
            {
                'title': 'Segurança e Higiene - Novos Procedimentos',
                'subtitle': 'Atualizações importantes sobre protocolos de saúde e segurança',
                'content': '<p>Para garantir um ambiente seguro para todos, implementamos novos procedimentos. Todos os colaboradores devem seguir:</p><ul><li>Uso de máscaras em áreas de estoque</li><li>Higiene das mãos a cada 2 horas</li><li>Distanciamento mínimo de 1 metro</li><li>Relatório de qualquer problema</li></ul>',
            },
            {
                'title': 'Histórias de Sucesso - Colaborador do Mês',
                'subtitle': 'Conheça a história de Maria Silva, atendente destaque',
                'content': '<p>Maria trabalha há 3 anos como atendente e é referência em atendimento ao cliente. Sua dedicação e simpatia conquistam clientes todos os dias. Ela é um exemplo para todos nós!</p><p>Parabéns Maria, você merece!</p>',
            },
        ]

        publications = []
        for feed_data in feeds_data:
            pub, created = Publication.objects.get_or_create(
                title=feed_data['title'],
                defaults={
                    'subtitle': feed_data['subtitle'],
                    'content': feed_data['content'],
                    'status': 'published',
                    'published_at': timezone.now(),
                }
            )
            if created:
                publications.append(pub)

        return publications

    def create_wiki_publications(self):
        """Criar artigos wiki/referência"""
        wikis_data = [
            {
                'title': 'Como Usar o Sistema de PDV',
                'subtitle': 'Guia completo do sistema de ponto de venda',
                'content': '<h2>Iniciando o PDV</h2><p>1. Faça login com suas credenciais<br>2. Selecione a caixa/terminal<br>3. Está pronto para começar</p><h2>Operações Básicas</h2><p>- Escanear produto: aponte o leitor de código de barras<br>- Alterar quantidade: pressione F2 e digite a quantidade<br>- Aplicar desconto: pressione F3 e selecione o motivo</p>',
            },
            {
                'title': 'Políticas de Devolução e Troca',
                'subtitle': 'Regras para devoluções e trocas de produtos',
                'content': '<h2>Direito do Cliente</h2><p>Clientes têm direito a devolução em até 30 dias. Requisitos:</p><ul><li>Produto com embalagem original</li><li>Nota fiscal ou comprovante</li><li>Sem sinais de uso</li></ul><h2>Como Processar</h2><p>1. Verificar documento de compra<br>2. Inspecionar produto<br>3. Emitir devolução no PDV<br>4. Processar reembolso ou troca</p>',
            },
            {
                'title': 'Organograma do Bourbon Shopping',
                'subtitle': 'Estrutura hierárquica e contatos',
                'content': '<h2>Diretoria</h2><p>Diretor Geral: João Silva - ramal 1000</p><h2>Gerência de Operações</h2><p>Gerente: Maria Santos - ramal 1001</p><h2>Gerentes por Área</h2><ul><li>Moda: Carlos (ramal 2001)</li><li>Eletrônicos: Ana (ramal 2002)</li><li>Alimentação: Roberto (ramal 2003)</li></ul>',
            },
            {
                'title': 'Guia de Benefícios',
                'subtitle': 'Conheça todos os benefícios dos colaboradores',
                'content': '<h2>Benefícios Oferecidos</h2><ul><li>Vale refeição: R$ 400/mês</li><li>Vale transporte: 100% do valor</li><li>Convênio médico: sem custo</li><li>Convênio dentário: 50% de desconto</li><li>Desconto em compras: 20% no shopping</li><li>Auxílio creche: R$ 300/filho</li></ul>',
            },
            {
                'title': 'Processo de Promoção',
                'subtitle': 'Como avançar na carreira no Bourbon Shopping',
                'content': '<h2>Critérios</h2><p>Promoções levam em conta:</p><ul><li>Desempenho nas metas</li><li>Avaliação de desempenho</li><li>Assiduidade e pontualidade</li><li>Conclusão de treinamentos</li><li>Feedback de clientes e colegas</li></ul><h2>Próximos Passos</h2><p>1. Converse com seu gerente<br>2. Elabore um plano de desenvolvimento<br>3. Complete os treinamentos necessários<br>4. Aguarde a próxima rodada de promoções</p>',
            },
        ]

        wikis = []
        for wiki_data in wikis_data:
            pub, created = Publication.objects.get_or_create(
                title=wiki_data['title'],
                defaults={
                    'subtitle': wiki_data['subtitle'],
                    'content': wiki_data['content'],
                    'status': 'published',
                    'published_at': timezone.now(),
                }
            )
            if created:
                wikis.append(pub)

        return wikis

    def create_documents(self):
        """Criar documentos de referência"""
        docs_data = [
            {
                'title': 'Código de Conduta - Bourbon Shopping',
                'description': 'Documento oficial com regras e valores da empresa',
            },
            {
                'title': 'Regulamento de Pessoal',
                'description': 'Regulamento geral de pessoal e relacionamento trabalhista',
            },
            {
                'title': 'Manual de Operação de Loja',
                'description': 'Procedimentos e rotinas de operação diárias',
            },
            {
                'title': 'Tabela de Salários 2026',
                'description': 'Tabela oficial de salários e benefícios',
            },
            {
                'title': 'Política de Segurança e Higiene',
                'description': 'Normas de segurança, higiene e prevenção de acidentes',
            },
            {
                'title': 'Formulário de Solicitação de Férias',
                'description': 'Documento para solicitação de período de férias',
            },
        ]

        documents = []
        for doc_data in docs_data:
            doc, created = Document.objects.get_or_create(
                title=doc_data['title'],
                defaults={
                    'description': doc_data['description'],
                    'status': 'published',
                }
            )
            if created:
                documents.append(doc)

        return documents

    def update_onboarding_trails_with_courses(self, courses):
        """Atualizar trails de onboarding com IDs dos cursos"""
        trails = CandidateOnboardingTrail.objects.all()
        course_ids = [course.id for course in courses[:2]]  # Primeiros 2 cursos

        for trail in trails:
            trail.courses = course_ids
            trail.save()

        self.stdout.write(self.style.SUCCESS(f"✓ {trails.count()} trilhas atualizadas com cursos"))
