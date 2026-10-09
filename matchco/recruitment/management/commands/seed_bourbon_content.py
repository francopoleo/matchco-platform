from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from courses.models import Course, Module, Text, Content
from tenants_core.models import TenantUser
from courses.models import Subject
from publishing.models import Publication
from documents.models import Document


class Command(BaseCommand):
    help = 'Seed content (courses, feeds, wikis, documents) for Bourbon Shopping'

    def add_arguments(self, parser):
        parser.add_argument('--org-id', type=int, default=None, help='TenantOrganization ID')

    def handle(self, *args, **options):
        org_id = options.get('org_id')

        self.stdout.write(f"📚 Criando conteúdo para Bourbon Shopping...\n")

        # Criar cursos de varejo
        courses = self.create_retail_courses()
        self.stdout.write(self.style.SUCCESS(f"✓ {len(courses)} cursos criados"))

        # Criar feeds/publicações
        feeds = self.create_publications_feed()
        self.stdout.write(self.style.SUCCESS(f"✓ {len(feeds)} publicações de feed criadas"))

        # Criar wikis/referências
        wikis = self.create_wiki_publications()
        self.stdout.write(self.style.SUCCESS(f"✓ {len(wikis)} artigos wiki criados"))

        # Criar documentos
        docs = self.create_documents()
        self.stdout.write(self.style.SUCCESS(f"✓ {len(docs)} documentos criados"))

        self.stdout.write(self.style.SUCCESS("\n✅ Seed de conteúdo concluído com sucesso!\n"))

    def create_retail_courses(self):
        """Criar cursos de varejo e treinamento"""
        owner = TenantUser.objects.order_by('id').first()
        if not owner:
            self.stdout.write(self.style.WARNING('Nenhum owner encontrado; cursos não foram criados.'))
            return []
        subject, _ = Subject.objects.get_or_create(title='Retail Training', slug='retail-training')
        text_type = ContentType.objects.get_for_model(Text)
        courses_data = [
            {
                'title': 'Fundamentos de Atendimento ao Cliente',
                'overview': 'Uma trilha prática para transformar cada contato em uma experiência positiva, com comunicação, empatia, solução de problemas e padrão de atendimento.',
                'modules': [
                    {'title': 'Comunicação Efetiva', 'description': 'Clareza, linguagem positiva e postura profissional.', 'content': '<h2>O primeiro contato define a experiência</h2><p>Cumprimente, mantenha contato visual e use linguagem simples. Troque respostas negativas por alternativas: em vez de “não tem”, diga “posso verificar outra opção”.</p><h3>Prática</h3><ol><li>Apresente-se e pergunte como pode ajudar.</li><li>Confirme o pedido com suas próprias palavras.</li><li>Finalize informando o próximo passo.</li></ol><p><strong>Checklist:</strong> clareza · cordialidade · agilidade · confirmação.</p>'},
                    {'title': 'Empatia e Escuta Ativa', 'description': 'Como identificar a necessidade real antes de oferecer uma solução.', 'content': '<h2>Escutar é entender antes de responder</h2><p>Faça perguntas abertas, não interrompa e observe o contexto. Repare no que a pessoa diz e no que ela precisa resolver. Acolha a emoção sem prometer o que não pode cumprir.</p><h3>Roteiro de escuta</h3><p>“Entendi que você precisa de…”. “O que seria mais importante para você?”. “Posso apresentar duas alternativas?”.</p><p><strong>Atividade:</strong> registre três perguntas abertas que você usaria em sua loja.</p>'},
                    {'title': 'Resolução de Conflitos', 'description': 'Como recuperar a confiança de um cliente insatisfeito.', 'content': '<h2>Conflito pode virar fidelização</h2><p>Mantenha a calma, agradeça o relato, descubra os fatos e ofereça uma solução dentro da política da loja. Nunca discuta ou culpe outro colega na frente do cliente.</p><h3>Método A.C.O.R.D.O.</h3><p><strong>A</strong>colher · <strong>C</strong>onhecer os fatos · <strong>O</strong>rientar opções · <strong>R</strong>esolver · <strong>D</strong>ocumentar · <strong>O</strong>bservar o retorno.</p>'},
                ]
            },
            {
                'title': 'Técnicas de Vendas para Varejo',
                'overview': 'Aprenda um processo consultivo de venda: abordagem, descoberta, demonstração de valor, fechamento e relacionamento pós-venda.',
                'modules': [
                    {'title': 'Abordagem do Cliente', 'description': 'Como iniciar uma conversa sem pressionar.', 'content': '<h2>Abordagem consultiva</h2><p>Dê espaço para o cliente explorar, depois ofereça ajuda com contexto. Use perguntas como “Você já tem algo em mente?” e “É para uso próprio ou presente?”.</p><h3>Evite</h3><ul><li>Seguir o cliente pela loja.</li><li>Falar de preço antes de entender a necessidade.</li><li>Fazer suposições sobre o orçamento.</li></ul>'},
                    {'title': 'Apresentação de Produtos', 'description': 'Conecte características a benefícios reais.', 'content': '<h2>Venda valor, não apenas características</h2><p>Uma característica descreve o produto; um benefício explica por que isso importa. Apresente no máximo três opções e demonstre o uso sempre que possível.</p><p><strong>Fórmula:</strong> “Este produto tem [característica], o que ajuda você a [benefício]”. Confirme: “Isso atende ao que você procura?”.</p>'},
                    {'title': 'Fechamento de Vendas', 'description': 'Reconheça sinais de decisão e conduza o próximo passo.', 'content': '<h2>Fechar é facilitar uma decisão</h2><p>Resuma a necessidade, confirme a escolha e apresente o próximo passo. Se houver dúvida, pergunte qual ponto falta esclarecer; não pressione.</p><h3>Exemplos</h3><p>“Entre as duas opções, qual combina mais com você?” · “Posso separar este item para finalizarmos no caixa?”</p>'},
                    {'title': 'Venda Cruzada e Upsell', 'description': 'Aumente o valor da compra com relevância.', 'content': '<h2>Oferta complementar com propósito</h2><p>Só ofereça algo que resolva uma necessidade relacionada. Explique o ganho e respeite o “não”. Registre combinações que funcionam para sua categoria.</p><p><strong>Exemplo:</strong> depois de entender o produto principal, sugira um complemento que proteja, facilite o uso ou economize tempo.</p>'},
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
            course, _ = Course.objects.get_or_create(
                title=course_data['title'],
                defaults={
                    'overview': course_data['overview'],
                    'state': 'published',
                    'owner': owner,
                    'subject': subject,
                }
            )
            course.overview = course_data['overview']
            course.state = 'published'
            course.save(update_fields=['overview', 'state'])

            for idx, module_data in enumerate(course_data.get('modules', []), 1):
                module, _ = Module.objects.get_or_create(
                    course=course,
                    title=module_data['title'],
                    defaults={
                        'description': module_data['description'],
                        'order': idx,
                    }
                )
                module.description = module_data['description']
                module.order = idx
                module.save(update_fields=['description', 'order'])

                text, _ = Text.objects.get_or_create(
                    owner=owner,
                    title=f'{course.title} · {module_data["title"]}',
                    defaults={
                        'content': module_data.get('content', f'<p><strong>{module_data["description"]}</strong></p>'),
                    }
                )
                text.title = f'{course.title} · {module_data["title"]}'
                text.content = module_data.get('content', f'<p><strong>{module_data["description"]}</strong></p>')
                text.save(update_fields=['title', 'content'])
                content, _ = Content.objects.get_or_create(
                    module=module, content_type=text_type, object_id=text.pk,
                    defaults={'order': 1},
                )
                text.content_type = content
                text.save(update_fields=['content_type'])

            courses.append(course)

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
            pub, _ = Publication.objects.get_or_create(
                title=feed_data['title'],
                defaults={
                    'subtitle': feed_data['subtitle'],
                    'content': feed_data['content'],
                    'status': 'published',
                    'published_at': timezone.now(),
                }
            )
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
            pub, _ = Publication.objects.get_or_create(
                title=wiki_data['title'],
                defaults={
                    'subtitle': wiki_data['subtitle'],
                    'content': wiki_data['content'],
                    'status': 'published',
                    'published_at': timezone.now(),
                }
            )
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
            doc, _ = Document.objects.get_or_create(
                title=doc_data['title'],
                defaults={
                    'description': doc_data['description'],
                    'status': 'published',
                }
            )
            documents.append(doc)

        return documents
