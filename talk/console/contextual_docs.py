"""
Sistema de Documentação Contextual
Detecta a página atual e carrega documentação relevante baseado em contexto.
"""

# Mapeamento de rotas → documentação contextual
# Permite que cada seção do sistema mostre doc relevante

CONTEXTUAL_DOCS = {
    # ADMIN: Recrutamento
    'recruitment_candidate_list': {
        'titulo': '👥 Candidatos',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.md',
        'categoria': '03-features',
        'ancora': 'fase-2-candidatos',
        'descricao': 'Gerencie candidatos, veja scores, histórico',
    },
    'recruitment_position_list': {
        'titulo': '💼 Vagas',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.md',
        'categoria': '03-features',
        'ancora': 'fase-3-vagas',
        'descricao': 'Crie e gerencie posições abertas',
    },
    'recruitment_application_queue': {
        'titulo': '📮 Candidaturas',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.md',
        'categoria': '03-features',
        'ancora': 'fase-4-matching',
        'descricao': 'Veja e responda candidaturas em fila',
    },

    # ADMIN: Cursos
    'course_console_list': {
        'titulo': '📚 Cursos',
        'secao': 'Cursos',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.md',
        'categoria': '03-features',
        'ancora': 'fase-1-estructura',
        'descricao': 'Crie e gerencie cursos de treinamento',
    },

    # ADMIN: Configurações
    'console_dashboard': {
        'titulo': '⚙️ Dashboard',
        'secao': 'Admin',
        'arquivo': '06_OPERATIONS_TROUBLESHOOTING.md',
        'categoria': '06-operacoes',
        'ancora': 'monitoramento',
        'descricao': 'Visão geral do sistema e métricas',
    },

    # ADMIN: Setup
    'admin_dashboard': {
        'titulo': '🔧 Admin Dashboard',
        'secao': 'Admin',
        'arquivo': '01_ADMIN_SETUP_QUICK_REFERENCE.md',
        'categoria': '01-inicio-rapido',
        'ancora': 'phase-1',
        'descricao': 'Setup inicial de nova organização',
    },

    # PÚBLICO: Signup
    'recruitment_candidate_signup': {
        'titulo': '📝 Criar Perfil',
        'secao': 'Candidato',
        'arquivo': 'GUIA_RAPIDO_NAVEGACAO.md',
        'categoria': '00-indice',
        'ancora': 'candidato-novo',
        'descricao': 'Complete seu perfil em 5 minutos',
    },

    # PÚBLICO: Feed de oportunidades
    'recruitment_candidate_feed': {
        'titulo': '🎯 Oportunidades',
        'secao': 'Candidato',
        'arquivo': 'GUIA_RAPIDO_NAVEGACAO.md',
        'categoria': '00-indice',
        'ancora': 'candidato-feed',
        'descricao': 'Veja oportunidades perto de você',
    },

    # PÚBLICO: Matches
    'recruitment_candidate_matches': {
        'titulo': '💬 Matches',
        'secao': 'Candidato',
        'arquivo': 'GUIA_RAPIDO_NAVEGACAO.md',
        'categoria': '00-indice',
        'ancora': 'candidato-matches',
        'descricao': 'Converse com empregadores interessados',
    },

    # Padrões (fallback)
    'console:*': {
        'titulo': '📖 Help',
        'secao': 'Admin',
        'arquivo': 'INDEX.md',
        'categoria': '00-indice',
        'descricao': 'Índice de documentação',
    },
    'recruitment_public:*': {
        'titulo': '❓ Ajuda',
        'secao': 'Candidato',
        'arquivo': 'GUIA_RAPIDO_NAVEGACAO.md',
        'categoria': '00-indice',
        'descricao': 'Guia de uso do MatchCo',
    },
}

# Adicionar todos os documentos de DOCS_STRUCTURE como opções de navegação
OUTROS_DOCS = {
    ('02_ARCHITECTURE_MULTITENANT.md', '02-arquitetura'): {
        'titulo': '🏗️ Arquitetura Multi-Tenant',
        'secao': 'Admin',
        'categoria': '02-arquitetura',
    },
    ('03_COURSES_IMPLEMENTATION_CHECKLIST.md', '03-features'): {
        'titulo': '✅ Cursos - Checklist',
        'secao': 'Cursos',
        'categoria': '03-features',
    },
    ('04_CHANGELOG.md', '04-versioning'): {
        'titulo': '📋 Changelog',
        'secao': 'Admin',
        'categoria': '04-versioning',
    },
    ('05_ADMIN_GUIDE_BY_SECTOR.md', '05-usuarios'): {
        'titulo': '📖 Guia Admin por Setor',
        'secao': 'Admin',
        'categoria': '05-usuarios',
    },
    ('06_OPERATIONS_TROUBLESHOOTING.md', '06-operacoes'): {
        'titulo': '🛠️ Troubleshooting',
        'secao': 'Admin',
        'categoria': '06-operacoes',
    },
    ('07_INTEGRATION_PORTS.md', '07-integracao'): {
        'titulo': '📱 Integração & APIs',
        'secao': 'Admin',
        'categoria': '07-integracao',
    },
}

# Merge para criar lista completa
for (arquivo, categoria), dados in OUTROS_DOCS.items():
    key = arquivo.replace('.md', '').lower()
    CONTEXTUAL_DOCS[key] = {**dados, 'arquivo': arquivo}


def get_contextual_doc(view_name, is_admin=False):
    """
    Retorna documentação baseada na view atual.

    Args:
        view_name: nome da view Django (ex: 'recruitment_candidate_list')
        is_admin: True se usuário é admin

    Returns:
        dict com info da documentação ou None
    """

    # Procurar correspondência exata
    if view_name in CONTEXTUAL_DOCS:
        return CONTEXTUAL_DOCS[view_name]

    # Procurar correspondência com wildcard
    for pattern, doc_info in CONTEXTUAL_DOCS.items():
        if '*' in pattern:
            prefix = pattern.replace('*', '').rstrip(':')
            if view_name.startswith(prefix):
                return doc_info

    # Fallback baseado em prefixo
    if is_admin:
        return CONTEXTUAL_DOCS.get('console:*')
    else:
        return CONTEXTUAL_DOCS.get('recruitment_public:*')


def get_docs_for_section(section):
    """
    Retorna todos os documentos de uma seção.
    Útil para menu lateral.

    Args:
        section: nome da seção ('Recrutamento', 'Cursos', 'Admin', 'Candidato')

    Returns:
        list de dicts com documentação
    """
    return [
        doc for doc in CONTEXTUAL_DOCS.values()
        if doc.get('secao') == section
    ]
