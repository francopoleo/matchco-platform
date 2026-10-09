"""
Sistema de Documentação Contextual
Detecta a página atual e carrega documentação relevante baseado em contexto.
"""

# Mapeamento de rotas → documentação contextual
# Permite que cada seção do sistema mostre doc relevante

CONTEXTUAL_DOCS = {
    'user_profile_detail': {
        'titulo': 'Preferências de idioma',
        'secao': 'Conta',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'idiomas-e-localizacao',
        'descricao': 'Escolha o idioma da interface. Conteúdos publicados por empresas não são traduzidos automaticamente.',
    },
    # ADMIN: Recrutamento
    'recruitment_employer_declare_need': {
        'titulo': 'Declarar necessidade e abrir rodadas',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'fase-5-catalogo-canonico',
        'descricao': 'Escolha cargo local com vínculo canônico e perfil operacional; preencha Onde, O quê, Quando e distribuição',
    },
    # ADMIN: Cursos
    'course_console_list': {
        'titulo': 'Cursos',
        'secao': 'Cursos',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'navegacao-de-registros',
        'descricao': 'Crie e gerencie cursos no escopo da organização ou empresa ativa; ao editar, use breadcrumb e navegação da lista filtrada',
    },
    'course-list': {
        'titulo': 'Cursos',
        'secao': 'Conteúdo',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'autonomia-por-empresa',
        'descricao': 'Filtre cursos pela empresa responsável; conteúdo organizacional continua compartilhado conforme a audiência',
    },
    'publication-list': {
        'titulo': 'Feed e Wiki',
        'secao': 'Conteúdo',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'autonomia-de-conteudo-por-empresa',
        'descricao': 'Escolha a empresa responsável e defina a audiência; empresa proprietária e público autorizado são controles complementares',
    },
    'course_editor_list': {
        'titulo': 'Editor de módulos',
        'secao': 'Cursos',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'navegacao-de-registros',
        'descricao': 'Organize módulos e conteúdos; o editor identifica o curso atual e permite navegar entre cursos',
    },
    'course_editor_detail': {
        'titulo': 'Editor de módulos',
        'secao': 'Cursos',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'navegacao-de-registros',
        'descricao': 'Edite a estrutura do curso com contexto, breadcrumb compacto e navegação entre registros',
    },
    'certification_list': {
        'titulo': 'Certificações',
        'secao': 'Cursos',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'certificacoes-governadas',
        'descricao': 'Defina processos rígidos de competência com requisitos, nota mínima, tentativas, validade e evidências',
    },

    # ADMIN: Configurações
    'console_dashboard': {
        'titulo': 'Dashboard',
        'secao': 'Admin',
        'arquivo': '06_OPERATIONS_TROUBLESHOOTING.html',
        'categoria': '05-operacao',
        'ancora': 'monitoramento',
        'descricao': 'Visão geral do sistema e métricas',
    },
    'user-list': {
        'titulo': 'Usuários e acessos',
        'secao': 'Admin',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'usuarios-e-acessos',
        'descricao': 'Consulte organizações, empresas, papéis e escopos de acesso',
    },
    'user-edit': {
        'titulo': 'Perfil e permissões',
        'secao': 'Admin',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'perfil-e-permissoes',
        'descricao': 'Edite o perfil e todas as associações de uma pessoa',
    },
    'document-list': {
        'titulo': 'Documentos e links reutilizáveis',
        'secao': 'Conteúdo',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'autonomia-de-conteudo-por-empresa',
        'descricao': 'Gerencie documentos da empresa selecionada ou compartilhados pela organização; o seletor também limita a lista e as ações',
    },
    'compliance-dashboard': {
        'titulo': 'Proteção, LGPD e incidentes',
        'secao': 'Segurança',
        'arquivo': '03_RECRUITMENT_PRIVACY_LGPD.html',
        'categoria': '03-recrutamento',
        'ancora': 'roadmap',
        'descricao': 'Controles de autenticação, anti-abuso, isolamento, retenção e resposta a incidentes',
    },
    'publication-edit': {
        'titulo': 'Editar Feed ou Wiki',
        'secao': 'Conteúdo',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'biblioteca-de-conteudo',
        'descricao': 'Organize conteúdo, empresa responsável, audiência e documentos relacionados; usuários veem apenas conteúdo autorizado',
    },
    'media-list': {
        'titulo': 'Biblioteca de mídia',
        'secao': 'Conteúdo',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'autonomia-de-conteudo-por-empresa',
        'descricao': 'Filtre a biblioteca por empresa; arquivos da organização podem ser compartilhados, enquanto conteúdo empresarial permanece isolado',
    },
    'content-audit': {
        'titulo': 'Auditoria de conteúdo',
        'secao': 'Conteúdo',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'biblioteca-de-conteudo',
        'descricao': 'Acompanhe alterações, versões, vínculos e responsáveis',
    },
    'media-metrics': {
        'titulo': 'Métricas da biblioteca',
        'secao': 'Conteúdo',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'biblioteca-de-conteudo',
        'descricao': 'Entenda uso, armazenamento, vencimentos e dependências',
    },

    # ADMIN: Setup
    'admin_dashboard': {
        'titulo': 'Organizações e estrutura',
        'secao': 'Admin',
        'arquivo': '00_MATCHCO_ORGANIZATIONS_CHANNELS_AND_AUDIENCES.html',
        'categoria': '00-indice',
        'ancora': 'painel-administracao-organizacao',
        'descricao': 'Consulte a organização, empresas, unidades, áreas, vínculos, QRs e audiências sem misturar tenants; veja também o plano SaaS em fases',
    },
    'organization_architecture': {
        'titulo': 'Plano SaaS e serviços modulares',
        'secao': 'Admin',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'plano-implementacao-incremental',
        'descricao': 'Entenda como a estrutura atual sustenta Conteúdo, Talk, Aprendizagem, Match, Parceiros e Operação com isolamento por organização',
    },
    'ops_ledger': {
        'titulo': 'Ledger de auditoria operacional',
        'secao': 'Admin',
        'arquivo': '03_RECRUITMENT_PRIVACY_LGPD.html',
        'categoria': '03-recrutamento',
        'ancora': 'auditoria-atual',
        'descricao': 'Consulte eventos append-only de segurança, autoridade, QR, oportunidade e relacionamento',
    },

    # PÚBLICO: Signup
    'recruitment_candidate_signup': {
        'titulo': 'Criar Perfil',
        'secao': 'Candidato',
        'arquivo': '00_MATCHCO_CORE_STAKEHOLDER_FLOWS.html',
        'categoria': '00-indice',
        'ancora': 'template-padrao-sem-cv',
        'descricao': 'Veja o formulário externo, OTP e reutilização do perfil',
    },

    # PÚBLICO: Feed de oportunidades
    'recruitment_candidate_feed': {
        'titulo': 'Oportunidades',
        'secao': 'Candidato',
        'arquivo': 'GUIA_RAPIDO_NAVEGACAO.html',
        'categoria': '00-indice',
        'ancora': 'candidato-feed',
        'descricao': 'Veja oportunidades perto de você',
    },

    # PÚBLICO: Matches
    'recruitment_candidate_matches': {
        'titulo': 'Matches',
        'secao': 'Candidato',
        'arquivo': 'GUIA_RAPIDO_NAVEGACAO.html',
        'categoria': '00-indice',
        'ancora': 'candidato-matches',
        'descricao': 'Converse com empregadores interessados',
    },
    'recruitment_public:lojista_declarar': {
        'titulo': 'Criar necessidade e rodadas automáticas',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'fase-5-catalogo-canonico',
        'descricao': 'Escolha cargo local com vínculo canônico; a necessidade congela os termos e usa o mesmo gate do Perfil do candidato',
    },
    'recruitment:store_function_catalog': {
        'titulo': 'Cargo estrutural e vínculo canônico',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'fase-2-catalogo-canonico',
        'descricao': 'Configure o cargo em três abas: cargo e funções canônicas, descrição e requisitos, e remuneração e contratação. A necessidade congela os termos e usa o mesmo gate do Perfil do candidato.',
    },
    'console:job_function_list': {
        'titulo': 'Cargos da estrutura e catálogo Match',
        'secao': 'Serviços',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'distincao-de-cadastro',
        'descricao': 'Cadastre aqui o cargo oficial da empresa. O de-para com funções canônicas e os campos da operação são configurados por unidade em Configurar Match.',
    },
    'console:business_unit_list': {
        'titulo': 'Unidades e lojas',
        'secao': 'Organização e estrutura',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'cadastro-canonico-unidade',
        'descricao': 'Consulte e mantenha lojas de rua, lojas em shopping, quiosques, serviços, centros de distribuição e outras unidades com endereço, CEP, contatos e contexto físico.',
    },
    'console:business_unit_create': {
        'titulo': 'Cadastrar unidade ou loja',
        'secao': 'Organização e estrutura',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'cadastro-canonico-unidade',
        'descricao': 'Cadastre identidade, tipo de unidade, localização, endereço, contatos, dados fiscais e horário.',
    },
    'console:business_unit_update': {
        'titulo': 'Editar unidade ou loja',
        'secao': 'Organização e estrutura',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'cadastro-canonico-unidade',
        'descricao': 'Atualize o cadastro da unidade sem criar uma segunda representação para o mesmo local físico.',
    },
    'console:organization_services': {
        'titulo': 'Serviços da organização',
        'secao': 'Organização e estrutura',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'servicos-modulares',
        'descricao': 'Defina o padrão de serviços da organização e, quando necessário, crie uma exceção por empresa. A empresa herda o padrão até receber uma configuração própria.',
    },
    'recruitment_public:lojista_contexto': {
        'titulo': 'Trocar organização e proteger o contexto',
        'secao': 'Recrutamento',
        'arquivo': '00_MATCHCO_CANONICAL_URLS.html',
        'categoria': '00-indice',
        'descricao': 'Escolha explicitamente a empresa; a unidade e a porta de entrada anteriores são limpas',
    },
    'recruitment_public:lojista_relation': {
        'titulo': 'Por que este match aconteceu',
        'secao': 'Recrutamento',
        'arquivo': '00_MATCHCO_CORE_STAKEHOLDER_FLOWS.html',
        'categoria': '00-indice',
        'ancora': 'algoritmo',
        'descricao': 'Veja funções canônicas, disponibilidade, início, território e proximidade aproximada sem ranking',
    },
    'recruitment:employer_relation_detail': {
        'titulo': 'Detalhe administrativo do match',
        'secao': 'Recrutamento',
        'arquivo': '00_MATCHCO_CORE_STAKEHOLDER_FLOWS.html',
        'categoria': '00-indice',
        'ancora': 'algoritmo',
        'descricao': 'Consulte critérios do match e, somente para administração, os CEPs de referência do candidato e da unidade',
    },
    'recruitment_public:candidate_enrichment_campaign': {
        'titulo': 'Atualização opcional de perfil',
        'secao': 'Candidato',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'fase-6-cobertura-e-campanhas',
        'descricao': 'Responda perguntas opcionais de uma campanha sem alterar seu Perfil silenciosamente',
    },
    'recruitment_public:candidate_survey': {
        'titulo': 'Pré-onboarding contextual',
        'secao': 'Candidato',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'fase-7-pre-onboarding-contextual',
        'descricao': 'Entenda atribuições, evidências e acesso aprovado sem ranking',
    },

    # Padrões (fallback)
    'console:*': {
        'titulo': 'Documentação',
        'secao': 'Admin',
        'arquivo': 'INDEX.html',
        'categoria': '00-indice',
        'descricao': 'Índice de documentação',
    },
    'recruitment_public:*': {
        'titulo': 'Ajuda',
        'secao': 'Candidato',
        'arquivo': '00_MATCHCO_CORE_STAKEHOLDER_FLOWS.html',
        'categoria': '00-indice',
        'ancora': 'template-padrao-sem-cv',
        'descricao': 'Fluxo do candidato, formulário sem CV e OTP',
    },
}

# Adicionar todos os documentos de DOCS_STRUCTURE como opções de navegação
OUTROS_DOCS = {
    ('00_MATCHCO_PRODUCT_AND_MARKET_MODEL.html', '00-indice'): {
        'titulo': 'Modelo de Produto e Mercados',
        'secao': 'Admin',
        'categoria': '00-indice',
    },
    ('00_MATCHCO_CANONICAL_URLS.html', '00-indice'): {
        'titulo': 'Matriz de URLs Canônicas',
        'secao': 'Admin',
        'categoria': '00-indice',
    },
    ('01_MATCHCO_ORGANIZATION_AND_RECRUITMENT_PLAYBOOK.html', '01-inicio-rapido'): {
        'titulo': 'Setup de Organização e Recrutamento',
        'secao': 'Admin',
        'categoria': '01-inicio-rapido',
    },
    ('02_ARCHITECTURE_MULTITENANT.html', '02-arquitetura'): {
        'titulo': 'Arquitetura Multi-Tenant',
        'secao': 'Admin',
        'categoria': '02-arquitetura',
    },
    ('03_COURSES_IMPLEMENTATION_CHECKLIST.html', '04-cursos-conteudo'): {
        'titulo': 'Cursos - Checklist',
        'secao': 'Cursos',
        'categoria': '04-cursos-conteudo',
    },
    ('04_CHANGELOG.html', '07-release'): {
        'titulo': 'Changelog',
        'secao': 'Admin',
        'categoria': '07-release',
    },
    ('05_ADMIN_GUIDE_BY_SECTOR.html', '05-operacao'): {
        'titulo': 'Guia Admin por Setor',
        'secao': 'Admin',
        'categoria': '05-operacao',
    },
    ('06_OPERATIONS_TROUBLESHOOTING.html', '05-operacao'): {
        'titulo': 'Troubleshooting',
        'secao': 'Admin',
        'categoria': '05-operacao',
    },
    ('07_INTEGRATION_PORTS.html', '06-integracoes'): {
        'titulo': 'Integração & APIs',
        'secao': 'Admin',
        'categoria': '06-integracoes',
    },
}

# Merge para criar lista completa
for (arquivo, categoria), dados in OUTROS_DOCS.items():
    key = arquivo.replace('.html', '').lower()
    CONTEXTUAL_DOCS[key] = {**dados, 'arquivo': arquivo}


def get_contextual_doc(view_name, is_admin=False):
    """
    Retorna documentação baseada na view atual.

    Args:
        view_name: nome da view Django (ex: 'recruitment_position_list')
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
