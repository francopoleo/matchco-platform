"""
Centro de Documentação do Talk - Views para servir documentos .md integrados no console.
"""

import os
import markdown
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.urls import reverse


DOCS_DIR = os.path.join(settings.BASE_DIR, '..', 'docs')

# Mapa de documentos por categoria
DOCS_STRUCTURE = {
    '00-indice': {
        'titulo': '📖 Índice & Navegação',
        'descricao': 'Guias rápidos e índices para encontrar tudo',
        'documentos': [
            ('README.md', 'Visão Geral da Documentação'),
            ('INDEX.md', 'Índice Completo'),
            ('GUIA_RAPIDO_NAVEGACAO.md', 'Guia Rápido de Navegação'),
        ]
    },
    '01-inicio-rapido': {
        'titulo': '📋 Início Rápido',
        'descricao': 'Cartões de referência e guias rápidos para começar',
        'documentos': [
            ('01_ADMIN_SETUP_QUICK_REFERENCE.md', 'Setup Rápido - Tenant Novo'),
            ('ADMIN_QUICK_SETUP_REFERENCE.md', 'Setup Rápido (EN)'),
        ]
    },
    '02-arquitetura': {
        'titulo': '🏗️ Arquitetura',
        'descricao': 'Design de sistema, decisões arquiteturais, multi-tenancy',
        'documentos': [
            ('02_ARCHITECTURE_MULTITENANT.md', 'Arquitetura Multi-Tenant (PT)'),
            ('MATCHCO_MULTITENANT_ARCHITECTURE.md', 'Arquitetura Multi-Tenant (EN)'),
        ]
    },
    '03-features': {
        'titulo': '📚 Features & Implementação',
        'descricao': 'Checklists de features, status de implementação',
        'documentos': [
            ('03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.md', 'Recrutamento - Checklist (PT)'),
            ('03_COURSES_IMPLEMENTATION_CHECKLIST.md', 'Cursos - Checklist (PT)'),
            ('RECRUTAMENTO_ENTERPRISE_IMPLEMENTACAO.md', 'Recrutamento - Enterprise (EN)'),
            ('CURSOS_ENTERPRISE_IMPLEMENTACAO.md', 'Cursos - Enterprise (EN)'),
        ]
    },
    '04-versioning': {
        'titulo': '📦 Release & Versioning',
        'descricao': 'Guia de versioning, workflow de release, changelog',
        'documentos': [
            ('04_VERSIONING_GUIDE.md', 'Guia de Versionamento'),
            ('04_CHANGELOG.md', 'Changelog'),
        ]
    },
    '05-usuarios': {
        'titulo': '👥 Guias de Usuário',
        'descricao': 'Documentação por setor, guias de administração',
        'documentos': [
            ('05_ADMIN_GUIDE_BY_SECTOR.md', 'Guia Admin por Setor'),
        ]
    },
    '06-operacoes': {
        'titulo': '🛠️ Operações & DevOps',
        'descricao': 'Troubleshooting, diagnóstico, checklist operacional',
        'documentos': [
            ('06_OPERATIONS_TROUBLESHOOTING.md', 'Troubleshooting & Operações'),
        ]
    },
    '07-integracao': {
        'titulo': '📱 Integração & APIs',
        'descricao': 'Arquitetura de ports, contratos de integração',
        'documentos': [
            ('07_INTEGRATION_PORTS.md', 'Ports & Integração'),
        ]
    },
}


def get_doc_path(filename):
    """Retorna caminho seguro para arquivo de documento."""
    return os.path.join(DOCS_DIR, filename)


def read_markdown_file(filename):
    """Lê e converte arquivo markdown para HTML."""
    path = get_doc_path(filename)

    # Segurança: não permitir path traversal
    if not os.path.abspath(path).startswith(os.path.abspath(DOCS_DIR)):
        return None, None

    if not os.path.exists(path):
        return None, None

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Converter markdown para HTML com extensões
    html = markdown.markdown(
        content,
        extensions=[
            'markdown.extensions.tables',
            'markdown.extensions.toc',
            'markdown.extensions.codehilite',
            'markdown.extensions.fenced_code',
        ]
    )

    return html, content


class DocumentacaoIndexView(LoginRequiredMixin, TemplateView):
    """Página inicial/índice de documentação."""
    template_name = 'console/documentation/index.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Ler arquivo INDEX.md se existir
        index_html, index_raw = read_markdown_file('INDEX.md')

        context.update({
            'titulo': 'Central de Documentação',
            'descricao': 'Documentação completa do Talk/MatchCo',
            'index_html': index_html,
            'categorias': [
                {
                    'slug': slug,
                    'titulo': dados['titulo'],
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
                        'slug': filename.replace('.md', '').lower()
                    }),
                }
                for filename, titulo in cat_data['documentos']
            ],
            'categorias': [
                {
                    'slug': slug,
                    'titulo': dados['titulo'],
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
            fname_slug = fname.replace('.md', '').lower()
            if fname_slug == normalized_slug:
                filename = fname
                titulo = ftitulo
                break

        if not filename:
            context['error'] = 'Documento não encontrado'
            return context

        # Ler e renderizar documento
        html, raw = read_markdown_file(filename)

        if html is None:
            context['error'] = 'Erro ao ler documento'
            return context

        context.update({
            'categoria': categoria,
            'slug': slug,
            'titulo': titulo,
            'categoria_titulo': cat_data['titulo'],
            'conteudo_html': html,
            'conteudo_raw': raw,
            'categorias': [
                {
                    'slug': cat_slug,
                    'titulo': cat_dados['titulo'],
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
                        'slug': fname.replace('.md', '').lower()
                    }),
                    'active': fname == filename,
                }
                for fname, ftitulo in cat_data['documentos']
            ],
        })

        return context
