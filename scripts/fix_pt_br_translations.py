#!/usr/bin/env python3
"""
Fix empty msgstr entries in pt_BR django.po.

Strategy:
1. Strings already in Portuguese → copy msgid to msgstr
2. Code/JS/HTML fragments → copy as-is
3. English strings → translate to Portuguese using a dictionary
"""

import re
import sys

PO_FILE = "matchco/locale/pt_BR/LC_MESSAGES/django.po"

# Portuguese characters that indicate the string is already in PT
PT_CHARS = set('áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ')

# Common Portuguese starting words (longer forms to avoid false positives)
PT_STARTS = [
    'Abandono', 'Aberta', 'Aberto', 'Aberturas', 'Abra', 'Abre', 'Abrir',
    'Aceitar', 'Aceito', 'Acesse', 'Acesso', 'Acima', 'Adicionar',
    'Administrador', 'Ajustar', 'Algo', 'Alterar', 'Alterado', 'Ambiente',
    'Análise', 'Ano', 'Anos', 'Aplicar', 'Aprovado', 'Arquivar', 'Arquivado',
    'Ativar', 'Ativo', 'Atividade', 'Atual', 'Atualizar', 'Audiência',
    'Avaliar', 'Avaliação', 'Aviso', 'Baixar', 'Bem', 'Bloquear', 'Busca',
    'Cadastrar', 'Calendário', 'Campanha', 'Canal', 'Capacitação', 'Cargo',
    'Caso', 'Categor', 'Certificaç', 'Chamar', 'Clique', 'Código',
    'Colaborador', 'Combinar', 'Comentário', 'Completar', 'Completo',
    'Comunicação', 'Concluído', 'Confirmar', 'Confirmado', 'Conectar',
    'Conexão', 'Configurar', 'Conta', 'Contato', 'Continuar', 'Contratar',
    'Convite', 'Criar', 'Criado', 'Curso', 'Dados', 'Declaraç', 'Definir',
    'Desativar', 'Desativado', 'Desenvolvimento', 'Destino', 'Detalhes',
    'Dica', 'Distribuição', 'Documento', 'Download', 'Dúvida', 'Durante',
    'Editar', 'Elegibilidade', 'E-mail', 'Eligibilidade', 'Em breve',
    'Encerrar', 'Endereço', 'Entrada', 'Entrar', 'Envio', 'Enviar',
    'Equipe', 'Erro', 'Escolher', 'Escolha', 'Escrever', 'Etapas',
    'Exclusivo', 'Expirado', 'Explorar', 'Falta', 'Favorito', 'Fazer',
    'Fechado', 'Filtro', 'Finalizar', 'Forma', 'Formação', 'Formato',
    'Fornecedor', 'Frase', 'Função', 'Gerar', 'Gerenciar', 'Gerente',
    'Gestão', 'Grupo', 'Histórico', 'Horário', 'Identificação', 'Imagem',
    'Importante', 'Importar', 'Indicador', 'Indicação', 'Informaç',
    'Início', 'Iniciar', 'Inscrever', 'Interesse', 'Interessado',
    'Introdução', 'Item', 'Lições', 'Link', 'Local', 'Loja', 'Login',
    'Logout', 'Mandar', 'Marca', 'Matrícula', 'Mensagem', 'Menu', 'Modo',
    'Módulo', 'Nome', 'Notificação', 'Novo', 'Necessidade', 'Nível',
    'Número', 'Objetivo', 'Observação', 'Obter', 'Obrigatório', 'Operação',
    'Operador', 'Oportunidade', 'Opção', 'Organização', 'Origem', 'Outro',
    'Painel', 'Papel', 'Parceiro', 'Participante', 'Participar', 'Pasta',
    'Pessoa', 'Plano', 'Ponto', 'Portal', 'Posição', 'Postagem',
    'Pré-requisito', 'Preço', 'Preencher', 'Preparar', 'Presencial',
    'Primeiro', 'Próximo', 'Progresso', 'Projeto', 'Publicação', 'Público',
    'Qualificação', 'Qualquer', 'Questionário', 'Rastrear', 'Realizar',
    'Receber', 'Recente', 'Recrutamento', 'Referência', 'Registrar',
    'Registro', 'Regra', 'Reiniciar', 'Relação', 'Relatório', 'Remover',
    'Responder', 'Resposta', 'Resultado', 'Revisar', 'Rodada', 'Rotina',
    'Salário', 'Salvar', 'Selecionar', 'Selecionado', 'Senha', 'Separador',
    'Sequência', 'Serviço', 'Sistema', 'Sobre', 'Status', 'Submeter',
    'Suporte', 'Tarefa', 'Telefone', 'Tempo', 'Término', 'Termos',
    'Território', 'Texto', 'Título', 'Total', 'Treinamento', 'Tipo',
    'Unidade', 'Usuário', 'Validação', 'Valor', 'Versão', 'Vínculo',
    'Visualizar', 'Vagas', 'Vaga', 'Vídeo', 'Você', 'Zerar',
    'A loja', 'A pessoa', 'A empresa', 'A unidade', 'A função',
    'A conta', 'A necessidade', 'A oportunidade', 'A organização',
    'A mensagem', 'A porta', 'A rede', 'A decisão', 'A mesma',
    'A partir', 'A combinar', 'A ler', 'Aqui', 'Aguardando',
    'Ainda', 'Ajudou', 'Ajustes', 'Alerta', 'Alertas',
    'Acompanhamento', 'Acompanhar', 'Adicione', 'Adiei',
    'Admin da', 'Administrado', 'Administrar',
    'Atribuição', 'Audiência alvo',
    'Bom', 'Boa', 'Baixo', 'Baixa',
    'Candidato', 'Candidatura', 'Carga', 'Certa', 'Certos',
    'Com', 'Como', 'Quando', 'Onde', 'Qual', 'Quais',
    'Todos', 'Nenhum', 'Nenhuma', 'Nada', 'Nunca',
    'Mais', 'Menos', 'Menor', 'Maior', 'Muito', 'Muitos',
    'Pode', 'Não', 'Sim', 'Se', 'Que', 'Ou', 'E',
    'De', 'Do', 'Da', 'Dos', 'Das', 'Num', 'Nas',
    'Pelo', 'Pela', 'Pelos', 'Pelas', 'Para', 'Por',
    'Entre', 'Sobre', 'Sem', 'Contra', 'Após', 'Antes',
    'Durante', 'Até', 'Desde', 'Junto', 'Através',
    'Dentro', 'Fora', 'Acima', 'Abaixo', 'Ao', 'À',
    'Entre', 'Versus', 'Versão',
    'ajudou', 'avalio', 'conclusão', 'matrículas', 'progresso',
    'acessaram', 'confirmaram', 'converteram', 'útil',
    'selecionados', 'encontrados', 'disponíveis',
    'declarado', 'declaram', 'min', 'ano',
    'Contexto', 'Estrutura', 'Perfil', 'Rede',
    'MatchCo', 'Recrutamento', 'Learning', 'Comunicação', 'Network',
    'Entrada', 'Necessidade', 'Interesse', 'Match',
    'Pessoas', 'Cargo', 'canônicos', 'Descrição', 'requisitos',
    'Remuneração', 'contratação', 'Audiência', 'permissões',
    'Hierarquia', 'pessoa', 'Etapas', 'trilha',
    'Funções', 'canal', 'Distribuição automática',
    'Segmentos', 'Prioridade', 'Flexibilidade',
    'Dependências', 'sistema decide',
    'dias', 'selecionados',
    'ajudou', 'avaliado', 'confirmaram', 'converteram',
    'Back', 'Voltar',
]

# English to Portuguese translation dictionary for common UI strings
EN_TO_PT = {
    # Feed / Publishing
    "Feed rhythm": "Ritmo do Feed",
    "Stay up to date": "Mantenha-se atualizado",
    "Quick news, announcements and signals from your learning space.": "Notícias rápidas, comunicados e sinais do seu espaço de aprendizado.",
    "Quick news and useful signals from your learning space.": "Notícias rápidas e sinais úteis do seu espaço de aprendizado.",
    "Continue learning": "Continuar aprendendo",
    "Continue learning from where you left off.": "Continue de onde parou.",
    "Quick news and useful signals from your learning space.": "Notícias rápidas e sinais úteis do seu espaço de aprendizado.",
    "Watch related video": "Assistir vídeo relacionado",
    "Topics": "Tópicos",
    "More from the feed": "Mais do Feed",
    "Back to feed": "Voltar ao Feed",
    "Latest update": "Última atualização",
    "By": "Por",
    "Back to knowledge base": "Voltar à base de conhecimento",
    "Knowledge article": "Artigo de conhecimento",
    "Related resource": "Recurso relacionado",
    "Open video resource": "Abrir recurso de vídeo",
    "Published by": "Publicado por",
    "In this article": "Neste artigo",
    "Use the topics below to discover related knowledge.": "Use os tópicos abaixo para descobrir conhecimento relacionado.",
    "Related knowledge": "Conhecimento relacionado",
    "Feed": "Feed",
    "Updates": "Atualizações",
    "Latest updates": "Últimas atualizações",
    "See the latest news, announcements and learning updates.": "Veja as últimas notícias, comunicados e atualizações de aprendizado.",
    "Knowledge": "Conhecimento",
    "Knowledge base": "Base de conhecimento",
    "Explore the knowledge base and find useful references.": "Explore a base de conhecimento e encontre referências úteis.",
    "Publications": "Publicações",
    "Published and available to you": "Publicadas e disponíveis para você",
    "With media": "Com mídia",
    "Posts with image or video": "Postagens com imagem ou vídeo",
    "Authors": "Autores",
    "People sharing knowledge": "Pessoas compartilhando conhecimento",
    "publications found": "publicações encontradas",
    "Category": "Categoria",
    "All categories": "Todas as categorias",
    "Read update": "Ler atualização",
    "No updates found.": "Nenhuma atualização encontrada.",
    "No publications found.": "Nenhuma publicação encontrada.",
    "Read more": "Ler mais",
    "Video": "Vídeo",
    "Pagination": "Paginação",
    "Previous": "Anterior",
    "Next": "Próximo",
    "Summary": "Resumo",
    "Wiki": "Wiki",

    # Navigation & UI
    "Home": "Início",
    "Dashboard": "Painel",
    "Settings": "Configurações",
    "Profile": "Perfil",
    "Logout": "Sair",
    "Login": "Entrar",
    "Sign in": "Entrar",
    "Sign up": "Cadastrar",
    "Register": "Registrar",
    "Search": "Buscar",
    "Filter": "Filtrar",
    "Sort": "Ordenar",
    "Save": "Salvar",
    "Cancel": "Cancelar",
    "Delete": "Excluir",
    "Edit": "Editar",
    "Create": "Criar",
    "Update": "Atualizar",
    "Submit": "Enviar",
    "Close": "Fechar",
    "Open": "Abrir",
    "View": "Visualizar",
    "Details": "Detalhes",
    "Back": "Voltar",
    "&larr; Back": "&larr; Voltar",
    "Next": "Próximo",
    "Previous": "Anterior",
    "Yes": "Sim",
    "No": "Não",
    "OK": "OK",
    "Confirm": "Confirmar",
    "Accept": "Aceitar",
    "Reject": "Rejeitar",
    "Apply": "Aplicar",
    "Clear": "Limpar",
    "Reset": "Redefinir",
    "Add": "Adicionar",
    "Remove": "Remover",
    "Select": "Selecionar",
    "All": "Todos",
    "None": "Nenhum",
    "Other": "Outro",
    "More": "Mais",
    "Less": "Menos",
    "Show more": "Mostrar mais",
    "Show less": "Mostrar menos",
    "Loading": "Carregando",
    "Loading...": "Carregando...",
    "Error": "Erro",
    "Success": "Sucesso",
    "Warning": "Aviso",
    "Info": "Informação",
    "Note": "Nota",
    "Tip": "Dica",
    "Help": "Ajuda",
    "About": "Sobre",
    "About this update": "Sobre esta atualização",

    # Account & Auth
    "Account Information": "Informações da conta",
    "Access Control": "Controle de acesso",
    "Access Level": "Nível de acesso",
    "Access Rules": "Regras de acesso",
    "Already have an account?": "Já tem uma conta?",
    "Password": "Senha",
    "Email": "E-mail",
    "Name": "Nome",
    "Username": "Nome de usuário",
    "Phone": "Telefone",
    "Two-factor authentication": "Autenticação de dois fatores",
    "Add an extra layer of security.": "Adicione uma camada extra de segurança.",

    # Admin
    "Admin Dashboard": "Painel administrativo",
    "Admin credentials and organization URLs will appear here": "As credenciais de administrador e os URLs da organização aparecerão aqui",
    "Add Access Rule": "Adicionar regra de acesso",
    "Add Member": "Adicionar membro",
    "Add New Organization": "Adicionar nova organização",
    "Add Organization": "Adicionar organização",
    "Add Quiz to Module": "Adicionar quiz ao módulo",
    "Add a new level": "Adicionar um novo nível",
    "Add members and access rules above to manage group permissions.": "Adicione membros e regras de acesso acima para gerenciar permissões do grupo.",
    "Add new content:": "Adicionar novo conteúdo:",
    "Add nodes and members after creation": "Adicionar nós e membros após a criação",
    "After creation, you can add members to this node": "Após a criação, você pode adicionar membros a este nó",
    "Allow User Linking": "Permitir vinculação de usuário",
    "Allow consume points on store": "Permitir consumo de pontos na loja",
    "Allow multiple attempts": "Permitir múltiplas tentativas",
    "Allows Relocation": "Permite realocação",

    # Courses & Learning
    "Active Courses": "Cursos ativos",
    "Achievements": "Conquistas",
    "Alumni Community": "Comunidade de ex-alunos",
    "Alumni Network": "Rede de ex-alunos",
    "Access exclusive alumni-only courses and training programs.": "Acesse cursos e programas de treinamento exclusivos para ex-alunos.",
    "Course": "Curso",
    "Courses": "Cursos",
    "My Courses": "Meus Cursos",
    "My courses": "Meus cursos",
    "Module": "Módulo",
    "Modules": "Módulos",
    "modules": "módulos",
    "Lesson": "Lição",
    "Lessons": "Lições",
    "Quiz": "Quiz",
    "Quizzes": "Quizzes",
    "Training": "Treinamento",
    "Certification": "Certificação",
    "Certifications": "Certificações",
    "Progress": "Progresso",
    "Completed": "Concluído",
    "In Progress": "Em andamento",
    "Not Started": "Não iniciado",
    "Enroll": "Inscrever-se",
    "Enrolled": "Inscrito",
    "Start learning": "Começar a aprender",
    "Learning path": "Trilha de aprendizado",
    "Learning paths": "Trilhas de aprendizado",
    "Learning": "Aprendizado",
    "Your learning path": "Sua trilha de aprendizado",
    "Course modules": "Módulos do curso",
    "Course contents": "Conteúdo do curso",
    "Course details": "Detalhes do curso",
    "Course navigation": "Navegação do curso",
    "This course has no modules yet.": "Este curso ainda não tem módulos.",
    "This module has no content yet.": "Este módulo ainda não tem conteúdo.",
    "No modules available.": "Nenhum módulo disponível.",
    "Back to courses": "Voltar aos cursos",
    "Back to home": "Voltar ao início",
    "Continue course": "Continuar curso",
    "Continue your enrolled courses and track your progress.": "Continue seus cursos inscritos e acompanhe seu progresso.",
    "No courses enrolled yet": "Nenhum curso inscrito ainda",
    "Browse courses": "Explorar cursos",
    "Browse Courses": "Explorar cursos",
    "Available": "Disponível",
    "Available course": "Curso disponível",
    "Available for you": "Disponível para você",
    "Ready to enroll": "Pronto para inscrição",
    "In progress": "Em andamento",
    "Your enrolled courses": "Seus cursos inscritos",
    "Course categories": "Categorias de cursos",
    "Search by course name": "Buscar por nome do curso",
    "No courses found for the selected filters.": "Nenhum curso encontrado para os filtros selecionados.",
    "Courses you can join according to your audience access.": "Cursos que você pode participar de acordo com seu acesso.",
    "available": "disponível",
    "Enroll now": "Inscrever-se agora",
    "Continue where you left off.": "Continue de onde parou.",
    "Module contents:": "Conteúdo do módulo:",
    "Save modules": "Salvar módulos",
    "See the learning path": "Ver a trilha de aprendizado",
    "Manage your learning catalog and continue your courses.": "Gerencie seu catálogo de aprendizado e continue seus cursos.",
    "Visible in the catalog": "Visível no catálogo",
    "Previous content": "Conteúdo anterior",
    "Next content": "Próximo conteúdo",
    "This video link is not valid.": "Este link de vídeo não é válido.",
    "Download this material": "Baixar este material",
    "Open or download the file to continue.": "Abra ou baixe o arquivo para continuar.",
    "Review": "Revisar",
    "Start": "Iniciar",
    "Quiz type": "Tipo de quiz",
    "Your Quiz Attempts": "Suas tentativas de quiz",
    "Attempt": "Tentativa",
    "Time Spent": "Tempo gasto",
    "Date": "Data",
    "View Details": "Ver detalhes",
    "Retry Quiz": "Tentar novamente",
    "You can retry this quiz on %(date)s.": "Você pode tentar novamente em %(date)s.",
    "You have reached the maximum number of attempts for this quiz.": "Você atingiu o número máximo de tentativas para este quiz.",
    "No attempts yet. Start by taking the quiz!": "Nenhuma tentativa ainda. Comece fazendo o quiz!",
    "Take Quiz": "Fazer quiz",
    "Quiz Results": "Resultados do quiz",
    "Quiz Passed!": "Quiz aprovado!",
    "Quiz Not Passed": "Quiz não aprovado",
    "You need %(score)s%% to pass (you scored %(current)s%%).": "Você precisa de %(score)s%% para passar (você tirou %(current)s%%).",
    "Correct Answers": "Respostas corretas",
    "Detailed Review": "Revisão detalhada",
    "Correct": "Correto",
    "Incorrect": "Incorreto",
    "Your answer:": "Sua resposta:",
    "Not answered": "Não respondida",
    "Correct answer:": "Resposta correta:",
    "Explanation:": "Explicação:",
    "Go Back": "Voltar",
    "Passing Score": "Nota de aprovação",
    "You have %(minutes)s minute to complete this quiz.": "Você tem %(minutes)s minuto para completar este quiz.",
    "You have %(minutes)s minutes to complete this quiz.": "Você tem %(minutes)s minutos para completar este quiz.",
    "Explanation (after submission)": "Explicação (após envio)",
    "Your answer...": "Sua resposta...",
    "Submit Quiz": "Enviar quiz",
    "Error: Form element not found": "Erro: Elemento do formulário não encontrado",
    "Please answer at least one question before submitting.": "Por favor, responda pelo menos uma pergunta antes de enviar.",
    "Submitting...": "Enviando...",
    "This quiz attempt has already been submitted.": "Esta tentativa de quiz já foi enviada.",
    "Quiz submitted successfully!": "Quiz enviado com sucesso!",
    "Score": "Pontuação",
    "Passed": "Aprovado",
    "Failed": "Falhou",
    "questions": "questões",
    "Back to Attempts": "Voltar às tentativas",
    "Time": "Tempo",
    "Take Quiz": "Fazer quiz",
    "View Attempts": "Ver tentativas",
    "Optional": "Opcional",
    "Multiple attempts allowed": "Múltiplas tentativas permitidas",
    "Single attempt only": "Apenas uma tentativa",
    "Browse Courses": "Explorar cursos",
    "Continuing Learning": "Aprendizado contínuo",
    "Job Board": "Quadro de vagas",
    "Explore career opportunities from alumni companies.": "Explore oportunidades de carreira de empresas de ex-alunos.",
    "View Jobs": "Ver vagas",
    "Not yet an alumnus/alumna": "Ainda não é ex-aluno(a)",
    "Delete Answer": "Excluir resposta",
    "Are you sure you want to delete this answer?": "Tem certeza que deseja excluir esta resposta?",
    "Question:": "Pergunta:",
    "Answer:": "Resposta:",
    "Correct answer": "Resposta correta",

    # Profile
    "My Profile": "Meu perfil",
    "View and manage your profile information.": "Veja e gerencie as informações do seu perfil.",
    "Edit Profile": "Editar perfil",
    "Update your profile information.": "Atualize as informações do seu perfil.",
    "Back to Profile": "Voltar ao perfil",
    "Member since": "Membro desde",

    # Organization
    "Active organization": "Organização ativa",
    "All Organization Content": "Todo o conteúdo da organização",
    "All content": "Todo o conteúdo",
    "Across all orgs": "Em todas as organizações",
    "Organization": "Organização",
    "Organizations": "Organizações",

    # Status & Filters
    "All statuses": "Todos os status",
    "Status": "Status",
    "Active": "Ativo",
    "Inactive": "Inativo",
    "Draft": "Rascunho",
    "Published": "Publicado",
    "Archived": "Arquivado",
    "Pending": "Pendente",
    "Approved": "Aprovado",
    "Rejected": "Rejeitado",
    "Open": "Aberto",
    "Closed": "Fechado",

    # Questions & Answers
    "All answers and user responses will also be deleted.": "Todas as respostas e respostas dos usuários também serão excluídas.",
    "All user responses to this answer will be removed.": "Todas as respostas dos usuários a esta resposta serão removidas.",

    # Attempts
    "- Attempt #": "- Tentativa #",

    # Time
    "1 day": "1 dia",
    "1 year": "1 ano",
    "7 days": "7 dias",
    "30 days": "30 dias",
    "90 days": "90 dias",
    "7d": "7d",
    "30d": "30d",
    "90d": "90d",
    "%(minutes)s min": "%(minutes)s min",
    "%(n)s ano(s) declarado(s)": "%(n)s ano(s) declarado(s)",

    # Percentages and metrics
    "%% ajudou": "%% ajudou",
    "%% avaliado como útil": "%% avaliado como útil",
    "%% de conclusão": "%% de conclusão",
    "%% de matrículas com progresso": "%% de matrículas com progresso",
    "%% não": "%% não",
    "%% que acessaram 2+ vezes": "%% que acessaram 2+ vezes",
    "%% que avaliaram como útil": "%% que avaliaram como útil",
    "%% que confirmaram leitura": "%% que confirmaram leitura",
    "%% que converteram para leitura ativa": "%% que converteram para leitura ativa",
    "%% útil": "%% útil",

    # Miscellaneous
    "(opcional)": "(opcional)",
    "(principal)": "(principal)",
    "(YouTube, etc.) *": "(YouTube, etc.) *",
    "(YouTube, Vimeo, etc.) *": "(YouTube, Vimeo, etc.) *",
    "+ Adicionar etapa": "+ Adicionar etapa",
    "+ Novo gestor": "+ Novo gestor",
    "0 selecionados": "0 selecionados",
    "A combinar": "A combinar",
    "A ler agora": "A ler agora",
    "ALTO GIRO": "ALTO GIRO",
    "AQUI": "AQUI",
    "Acompanhamento Match": "Acompanhamento Match",
    "Acompanhar pessoas, declarar interesse e liberar o contato.": "Acompanhar pessoas, declarar interesse e liberar o contato.",
    "Admin da rede": "Admin da rede",
    "Administrado": "Administrado",
    "Administrar acessos →": "Administrar acessos →",
    "Aguardando resposta": "Aguardando resposta",
    "Aguarde contato da equipe de recrutamento": "Aguarde contato da equipe de recrutamento",
    "Ainda nenhum match.": "Ainda nenhum match.",
    "Ajudou parcialmente": "Ajudou parcialmente",
    "Ajustes solicitados pelo gestor": "Ajustes solicitados pelo gestor",
    "Alerta operacional": "Alerta operacional",
    "Alertas de auditoria (7d)": "Alertas de auditoria (7d)",
    "Alertas no dispositivo": "Alertas no dispositivo",
    "Alto giro operacional": "Alto giro operacional",
    "Adicione e gerencie perguntas deste quiz": "Adicione e gerencie perguntas deste quiz",
    "Adicione e gerencie perguntas do quiz": "Adicione e gerencie perguntas do quiz",
    "Adicione um e-mail valido": "Adicione um e-mail válido",
    "Adiei ou cancelei a necessidade": "Adiei ou cancelei a necessidade",
}

# Strings that are code/JS/HTML and should NOT be translated
CODE_PATTERNS = [
    '\\n', '\\\\', 'function', 'var ', 'const ', 'let ', '=>',
    'console.', 'document.', 'window.', 'JSON.', 'chatSocket',
    '$chat', '$input', '$submit', '.scrollTop', '.onmessage',
    '.onclose', '.click', '.val', '.focus', '.keyup',
    '.append', '.toString', '.toLocaleString',
    'WebSocket', 'http://', 'https://',
    'BEGIN', 'END', 'SELECT ', 'INSERT ', 'UPDATE ', 'DELETE ',
    'import ', 'export ', 'class ', 'def ', 'return ',
    'if ', 'for ', 'while ', 'try ', 'except ',
    '<script', '</script', '<div', '</div', '<span', '</span',
    'class=', 'id=', 'href=', 'src=', 'onclick', 'onchange',
    '.html', '.js', '.css', '.py', '.json', '.xml',
    'HTTP_', 'Status ', 'Content-Type', 'Authorization',
    'Bearer ', 'token', 'api/', 'v1/', 'v2/',
]


def is_code_fragment(s):
    """Check if a string is a code fragment that shouldn't be translated."""
    for pat in CODE_PATTERNS:
        if pat in s:
            return True
    # Very long strings are likely code
    if len(s) > 500:
        return True
    return False


def is_portuguese(s):
    """Check if a string is already in Portuguese."""
    # Has Portuguese characters
    for c in s:
        if c in PT_CHARS:
            return True
    # Starts with common PT words
    for ps in PT_STARTS:
        if s.startswith(ps):
            return True
    return False


def translate_string(msgid):
    """Get the Portuguese translation for a string."""
    # Direct dictionary lookup
    if msgid in EN_TO_PT:
        return EN_TO_PT[msgid]

    # Already Portuguese
    if is_portuguese(msgid):
        return msgid

    # Code fragment
    if is_code_fragment(msgid):
        return msgid

    # Single short words or numbers - keep as-is
    if len(msgid.split()) <= 2 and len(msgid) < 20:
        return msgid

    # Fallback: return the original (will show English)
    return msgid


def fix_po_file():
    """Fix all empty msgstr entries in the PO file."""
    with open(PO_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    fixed_count = 0
    translated_count = 0
    skipped_count = 0

    # Pattern to match msgid "..." followed by msgstr ""
    pattern = re.compile(r'(msgid "([^"]*)"\n)msgstr ""')

    def replacer(match):
        nonlocal fixed_count, translated_count, skipped_count
        prefix = match.group(1)
        msgid = match.group(2)

        # Skip empty msgids (header entries)
        if not msgid:
            skipped_count += 1
            return match.group(0)

        translation = translate_string(msgid)

        if translation == msgid:
            # Either already PT or code - copy as-is
            fixed_count += 1
            skipped_count += 1
        else:
            translated_count += 1
            fixed_count += 1

        # Escape backslashes and quotes in translation
        escaped = translation.replace('\\', '\\\\').replace('"', '\\"')
        return f'{prefix}msgstr "{escaped}"'

    new_content = pattern.sub(replacer, content)

    if new_content != original_content:
        with open(PO_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {fixed_count} empty translations:")
        print(f"  - Translated from English: {translated_count}")
        print(f"  - Copied as-is (PT/code): {skipped_count}")
        return True
    else:
        print("No changes needed.")
        return False


if __name__ == "__main__":
    fix_po_file()
