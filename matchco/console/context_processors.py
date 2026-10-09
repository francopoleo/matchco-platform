"""
Context processors para injetar documentação contextual em templates.
"""

from django.urls import resolve
from .contextual_docs import get_contextual_doc, get_docs_for_section


def documentation_context(request):
    """
    Adiciona informação de documentação ao contexto de cada request.
    Detecta a página atual e fornece doc relevante.

    Uso em template:
        {{ doc.titulo }}
        {{ doc.arquivo }}
        {{ doc_sections.Recrutamento }}
    """

    try:
        # Resolver a view atual
        resolver_match = resolve(request.path)
        view_name = resolver_match.url_name or ''
    except:
        view_name = ''

    # Detectar se é admin
    is_admin = request.path.startswith('/console/')

    # Obter documentação contextual
    contextual_doc = get_contextual_doc(view_name, is_admin)

    # Obter docs por seção
    doc_sections = {
        'Recrutamento': get_docs_for_section('Recrutamento'),
        'Cursos': get_docs_for_section('Cursos'),
        'Admin': get_docs_for_section('Admin'),
        'Candidato': get_docs_for_section('Candidato'),
    }

    return {
        'doc': contextual_doc or {},
        'doc_sections': doc_sections,
        'view_name': view_name,
        'is_admin': is_admin,
    }
