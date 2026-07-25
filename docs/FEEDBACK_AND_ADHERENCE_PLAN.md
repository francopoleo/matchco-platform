# Talk — Feedback e Aderência da Informação

**Data:** 2026-07-24  
**Status:** Diretriz de produto para implementação

## Objetivo

Transformar cada conteúdo do Talk em um ponto de aprendizagem operacional: o usuário informa, de maneira simples e privada, se a informação ajudou; a gestão usa os sinais para corrigir conteúdo, reduzir dúvidas e aumentar a aderência.

O recurso não é uma rede social nem um mural de comentários. É um mecanismo controlado de qualidade e melhoria contínua.

## Hierarquia de informação

O Talk não deve criar um volume artificial de Feed. Cada conteúdo precisa declarar sua importância:

- **Rotina:** informação útil, sem interromper a jornada.
- **Importante:** mudança que exige atenção no ciclo normal de trabalho.
- **Crítica:** informação que pode afetar o dia da operação e deve aparecer como alerta.

Também deve declarar sua natureza: atualização, mudança de procedimento, atualização de documento, documento obrigatório, conteúdo obsoleto, alerta operacional ou comunicado.

Conteúdos críticos ou que exigem ciência permanecem destacados na Home até serem abertos e reconhecidos. O lembrete pode ser repetido conforme a política do cliente, sem transformar toda publicação em push.

Exemplos de conteúdo crítico:

- mudança de procedimento;
- alteração de documento obrigatório;
- documento ou protocolo obsoleto;
- indisponibilidade ou problema operacional;
- manutenção que afeta uma unidade;
- orientação de segurança ou conformidade.

## Ranking da Home

O ranking não será um concurso de popularidade. Ele deve priorizar o que precisa ser lido:

```text
prioridade = importância + não lido + atualidade + criticidade operacional
```

Para a gestão, o ranking de melhoria combina alcance e utilidade:

```text
prioridade de melhoria = visualizações × taxa de não utilidade × criticidade operacional
```

Assim, um documento muito acessado e pouco útil fica acima de uma publicação popular, mas sem impacto operacional.

## Push web e lembretes

O primeiro nível é persistente e já deve funcionar dentro da Home: alertas críticos não lidos continuam destacados até a leitura/ciência.

O segundo nível é push no navegador desktop e mobile:

1. registrar o dispositivo com um Service Worker;
2. solicitar permissão somente após uma ação clara do usuário;
3. armazenar a assinatura por usuário, dispositivo e organização;
4. enviar somente conteúdos críticos ou lembretes autorizados;
5. cancelar ou renovar assinaturas inválidas;
6. respeitar horário, frequência, expiração e preferências do usuário.

O envio requer chaves VAPID e um provedor de Web Push no backend. O push é complemento do alerta persistente, nunca o único lugar onde uma informação crítica aparece.

## Experiência do usuário

Após uma Wiki, publicação, curso ou conteúdo relevante:

> Esta informação ajudou?

Respostas rápidas:

- Sim, ajudou
- Parcialmente
- Não ajudou

Para respostas parcial ou negativa, mostrar uma etapa curta e opcional:

- O que faltou?
- Estava desatualizada?
- Não estava claro?
- Foi difícil encontrar a resposta?
- Preciso de outro tipo de ajuda

Também pode existir um campo livre opcional, com limite de tamanho e sem exposição pública.

## Privacidade e escopo

- Nenhum comentário aparece para outros usuários.
- O autor do conteúdo não vê automaticamente a identidade do usuário.
- O sistema pode operar em modo identificado, pseudonimizado ou agregado conforme política do cliente.
- O gestor só visualiza sinais de organizações, unidades, funções e canais que administra.
- Feedback não é canal de emergência, denúncia, suporte clínico ou solicitação urgente.
- Em conteúdos de saúde, a interface deve indicar o canal adequado para atendimento profissional.

## Modelo conceitual

### FeedbackSignal

- `content_type` e `content_id`
- `content_version`
- `organization`, `company`, `unit`, `business_channel`, `function`
- `actor` opcional e modo de privacidade
- `rating`: helpful, partial, not_helpful
- `reason` opcional
- `comment` opcional
- `created_at`

### FeedbackCase

Quando a política do cliente exigir tratamento, o sinal pode gerar um caso privado:

- responsável
- status: recebido, em análise, ação planejada, resolvido, descartado
- prioridade e prazo
- observação interna
- conteúdo/versão corrigida
- histórico de alterações

## Fluxo de gestão

1. Registrar a reação junto com o conteúdo, versão e contexto de audiência.
2. Agregar os indicadores por conteúdo, versão, unidade, função e organização.
3. Criar caso somente para sinais que precisem de ação ou para regras de volume/prioridade.
4. Encaminhar ao gestor responsável, sem expor a audiência inteira.
5. Publicar nova versão ou complementar a informação.
6. Comparar o resultado antes e depois da correção.

## Métricas

- Taxa de utilidade por conteúdo.
- Conteúdos com alto acesso e baixa utilidade.
- Distribuição de motivos de insatisfação.
- Tempo médio até triagem e resolução.
- Redução de feedback negativo após nova versão.
- Diferença entre unidades, funções, canais e organizações.
- Relação entre utilidade, conclusão de curso, busca e retorno ao conteúdo.

### Indicador prioritário

Priorizar conteúdos com a combinação:

```text
prioridade = alcance × taxa de não utilidade × criticidade operacional
```

Isso evita gastar esforço em conteúdos pouco usados enquanto materiais essenciais continuam gerando dúvida.

## Roadmap

### Lacuna registrada — cursos

O mecanismo inicial de abertura, feedback e métricas foi conectado às publicações Feed/Wiki. Os cursos ainda precisam registrar abertura do curso, módulo e conteúdo, tempo ativo estimado, vídeo, anexos, progresso, abandono, conclusão e feedback. A especificação está em [CONTENT_INTELLIGENCE_ANALYTICS_PLAN.md](CONTENT_INTELLIGENCE_ANALYTICS_PLAN.md).

### Fase 1 — MVP

- Reação “ajudou / parcialmente / não ajudou”.
- Motivo opcional para respostas negativas.
- Privacidade e permissão por audiência.
- Lista de feedback no console.
- Métricas básicas por conteúdo e versão.
- Instrumentar cursos, módulos e conteúdos com o mesmo modelo de interação.

### Fase 2 — Melhoria contínua

- Inbox por gestor/responsável.
- Casos com status, prioridade e prazo.
- Resposta privada ao usuário quando permitido.
- Comparação entre versões.
- Notificação de conteúdo com queda de utilidade.

### Fase 3 — Enterprise

- SLA por tipo de conteúdo.
- Workflow por organização, unidade e canal.
- Integração com suporte, chamados e notificações.
- Relatórios de aderência e ROI.
- Exportação auditável e retenção configurável.

## Referências de padrão

O padrão se inspira em centrais de conhecimento enterprise que combinam reação rápida, investigação privada e análise por artigo. O Intercom, por exemplo, registra reações por artigo, pode iniciar uma conversa após uma reação negativa e recomenda priorizar conteúdos de alto tráfego com reações negativas: [Quick article feedback with reactions](https://www.intercom.com/help/en/articles/56651-get-quick-article-feedback-with-reactions).

O Talk adapta esse padrão para organizações com hierarquia de audiência, unidades, funções e canais, mantendo o controle institucional e evitando exposição de comentários.
