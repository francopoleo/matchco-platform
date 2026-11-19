"""
Sistema de Documentação Contextual
Detecta a página atual e carrega documentação relevante baseado em contexto.
"""

from django.utils.translation import gettext_lazy as _

# Mapeamento de rotas → documentação contextual
# Permite que cada seção do sistema mostre doc relevante

CONTEXTUAL_DOCS = {
    'profile': {
        'titulo': 'Meu perfil pessoal',
        'secao': 'Conta',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'perfil-pessoal-canonico',
        'descricao': 'Consulte e edite somente seus dados pessoais permitidos. Organização, empresa, Memberships e permissões são administrados no Console por gestores autorizados.',
    },
    'console:demo-reset': {
        'titulo': 'Resetar ambiente de demonstração',
        'secao': 'Operação técnica',
        'arquivo': '03_RECRUITMENT_DEMO_DATA.html',
        'categoria': '03-recrutamento',
        'ancora': 'reset-seguro',
        'descricao': 'Apaga dados de todos os tenants não públicos e recria os três cenários demo; use apenas no banco local de desenvolvimento.',
    },
    'console:matchco-demo-seed': {
        'titulo': 'Atualizar dados de demonstração',
        'secao': 'Operação técnica',
        'arquivo': '03_RECRUITMENT_DEMO_DATA.html',
        'categoria': '03-recrutamento',
        'ancora': 'seeds-separados',
        'descricao': 'Atualize Recrutamento ou Conteúdo separadamente para Bourbon, Drogasil e ElectraTech; o reset completo fica em uma ação protegida distinta.',
    },
    'console:demo-visits': {
        'titulo': 'Visitas da demonstração',
        'secao': 'Operação técnica',
        'arquivo': '03_RECRUITMENT_DEMO_DATA.html',
        'categoria': '03-recrutamento',
        'ancora': 'seeds-separados',
        'descricao': 'Acompanhe visitas à demonstração, atividade e páginas consultadas.',
    },
    'user_profile_detail': {
        'titulo': 'Perfil legado',
        'secao': 'Conta',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'perfil-pessoal-canonico',
        'descricao': 'Rota mantida apenas para compatibilidade com links antigos. O perfil pessoal atual é /app/profile/; a edição administrativa fica em /console/users/<id>/edit/.',
    },
    'user_profile_settings_menu': {
        'titulo': 'Configurações da conta',
        'secao': 'Conta',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'perfil-pessoal-canonico',
        'descricao': 'Rota de compatibilidade. Use /app/settings/ para as configurações da conta e preferências pessoais.',
    },
    'select-organization': {
        'titulo': 'Trocar organização ativa',
        'secao': 'Organização e estrutura',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'troca-de-organizacao',
        'descricao': 'A troca sincroniza a organização ativa do Console e limpa empresa, unidade, audiência e porta anteriores; também remove da URL um filtro de empresa que pertencia à organização anterior. Se a página atual exigir um serviço que o novo tenant não oferece, a troca retorna à visão geral da organização. A visão global remove todo o contexto de tenant. Ao permanecer na mesma organização, mantém o filtro empresarial escolhido.',
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
        'descricao': 'Veja todos os cursos da organização; filtre pela empresa responsável. Se a empresa ou o serviço não têm cursos, a página mostra "Nenhum curso encontrado". Ao acessar um curso que não pertence à empresa, você é redirecionado para a lista com uma mensagem explicativa.',
    },
    'course-subject-list': {
        'titulo': 'Categorias de cursos',
        'secao': 'Conteúdo',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'autonomia-por-empresa',
        'descricao': 'Cadastre e organize as categorias reutilizáveis do catálogo de aprendizagem; cada curso pode receber uma categoria ao ser criado ou editado.',
    },
    'course-subject-create': {
        'titulo': 'Nova categoria de cursos',
        'secao': 'Conteúdo',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'autonomia-por-empresa',
        'descricao': 'Crie uma categoria reutilizável para organizar cursos; o identificador é normalizado automaticamente e a categoria pertence ao catálogo compartilhado.',
    },
    'course-subject-edit': {
        'titulo': 'Editar categoria de cursos',
        'secao': 'Conteúdo',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'autonomia-por-empresa',
        'descricao': 'Atualize o nome ou identificador da categoria; categorias vinculadas a cursos não podem ser excluídas.',
    },
    'course-edit': {
        'titulo': 'Editar curso',
        'secao': 'Cursos',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'autonomia-por-empresa',
        'descricao': 'Edite as informações do curso e a segmentação de audiência; cursos da organização inteira estão disponíveis para edição',
    },
    'quiz-list': {
        'titulo': 'Avaliações',
        'secao': 'Cursos',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'fase-6-quiz-e-dominio',
        'descricao': 'Liste avaliações do serviço de Treinamento, busque por nome ou descrição e abra perguntas ou configurações dentro da organização ativa.',
    },
    'quiz-create': {
        'titulo': 'Nova avaliação',
        'secao': 'Cursos',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'fase-6-quiz-e-dominio',
        'descricao': 'Configure uma avaliação com nota mínima, obrigatoriedade, tentativas, tempo e feedback; o quiz é criado na organização ativa.',
    },
    'quiz-edit': {
        'titulo': 'Editar avaliação',
        'secao': 'Cursos',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'fase-6-quiz-e-dominio',
        'descricao': 'Atualize as regras e a experiência da avaliação sem sair do escopo da organização ativa.',
    },
    'trail-list': {
        'titulo': 'Trilhas e recomendações',
        'secao': 'Cursos',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'autonomia-por-empresa',
        'descricao': 'Organize sequências de conteúdo, acompanhe aderência e filtre trilhas por tipo e status dentro da organização ativa.',
    },
    'trail-create': {
        'titulo': 'Nova trilha',
        'secao': 'Cursos',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'autonomia-por-empresa',
        'descricao': 'Monte uma sequência de conteúdos com abas de identificação, audiência e etapas; configure ordem, dependências e status de publicação.',
    },
    'trail-assignment-create': {
        'titulo': 'Atribuir trilha',
        'secao': 'Cursos',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'autonomia-por-empresa',
        'descricao': 'Atribua uma trilha publicada a uma audiência ou a uma pessoa da organização ativa.',
    },
    'publication-list': {
        'titulo': 'Feed e Wiki',
        'secao': 'Conteúdo',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'autonomia-de-conteudo-por-empresa',
        'descricao': 'Escolha uma empresa com Conteúdo ativo e defina a audiência; sem publicações, a lista permanece vazia; empresa proprietária e público autorizado são controles complementares',
    },
    'publication-create': {
        'titulo': 'Nova publicação',
        'secao': 'Conteúdo',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'autonomia-de-conteudo-por-empresa',
        'descricao': 'Crie uma publicação de Feed ou Wiki com abas de conteúdo, prioridade, recursos, documentos e audiência autorizada; a audiência segue a hierarquia da organização.',
    },
    'publication-edit': {
        'titulo': 'Editar publicação',
        'secao': 'Conteúdo',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'autonomia-de-conteudo-por-empresa',
        'descricao': 'Atualize conteúdo, publicação, documentos e audiência mantendo o escopo da organização e da empresa selecionadas; a aba de audiência usa o padrão compartilhado dos conteúdos.',
    },
    'course_editor_list': {
        'titulo': 'Editor de módulos',
        'secao': 'Cursos',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'navegacao-de-registros',
        'descricao': 'Organize módulos e conteúdos; o editor identifica o curso atual, mantém o escopo da organização e mostra uma lista vazia quando não há cursos',
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
        'descricao': 'Defina processos rígidos de competência com requisitos, nota mínima, tentativas, validade e evidências; o seletor oferece apenas empresas com Certificação ativa e, quando não houver registros, a lista permanece vazia',
    },
    'certification-create': {
        'titulo': 'Nova certificação',
        'secao': 'Cursos',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'certificacoes-governadas',
        'descricao': 'Crie uma certificação com empresa, requisitos de cursos e avaliações, nota mínima, validade e aprovação manual.',
    },
    'certification-edit': {
        'titulo': 'Editar certificação',
        'secao': 'Cursos',
        'arquivo': '03_COURSES_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '04-cursos-conteudo',
        'ancora': 'certificacoes-governadas',
        'descricao': 'Atualize requisitos, validade e regras da certificação dentro da organização ativa.',
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
    'user-create': {
        'titulo': 'Cadastrar usuário',
        'secao': 'Admin',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'usuarios-e-acessos',
        'descricao': 'Crie a conta e configure seus acessos por organização, empresa, unidade e papel.',
    },
    'assignment': {
        'titulo': 'Atribuir acessos',
        'secao': 'Admin',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'atribuicao-em-etapas',
        'descricao': 'Selecione pessoas, defina o escopo hierárquico e refine o acesso por função e canal; a importação CSV é indicada para cargas em lote.',
    },
    'management-assignments': {
        'titulo': 'Papéis de gestão',
        'secao': 'Admin',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'papeis-de-gestao',
        'descricao': 'Consulte os papéis administrativos e o escopo de organização, empresa ou unidade que cada pessoa pode operar.',
    },
    'management-assignment-new': {
        'titulo': 'Novo papel de gestão',
        'secao': 'Admin',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'papeis-de-gestao',
        'descricao': 'Escolha a pessoa, a responsabilidade e o escopo; deixar níveis inferiores vazios mantém o alcance no nível superior.',
    },
    'group-hierarchy-list': {
        'titulo': 'Grupos e hierarquias',
        'secao': 'Admin',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'grupos-e-hierarquias',
        'descricao': 'Configure agrupamentos adicionais da organização sem substituir a hierarquia canônica de empresa e unidades.',
    },
    'group-hierarchy-create': {
        'titulo': 'Nova hierarquia',
        'secao': 'Admin',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'grupos-e-hierarquias',
        'descricao': 'Crie um tipo de agrupamento, defina seus níveis e escolha se relações ou criação automática serão permitidas.',
    },
    'hierarchy_audit_log': {
        'titulo': 'Auditoria da estrutura',
        'secao': 'Segurança',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'auditoria-da-estrutura',
        'descricao': 'Consulte alterações de empresas e unidades na organização ativa, com filtros por recurso e ação; a tela é somente leitura.',
    },
    'user-edit': {
        'titulo': 'Perfil e permissões',
        'secao': 'Admin',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'perfil-e-permissoes',
        'descricao': 'Edite o perfil, associações e o vínculo verificado com uma identidade de candidato sem apagar histórico',
    },
    'document-list': {
        'titulo': 'Documentos e links reutilizáveis',
        'secao': 'Conteúdo',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'autonomia-de-conteudo-por-empresa',
        'descricao': 'Gerencie documentos da empresa selecionada ou compartilhados pela organização; o seletor oferece apenas empresas com Conteúdo ativo e, sem registros, a lista permanece vazia',
    },
    'document-create': {
        'titulo': 'Novo documento',
        'secao': 'Conteúdo',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'autonomia-de-conteudo-por-empresa',
        'descricao': 'Cadastre um documento com abas de identificação, conteúdo, versão e permissões de audiência dentro da organização ativa.',
    },
    'document-edit': {
        'titulo': 'Editar documento',
        'secao': 'Conteúdo',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'autonomia-de-conteudo-por-empresa',
        'descricao': 'Atualize dados e versões do documento, acompanhe vínculos e mantenha o compartilhamento temporário sob controle.',
    },
    'compliance-dashboard': {
        'titulo': 'Conformidade e treinamento',
        'secao': 'Segurança',
        'arquivo': '03_RECRUITMENT_PRIVACY_LGPD.html',
        'categoria': '03-recrutamento',
        'ancora': 'painel-de-conformidade',
        'descricao': 'Acompanhe treinamentos obrigatórios por pessoa, prazo e status dentro da organização ativa; o painel não substitui políticas ou evidências de LGPD.',
    },
    'audience-policy-list': {
        'titulo': 'Políticas de audiência',
        'secao': 'Audiência',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'politicas-de-audiencia',
        'descricao': 'Consulte e gerencie regras de acesso da organização ativa; políticas ativas controlam experiências autorizadas e inativas permanecem para revisão.',
    },
    'audience-policy-create': {
        'titulo': 'Nova política de audiência',
        'secao': 'Audiência',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'politicas-de-audiencia',
        'descricao': 'Crie uma regra de audiência limitada ao tenant atual e combine condições por empresa, unidade, canal, função ou papel.',
    },
    'audience-policy-edit': {
        'titulo': 'Editar política de audiência',
        'secao': 'Audiência',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'politicas-de-audiencia',
        'descricao': 'Revise a definição e o status da política sem ampliar o escopo além da organização ativa.',
    },
    'audience-simulation': {
        'titulo': 'Simulador de audiência',
        'secao': 'Audiência',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'simulador-de-audiencia',
        'descricao': 'Teste um recorte de organização, empresa, unidade, canal ou função e veja conteúdos publicados e alcance estimado.',
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
        'descricao': 'Filtre a biblioteca por empresas com Conteúdo ativo; arquivos da organização podem ser compartilhados, enquanto conteúdo empresarial permanece isolado',
    },
    'media-create': {
        'titulo': 'Nova mídia',
        'secao': 'Conteúdo',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'autonomia-de-conteudo-por-empresa',
        'descricao': 'Adicione uma imagem, vídeo ou arquivo à biblioteca com escopo, audiência, validade e regras de acesso.',
    },
    'media-edit': {
        'titulo': 'Editar mídia',
        'secao': 'Conteúdo',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'autonomia-de-conteudo-por-empresa',
        'descricao': 'Atualize uma mídia nas abas de dados, audiência, visualização, uso e histórico; preserve versões, acompanhe vínculos e controle compartilhamento e publicação. A exclusão definitiva fica bloqueada enquanto houver conteúdo vinculado; nesse caso, remova os usos ou arquive a mídia.',
    },
    'media-collection-list': {
        'titulo': 'Coleções de mídia',
        'secao': 'Conteúdo',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'autonomia-de-conteudo-por-empresa',
        'descricao': 'Organize mídias reutilizáveis por contexto sem alterar o escopo de acesso dos arquivos.',
    },
    'media-collection-create': {
        'titulo': 'Nova coleção de mídia',
        'secao': 'Conteúdo',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'autonomia-de-conteudo-por-empresa',
        'descricao': 'Crie ou edite uma coleção no tenant ativo para facilitar a organização da biblioteca.',
    },
    'media-bulk-upload': {
        'titulo': 'Upload de mídia em lote',
        'secao': 'Conteúdo',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'autonomia-de-conteudo-por-empresa',
        'descricao': 'Envie vários arquivos, aplique classificação comum e preserve a verificação de duplicidade por organização.',
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
    'content-metrics': {
        'titulo': 'Métricas de conteúdo',
        'secao': 'Análises e auditoria',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'biblioteca-de-conteudo',
        'descricao': 'Acompanhe alcance, leitura, feedback e dúvidas sem misturar organizações.',
    },
    'learning-metrics': {
        'titulo': 'Métricas de aprendizagem',
        'secao': 'Análises e auditoria',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'biblioteca-de-conteudo',
        'descricao': 'Compare matrículas, conclusões, tempo ativo e utilidade dos cursos.',
    },
    'engagement-funnel': {
        'titulo': 'Funil de engajamento',
        'secao': 'Análises e auditoria',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'biblioteca-de-conteudo',
        'descricao': 'Leia alcance, leitores e conclusões por tipo de conteúdo e período.',
    },
    'content-questions': {
        'titulo': 'Dúvidas e feedback',
        'secao': 'Análises e auditoria',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'biblioteca-de-conteudo',
        'descricao': 'Responda dúvidas privadas vinculadas ao conteúdo da organização ativa.',
    },
    'management-reports': {
        'titulo': 'Relatórios subordinados',
        'secao': 'Análises e auditoria',
        'arquivo': '08_USER_ACCESS_GOVERNANCE.html',
        'categoria': '05-operacao',
        'ancora': 'biblioteca-de-conteudo',
        'descricao': 'Veja usuários dentro dos escopos de gestão autorizados.',
    },

    # ADMIN: Setup
    'admin_dashboard': {
        'titulo': 'Administração global',
        'secao': 'Admin',
        'arquivo': '00_MATCHCO_ORGANIZATIONS_CHANNELS_AND_AUDIENCES.html',
        'categoria': '00-indice',
        'ancora': 'painel-administracao-organizacao',
        'descricao': 'Consulte todas as organizações e métricas agregadas da plataforma; abra cada organização separadamente sem misturar tenants.',
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
    'recruitment:access_audit': {
        'titulo': 'Auditoria de acessos e QR',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_PRIVACY_LGPD.html',
        'categoria': '03-recrutamento',
        'ancora': 'separacao-de-papeis',
        'descricao': 'Consulte vínculos, trocas de contexto e leituras de QR somente na organização autorizada',
    },
    'recruitment:entry_point_list': {
        'titulo': 'Portas de entrada e QR Codes',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'fase-1',
        'descricao': 'Gere e valide QRs Match; o domínio público é definido por ambiente em QR_CODE_BASE_URL e pode mudar sem recriar a entrada',
    },
    'console:questionnaire-templates': {
        'titulo': 'Templates de recrutamento',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'fase-5-catalogo-canonico',
        'descricao': 'Crie e publique perguntas por contexto; somente versões publicadas entram nos fluxos de entrada.',
    },
    'console:questionnaire-template-edit': {
        'titulo': 'Editar template de recrutamento',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'fase-5-catalogo-canonico',
        'descricao': 'Edite contexto, publicação e perguntas do template preservando a versão usada nos fluxos já publicados.',
    },
    'recruitment:matchco_opportunity_list': {
        'titulo': 'Necessidades declaradas',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'fase-5-catalogo-canonico',
        'descricao': 'Acompanhe necessidades Match da organização ativa, estado, interessados e respostas pendentes.',
    },
    'recruitment:employer_opportunity_interest': {
        'titulo': 'Pessoas interessadas',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'fase-5-catalogo-canonico',
        'descricao': 'Veja os interesses recebidos para uma necessidade, preservando o contato da pessoa até que o interesse seja mútuo.',
    },
    'recruitment:employer_declare_need': {
        'titulo': 'Declarar necessidade',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'fase-5-catalogo-canonico',
        'descricao': 'Declare onde, qual função, quando e como distribuir uma necessidade sem transformá-la em vaga pública.',
    },
    'recruitment:entry_point_create': {
        'titulo': 'Novo ponto de entrada',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'fase-1',
        'descricao': 'Crie um QR com identidade, finalidade, público e unidade dentro da organização ativa.',
    },

    # PÚBLICO: Signup
    'recruitment_candidate_signup': {
        'titulo': 'Criar Perfil',
        'secao': 'Candidato',
        'arquivo': '00_MATCHCO_CORE_STAKEHOLDER_FLOWS.html',
        'categoria': '00-indice',
        'ancora': 'otp-seguranca',
        'descricao': 'Veja os limites e a validade do código de acesso e entenda as autorizações territoriais do Perfil',
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
    'recruitment:store_function_catalog': {
        'titulo': 'Cargo estrutural e vínculo canônico',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'fase-2-catalogo-canonico',
        'descricao': 'Configure o cargo em três abas: cargo e funções canônicas, descrição e requisitos, e remuneração e contratação. A necessidade congela os termos e usa o mesmo gate do Perfil do candidato.',
    },
    'recruitment:flow_contract': {
        'titulo': 'Contrato do fluxo de Recrutamento Match',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'contrato-recrutamento-2-1',
        'descricao': 'Entenda o que pertence ao Cargo, à função canônica, ao Perfil, à necessidade e à negociação, incluindo os chips e as respostas determinísticas do Match.',
    },
    'console:job_function_list': {
        'titulo': 'Cargos da estrutura e catálogo Match',
        'secao': 'Organização e estrutura',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'distincao-de-cadastro',
        'descricao': 'Cadastre aqui o cargo oficial da empresa. O de-para com funções canônicas e os campos da operação são configurados por unidade em Configurar Match.',
    },
    'console:job_function_create': {
        'titulo': 'Cadastrar cargo estrutural',
        'secao': 'Organização e estrutura',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'distincao-de-cadastro',
        'descricao': 'Cadastre o cargo da empresa e seus canais. As funções canônicas do candidato são associadas depois na unidade de negócio.',
    },
    'console:company_list': {
        'titulo': 'Empresas da organização',
        'secao': 'Organização e estrutura',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'distincao-de-cadastro',
        'descricao': 'Consulte as empresas do contexto ativo e veja quantas unidades de negócio pertencem a cada uma. A administração de um shopping e seus lojistas permanecem separados nesta hierarquia.',
    },
    'console:company_create': {
        'titulo': 'Cadastrar empresa',
        'secao': 'Organização e estrutura',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'distincao-de-cadastro',
        'descricao': 'Cadastre a identidade, os contatos e o status da empresa antes de criar suas unidades de negócio e vínculos de acesso.',
    },
    'console:business_channel_list': {
        'titulo': 'Canais de negócio',
        'secao': 'Organização e estrutura',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'distincao-de-cadastro',
        'descricao': 'Consulte os canais pertencentes às empresas da organização e mantenha os contextos usados por cargos e unidades.',
    },
    'console:business_channel_create': {
        'titulo': 'Cadastrar canal de negócio',
        'secao': 'Organização e estrutura',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'distincao-de-cadastro',
        'descricao': 'Cadastre um canal dentro da empresa correta para reutilizá-lo em cargos e unidades.',
    },
    'console:operational_unit_list': {
        'titulo': 'Unidades operacionais',
        'secao': 'Organização e estrutura',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'distincao-de-cadastro',
        'descricao': 'Consulte as áreas e equipes operacionais vinculadas a cada unidade de negócio, sem misturar empresa, unidade física e operação interna.',
    },
    'console:operational_unit_create': {
        'titulo': 'Cadastrar unidade operacional',
        'secao': 'Organização e estrutura',
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'distincao-de-cadastro',
        'descricao': 'Crie uma área, equipe ou frente operacional dentro de uma unidade de negócio ativa.',
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
        'titulo': _('Serviços da organização'),
        'secao': _('Organização e estrutura'),
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'servicos-modulares',
        'descricao': _('Defina o padrão de serviços da organização e, quando necessário, crie uma exceção por empresa. A empresa herda o padrão até receber uma configuração própria. O servidor também bloqueia rotas diretas de serviços suspensos; esta tela continua acessível para ativar o primeiro serviço.'),
    },
    'console:organization_settings': {
        'titulo': _('Terminologia e tipos de pessoa'),
        'secao': _('Organização e estrutura'),
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'terminologia-e-tipos-de-pessoa',
        'descricao': _('Use as abas Hierarquia e Tipos de pessoa para separar os dois trabalhos. Adapte os nomes da estrutura e cadastre vínculos como colaborador, lojista ou prestador. Para retirar um tipo de uso, edite e desative sem apagar o histórico.'),
    },
    'person_type_list': {
        'titulo': _('Tipos de público e vínculo'),
        'secao': _('Organização e estrutura'),
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'terminologia-e-tipos-de-pessoa',
        'descricao': _('Cadastre as categorias de relação com a organização, mantendo-as separadas de cargos e funções profissionais.'),
    },
    'person_type_create': {
        'titulo': _('Novo tipo de público e vínculo'),
        'secao': _('Organização e estrutura'),
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'terminologia-e-tipos-de-pessoa',
        'descricao': _('Crie um tipo localizado na organização ativa, como colaborador, lojista, prestador ou parceiro.'),
    },
    'person_type_update': {
        'titulo': _('Editar tipo de público e vínculo'),
        'secao': _('Organização e estrutura'),
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'terminologia-e-tipos-de-pessoa',
        'descricao': _('Atualize o nome, a descrição ou a disponibilidade sem apagar vínculos históricos.'),
    },
    'console:organization_home': {
        'titulo': _('Visão geral da organização'),
        'secao': _('Organização e estrutura'),
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'hub-da-organizacao',
        'descricao': _('Use este hub para confirmar o tenant ativo, ler os principais indicadores por categoria e abrir rapidamente a estrutura, a marca, as entradas, os templates, as integrações e a governança. As ações continuam limitadas à organização selecionada.'),
    },
    'console:organization_brand': {
        'titulo': _('Marca e white-label'),
        'secao': _('Organização e estrutura'),
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'hub-da-organizacao',
        'descricao': _('Configure o nome público, logo, favicon, cor, template de entrada, domínio e white-label da organização ativa. Os rótulos e mensagens acompanham o idioma escolhido. As alterações afetam as experiências públicas, não o console administrativo.'),
    },
    'console:integration_connections': {
        'titulo': _('Integrações da organização'),
        'secao': _('Organização e estrutura'),
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'integracoes-da-organizacao',
        'descricao': _('Cadastre a referência de HRIS, CRM, LMS, SSO e notificações da organização. Revise o status e valide a configuração sem expor credenciais no Console.'),
    },
    'console:integration_edit': {
        'titulo': _('Editar conexão'),
        'secao': _('Organização e estrutura'),
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'integracoes-da-organizacao',
        'descricao': _('Atualize uma conexão dentro da organização ativa e valide a configuração novamente antes de ativá-la.'),
    },
    'console:organization_onboarding': {
        'titulo': _('Criar uma organização'),
        'secao': _('Organização e estrutura'),
        'arquivo': '02_ARCHITECTURE_MULTITENANT.html',
        'categoria': '02-arquitetura',
        'ancora': 'hub-da-organizacao',
        'descricao': _('Crie o tenant, a primeira empresa e a unidade inicial em um fluxo guiado. O checkbox de white-label fica agrupado com sua explicação, e as mensagens de campos obrigatórios seguem o idioma escolhido. Depois do cadastro, revise a estrutura, ative serviços e configure as entradas da organização.'),
    },
    'recruitment_public:lojista_contexto': {
        'titulo': 'Trocar organização e proteger o contexto',
        'secao': 'Recrutamento',
        'arquivo': '00_MATCHCO_CANONICAL_URLS.html',
        'categoria': '00-indice',
        'descricao': 'Escolha explicitamente a empresa; a unidade e a porta de entrada anteriores são limpas',
    },
    'recruitment_public:lojista_necessidades': {
        'titulo': 'Ler a fila de necessidades e convites',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'fase-3',
        'descricao': 'A contagem de elegíveis usa os mesmos critérios da rodada e inclui Perfis de outras organizações somente após consentimento válido. A lista nominal aparece apenas depois do interesse da pessoa.',
    },
    'recruitment_public:lojista_declarar': {
        'titulo': 'Declarar uma necessidade de alto giro',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'fase-3',
        'descricao': 'Defina função local e critérios objetivos. A prévia mostra o volume elegível, não nomes; convites e interesse seguem as regras de consentimento e prazo.',
    },
    'recruitment_public:lojista_job_functions': {
        'titulo': 'Consultar funções da unidade',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'catalogo-por-categoria-da-loja',
        'descricao': 'A lista de funções só consulta a unidade da organização ativa; unidades de outra organização são tratadas como inexistentes.',
    },
    'recruitment_public:lojista_simular': {
        'titulo': 'Estimar o alcance da necessidade',
        'secao': 'Recrutamento',
        'arquivo': '03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html',
        'categoria': '03-recrutamento',
        'ancora': 'fase-3',
        'descricao': 'A estimativa usa apenas a unidade da organização ativa e os critérios publicados; não revela nomes de candidatos.',
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
        'descricao': 'Consulte os critérios do match, negocie apenas os campos autorizados e, somente para administração, os CEPs de referência do candidato e da unidade',
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
        'ancora': 'otp-seguranca',
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
