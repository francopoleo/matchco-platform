"""
Centro de Documentação do Talk - Views para servir documentos HTML integrados no console.
"""

import os
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.urls import reverse


DOCS_DIR = os.path.join(settings.BASE_DIR, 'documentation', 'html')

# Mapa de documentos por categoria
DOCS_STRUCTURE = {
    '00-indice': {
        'titulo': '📖 Índice & Navegação',
        'descricao': 'Guias rápidos e índices para encontrar tudo',
        'documentos': [
            ('README.html', 'Visão Geral da Documentação'),
            ('INDEX.html', 'Índice Completo'),
            ('GUIA_RAPIDO_NAVEGACAO.html', 'Guia Rápido de Navegação'),
        ]
    },
    '01-inicio-rapido': {
        'titulo': '📋 Início Rápido',
        'descricao': 'Cartões de referência e guias rápidos para começar',
        'documentos': [
            ('01_ADMIN_SETUP_QUICK_REFERENCE.html', 'Setup Rápido - Tenant Novo'),
            ('ADMIN_QUICK_SETUP_REFERENCE.html', 'Setup Rápido (EN)'),
        ]
    },
    '02-arquitetura': {
        'titulo': '🏗️ Arquitetura',
        'descricao': 'Design de sistema, decisões arquiteturais, multi-tenancy',
        'documentos': [
            ('02_ARCHITECTURE_MULTITENANT.html', 'Arquitetura Multi-Tenant (PT)'),
            ('MATCHCO_MULTITENANT_ARCHITECTURE.html', 'Arquitetura Multi-Tenant (EN)'),
        ]
    },
    '03-features': {
        'titulo': '📚 Features & Implementação',
        'descricao': 'Checklists de features, status de implementação',
        'documentos': [
            ('03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html', 'Recrutamento - Checklist (PT)'),
            ('03_COURSES_IMPLEMENTATION_CHECKLIST.html', 'Cursos - Checklist (PT)'),
            ('RECRUTAMENTO_ENTERPRISE_IMPLEMENTACAO.html', 'Recrutamento - Enterprise (EN)'),
            ('CURSOS_ENTERPRISE_IMPLEMENTACAO.html', 'Cursos - Enterprise (EN)'),
        ]
    },
    '04-versioning': {
        'titulo': '📦 Release & Versioning',
        'descricao': 'Guia de versioning, workflow de release, changelog',
        'documentos': [
            ('04_VERSIONING_GUIDE.html', 'Guia de Versionamento'),
            ('04_CHANGELOG.html', 'Changelog'),
        ]
    },
    '05-usuarios': {
        'titulo': '👥 Guias de Usuário',
        'descricao': 'Documentação por setor, guias de administração',
        'documentos': [
            ('05_ADMIN_GUIDE_BY_SECTOR.html', 'Guia Admin por Setor'),
        ]
    },
    '06-operacoes': {
        'titulo': '🛠️ Operações & DevOps',
        'descricao': 'Troubleshooting, diagnóstico, checklist operacional',
        'documentos': [
            ('06_OPERATIONS_TROUBLESHOOTING.html', 'Troubleshooting & Operações'),
        ]
    },
    '07-integracao': {
        'titulo': '📱 Integração & APIs',
        'descricao': 'Arquitetura de ports, contratos de integração',
        'documentos': [
            ('07_INTEGRATION_PORTS.html', 'Ports & Integração'),
        ]
    },
}


def get_doc_path(filename):
    """Retorna caminho seguro para arquivo de documento."""
    return os.path.join(DOCS_DIR, filename)


def read_html_file(filename):
    """Lê arquivo HTML profissional e extrai conteúdo."""
    path = get_doc_path(filename)

    # Segurança: não permitir path traversal
    if not os.path.abspath(path).startswith(os.path.abspath(DOCS_DIR)):
        return None

    if not os.path.exists(path):
        return None

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extrair conteúdo da div.content (novo template profissional)
    match = re.search(r'<div class="content">(.*?)</div>\s*<div class="footer">', content, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback para conteúdo antigo
    match = re.search(r'<div class="container">(.*?)</div>\s*</body>', content, re.DOTALL)
    if match:
        return match.group(1).strip()

    return content


class DocumentacaoIndexView(LoginRequiredMixin, TemplateView):
    """Página inicial/índice de documentação."""
    template_name = 'console/documentation/index.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Ler arquivo INDEX.html se existir
        index_html = read_html_file('INDEX.html')

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

    def dispatch(self, request, *args, **kwargs):
        """Redirecionar URLs antigas com .html ou .md"""
        slug = kwargs.get('slug', '')
        if slug and (slug.endswith('.html') or slug.endswith('.md')):
            clean_slug = slug.replace('.html', '').replace('.md', '')
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
            fname_slug = fname.replace('.html', '').lower()
            if fname_slug == normalized_slug:
                filename = fname
                titulo = ftitulo
                break

        if not filename:
            context['error'] = 'Documento não encontrado'
            return context

        # Ler documento HTML
        html_content = read_html_file(filename)

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
