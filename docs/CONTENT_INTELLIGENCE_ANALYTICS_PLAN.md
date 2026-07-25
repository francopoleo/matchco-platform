# Talk — Inteligência de Conteúdo, Audiência e Aderência

**Data:** 2026-07-24  
**Status:** Planejamento estratégico e técnico

## Lacuna atual

O Talk já registra abertura de publicações, visualizações, ciência, feedback privado e prioridade na Home. A página administrativa **Métricas de conteúdo** também já existe para Feed e Wiki.

Ainda falta conectar os cursos ao mesmo modelo. Precisamos registrar abertura do curso, módulo e conteúdo, tempo ativo estimado, vídeo, anexos, progresso, abandono, conclusão, feedback e dúvidas.

## Objetivo

Medir se uma informação operacional importante chegou, foi lida, compreendida e produziu a ação esperada. O produto não deve vender vigilância individual; deve vender **prova de aderência da informação crítica**.

```text
publicado → elegível → alcançado → aberto → leitura ativa
          → reconhecido → considerado útil → ação ou conclusão
```

Visualização não é leitura. Leitura não é compreensão. Compreensão não é execução.

## Métricas de alcance

- público elegível, alcançado e ainda não alcançado;
- taxa de alcance por organização, unidade, função e canal;
- primeira abertura e tempo até a primeira abertura;
- reaberturas e acesso dentro do prazo recomendado;
- alcance por versão do conteúdo;
- usuários elegíveis que nunca acessaram a plataforma.

## Métricas de leitura e aprendizagem

- tempo ativo estimado;
- tempo até a primeira interação;
- rolagem significativa;
- percentual de vídeo assistido;
- abertura de anexos;
- retorno ao conteúdo;
- abandono antes do ponto essencial;
- início, progresso e conclusão de módulo e curso;
- etapa em que o usuário abandona;
- diferença entre curso iniciado e curso concluído.

O sistema deve exibir **tempo ativo estimado**, nunca afirmar que uma aba aberta equivale a leitura. A sessão deve considerar visibilidade da aba, atividade e heartbeat limitado.

## Métricas de utilidade e comportamento

- ajudou, parcialmente, não ajudou;
- motivo: desatualizado, pouco claro, informação faltante ou difícil de encontrar;
- dúvidas enviadas e dúvidas sem resposta;
- buscas sem resultado;
- conteúdo relacionado aberto após a leitura;
- retorno ao mesmo conteúdo em curto intervalo;
- alto acesso com baixa utilidade;
- alta criticidade com baixa leitura;
- conteúdo obsoleto ainda acessado;
- excesso de comunicações para a mesma audiência.

## Grupo do Console: Inteligência e métricas

O Console deve ter um grupo próprio, separado de Conteúdo e Audiência:

1. **Visão executiva** — saúde da comunicação, alcance, leitura, ciência, utilidade e risco.
2. **Conteúdo e prioridade** — matriz importância × alcance × utilidade, versões, conteúdo obsoleto e fila de revisão.
3. **Audiência e aderência** — funil por empresa, unidade, função e canal; grupos atrasados ou que leem sem considerar útil.
4. **Cursos e aprendizagem** — progresso, tempo por módulo, abandono, conclusão e pontos de dificuldade.
5. **Feedback e dúvidas** — inbox privado, motivos, casos, responsáveis, SLA e resolução.
6. **Acesso e adoção** — logins, usuários ativos em 7/30/90 dias, páginas mais acessadas, busca sem resultado e usuários que nunca entraram.

## Indicadores compostos

```text
aderência = alcance × leitura ativa × ciência × utilidade
risco = criticidade × (1 - alcance) × atualidade × audiência pendente
dívida de conteúdo = acessos recorrentes + buscas relacionadas + feedback negativo + idade sem revisão
valor da informação = pessoas alcançadas × utilidade × criticidade × ação concluída
```

O principal ranking de melhoria continua sendo:

```text
prioridade de melhoria = alcance × taxa de não utilidade × criticidade operacional
```

Isso coloca na frente o conteúdo essencial que é muito usado, mas ainda gera dúvida.

## Modelo técnico de eventos

Criar uma camada de eventos imutáveis e agregados, sem substituir os registros atuais de interação.

### ContentEvent

- usuário ou identificador pseudonimizado;
- organização, empresa, unidade, canal e função no momento do evento;
- tipo, id e versão do conteúdo;
- `event_name`, data/hora e `session_id`;
- metadados limitados e sem conteúdo sensível.

Eventos iniciais:

`platform_login`, `session_started`, `session_ended`, `content_impression`, `content_opened`, `content_active_ping`, `content_scrolled`, `content_video_progress`, `content_attachment_opened`, `content_acknowledged`, `content_feedback_submitted`, `content_question_submitted`, `content_related_opened`, `course_started`, `module_started`, `module_completed`, `course_completed`, `search_submitted` e `search_no_result`.

Regras de coleta:

- não registrar cada movimento do mouse;
- agrupar rolagem;
- heartbeat somente com aba visível e ativa;
- encerrar sessão por inatividade;
- limitar retenção dos eventos brutos;
- manter agregados históricos;
- preservar a mesma permissão de audiência nos relatórios.

## Privacidade e governança

Cada organização deve escolher:

1. **Agregado:** somente grupos acima de um tamanho mínimo.
2. **Pseudonimizado:** investigação por identificador técnico.
3. **Identificado:** somente para funções autorizadas, com justificativa e auditoria.

Regras obrigatórias:

- não exibir comportamento individual em grupos pequenos;
- usar limiar mínimo configurável, recomendado em cinco pessoas;
- registrar quem abriu relatórios sensíveis;
- não usar tempo de leitura como avaliação de desempenho;
- não transformar “não ajudou” em punição;
- informar quais sinais são coletados e por quê.

O Microsoft Viva separa análises pessoais, de equipe, de audiência e de rede, e usa limites de acesso e tamanho de audiência em determinadas visões ([Viva Engage Analytics](https://learn.microsoft.com/en-us/Viva/engage/analytics), [Viva Insights](https://learn.microsoft.com/en-us/viva/insights/introduction)).

## O que aprender com ferramentas líderes

O Amplitude oferece funis, retenção, jornadas, matriz de engajamento e cohorts reutilizáveis. O Talk deve usar essa lógica para comparar unidades, funções e canais, sempre ponderada pela criticidade operacional ([Analytics](https://amplitude.com/docs/analytics), [Cohorts](https://amplitude.com/docs/analytics/define-cohort)).

O Intercom combina visualizações, reações e conversas iniciadas a partir de artigos, recomendando priorizar artigos muito acessados com reações negativas. O Talk adapta esse padrão para conteúdos privados e audiências empresariais ([Article feedback](https://www.intercom.com/help/en/articles/56651-get-quick-article-feedback-with-reactions), [Articles report](https://www.intercom.com/help/en/articles/56653-articles-report)).

## Diferencial do Talk

As ferramentas normalmente separam analytics de produto, base de conhecimento, comunicação e aprendizagem. O Talk pode unir:

- prioridade operacional;
- audiência elegível;
- alcance real;
- leitura ativa estimada;
- ciência obrigatória;
- utilidade percebida;
- dúvida ou bloqueio;
- conclusão de curso ou ação;
- comparação por unidade, função e canal;
- resultado antes e depois de uma correção.

> O Talk mostra não apenas quem recebeu uma comunicação, mas onde ela parou de funcionar: na entrega, na leitura, na compreensão ou na execução.

## Roadmap

### Fase A — Instrumentação

- criar eventos e sessões;
- registrar login e acesso;
- conectar cursos, módulos e conteúdos;
- [x] adicionar feedback aos conteúdos de curso;
- registrar versão do conteúdo;
- aplicar tempo ativo e regras de privacidade.

### Fase B — Console de inteligência

- dashboard executivo;
- relatório de conteúdo;
- relatório de audiência;
- relatório de cursos;
- relatório de acesso à plataforma;
- filtros pela hierarquia empresarial;
- exportação controlada.

### Fase C — Ação

- alertas de alto risco;
- inbox de feedback;
- casos e SLA;
- recomendações de revisão;
- notificações de baixa aderência;
- comparação automática de versões.

### Fase D — Valor comercial

- relatório mensal por cliente;
- evidência antes/depois;
- redução de conteúdo obsoleto;
- redução de dúvidas repetidas;
- alcance de comunicações críticas;
- ROI estimado com premissas explícitas.

## Backlog consolidado de implementação

Esta seção é a lista oficial para não perder as capacidades discutidas durante a evolução das trilhas.

### Entregue nesta primeira implementação

- [x] `ContentEvent` unificado para publicações, cursos, módulos e conteúdos.
- [x] Abertura, leitura ativa, vídeo, anexos, feedback, inscrição e conclusão.
- [x] Modelos de trilha, etapa, atribuição, progresso e recomendação.
- [x] Editor de trilhas no Console com seleção e ordenação de conteúdos.
- [x] Audiência e versão da trilha.
- [x] Pré-requisitos entre etapas.
- [x] Recomendações elegíveis na Home.
- [x] Início formal de trilha pelo usuário.
- [x] Relatório de progresso por atribuição.
- [x] Relatório inicial de métricas de aprendizagem por curso.
- [x] Funil inicial no Console.
- [x] Repositório documental multiempresa com categorias, vigência e audiência.
- [x] Versionamento imutável de documentos com resumo de alteração, vigência/expiração e versão vigente.
- [x] Visualização, download, tempo ativo e auditoria por versão.
- [x] Permissões explícitas por usuário para visualizar, baixar e gerenciar documentos.
- [x] Console e frontend para consulta e gestão documental.
- [x] Documentos publicados aparecem na busca geral com categoria e controle de audiência.
- [x] Fila inicial de conteúdos muito acessados e pouco úteis.
- [x] Comunicação automática no Feed para publicação, atualização e arquivamento de documentos.
- [x] Preferências por usuário e organização para central interna e prioridade mínima.
- [x] Registro de entrega por canal para e-mail e push, com estados pendente, enviada e falhou.
- [x] Consentimento e cadastro de inscrição Web Push por usuário, empresa e navegador.
- [x] Exportação CSV das métricas agregadas de conteúdo com filtros aplicados.

### Próxima frente — operação em escala

- [x] Expandir atribuições de audiência para usuários elegíveis de forma lazy e auditável.
- [x] Recalcular atribuições quando a política, unidade, função ou canal mudar (com revogação reversível e comando `reconcile_trail_assignments`).
- [x] Mostrar impacto estimado antes da confirmação da atribuição.
- [x] Criar página **Minhas trilhas** no frontend.
- [x] Mostrar progresso resumido das trilhas no perfil e na Home.
- [x] Exibir histórico de etapas concluídas e pendentes.
- [x] Permitir feedback privado por etapa concluída.
- [x] Exibir prazos e avisos de atraso.

### Recomendações contextuais

- [x] Recomendar conteúdo relacionado ao final de Feed e Wiki.
- [x] Explicar a origem de cada recomendação.
- [x] Registrar impressão e abertura de recomendações.
- [x] Evitar repetição de recomendações abertas ou dispensadas.
- [x] Recomendar com base em busca sem resultado, dúvidas e feedback negativo.
- [x] Separar recomendação opcional de comunicação obrigatória.

### Analytics avançado

- [x] Funil filtrável por trilha, curso, Feed, Wiki, empresa, unidade, função e canal.
- [x] Abandono por etapa e retorno posterior, com gargalos por etapa e usuários que retornaram à trilha.
- [x] Tempo ativo por conteúdo, módulo e curso.
- [x] Percentual médio de vídeo registrado e uso agregado de anexos nos cursos.
- [x] Comparação entre versões de conteúdo e trilhas (documentos com visualização lado a lado e métricas de uso por versão; trilhas versionadas no editor/progresso).
- [x] Relatório de conteúdos com alto acesso e baixa utilidade.
- [x] Relatório de conteúdos críticos sem leitura registrada.
- [x] Exportação CSV/PDF com permissão e auditoria; ambos registram usuário, organização, filtros e quantidade de linhas.

Implementação atual: o funil do Console (`/console/engagement-funnel/`) exibe alcance, leitores, conclusões e tempo ativo por Feed, Wiki, curso e trilha, com período selecionável (7/30/90/365 dias) e recorte pela hierarquia de audiência, empresa, unidade, canal e função. A página de métricas mantém exportações CSV/PDF auditáveis; o funil serve à comparação operacional e não expõe indivíduos abaixo do limiar de privacidade.

### Cursos e aprendizagem

- [x] Instrumentar quizzes, vídeos e arquivos com granularidade completa.
- [x] Medir início, retomada, abandono inferido por ausência de atenção ativa e conclusão.
- [x] Relacionar cursos e módulos a trilhas por etapas genéricas com ContentType.
- [x] Criar certificados verificáveis e evidências de conclusão.
- [x] Mostrar dificuldades por módulo e questão via eventos de quiz com nota e questões erradas.

### Notificações

- [x] Central de notificações internas.
- [x] E-mail por prioridade e regra de audiência.
- [ ] Push web e mobile com consentimento. Web Push está preparado com inscrição e entrega VAPID; o cliente mobile nativo permanece na camada futura.
- [x] Reenvio controlado de conteúdo crítico não lido via comando `resend_critical_notifications`, com limite e idade mínima configuráveis.
- [x] Preferências por usuário e organização.
- [x] Rastreamento de entrega, abertura interna e falha por canal.

### Governança e ROI

- [x] Redução de dúvidas repetidas: perguntas privadas têm chave normalizada e métrica de repetição para orientar revisão de conteúdo.
- [x] Tempo até localizar uma orientação medido no fluxo de busca e agregado no evento `SEARCH_PERFORMED`.
- [x] Relação entre conclusão e ação operacional por evento `ACTION_COMPLETED`, com endpoint provider-neutral para integrações.
- [x] Comparativo antes/depois de uma correção de conteúdo por versões, com uso, leitores, tempo ativo e downloads comparáveis.
- [x] Relatórios para gestores por nível hierárquico, limitados pelos `ManagementAssignment` e escopo de organização/unidade.
- [x] Limiar mínimo para relatórios agregados, configurável por `ANALYTICS_MIN_GROUP_SIZE`.
- [x] Pseudonimização e auditoria de relatórios identificados (exportações registradas no Console).
- [x] Retenção e anonimização de eventos via comando `anonymize_learning_events`.

### Critérios de conclusão do plano

O plano só será considerado completo quando um gestor conseguir:

1. criar uma trilha com audiência, etapas, dependências e versão;
2. atribuí-la a uma audiência e visualizar o impacto estimado;
3. acompanhar usuários elegíveis sem expor grupos pequenos;
4. receber recomendações explicáveis e medir sua aceitação;
5. identificar abandono, baixa utilidade e baixa leitura;
6. notificar apenas o que exige atenção;
7. demonstrar resultado operacional com período, denominador e premissas de ROI.

## Métricas que nunca devem aparecer isoladas

Não usar como prova única: número bruto de visualizações, tempo de tela sem atividade, ranking individual, cliques sem contexto ou “usuário ativo” sem definição de ação. Todo painel deve mostrar período, denominador, tamanho da audiência, definição da métrica e nível de confiança.
