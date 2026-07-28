from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from configuration.models import Organization, Company, BusinessUnit, BusinessChannel, JobFunction
from courses.models import Course, Module, Text
from publishing.models import Publication
from documents.models import Document
from recruitment.models import Position

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed recruitment data for Bourbon Shopping with realistic retail stores and positions'

    def add_arguments(self, parser):
        parser.add_argument('--org-slug', type=str, default='bourbon-shopping', help='Organization slug')

    def handle(self, *args, **options):
        org_slug = options['org_slug']

        self.stdout.write(f"🏪 Iniciando seed de recrutamento para {org_slug}...\n")

        # Obter organização (deve existir)
        org = Organization.objects.get(slug=org_slug)
        self.stdout.write(self.style.SUCCESS(f"✓ Organização: {org.name}"))

        # Criar company (SHARED_APPS)
        company = self.get_or_create_company(org)
        self.stdout.write(self.style.SUCCESS(f"✓ Empresa: {company.name}"))

        # Criar canais de negócio
        channels = self.create_business_channels(company)
        self.stdout.write(self.style.SUCCESS(f"✓ {len(channels)} canais de negócio criados"))

        # Criar funções de trabalho
        job_functions = self.create_job_functions(company, channels)
        self.stdout.write(self.style.SUCCESS(f"✓ {len(job_functions)} funções criadas"))

        # Criar lojas (business units) com channels
        stores = self.create_stores(company, channels)
        self.stdout.write(self.style.SUCCESS(f"✓ {len(stores)} lojas criadas com channels"))

        # Criar posições de vendas
        positions = self.create_store_positions(org, stores, job_functions)
        self.stdout.write(self.style.SUCCESS(f"✓ {len(positions)} posições de vendas criadas"))

        self.stdout.write(self.style.SUCCESS("\n✅ Seed do recrutamento concluído com sucesso!\n"))
        self.stdout.write(self.style.WARNING(
            "📚 Próxima: Executar seed_bourbon_content para adicionar cursos, feeds, wikis e documentos\n"
        ))
        self.stdout.write(self.style.WARNING(
            "📋 Estrutura criada:\n"
            f"  • {len(stores)} lojas principais\n"
            f"  • {len(job_functions)} funções de trabalho\n"
            f"  • {len(channels)} canais de negócio\n"
            f"  • {len(positions)} posições de vendas\n"
            "\n🎯 Próximas fases:\n"
            "  1. QR Code por loja/hierarquia de audiência\n"
            "  2. Fluxo de candidato com seleção de funções\n"
            "  3. Trilha de onboarding com pesquisa/entrevista\n"
            "  4. Dashboard do empregado com scores\n"
        ))

    def get_or_create_company(self, org):
        """Obter ou criar empresa na schema SHARED"""
        company, created = Company.objects.get_or_create(
            organization=org,
            name='Bourbon Shopping',
            defaults={'code': 'BOURBON001', 'active': True}
        )
        return company

    def create_business_channels(self, company):
        """Criar canais de negócio (categorias de lojas)"""
        channel_data = [
            'Moda & Vestuário',
            'Eletrônicos',
            'Alimentação & Bebidas',
            'Beleza & Cuidados Pessoais',
            'Serviços',
            'Varejo Geral',
        ]

        channels = []
        for name in channel_data:
            channel, _ = BusinessChannel.objects.get_or_create(
                company=company,
                name=name,
                defaults={'active': True}
            )
            channels.append(channel)

        return channels

    def create_job_functions(self, company, channels):
        """Criar funções de trabalho para varejo"""
        functions_data = [
            {'name': 'Vendedor', 'channels': [0, 1, 2, 3, 5]},
            {'name': 'Atendente de Loja', 'channels': [0, 1, 2, 3, 4, 5]},
            {'name': 'Supervisor de Loja', 'channels': [0, 1, 2, 3, 4, 5]},
            {'name': 'Gerente de Loja', 'channels': [0, 1, 2, 3, 4, 5]},
            {'name': 'Operacional', 'channels': [0, 1, 2, 3, 5]},
            {'name': 'Caixa', 'channels': [0, 1, 2, 3, 4, 5]},
        ]

        functions = []
        for func_data in functions_data:
            function, _ = JobFunction.objects.get_or_create(
                company=company,
                name=func_data['name'],
                defaults={'active': True}
            )

            channel_indices = func_data.get('channels', [])
            for idx in channel_indices:
                if idx < len(channels):
                    function.channels.add(channels[idx])

            functions.append(function)

        return functions

    def create_stores(self, company, channels):
        """Criar lojas (business units) do Bourbon Shopping com channels específicos"""
        # Mapeamento de lojas para seus channels (baseado em tipo de negócio)
        channel_map = {
            'Moda & Vestuário': ['Riachuelo', 'Hering', 'Marisa', 'Renner'],
            'Eletrônicos': ['Lojas Americanas', 'Ponto Frio'],
            'Alimentação & Bebidas': ['Mc Donalds', 'Burger King', 'Subway'],
            'Beleza & Cuidados Pessoais': ['Natura Cosméticos', 'O Boticário'],
            'Serviços': ['Cine Bourbon'],
            'Varejo Geral': ['Bourbon Shopping Centro', 'Bourbon Shopping Lloyds', 'C&C'],
        }

        stores_data = [
            {'name': 'Bourbon Shopping Centro', 'code': 'BOURBON-001'},
            {'name': 'Bourbon Shopping Lloyds', 'code': 'BOURBON-002'},
            {'name': 'Riachuelo', 'code': 'RIACHUELO-001'},
            {'name': 'Hering', 'code': 'HERING-001'},
            {'name': 'C&C', 'code': 'CC-001'},
            {'name': 'Natura Cosméticos', 'code': 'NATURA-001'},
            {'name': 'O Boticário', 'code': 'BOTICARIO-001'},
            {'name': 'Lojas Americanas', 'code': 'AMERICANAS-001'},
            {'name': 'Ponto Frio', 'code': 'PONTOFRIO-001'},
            {'name': 'Marisa', 'code': 'MARISA-001'},
            {'name': 'Renner', 'code': 'RENNER-001'},
            {'name': 'Mc Donalds', 'code': 'MCDONALDS-001'},
            {'name': 'Burger King', 'code': 'BURGERKING-001'},
            {'name': 'Subway', 'code': 'SUBWAY-001'},
            {'name': 'Cine Bourbon', 'code': 'CINE-001'},
        ]

        # Criar mapa de nome de loja para channel
        store_to_channel = {}
        for channel_name, store_names in channel_map.items():
            channel = next((c for c in channels if c.name == channel_name), None)
            if channel:
                for store_name in store_names:
                    store_to_channel[store_name] = channel

        stores = []
        for store_data in stores_data:
            channel = store_to_channel.get(store_data['name'])
            store, _ = BusinessUnit.objects.get_or_create(
                company=company,
                name=store_data['name'],
                defaults={
                    'code': store_data['code'],
                    'channel': channel,
                    'active': True,
                }
            )
            # Atualizar channel se já existia sem channel
            if store.channel is None and channel:
                store.channel = channel
                store.save()
            stores.append(store)

        return stores

    def create_store_positions(self, org, stores, job_functions):
        """Criar posições de vendas específicas por loja com job_function"""
        positions = []

        for store in stores:
            # Filtrar job_functions válidas para o channel da loja
            valid_job_funcs = []
            if store.channel:
                valid_job_funcs = [jf for jf in job_functions if store.channel in jf.channels.all()]
            else:
                valid_job_funcs = job_functions[:3]

            for job_func in valid_job_funcs[:3]:
                position_title = f'{job_func.name} - {store.name}'

                position, _ = Position.objects.get_or_create(
                    organization=org,
                    title=position_title,
                    business_unit=store,
                    defaults={
                        'job_function': job_func,
                        'description': f'{job_func.name} na {store.name}',
                        'active': True,
                        'city': 'Porto Alegre',
                        'salary_min': self.get_salary_for_role(job_func.name),
                        'salary_max': self.get_salary_for_role(job_func.name) + 500,
                    }
                )

                # Atualizar job_function se não estava setado
                if position.job_function is None:
                    position.job_function = job_func
                    position.save()

                positions.append(position)

        return positions

    def get_salary_for_role(self, role_title):
        """Retornar salário base por função (valores em BRL)"""
        salaries = {
            'Vendedor': 1500,
            'Atendente de Loja': 1200,
            'Supervisor de Loja': 2200,
            'Gerente de Loja': 3500,
            'Operacional': 1200,
            'Caixa': 1300,
        }
        return salaries.get(role_title, 1200)

    def create_retail_courses(self, org):
        """Criar cursos de varejo e treinamento"""
        courses_data = [
            {
                'title': 'Fundamentos de Atendimento ao Cliente',
                'description': 'Aprenda as melhores práticas para atender clientes com excelência no varejo',
                'modules': [
                    {'title': 'Comunicação Efetiva', 'description': 'Como se comunicar de forma clara e profissional com clientes'},
                    {'title': 'Empatia e Escuta Ativa', 'description': 'Entenda as necessidades do cliente e ofereça soluções'},
                    {'title': 'Resolução de Conflitos', 'description': 'Como lidar com clientes insatisfeitos de forma profissional'},
                ]
            },
            {
                'title': 'Técnicas de Vendas para Varejo',
                'description': 'Domine as técnicas essenciais para aumentar suas vendas',
                'modules': [
                    {'title': 'Abordagem do Cliente', 'description': 'Como iniciar uma conversa com potencial de venda'},
                    {'title': 'Apresentação de Produtos', 'description': 'Destaque benefícios e características dos produtos'},
                    {'title': 'Fechamento de Vendas', 'description': 'Estratégias para concluir vendas com sucesso'},
                    {'title': 'Venda Cruzada e Upsell', 'description': 'Técnicas para aumentar o ticket médio'},
                ]
            },
            {
                'title': 'Organização e Visual Merchandising',
                'description': 'Mantenha a loja atraente e bem organizada para potencializar vendas',
                'modules': [
                    {'title': 'Princípios de Visual Merchandising', 'description': 'Como dispor produtos para atrair clientes'},
                    {'title': 'Controle de Estoque', 'description': 'Gerenciamento eficiente de inventário'},
                    {'title': 'Manutenção da Loja', 'description': 'Limpeza, organização e segurança do espaço'},
                ]
            },
            {
                'title': 'Sistemas de PDV e Formas de Pagamento',
                'description': 'Trabalhe com sistemas modernos de caixa',
                'modules': [
                    {'title': 'Operação do Sistema PDV', 'description': 'Como usar corretamente o sistema de ponto de venda'},
                    {'title': 'Formas de Pagamento', 'description': 'Dinheiro, cartão, PIX, crediário e outras modalidades'},
                    {'title': 'Segurança Financeira', 'description': 'Procedimentos seguros e conformidade na caixa'},
                ]
            },
            {
                'title': 'Políticas e Código de Conduta',
                'description': 'Conheça as políticas da empresa e nossos valores',
                'modules': [
                    {'title': 'Código de Conduta', 'description': 'Valores, ética e comportamento esperado'},
                    {'title': 'Direitos e Deveres', 'description': 'Direitos e deveres dos colaboradores'},
                    {'title': 'Segurança e Saúde', 'description': 'Ambientes seguros, higiene e prevenção'},
                ]
            },
        ]

        courses = []
        for course_data in courses_data:
            course, _ = Course.objects.get_or_create(
                organization=org,
                title=course_data['title'],
                defaults={
                    'overview': course_data['description'],
                    'state': 'published',
                }
            )

            for idx, module_data in enumerate(course_data.get('modules', []), 1):
                module, _ = Module.objects.get_or_create(
                    course=course,
                    title=module_data['title'],
                    defaults={
                        'description': module_data['description'],
                        'order': idx,
                    }
                )

                Text.objects.get_or_create(
                    module=module,
                    order=1,
                    defaults={
                        'title': module_data['title'],
                        'text': f'<p><strong>{module_data["description"]}</strong></p><p>Este módulo contém conteúdo educacional sobre o tema. O treinamento completo inclui videos, exercícios práticos e avaliações.</p>',
                    }
                )

            courses.append(course)

        return courses

    def create_publications_feed(self, org):
        """Criar feed de publicações/notícias"""
        feeds_data = [
            {
                'title': 'Bem-vindo ao Bourbon Shopping!',
                'description': 'Estamos felizes em ter você no nosso time. Aqui você encontrará todas as informações que precisa.',
                'content': '<p>Bem-vindo ao Bourbon Shopping! Somos um centro de compras com mais de 100 lojas e milhares de oportunidades. Nossa missão é oferecer a melhor experiência de compra e trabalho.</p><p>Nesta plataforma, você poderá acessar treinamentos, políticas, notícias e recursos que te ajudarão a ter sucesso em sua carreira.</p>',
            },
            {
                'title': 'Dicas de Atendimento para Aumentar Vendas',
                'description': 'Conheça as melhores práticas que nossos vendedores top utilizam',
                'content': '<p>Nossos melhores vendedores têm algo em comum: eles entendem seus clientes. Aqui estão 5 dicas que fazem diferença:</p><ul><li>Aborde com genuíno interesse</li><li>Escute mais do que fale</li><li>Personalize o atendimento</li><li>Demonstre expertise sobre produtos</li><li>Sempre tente agregar valor</li></ul>',
            },
            {
                'title': 'Campanha de Vendas Julho - Desafio de Metas',
                'description': 'Participe do desafio mensal e ganhe prêmios incríveis',
                'content': '<p>Este mês, estamos lançando um desafio especial! Os 10 melhores vendedores de cada categoria ganham prêmios em dinheiro.</p><p>Saiba mais com seu gerente de loja ou acesse a intranet para ver o regulamento completo.</p>',
            },
            {
                'title': 'Segurança e Higiene - Novos Procedimentos',
                'description': 'Atualizações importantes sobre protocolos de saúde e segurança',
                'content': '<p>Para garantir um ambiente seguro para todos, implementamos novos procedimentos. Todos os colaboradores devem seguir:</p><ul><li>Uso de máscaras em áreas de estoque</li><li>Higiene das mãos a cada 2 horas</li><li>Distanciamento mínimo de 1 metro</li><li>Relatório de qualquer problema</li></ul>',
            },
            {
                'title': 'Histórias de Sucesso - Colaborador do Mês',
                'description': 'Conheça a história de Maria Silva, atendente destaque',
                'content': '<p>Maria trabalha há 3 anos como atendente e é referência em atendimento ao cliente. Sua dedição e simpatia conquistam clientes todos os dias. Ela é um exemplo para todos nós!</p><p>Parabéns Maria, você merece!</p>',
            },
        ]

        publications = []
        for feed_data in feeds_data:
            pub, _ = Publication.objects.get_or_create(
                organization=org,
                title=feed_data['title'],
                defaults={
                    'subtitle': feed_data['description'],
                    'content': feed_data['content'],
                    'status': 'published',
                    'published_at': timezone.now(),
                }
            )
            publications.append(pub)

        return publications

    def create_wiki_publications(self, org):
        """Criar artigos wiki/referência"""
        wikis_data = [
            {
                'title': 'Como Usar o Sistema de PDV',
                'description': 'Guia completo do sistema de ponto de venda',
                'content': '<h2>Iniciando o PDV</h2><p>1. Faça login com suas credenciais<br>2. Selecione a caixa/terminal<br>3. Está pronto para começar</p><h2>Operações Básicas</h2><p>- Escanear produto: aponte o leitor de código de barras<br>- Alterar quantidade: pressione F2 e digite a quantidade<br>- Aplicar desconto: pressione F3 e selecione o motivo</p>',
            },
            {
                'title': 'Políticas de Devolução e Troca',
                'description': 'Regras para devoluções e trocas de produtos',
                'content': '<h2>Direito do Cliente</h2><p>Clientes têm direito a devolução em até 30 dias. Requisitos:</p><ul><li>Produto com embalagem original</li><li>Nota fiscal ou comprovante</li><li>Sem sinais de uso</li></ul><h2>Como Processar</h2><p>1. Verificar documento de compra<br>2. Inspecionar produto<br>3. Emitir devolução no PDV<br>4. Processar reembolso ou troca</p>',
            },
            {
                'title': 'Organograma do Bourbon Shopping',
                'description': 'Estrutura hierárquica e contatos',
                'content': '<h2>Diretoria</h2><p>Diretor Geral: João Silva - ramal 1000</p><h2>Gerência de Operações</h2><p>Gerente: Maria Santos - ramal 1001</p><h2>Gerentes por Área</h2><ul><li>Moda: Carlos (ramal 2001)</li><li>Eletrônicos: Ana (ramal 2002)</li><li>Alimentação: Roberto (ramal 2003)</li></ul>',
            },
            {
                'title': 'Guia de Benefícios',
                'description': 'Conheça todos os benefícios dos colaboradores',
                'content': '<h2>Benefícios Oferecidos</h2><ul><li>Vale refeição: R$ 400/mês</li><li>Vale transporte: 100% do valor</li><li>Convênio médico: sem custo</li><li>Convênio dentário: 50% de desconto</li><li>Desconto em compras: 20% no shopping</li><li>Auxílio creche: R$ 300/filho</li></ul>',
            },
            {
                'title': 'Processo de Promoção',
                'description': 'Como avançar na carreira no Bourbon Shopping',
                'content': '<h2>Critérios</h2><p>Promoções levam em conta:</p><ul><li>Desempenho nas metas</li><li>Avaliação de desempenho</li><li>Assiduidade e pontualidade</li><li>Conclusão de treinamentos</li><li>Feedback de clientes e colegas</li></ul><h2>Próximos Passos</h2><p>1. Converse com seu gerente<br>2. Elabore um plano de desenvolvimento<br>3. Complete os treinamentos necessários<br>4. Aguarde a próxima rodada de promoções</p>',
            },
        ]

        wikis = []
        for wiki_data in wikis_data:
            pub, _ = Publication.objects.get_or_create(
                organization=org,
                title=wiki_data['title'],
                defaults={
                    'subtitle': wiki_data['description'],
                    'content': wiki_data['content'],
                    'status': 'published',
                    'published_at': timezone.now(),
                    'is_wiki': True,  # Se o modelo suporta
                }
            )
            wikis.append(pub)

        return wikis

    def create_documents(self, org):
        """Criar documentos de referência"""
        docs_data = [
            {
                'title': 'Código de Conduta - Bourbon Shopping',
                'description': 'Documento oficial com regras e valores da empresa',
                'file_url': 'https://example.com/docs/codigo-conduta.pdf',
            },
            {
                'title': 'Regulamento de Pessoal',
                'description': 'Regulamento geral de pessoal e relacionamento trabalhista',
                'file_url': 'https://example.com/docs/regulamento-pessoal.pdf',
            },
            {
                'title': 'Manual de Operação de Loja',
                'description': 'Procedimentos e rotinas de operação diárias',
                'file_url': 'https://example.com/docs/manual-operacao.pdf',
            },
            {
                'title': 'Tabela de Salários 2026',
                'description': 'Tabela oficial de salários e benefícios',
                'file_url': 'https://example.com/docs/tabela-salarios-2026.pdf',
            },
            {
                'title': 'Política de Segurança e Higiene',
                'description': 'Normas de segurança, higiene e prevenção de acidentes',
                'file_url': 'https://example.com/docs/politica-seguranca.pdf',
            },
            {
                'title': 'Formulário de Solicitação de Férias',
                'description': 'Documento para solicitação de período de férias',
                'file_url': 'https://example.com/docs/formulario-ferias.pdf',
            },
        ]

        documents = []
        for doc_data in docs_data:
            doc, _ = Document.objects.get_or_create(
                organization=org,
                title=doc_data['title'],
                defaults={
                    'description': doc_data['description'],
                    'status': 'published',
                }
            )
            documents.append(doc)

        return documents
