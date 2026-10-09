"""
Centro de Documentação do MatchCo - Views para servir documentos HTML integrados no console.
"""

import os
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.urls import reverse


DOCS_DIR = os.path.join(settings.BASE_DIR, 'docs', 'help', 'html')
EMOJI_RE = re.compile(
    r'[\U0001F1E6-\U0001F1FF\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F]+',
)


def clean_document_html(html_content):
    """Remove emojis dos documentos para manter a linguagem visual do Console."""
    return EMOJI_RE.sub('', html_content or '').replace('  ', ' ')

# Mapa de documentos por categoria
DOCS_STRUCTURE = {
    '00-indice': {
        'titulo': 'Índice e navegação', 'icone': 'wiki',
        'descricao': 'Guias rápidos e índices para encontrar tudo',
        'documentos': [
            ('README.html', 'Visão Geral da Documentação'),
            ('INDEX.html', 'Índice Completo'),
            ('00_MATCHCO_GUIDE_FLOWS.html', 'Como funciona: fluxos e exemplos'),
            ('00_MATCHCO_CORE_STAKEHOLDER_FLOWS.html', 'Fluxos centrais: candidato e loja'),
            ('00_MATCHCO_ORGANIZATIONS_CHANNELS_AND_AUDIENCES.html', 'Organizações, canais e audiências'),
            ('00_MATCHCO_PRODUCT_AND_MARKET_MODEL.html', 'Modelo de Produto e Mercados'),
            ('00_MATCHCO_CANONICAL_URLS.html', 'Matriz de URLs Canônicas'),
            ('GUIA_RAPIDO_NAVEGACAO.html', 'Guia Rápido de Navegação'),
            ('DOCUMENTACAO_CONTEXTUAL.html', 'Documentação Contextual do Help'),
        ]
    },
    '01-inicio-rapido': {
        'titulo': 'Início rápido', 'icone': 'course',
        'descricao': 'Cartões de referência e guias rápidos para começar',
        'documentos': [
            ('01_MATCHCO_ORGANIZATION_AND_RECRUITMENT_PLAYBOOK.html', 'Setup de Organização e Recrutamento'),
            ('01_ADMIN_SETUP_QUICK_REFERENCE.html', 'Setup Rápido - Tenant Novo'),
        ]
    },
    '02-arquitetura': {
        'titulo': 'Produto e arquitetura', 'icone': 'console',
        'descricao': 'Modelo MatchCo, tenants, organizações e decisões estruturais',
        'documentos': [
            ('02_ARCHITECTURE_MULTITENANT.html', 'Arquitetura Multi-Tenant'),
        ]
    },
    '03-recrutamento': {
        'titulo': 'Recrutamento', 'icone': 'profile',
        'descricao': 'Entrada, Perfil Match, necessidades e relações de interesse',
        'documentos': [
            ('03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html', 'Recrutamento - Checklist'),
            ('03_RECRUITMENT_COMMERCIAL_VALIDATION.html', 'QR, intenção e leitura sem ranking'),
            ('03_RECRUITMENT_BOURBON_JOURNEYS.html', 'Jornada prática e catálogo de funções · Bourbon'),
            ('03_RECRUITMENT_PHARMACY_JOURNEYS.html', 'Jornada de farmácias e campanhas de enriquecimento'),
            ('03_RECRUITMENT_PRIVACY_LGPD.html', 'Plano de proteção, LGPD e segurança SaaS'),
            ('03_RECRUITMENT_QUESTIONNAIRE_TEMPLATES.html', 'Questionários por contexto'),
            ('03_RECRUITMENT_DEMO_DATA.html', 'Dados demo por mercado'),
        ]
    },
    '04-cursos-conteudo': {
        'titulo': 'Cursos e conteúdo', 'icone': 'feed',
        'descricao': 'Cursos, publicações, trilhas e conteúdos por audiência',
        'documentos': [
            ('03_COURSES_IMPLEMENTATION_CHECKLIST.html', 'Cursos - Checklist'),
        ]
    },
    '05-operacao': {
        'titulo': 'Usuários e operação', 'icone': 'profile',
        'descricao': 'Perfis, gestão diária e diagnóstico',
        'documentos': [
            ('05_ADMIN_GUIDE_BY_SECTOR.html', 'Guia Admin por Setor'),
            ('06_OPERATIONS_TROUBLESHOOTING.html', 'Troubleshooting e diagnóstico'),
        ]
    },
    '06-integracoes': {
        'titulo': 'Integrações e APIs', 'icone': 'search',
        'descricao': 'Contratos, ports, adapters e serviços externos',
        'documentos': [
            ('07_INTEGRATION_PORTS.html', 'Integrações e governança'),
        ]
    },
    '07-release': {
        'titulo': 'Release e versionamento', 'icone': 'policy',
        'descricao': 'Mudanças, versões e critérios de publicação',
        'documentos': [
            ('04_VERSIONING_GUIDE.html', 'Guia de Versionamento'),
            ('04_CHANGELOG.html', 'Changelog'),
        ]
    },
}


def get_doc_path(filename):
    """Retorna caminho seguro para arquivo de documento."""
    return os.path.join(DOCS_DIR, filename)


def read_html_file(filename):
    """Lê o arquivo HTML publicado e extrai apenas seu conteúdo.

    Os arquivos Markdown são fontes de edição, mas não devem substituir a
    apresentação HTML das páginas de documentação.
    """
    path = get_doc_path(filename)

    # Segurança: não permitir path traversal
    if not os.path.abspath(path).startswith(os.path.abspath(DOCS_DIR)):
        return None

    if not os.path.exists(path):
        return None

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extrair somente o conteúdo publicado, sem duplicar o layout HTML externo.
    match = re.search(r'<(?:div|article) class="content">(.*?)</(?:div|article)>\s*<(?:div|footer) class="footer">', content, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Documentos mais recentes usam <main> como área de conteúdo. Não
    # devemos inserir o documento inteiro no Console, pois isso também
    # carregaria os estilos do arquivo standalone e deixaria o
    # prefers-color-scheme do navegador sobrescrever o tema do Console.
    match = re.search(r'<main(?:\s[^>]*)?>(.*?)</main>', content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Fallback para conteúdo antigo
    match = re.search(r'<div class="container">(.*?)</div>\s*</body>', content, re.DOTALL)
    if match:
        return match.group(1).strip()

    return clean_document_html(content)


def rewrite_document_links(html_content):
    """Converte links relativos dos documentos para rotas HTML do Console."""
    if not html_content:
        return html_content

    known = {}
    for category, data in DOCS_STRUCTURE.items():
        for filename, _title in data['documentos']:
            known[filename.rsplit('.', 1)[0].lower()] = reverse(
                'console:documentation-detail',
                kwargs={'categoria': category, 'slug': filename.rsplit('.', 1)[0].lower()},
            )

    def replace(match):
        target = match.group(1)
        stem = os.path.basename(target.rsplit('#', 1)[0]).rsplit('.', 1)[0].lower()
        url = known.get(stem) or reverse('console:documentation-index')
        fragment = f'#{target.rsplit("#", 1)[1]}' if '#' in target else ''
        return f'href="{url}{fragment}"'

    return re.sub(r'href=["\']([^"\']+?\.(?:md|html)(?:#[^"\']*)?)["\']', replace, html_content, flags=re.I)


class DocumentacaoIndexView(LoginRequiredMixin, TemplateView):
    """Página inicial/índice de documentação."""
    template_name = 'console/documentation/index.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Ler arquivo INDEX.html se existir
        index_html = rewrite_document_links(read_html_file('INDEX.html'))

        context.update({
            'titulo': 'Central de Documentação',
            'descricao': 'Documentação completa do MatchCo/MatchCo',
            'index_html': index_html,
            'categorias': [
                {
                    'slug': slug,
                    'titulo': dados['titulo'],
                    'icone': dados.get('icone', 'wiki'),
                    'descricao': dados['descricao'],
                    'url': reverse('console:documentation-category', kwargs={'categoria': slug}),
                    'num_docs': len(dados['documentos']),
                }
                for slug, dados in DOCS_STRUCTURE.items()
            ],
        })

        return context


class DocumentacaoCategoryView(LoginRequiredMixin, TemplateView):
    """Página de categoria de documentação."""
    template_name = 'console/documentation/category.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categoria = kwargs.get('categoria')

        if categoria not in DOCS_STRUCTURE:
            context['error'] = 'Categoria não encontrada'
            return context

        cat_data = DOCS_STRUCTURE[categoria]

        context.update({
            'categoria': categoria,
            'titulo': cat_data['titulo'],
            'descricao': cat_data['descricao'],
            'documentos': [
                {
                    'filename': filename,
                    'titulo': titulo,
                    'url': reverse('console:documentation-detail', kwargs={
                        'categoria': categoria,
                        'slug': filename.rsplit('.', 1)[0].lower()
                    }),
                }
                for filename, titulo in cat_data['documentos']
            ],
            'categorias': [
                {
                    'slug': slug,
                    'titulo': dados['titulo'],
                    'icone': dados.get('icone', 'wiki'),
                    'url': reverse('console:documentation-category', kwargs={'categoria': slug}),
                    'active': slug == categoria,
                }
                for slug, dados in DOCS_STRUCTURE.items()
            ],
        })

        return context


class DocumentacaoDetailView(LoginRequiredMixin, TemplateView):
    """Página de detalhe de um documento."""
    template_name = 'console/documentation/detail.html'
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        """Normalizar URLs antigas que ainda contenham a extensão HTML."""
        slug = kwargs.get('slug', '')
        if slug and slug.endswith('.html'):
            clean_slug = slug.rsplit('.', 1)[0] if '.' in slug else slug
            return redirect('console:documentation-detail', categoria=kwargs.get('categoria'), slug=clean_slug)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categoria = kwargs.get('categoria')
        slug = kwargs.get('slug')

        if categoria not in DOCS_STRUCTURE:
            context['error'] = 'Categoria não encontrada'
            return context

        cat_data = DOCS_STRUCTURE[categoria]

        # Encontrar documento (normalizar slug para match com underscores)
        filename = None
        titulo = None
        normalized_slug = slug.replace('-', '_')  # Converter hífens em underscores
        for fname, ftitulo in cat_data['documentos']:
            fname_slug = fname.rsplit('.', 1)[0].lower()
            if fname_slug == normalized_slug:
                filename = fname
                titulo = ftitulo
                break

        if not filename:
            context['error'] = 'Documento não encontrado'
            return context

        # Ler documento HTML
        html_content = rewrite_document_links(read_html_file(filename))

        if html_content is None:
            context['error'] = 'Erro ao ler documento'
            return context

        context.update({
            'categoria': categoria,
            'slug': slug,
            'titulo': titulo,
            'categoria_titulo': cat_data['titulo'],
            'conteudo_html': html_content,
            'categorias': [
                {
                    'slug': cat_slug,
                    'titulo': cat_dados['titulo'],
                    'icone': cat_dados.get('icone', 'wiki'),
                    'url': reverse('console:documentation-category', kwargs={'categoria': cat_slug}),
                    'active': cat_slug == categoria,
                }
                for cat_slug, cat_dados in DOCS_STRUCTURE.items()
            ],
            'documentos_na_categoria': [
                {
                    'filename': fname,
                    'titulo': ftitulo,
                    'url': reverse('console:documentation-detail', kwargs={
                        'categoria': categoria,
                        'slug': fname.rsplit('.', 1)[0].lower()
                    }),
                    'active': fname == filename,
                }
                for fname, ftitulo in cat_data['documentos']
            ],
        })

        return context
