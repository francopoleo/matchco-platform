# Validação: Promessas Comerciais vs Plano Técnico

Atualização 2026-11-18: a visualização da mídia na edição deve usar a rota protegida do Console, inclusive para rascunhos e itens em aprovação; a rota pública permanece restrita a conteúdo aprovado/publicado. Validar tenant ativo, empresa, usuário gestor, arquivo local e URL externa.

Atualização visual: breadcrumbs do Console são uma linha discreta fora dos cards, no formato `grupo > página`; a página de primeiro nível da organização não repete breadcrumb. Validar esse contrato nas páginas de organização, integrações e cargos.

**Data:** 2026-10-09  
**Status:** plano canônico SaaS em execução incremental  
**Escopo:** QR por unidade, Perfil permanente, intenção contextual e Match bilateral

Este documento transforma as promessas comerciais em regras técnicas verificáveis.
O produto deve ajudar a pessoa e a loja a se encontrarem sem transformar o
Shopping ou a loja em donos de uma base nominal, sem currículo disfarçado e sem
ranking de pessoas.

> **Precedência deste plano:** a partir desta revisão, a seção **Plano canônico
> de execução SaaS unificado** é a referência para o desenvolvimento. As fases
> antigas abaixo preservam decisões de produto, mas não autorizam uma segunda
> hierarquia de recrutamento, uma jornada com CV ou seeds de outras empresas.
> Como não há legado de produção, o ambiente será recriado diretamente no
> modelo canônico com **Bourbon Shopping**, **Rede Drogasil** e **ElectraTech**;
> cada organização de demonstração permanece isolada.

## 1. Regras comerciais que o sistema deve preservar

### 1.1 Uma porta Match por unidade

Cada loja/unidade operacional possui um QR Match permanente e reutilizável para
vagas de alto giro. A entrada é sem currículo, portfólio ou documentação; a
necessidade da loja e o Perfil estruturado conduzem a distribuição.

O sistema pode ter vários Pontos no território — vitrine, balcão, corredor,
fachada ou transporte — mas cada unidade deve ter uma identidade de QR estável.
O QR não representa necessariamente uma vaga aberta e não deve ser recriado a
cada necessidade.

Regras técnicas:

- `EntryPoint` Match da unidade é reutilizado entre necessidades e há no máximo
  um ativo para a operação;
- a origem registra unidade, ponto e campanha, sem criar propriedade sobre a pessoa;
- não criar um QR novo para cada vaga ou questionário;
- o QR Match da unidade é genérico: não representa uma função, uma vaga ou uma
  loja exclusiva;
- a entrada por uma unidade apresenta o catálogo canônico de funções habilitado
  para todo o Shopping/tenant, e não apenas as funções daquela unidade;
- o candidato não deve responder uma pergunta escolhendo Shopping, rede ou loja;
- o QR registra origem e o contrato do Shopping define o território de circulação;
- a unidade de origem pode receber uma preferência contextual suave, sem bloquear
  oportunidades de outras lojas;
- o cadastro pode chegar por um QR de loja, mas a intenção só aponta para uma
  necessidade específica quando o candidato decide continuar.

### 1.2 A iniciativa começa na loja

“A loja procura” não significa que a loja abre uma lista e pesquisa candidatos.
Significa que a loja declara uma necessidade real e o sistema distribui essa
oportunidade para pessoas elegíveis.

O fluxo canônico é:

```text
Loja declara necessidade
        ↓
Sistema entrega a oportunidade a pessoas elegíveis
        ↓
Pessoa demonstra interesse
        ↓
Loja vê somente essas pessoas
        ↓
Loja também demonstra interesse
        ↓
MATCH
```

No exemplo de uma pessoa que escaneia o QR de uma loja Claro e informa que quer
trabalhar como caixa:

- o QR registra a origem, mas não torna a pessoa propriedade da Claro;
- a função “caixa” entra no Perfil como preferência profissional;
- a política territorial do Shopping pode permitir que outra loja declare uma
  necessidade compatível;
- o sistema entrega a oportunidade à pessoa;
- a loja só vê a pessoa depois que ela demonstra interesse naquela necessidade.

Não criar tela para a loja pesquisar “todos os candidatos”. O algoritmo faz a
distribuição das oportunidades, sem LLM e sem ranking de pessoas.

### 1.3 Perfil permanente, intenção contextual

O Perfil da pessoa permanece. Ele não deve nascer novamente a cada oportunidade.

Cada necessidade real cria uma nova relação e, quando aplicável, uma nova
resposta contextual. A resposta contextual nunca deve copiar respostas antigas.

Assim, o sistema separa:

- **Perfil:** o que a pessoa gostaria de fazer, onde e quando consegue trabalhar,
  experiências práticas e se aceita primeiro emprego;
- **Intenção:** interesse da pessoa naquela necessidade, naquela unidade e
  naquela versão das condições;
- **Resposta contextual:** perguntas práticas daquela necessidade, respondidas
  novamente quando o candidato decide continuar;
- **Relation:** estado bilateral entre pessoa e necessidade.

### 1.4 A intenção precisa ser específica

Não basta registrar que a pessoa “tem interesse na loja”. O interesse deve estar
ligado a uma necessidade concreta:

- unidade/loja;
- oportunidade ou necessidade;
- função ou atividade;
- versão das condições apresentadas;
- horário, local e data de início, quando aplicáveis;
- ponto de entrada que originou o contato.

Se a loja ainda não declarou uma necessidade, o QR pode criar ou atualizar o
Perfil, mas não deve criar uma intenção de contratação genérica.

### 1.5 A loja não pesquisa uma base

A loja não recebe uma lista nominal para pesquisar. Ela começa por uma
necessidade real e vê somente pessoas que demonstraram interesse naquela
relação, com as informações autorizadas e relevantes para decidir se também
quer continuar.

O Shopping não recebe uma base nominal e não se torna proprietário dos dados.

### 1.6 Não existe ranking de pessoas

O sistema não deve criar score comparativo, percentual de compatibilidade, Top N,
ordenação por “melhor candidato”, selo de excelência ou fila privilegiada.

Isso não impede a operação de ler melhor as relações. A leitura deve ser feita
com filtros e agrupamentos explicáveis, sem comparar pessoas entre si.

## 2. Estados de visibilidade e decisão

A visibilidade deve seguir a máquina de estados da `Relation`.

| Estado | O que acontece | O que a loja pode ver |
|---|---|---|
| `NOTICE_DELIVERED` | A necessidade pode chegar à pessoa | Nada nominal para a loja |
| `PERSON_INTERESTED` | A pessoa demonstra interesse naquela necessidade | Projeção limitada e autorizada |
| `EMPLOYER_INTEREST_VIEW` | A loja abriu a projeção para decidir | Somente informações relevantes à decisão |
| `EMPLOYER_INTERESTED` | A loja também decide continuar | Estado bilateral registrado |
| `MATCHED` | Interesse dos dois lados suficiente | Contato pode ser habilitado |
| `CONTACT_ENABLED` | Conversa direta liberada | Pessoa e loja conduzem a conversa |

O estado `EMPLOYER_INTEREST_VIEW` não é bilateral. Bilateralidade começa quando
a loja manifesta interesse. O contato direto só pode ser liberado em `MATCHED`
ou em estado posterior autorizado.

## 3. Como melhorar a leitura sem ranking

Para a loja, a tela da necessidade deve mostrar relações agrupadas por sinais
objetivos e não por uma nota global:

- função/atividade desejada;
- disponibilidade de dias e período;
- distância ou região informada;
- possibilidade de início;
- experiência prática diretamente relacionada à necessidade;
- aceite de primeiro emprego ou disposição para aprender;
- origem do Ponto/QR;
- tempo desde a demonstração de interesse;
- estado da relação e próxima ação permitida.

Esses filtros devem ser combináveis, auditáveis e neutros. A ordem padrão deve
ser por evento ou estado — por exemplo, interesse mais recente — nunca por
qualidade presumida da pessoa.

É permitido mostrar contagens operacionais, como “12 pessoas demonstraram
interesse” ou “4 aguardam decisão da loja”. Não é permitido transformar essas
contagens em classificação individual.

## 4. Perfil sem currículo

As perguntas devem explicar uma possibilidade real de trabalho, por exemplo:

- Você já realizou alguma atividade parecida?
- Que tipo de tarefa gostaria de fazer?
- Em quais dias e horários consegue trabalhar?
- Quando poderia começar?
- Você aceita aprender a atividade no local?

Não devem ser usadas como triagem curricular perguntas sobre escolaridade,
certificações, salário pretendido, ferramentas específicas, histórico detalhado
ou tempo no último emprego.

Regras técnicas:

- máximo recomendado de 6 perguntas práticas por experiência;
- tipos permitidos: texto curto, texto longo, escolha, sim/não e data;
- revisão operacional antes da publicação;
- auditoria de criação, alteração, publicação e arquivamento;
- perguntas antigas permanecem vinculadas à versão que foi respondida;
- uma nova visita nunca recebe respostas anteriores como valor inicial.

O limite de seis perguntas é uma regra de simplicidade operacional, não uma
promessa comercial isolada. O conteúdo deve continuar sendo revisado pelo
significado, não apenas pela quantidade.

## 5. Modelo de dados recomendado

### EntryPoint

- um registro ativo de QR Match por unidade para recrutamento de alto giro, sem CV;
- QR híbrido, shopping ou rede não substitui os dois pontos da loja; se houver
  campanhas institucionais, elas são entradas fora da unidade e não contam como
  porta de recrutamento da loja;
- Pontos físicos adicionais podem existir, mas devem representar superfícies de
  entrada distintas e manter a mesma unidade responsável;
- origem, campanha e localização são rastreamento, não propriedade.

### CandidateProfile

Mantém o Perfil permanente da pessoa. Não deve conter uma intenção específica
de uma vaga como se ela fosse global.

### CandidateSignupAnswer

Registra uma resposta contextual nova:

- `candidate`;
- `organization`;
- `business_unit`;
- `entry_point` de origem;
- `questionnaire_template` e versão;
- `relation`, quando já existente;
- snapshot do estado da relação no momento da resposta;
- respostas;
- datas de solicitação e conclusão de exclusão LGPD.

Cada submissão é preservada como contexto histórico e não substitui a anterior.

### Relation

Deve ligar a pessoa à necessidade específica, incluindo a versão da necessidade.
O Match depende de interesse dos dois lados e não de uma pontuação calculada.

## 6. Controles de segurança e autoridade

### Loja

A loja só pode acessar relações associadas às suas unidades e que já tenham
`PERSON_INTERESTED`. O retorno deve ser uma projeção limitada. A loja não pode:

- listar todos os perfis da organização;
- pesquisar candidatos sem uma necessidade;
- exportar uma base nominal;
- ordenar por score ou compatibilidade;
- acessar respostas de outra unidade;
- acessar campos não autorizados antes do Match.

### Shopping

O Shopping pode acompanhar instalação, operação, Pontos, origem agregada e
métricas territoriais. Não pode consultar uma lista nominal de pessoas nem
assumir prioridade ou propriedade sobre elas.

### Auditoria

Registrar `RecruitmentAuditEvent` para:

- acesso a uma projeção de relação;
- abertura de dados após `PERSON_INTERESTED`;
- habilitação de contato após `MATCHED`;
- tentativa de listar candidatos sem relação;
- tentativa de exportação, busca ampla ou acesso fora da unidade;
- criação e alteração de perguntas;
- solicitação e conclusão de exclusão LGPD.

Tentativas fora da autoridade devem gerar `AUTHORITY_VIOLATION` sem expor os
dados solicitados.

## 7. LGPD e direito ao esquecimento

Ao concluir uma exclusão de dados da pessoa:

- anonimizar ou excluir o Perfil conforme a política aplicável;
- remover ou anonimizar respostas contextuais;
- remover referências pessoais das projeções;
- preservar somente o evento de auditoria mínimo exigido, sem conteúdo pessoal
  desnecessário;
- manter a rastreabilidade agregada da origem sem transformar a origem em
  identificação nominal.

## 8. Checklist de aceite

### 8.1 Checklist visual reutilizável do Console

- [ ] Breadcrumb discreto fora de cards, no formato “grupo > página”.
- [ ] Primeiro nível do breadcrumb sem link e sem repetição como eyebrow.
- [ ] Um único `h1`: `text-2xl` no mobile e `sm:text-3xl` em telas maiores; não usar `lg:text-4xl` no Console.
- [ ] Subtítulo curto, controles Flowbite e raios pequenos; evitar pílulas em botões e campos.
- [ ] KPIs com ícone SVG, cor semântica e valores legíveis.
- [ ] Tabelas responsivas, filtros alinhados e checkboxes quadrados com cantos suaves.
- [ ] Linhas de tabela usam `bg-neutral-primary-soft`/`divide-default` ou tokens equivalentes; não usar `odd:bg-neutral-primary` e `even:bg-neutral-secondary-soft` sem uma regra explícita para o dark mode.
- [ ] KPIs usam o componente compartilhado com ícone SVG, cor semântica, label curto, valor legível e hint opcional; não criar cards KPI paralelos por página.
- [ ] Abas usam o padrão Flowbite de `border-b`, `-mb-px`, `p-3/p-4`, estado ativo com `border-brand`/`text-fg-brand` e estado inativo legível; não usar abas como botões-pílula.
- [ ] Uma função ou auditoria aparece uma única vez no menu; URLs legadas devem redirecionar para a página canônica, não duplicar a entrada.
- [ ] Dark mode com contraste mínimo para títulos, textos auxiliares, inputs e menus.
- [ ] Testar mobile, claro, escuro, estado vazio, erro e sucesso antes de concluir a tela.

- [x] Cada unidade possui um QR Match permanente e reutilizável para alto giro.
- [x] O domínio público dos QR Codes é configurável por ambiente (`QR_CODE_BASE_URL`), sem alterar a identidade da entrada.
- [ ] Necessidades novas reutilizam o QR da unidade.
- [ ] O candidato demonstra intenção para uma necessidade específica.
- [ ] O Perfil permanece entre oportunidades.
- [ ] Nova resposta contextual começa sem pré-preenchimento.
- [ ] A loja só vê uma projeção depois de `PERSON_INTERESTED`.
- [ ] A projeção não vira banco pesquisável.
- [ ] O contato só é liberado depois de `MATCHED`.
- [ ] Não existe ranking, score comparativo, Top N ou ordenação por qualidade.
- [ ] A leitura usa filtros e agrupamentos explicáveis.
- [ ] Perguntas práticas não viram currículo ou screening.
- [ ] O Shopping não recebe lista nominal.
- [ ] Origem do QR é rastreada sem propriedade sobre a pessoa.
- [ ] Exclusão LGPD cobre Perfil e respostas contextuais.
- [ ] Auditoria registra acessos, alterações e violações de autoridade.

## 9. Roadmap técnico revisado

| Fase | Entrega | Critério de aceite |
|---|---|---|
| 0 | Auditoria do fluxo atual | identificar listagens, scores e buscas amplas |
| 1 | Uma porta Match permanente por unidade | um QR Match sem CV, reutilizado entre necessidades; não existe QR Vaga ou modo híbrido |
| 2 | Intenção por necessidade | nenhuma intenção genérica de loja |
| 3 | Projeção por estado | loja vê apenas após interesse da pessoa |
| 4 | Leitura operacional sem ranking | filtros explicáveis e sem score comparativo |
| 5 | Questionário prático versionado | até 6 perguntas, revisão e sem pré-preenchimento |
| 6 | Auditoria e RBAC | violações registradas e dados limitados por unidade |
| 7 | Exclusão LGPD | Perfil e respostas contextuais tratados em conjunto |
| 8 | QA comercial | cenários de QR, intenção, Match, Shopping e loja |
| 9 | Feature flag | ativação controlada por organização/unidade |

## 10. Jornada externa de recrutamento de alto giro

O recrutamento ativo possui uma única jornada externa Match, sem currículo.

### 10.1 Jornada MatchCo sem currículo — iniciada por QR

Esta é a jornada principal para shopping, loja, rede e campanhas territoriais:

```text
QR externo /qr/<entry_point>
        ↓
Página pública da unidade ou campanha
        ↓
Telefone ou e-mail verificado
        ↓
Perfil existente recuperado ou Perfil novo criado
        ↓
Nova entrada registrada no histórico
        ↓
Formulário curto sem CV
        ↓
Perguntas contextuais versionadas
        ↓
Circulação territorial autorizada
        ↓
Oportunidades entregues e decisão da pessoa
```

Regras de aceite:

- telefone ou e-mail verificado identifica a pessoa no primeiro cadastro;
- CPF não é obrigatório para deduplicação ou distribuição;
- um Perfil existente nunca gera outro Perfil apenas porque a pessoa escaneou
  outro QR;
- cada novo QR registra unidade, origem, campanha, território e data no
  histórico;
- a nova experiência pode fazer novas perguntas, mas não sobrescreve respostas
  contextuais anteriores;
- a página não exige currículo, upload de documento ou histórico profissional
  completo;
- a loja nunca recebe o contato pessoal apenas por causa do cadastro;
- a pessoa pode pausar ou revogar circulação e campanhas adicionais.

### 10.2 Fluxo de currículo retirado

As rotas, modelos, uploads, QRs e páginas de currículo estão fora do produto
ativo. Não há jornada formal híbrida nem distribuição por currículo. Como não há
legado de produção, a limpeza de desenvolvimento deve remover dados e fixtures
desse fluxo, sem criar compatibilidade que reabra a porta.

## 11. Reutilização do Perfil e histórico de entradas

O `CandidateIdentity` é a referência global de deduplicação. O sistema precisa
complementá-lo com um histórico de contexto, por exemplo `CandidateContextEntry`:

- identidade e Perfil relacionado;
- `EntryPoint`, unidade, organização e campanha;
- segmento e território autorizado;
- data da primeira e da última entrada;
- versão dos consentimentos apresentados;
- status da experiência, sem criar propriedade sobre a pessoa.

`CandidateSignupAnswer` continua sendo o registro imutável das respostas. Cada
resposta deve guardar origem, finalidade, segmento, versão do questionário,
consentimento e oportunidade/relação quando existir.

O Perfil global deve conter apenas sinais reutilizáveis e autorizados. Uma
resposta específica de farmácia, alimentação ou uma unidade não deve alterar
silenciosamente a história anterior nem se tornar uma verdade global sem revisão
de finalidade.

## 12. Cobertura insuficiente e campanhas de enriquecimento

Quando uma necessidade não tiver pessoas elegíveis em quantidade suficiente, o
sistema não deve abrir uma lista nominal nem relaxar regras silenciosamente. Deve
registrar uma lacuna operacional:

```text
Necessidade aberta
        ↓
Elegíveis, entregues e interessados são contados
        ↓
Cobertura abaixo do mínimo configurado
        ↓
Lacuna de cobertura criada
        ↓
Campanha opcional para pessoas elegíveis com dados faltantes
        ↓
Resposta versionada e novo cálculo de elegibilidade
```

Uma campanha pode perguntar, por exemplo:

- aceita fechamento ou domingo alternado?
- pode começar em determinada data?
- aceita aprender uma função próxima?
- já realizou uma atividade prática relacionada?
- aceita oportunidades em outro território autorizado?

O texto correto é “responder pode ajudar a encontrar mais oportunidades
compatíveis”. Nunca prometer contratação, prioridade ou aumento de score.

Entidades recomendadas:

- `CoverageGap`: necessidade, contagens, limiar, motivo e estado;
- `EnrichmentCampaign`: finalidade, público, segmento, versão e validade;
- `EnrichmentInvitation`: pessoa, campanha, consentimento e entrega;
- `EnrichmentResponse`: pergunta, resposta, origem, versão e data.

## 13. Pré-onboarding contextual

O pré-onboarding pode ser oferecido quando a unidade marca uma necessidade como
`PODE_APRENDER` ou `SERIA_BOM`. Ele deve ser opcional ou explicitamente
obrigatório para aquela oportunidade, nunca uma exigência escondida para entrar
na base.

A atribuição deve ser contextual, por exemplo `PreboardingAssignment`, ligada a:

- pessoa;
- segmento, organização e unidade;
- oportunidade ou relação;
- programa/trilha e versão;
- finalidade e consentimento;
- status e evidência de conclusão.

Concluir uma trilha gera uma evidência contextual. Não altera automaticamente a
qualidade da pessoa, não cria score e não libera dados para outras lojas sem
finalidade compatível.

## 14. Critérios de aceite adicionais

- [ ] QR externo recupera Perfil existente por telefone/e-mail verificado.
- [ ] Novo QR registra histórico sem substituir a origem anterior.
- [ ] Cadastro MatchCo não exige currículo.
- [ ] Jornada formal com currículo tem página, consentimento e retenção próprios.
- [ ] Respostas de campanhas são imutáveis, versionadas e contextualizadas.
- [ ] Sistema identifica lacuna de cobertura sem relaxar regras automaticamente.
- [ ] Campanhas de enriquecimento são opcionais, pausáveis e auditáveis.
- [ ] Pré-onboarding pode ser associado a segmento, unidade ou oportunidade.
- [ ] Conclusão de curso ou trilha não cria score nem ranking.
- [ ] Nenhuma loja acessa dados de outra jornada sem autorização e finalidade.

## 15. Origem privada e circulação por segmento

O QR de uma marca ou loja pode personalizar a experiência sem revelar a origem
para outras empresas. Esse é o tratamento necessário para uma Drogasil que entra
por um shopping, mas deseja também circular oportunidades para outras farmácias
participantes.

### 15.1 O que o QR pode fazer

- selecionar um questionário de farmácia;
- registrar unidade, campanha, território e conversão;
- criar preferência operacional suave pela região de entrada;
- registrar que a pessoa teve contato com o segmento de farmácias;
- alimentar métricas internas autorizadas.

### 15.2 O que o QR não pode fazer

- tornar a pessoa propriedade da Drogasil ou do shopping;
- impedir oportunidades de outras farmácias autorizadas;
- revelar a outra farmácia a origem Drogasil da pessoa;
- compartilhar treinamento, sistema ou processo interno da rede;
- transformar origem em score, ranking ou critério oculto.

### 15.3 Escopos de resposta

Cada resposta contextual deve declarar seu escopo de reutilização:

| Escopo | Exemplo | Circulação |
|---|---|---|
| Global | dias, período, início e região ampla | oportunidades autorizadas compatíveis |
| Segmento | experiência em farmácia, caixa ou estoque | outras farmácias, quando a finalidade permitir |
| Organização | sistema, treinamento ou processo Drogasil | somente Drogasil e finalidade correspondente |
| Unidade | rotina específica daquela loja | somente a unidade ou relação correspondente |

O candidato não precisa responder “quero trabalhar na Drogasil” para ser elegível
em outras farmácias. A pergunta deve ser sobre o segmento e as atividades: “Você
tem interesse em trabalhar em farmácias?” ou “Quais atividades você aceitaria
realizar?”.

### 15.4 Regra de produto

```text
Origem personaliza a experiência
        ↓
Consentimento define a circulação
        ↓
Interesse da pessoa define a visibilidade
        ↓
Match define o contato
```

Essa regra vale para shopping, rede regional, rede nacional e qualquer novo
segmento. A organização da marca pode ter administração própria e questionário
próprio, mas não cria uma segunda identidade de candidato.

## 16. Roadmap de execução controlada

Esta seção transforma a análise em uma sequência de implementação. Uma fase só
pode ser marcada como concluída quando houver código, migração quando necessária,
testes, documentação central e validação de permissões. Documentar uma decisão
não significa que ela já esteja implementada no SaaS.

### Fase 0 — Auditoria e contrato do produto · CONCLUÍDA

- [x] Consolidar o fluxo comercial sem ranking.
- [x] Separar MatchCo sem CV de vaga formal com CV.
- [x] Definir origem privada e circulação por segmento.
- [x] Mapear shopping, rede, empresa, unidade, Talk e audiências.
- [x] Identificar caminhos legados de score, ranking e duplicação.
- [x] Atualizar a documentação HTML e este plano.

### Fase 1 — Identidade única e histórico de contexto · CONCLUÍDA

- [x] Definir a chave de identidade por e-mail e telefone normalizados; conflito
  entre contatos não é mesclado automaticamente.
- [x] Implementar recuperação idempotente do Perfil existente no fluxo Match sem CV.
- [x] Criar `CandidateContextEntry` para QR, unidade e campanha, com contagem de
  reentrada e última visita.
- [x] Impedir duplicação quando a pessoa entra novamente pela mesma unidade/QR ou
  por outra porta da mesma organização.
- [x] Preservar a origem anterior sem exibi-la a outras lojas.
- [x] Criar testes de reentrada por e-mail, telefone, QR repetido e conflito de
  contatos.
- [x] Reutilizar o OTP existente para registrar `verified_at` quando a pessoa
  comprova a posse do telefone no acesso público.
- [x] Exigir a confirmação OTP também no primeiro envio do formulário Match sem CV;
  o Perfil só é persistido depois da comprovação do telefone.
- [x] Aplicar as migrações `0037` e `0038` no ambiente de desenvolvimento. A
  restrição de QR ativo passa a ser uma porta Match por unidade; não existe
  segunda porta de currículo ativa.

### Fase 2 — Organização, rede, unidade e programa · CONCLUÍDA

- [x] Mapear a autoridade existente entre `Organization`, `Company`,
  `BusinessUnit`, `RecruitmentOrganization` e `RecruitmentStore`; a revisão
  canônica deste plano substitui a hierarquia paralela de recrutamento por uma
  estrutura SaaS única.
- [x] Criar vínculo de unidade física com múltiplos programas/contratos por
  `ProgramUnitScope`, sem duplicar a unidade física.
- [x] Permitir shopping, rede nacional e unidade participarem sem duplicar pessoa
  ou unidade física, usando `RecruitmentPhysicalUnit` e representações por
  organização.
- [x] Definir escopo por organização, empresa, canal, unidade e programa, com
  relações explícitas entre organizações e `ProgramUnitScope`.
- [x] Criar ponte explícita para o contexto compartilhado da plataforma por
  `RecruitmentPlatformBinding`, sem FK entre schemas e sem concessão automática
  de acesso.
- [x] Integrar a projeção ao avaliador central de Audience sem substituir a
  autorização de Membership.
- [x] Conectar o seletor de cursos ao avaliador contextual quando uma jornada
  aprovada envia `recruitment_platform_context` na sessão.
- [x] Criar adaptadores de sinais para conclusão de curso, certificação e
  interação Talk, exigindo capacidade do binding e consentimento específico.
- [x] Fazer os eventos automáticos de curso e certificação resolverem o binding
  da organização do Perfil antes de criar sinais contextuais.
- [x] Propagar o contexto para a sessão ao entrar por QR ou acesso direto de
  programa, permitindo que links de conteúdo usem a mesma projeção.
- [x] Atualizar Talk, recrutamento, cursos e certificações para consumirem essa
  projeção nos seus respectivos motores de Membership/Audience.

O contrato de autoridade e a sobreposição comercial estão implementados:
`RecruitmentPhysicalUnit` representa o local real, `RecruitmentStore` representa
o local dentro de uma organização, `RecruitmentOrganizationRelation` registra a
relação entre shopping, rede, marca ou parceira, e `ProgramUnitScope` registra a
participação em cada programa. A ponte `RecruitmentPlatformBinding` e o serviço
`resolve_platform_context` alimentam Audience e cursos; os adaptadores de curso,
certificação e Talk recusam eventos contextualizados quando a capacidade não foi
autorizada ou o consentimento não existe. O Talk guarda apenas metadados mínimos
da interação, nunca o texto da conversa.
O avaliador central já aceita essa projeção por
`can_view_with_recruitment_context`; os pontos de entrada de cada módulo ainda
passam o contexto explicitamente em suas jornadas; a listagem e o detalhe de
cursos usam a projeção pela sessão e o evento real do Talk gera apenas o sinal
consentido.

### Fase 3 — Entrada aprovada e Membership hierárquico · CONCLUÍDA

- [x] QR e convite criam uma `ControlledAccessRequest`, nunca acesso automático.
- [x] Persistir estados `invited`, `requested`, `pending_approval`, `approved`,
  `active`, `suspended`, `revoked` e `expired`.
- [x] Definir o nível exigido a partir do escopo: organização, empresa/rede,
  unidade ou programa; o aprovador precisa ter autoridade AA-3 no escopo ou ser
  administrador autorizado.
- [x] Registrar aprovador, escopo, data, motivo, validade e revogação em
  `ControlledAccessRequest` e `AccessApprovalEvent`.
- [x] Impedir que `ProgramInvite` e `LojistaInvite` ativem Membership/EmployerActor
  antes da aprovação.
- [x] Reutilizar a conta/identidade existente e provisionar Talk apenas depois
  da aprovação; nenhum usuário duplicado é criado.
- [x] Bloquear a abertura do WebSocket Talk sem Membership operacional ou
  solicitação controlada ativa.

O fluxo aprovado é: `QR/convite → solicitação → aprovação no escopo correto →
provisionamento mínimo → acesso`. A aprovação administrativa está disponível
no console por ação explícita; toda decisão deixa evento de auditoria. A entrada
de candidato da Porta Match continua pública e não recebe Membership de Talk:
ela registra contexto e consentimento de recrutamento, enquanto QR/convite de
programa, Talk, parceiro ou lojista seguem o caminho controlado.

### Fase 4 histórica — Duas jornadas externas · ENCERRADA

- [x] Página pública MatchCo sem CV iniciada pelo QR, com OTP e Perfil reutilizável.
- [x] A separação foi analisada, mas a jornada formal foi retirada do produto
  ativo; não criar novas rotas, uploads ou consentimentos de CV.
- [x] A reentrada do Perfil permanece somente na jornada Match sem CV; não há
  candidatura formal ativa.

Na Porta Match, o QR leva ao cadastro curto sem CV e as respostas ficam no
Perfil/contexto. Qualquer modelo ou rota antiga de candidatura formal é
encerrado e não participa dos seeds, menus, URLs ou distribuição atuais.

### Fase 5 — Respostas contextuais e catálogo canônico · CONCLUÍDA

- [x] Criar `CanonicalCatalog`, `CanonicalTerm` e aliases versionados para
  funções, categorias, segmentos e habilidades.
- [x] Mapear funções locais de cada organização para termos canônicos sem
  duplicar o cadastro da empresa ou da rede.
- [x] Separar respostas globais, de segmento, organização, unidade e
  oportunidade em `CandidateCanonicalResponse`.
- [x] Guardar finalidade, origem, versão do catálogo, consentimento, validade
  e revogação de cada resposta.
- [x] Projetar contexto compartilhado de rede sem expor organização de origem,
  resposta bruta ou referência interna; circulação externa exige consentimento.
- [x] Remover texto livre como chave de distribuição: resolução de sinônimos é
  exata e determinística; requisitos obrigatórios filtram elegibilidade sem
  criar ranking.
- [x] Conectar o formulário público Match ao catálogo: quando há versão
  publicada, a pessoa busca por texto, recebe sugestões canônicas e pode
  selecionar uma ou mais funções; cada resposta é gravada por contexto de
  QR/unidade; o conjunto de funções vem do catálogo habilitado para o
  Shopping/tenant, não da unidade de origem; texto livre não substitui os
  termos aprovados.

O catálogo é controlado no admin e pode evoluir por versão. Uma loja pode usar
“caixa”, “caixa de loja” ou outro alias aprovado, mas a necessidade é gravada
com o mesmo termo canônico. A resposta da pessoa permanece ligada ao contexto
em que foi coletada; o Perfil global não é sobrescrito por uma resposta de uma
unidade. A busca também usa aliases aprovados: “estoque” encontra
“Estoquista de loja” e “reposição” encontra funções de reposição. O caminho não
usa LLM.

Para o ambiente de Shopping, o catálogo inicial também contempla funções de
vitrine e visual merchandising, liderança e supervisão de loja, vendas, fiscal
de loja, recepção, alimentação, limpeza, segurança, estacionamento e
manutenção. A função só fica disponível para uma necessidade quando a loja ou
unidade a associa ao seu contexto operacional.

Esse de-para é mantido por loja: `local_label` preserva o nome usado pela
operação e aponta para um `CanonicalTerm` usado no cadastro do candidato. A
necessidade só pode ser ativada com mapeamento ativo específico da loja ou com
um mapeamento padrão da organização. O matching usa a função canônica e a
unidade da oportunidade; não usa texto livre nem LLM.

A contagem exibida no painel usa o mesmo motor de elegibilidade da rodada: função
mapeada, dias, período, formato, experiência, visibilidade e circulação ativa.

O formulário da loja é organizado nas mesmas seções de leitura do candidato:
Onde será a necessidade, O quê a loja precisa, Quando precisa, Distribuição
automática, Flexibilidade, Prioridade e Como o sistema decide
e decisão do sistema. Os antigos campos de texto `REQUIRED`, `DESIRABLE` e
`PODE APRENDER AQUI` não são mais apresentados como um segundo filtro. A
descrição continua existindo para explicar a rotina, mas a elegibilidade vem
dos campos estruturados. Para manter o contrato histórico de ativação, o
sistema grava internamente um critério REQUIRED de compatibilidade com os
filtros estruturados quando a loja não informa critérios adicionais.

## Catálogo de funções da loja e de-para

O cadastro do de-para fica disponível em dois níveis:

- no portal da loja, em **Gestão → Funções da loja**;
- no console, na área da unidade, em **Funções da loja**.

O gestor adiciona um cargo da loja e informa apenas o nome usado na operação,
sem cadastrar um cargo intermediário da empresa. Em seguida, vincula uma ou
mais funções canônicas do cadastro do candidato. O nome local pode ser “Estoquista”, enquanto as funções canônicas
podem ser “Estoquista de loja” e “Repositor de loja”. O login restrito à unidade
só enxerga e declara funções mapeadas daquela unidade;
um administrador pode trocar a unidade e o sistema recarrega o catálogo
correspondente. Sem de-para ativo, a necessidade não pode ser publicada.
Cada card do catálogo possui **Editar**, permitindo renomear o cargo local,
adicionar canônicos ou retirar vínculos sem criar outro cargo.
Alterar qualquer filtro atualiza a estimativa; a contagem não é apenas o total
de perfis da organização.

As perguntas de segmento não entram todas no primeiro cadastro. Elas são
templates contextuais, versionados e condicionais à função ou à oportunidade:

- alimentação: preferência entre atendimento, caixa, balcão, mesa e cozinha;
  disponibilidade para fechamento e fins de semana; experiência ou abertura
  para aprender rotinas de manipulação e atendimento;
- serviços: tipo de atendimento, uso de agenda, recepção, vendas consultivas,
  organização de materiais e disponibilidade de horário;
- operação do Shopping: limpeza, segurança, acesso, estacionamento,
  manutenção, trabalho em áreas comuns, escala noturna e necessidade de
  certificação objetiva quando aplicável.

Cada template deve ter no máximo seis perguntas práticas, finalidade, versão,
origem e consentimento. Respostas servem para filtrar elegibilidade e orientar
a decisão da loja; não criam score, ranking ou diagnóstico da pessoa.

No cadastro inicial, intenção e experiência são sinais diferentes: a pessoa
indica se quer trabalhar, aprender ou apenas avaliar a função; em separado,
indica seu nível de experiência e, opcionalmente, os segmentos em que já teve
contato, como roupas, calçados, alimentação, farmácia, serviços ou operação de
shopping. Nenhuma dessas respostas é tratada como prova de contratação.

### Necessidade estruturada e ondas de convite

Uma loja declara uma necessidade com descrição, função canônica, quantidade de
pessoas, tamanho da primeira rodada, dias, período, formato, início,
experiência, contexto de experiência e campos negociáveis. O sistema calcula
elegibilidade por filtros objetivos e mostra à loja três números diferentes:
elegíveis agora, convidados na rodada e pessoas desejadas. A rodada não é um
ranking; é apenas um limite operacional de distribuição.

Na tela, a loja não digita um cargo livre para ativar a necessidade: primeiro
seleciona um cargo local já cadastrado na unidade e visualiza as funções
canônicas vinculadas a ele. O tipo de trabalho (fixo, temporário ou ambos) é
uma escolha separada. Se a unidade não tiver um de-para canônico ativo, a tela
mostra o caminho para **Administrar funções e vínculos** e impede a ativação.

Cada convite tem prazo de resposta. Sem resposta, expira; com recusa, libera
espaço para outra rodada. Depois do interesse, a loja também tem prazo para
decidir. Critérios obrigatórios, como domingo ou certificação exigida, não são
negociados automaticamente. Critérios marcados como negociáveis podem gerar uma
confirmação condicional entre as partes, sem alterar silenciosamente a
necessidade original.

O perfil operacional do cargo local segue um padrão de mercado sem forçar uma
única forma de contratação: descrição da função; exigências e benefícios como
listas extensíveis; faixa salarial mínima e máxima com periodicidade (hora,
diária, mês, contrato total ou a combinar); tipo de contratação (CLT, PJ,
temporário, intermitente, freelance/diária, estágio/aprendiz, comissionado ou
misto); e forma de pagamento (mensal, hora, diária, comissão, fixo + comissão
ou a combinar). Esses dados ficam no cargo da unidade, são separados das
funções canônicas e são copiados para a necessidade como retrato inicial.

#### SLA e governança das rodadas

Os prazos são configuráveis em três níveis, sempre com a regra mais específica
vencendo a anterior: política geral da empresa/organização, override da loja ou
unidade e, por fim, ajuste explícito da necessidade. O cadastro da necessidade
grava um retrato desses valores para que uma mudança posterior de política não
altere convites já enviados.

- resposta da pessoa ao convite: padrão de 72 horas;
- decisão da loja depois do interesse: padrão de 120 horas;
- quantidade máxima de convites ativos por rodada: padrão de 12;
- espera entre rodadas após expiração: padrão de 24 horas.

Ao ativar uma necessidade, o sistema abre automaticamente a primeira rodada.
O processo periódico `process_match_invitation_rounds` expira convites sem
resposta, expira decisões da loja vencidas e abre nova rodada quando ainda há
vagas, pessoas elegíveis e o intervalo configurado já passou. A mesma versão
não reenvia a necessidade a quem já recebeu e encerrou um convite.

Negociação não é um campo livre. A loja marca previamente quais critérios podem
ser discutidos (`period`, `start_date`, `work_format`, `learn`). Uma proposta
fora dessa lista é rejeitada pelo domínio; requisitos obrigatórios não mudam
silenciosamente e a decisão fica registrada na Relation.

Os seeds canônicos atuais deixam o ambiente demonstrativo com relações em vários
estágios: convite entregue, convite expirado, interesse aguardando a loja,
negociação pendente, Match e contato liberado. Isso valida a única jornada Match
sem CV e a pilha operacional antes de usar dados reais.

### Fase 6 — Cobertura insuficiente e campanhas · CONCLUÍDA

- [x] Criar `CoverageGap` para necessidades com poucos elegíveis ou interessados.
- [x] Criar `EnrichmentCampaign`, convite opaco e resposta versionada.
- [x] Permitir perguntas opcionais para disponibilidade, segmento e disposição
  para aprender usando `QuestionnaireTemplate` publicado.
- [x] Recalcular elegibilidade por regras determinísticas, sem ranking, score ou
  promessa de contratação.
- [x] Permitir pausa, recusa, expiração, encerramento e revogação de campanhas.

O fluxo é: necessidade com cobertura baixa → campanha opcional → convite
individual → pessoa aceita ou recusa → resposta versionada → nova avaliação de
elegibilidade. A campanha não altera silenciosamente o Perfil global e não
expõe uma lista de candidatos à loja. O convite público usa token opaco e a
resposta só é gravada com consentimento explícito.

### Fase 7 — Pré-onboarding contextual · CONCLUÍDA

- [x] Substituir a trilha única por Perfil por `PreboardingAssignment`; a
  `CandidateOnboardingTrail` antiga permanece somente para compatibilidade.
- [x] Associar pré-onboarding a segmento, empresa, unidade, programa,
  oportunidade ou `Relation`.
- [x] Diferenciar `PRECISA`, `SERIA_BOM` e `PODE_APRENDER` sem usar peso de
  ranking.
- [x] Registrar `PreboardingEvidence` de curso, quiz, certificação, Talk ou
  validação manual sem criar score.
- [x] Liberar recursos contextuais somente quando o acesso aprovado e a
  audiência/Membership correspondente existirem.

Uma atribuição responde “o que essa pessoa precisa neste contexto?”, não “qual
é a nota dela?”. Evidências completam a atribuição por chave e tipo, preservando
validade e origem. Cursos, certificações e Talk continuam sujeitos aos sinais,
consentimentos e bindings já implementados.

### Fase 8 — Remoção do ranking legado · CONCLUÍDA

- [x] Remover o módulo de score comparativo e o caminho `rank_candidates`; a
  distribuição usa elegibilidade e interesse, sem API alternativa de ranking.
- [x] Remover `CandidatePosition` e seus campos, cálculos, índices e dados
  históricos por migração, em vez de manter notas de pessoas no banco.
- [x] Desativar a tela e o endpoint comparativo de matches com resposta `410`;
  a unidade usa necessidade, elegibilidade, interesse e recência.
- [x] Remover modelos de pontuação, regras ponderadas, conclusão duplicada de
  cursos e metadados de score nas perguntas. Evidência de cursos permanece no
  serviço de Aprendizagem e nos sinais contextuais consentidos, não em uma
  tabela de nota de candidato.
- [x] Remover telas administrativas e receivers que expunham ou recalculavam
  notas; testes garantem que modelos e módulos comparativos não estão disponíveis.

O fluxo ativo não responde “qual pessoa tem a maior nota?”. Ele responde “quem
é elegível para esta necessidade, recebeu a oportunidade e demonstrou interesse?”.
Isso preserva a decisão da pessoa e da unidade e evita ranking oculto ou
persistido. A migração `0075_remove_legacy_candidate_scoring` elimina também os
artefatos inativos do banco de desenvolvimento.

### Fase 9 — LGPD, segurança e validação SaaS · CONCLUÍDA

- [x] Confirmar que o cadastro inicial MatchCo não coleta endereço completo nem CEP.
- [x] Aplicar projeção mínima por finalidade e escopo; endereço, contato e
  respostas brutas não aparecem antes da liberação adequada.
- [x] Proteger a projeção da unidade contra endereço e payload de questionário
  fora da finalidade.
- [x] Validar que o feed respeita circulação, consentimento territorial e
  revogação sem reativar a pessoa automaticamente.
- [x] Completar a anonimização de Perfil, localização, disponibilidade,
  respostas, contexto, evidências e sinais de enriquecimento.
- [x] Atualizar Help contextual, documentação HTML, testes e checklist a cada
  entrega.

O cadastro MatchCo coleta somente identidade mínima, disponibilidade, região
de trabalho e intenção. CEP/endereço ficam fora desta porta. A projeção para a
loja é uma whitelist contextual; telefone só aparece depois de `CONTACT_ENABLED`
e respostas detalhadas não são compartilhadas por padrão. A anonimização mantém
o registro de auditoria, mas remove os dados pessoais e deixa o Perfil fora da
circulação.

### Fase 10 — Gate de go-live SaaS · EM PROGRESSO

- [x] Executar o Privacy Implementation Gate (PIG) contra o ambiente atual.
- [x] Confirmar retenção, gate de idade, consentimento granular, páginas públicas,
  ledger append-only e classes de resposta.
- [ ] Substituir e-mails `example` por DPO e canal real de direitos LGPD.
- [ ] Informar o nome legal do controlador.
- [ ] Cadastrar DPA e finalidade dos processadores ativos.
- [ ] Validar ou reprocessar o PIAG dos EntryPoints ativos antes do go-live.
- [x] Executar o smoke test da jornada externa Match sem currículo; confirmar que os endpoints legados de CV estão encerrados.

O PIG atual está em `6/11` verificações técnicas aprovadas. As cinco falhas
restantes não devem ser resolvidas com valores fictícios no código: dependem de
dados legais do controlador, contratos com processadores e validação das URLs
reais dos EntryPoints. Enquanto isso, o SaaS deve permanecer em modo de
desenvolvimento/homologação.

### Regra de acompanhamento

- `CONCLUÍDA`: código, testes, documentação e permissões validados;
- `EM PROGRESSO`: implementação parcial com cenários ainda descobertos;
- `PENDENTE`: decisão documentada, sem implementação suficiente;
- `BLOQUEADA`: depende de decisão de produto ou autoridade externa.

As fases antigas registram decisões e entregas já realizadas, mas não são o
status do novo plano canônico. O próximo ciclo começa na Fase 0 estrutural e só
marcará uma fase como concluída depois de validar código, dados, permissões,
testes e documentação no modelo unificado. As decisões antigas sobre identidade,
OTP, catálogo, cobertura, pré-onboarding, remoção de ranking e privacidade
continuam sendo requisitos e serão validados diretamente na base limpa.

## Plano canônico de execução SaaS unificado

Esta seção é a referência para a implementação. O recrutamento é uma extensão
da estrutura SaaS, e não um cadastro paralelo. Como não há dados de produção ou
legado a preservar, a base será recriada diretamente no modelo canônico, sem
trilha de migração ou camada temporária de compatibilidade.

### Modelo estrutural definitivo

```text
Organization — contexto de governança e isolamento SaaS
├── BusinessEntity — empresa real: Bourbon, Drogasil, prestador
├── OrganizationEntityParticipation — papel da empresa no contexto
├── PhysicalLocation — local físico único e neutro
├── BusinessUnit — unidade contextual: shopping, loja, quiosque, CD
├── OperationalUnit — área/departamento/equipe
├── JobFunction — função canônica usada por operação e Match
├── Membership — usuário, papel e escopo autorizado
├── Audience / Talk / Courses — serviços da organização
└── Recruitment — necessidades, convites, relações e Match
```

Regras de autoridade:

- `Organization` é o limite de tenant e audiência; uma unidade física compartilhada não atravessa organizações.
- `BusinessEntity` representa a empresa real. Drogasil pode ser lojista/parceira no Bourbon e empresa controladora na Rede Drogasil.
- `PhysicalLocation` representa o lugar real uma única vez. Cada organização pode ter sua `BusinessUnit` apontando para ele.
- `OperationalUnit` representa departamentos, áreas ou equipes. `JobFunction` representa função: “Caixa” é função; “Operação da loja” pode ser área.
- `Membership` é contextual e escopado. A mesma identidade global pode ter dois memberships, mas não herda permissões de um para o outro.
- O Perfil do candidato é global e não é Membership interno. O recrutamento entrega oportunidades conforme consentimento e escopo.

### Exemplo obrigatório dos seeds

```text
Bourbon Shopping
├── áreas internas: administração, segurança, limpeza, manutenção
├── parceiros lojistas: Drogasil, Centauro e demais lojas
├── prestadores externos autorizados pelo shopping
└── unidade contextual: Drogasil · Bourbon

Rede Drogasil
├── empresa controladora: Drogasil
├── unidades: Bourbon, Perdizes, Lapa e centro de distribuição
├── áreas e programas nacionais
└── unidade contextual: Drogasil · Bourbon
```

O local físico da Drogasil no Bourbon é único, mas pode receber conteúdo
operacional do shopping quando houver Membership Bourbon e conteúdo da rede
quando houver Membership Drogasil. Uma permissão nunca é inferida pela outra.

> **Status canônico:** o único checklist com estado de execução é o plano A–I
> desta página. As fases numeradas anteriores foram consolidadas nele para
> eliminar checkboxes duplicados e conflitantes. Modelo, exemplos e decisões
> acima permanecem como contrato; não devem ser tratados como uma segunda
> sequência de implementação.

## Serviços modulares do SaaS

A forma comercial e técnica recomendada é vender serviços integrados sobre um
único núcleo organizacional. A empresa não cria uma nova base para cada serviço;
ela ativa capacidades dentro da mesma organização, unidade ou programa.

### Núcleo obrigatório da plataforma

Toda organização começa com os serviços que garantem isolamento e governança:

- identidade global e autenticação;
- organização, empresas, parceiros, unidades e áreas;
- Membership, papéis, escopos e aprovação;
- audiências e circulação autorizada;
- notificações e preferências de contato;
- auditoria, LGPD, retenção e direitos do titular;
- configuração de domínios, QR e contexto.

Esse núcleo não deve ser tratado como um módulo opcional, porque todos os outros
serviços dependem dele.

### Serviços ativáveis

| Serviço | O que entrega | Escopo típico |
|---|---|---|
| Conteúdo | Feed, Wiki, documentos, avisos e comunicação assíncrona | organização, unidade ou audiência |
| Talk | Conversas, canais, mensagens e acompanhamento de presença | audiência, equipe, unidade ou programa |
| Treinamento | Cursos, trilhas, quizzes, tarefas e progresso | organização, função, unidade ou programa |
| Certificação | Certificados, validade, evidências e renovação | função, área, unidade ou rede |
| Recrutamento Match | Perfil, QR, necessidade, convite, interesse bilateral e Match | unidade, rede, território ou programa |
| Campanhas e pesquisas | Perguntas de enriquecimento, pesquisas e segmentação contextual | campanha, segmento ou unidade |
| Operação | Checklists, ocorrências, tarefas e rotinas operacionais | área, unidade ou prestador |
| Parceiros | Convites, acessos, escopos e gestão de prestadores externos | parceiro, contrato ou unidade |
| Indicadores | Métricas agregadas de conteúdo, aprendizagem, operação e Match | organização ou escopo autorizado |

### Conteúdo, Talk e Treinamento

Esses serviços podem ser vendidos separadamente, mas compartilham a mesma base:

```text
Conteúdo       → informa e comunica
Talk           → conversa e coordena
Treinamento    → ensina, verifica e certifica
Recrutamento   → distribui necessidades e cria Match
```

Tecnicamente, Conteúdo e Talk podem compartilhar o serviço comercial
**Comunicação**, mas devem permanecer capacidades distintas. Uma empresa pode
contratar Feed/Wiki sem contratar Talk. Treinamento deve ser um serviço separado,
porque possui matrícula, progresso, avaliação, evidência e regras próprias.

Recrutamento também é separado comercialmente e tecnicamente, mas usa as mesmas
unidades, funções, memberships, audiências e permissões. Ele nunca cria uma
organização paralela para funcionar.

### Ativação por organização e empresa

O modelo recomendado é um registro de serviço por organização, com escopo e
vigência:

```text
OrganizationServiceSubscription
├── organização
├── empresa (opcional: exceção comercial)
├── serviço/capacidade
├── plano comercial
├── status e vigência
└── limites e configuração
```

Exemplo:

- Bourbon ativa Conteúdo para todas as lojas do shopping como padrão da
  organização.
- Bourbon ativa Operação apenas para Segurança e Manutenção.
- Drogasil ativa Conteúdo, Talk e Treinamento para a rede nacional.
- Drogasil ativa Recrutamento para suas unidades.
- A loja Drogasil do Bourbon recebe conteúdo do shopping apenas pelo Membership
  Bourbon e conteúdo da rede apenas pelo Membership Drogasil.

Sem uma linha específica para a empresa, `service_enabled` usa o padrão da
organização. Com uma linha específica, o estado da empresa prevalece, inclusive
para suspender um serviço ativo no padrão. A exceção não altera o serviço das
demais empresas nem permite consultar outra organização.

Ativar um serviço não cria usuários, não copia conteúdo e não concede acesso
automático. O serviço sempre consulta Membership, audiência, escopo, finalidade,
consentimento e estado da organização.

### Serviços que agregam valor sem fragmentar o SaaS

Os próximos serviços com maior valor para shopping e redes são:

1. **Parceiros e prestadores:** entrada aprovada, documentos, treinamentos
   obrigatórios, validade e escopo por unidade.
2. **Campanhas e pesquisas:** enriquecimento de Perfil, satisfação, intenção de
   compra e pesquisas operacionais sem transformar respostas em ranking.
3. **Operação de unidade:** checklists, incidentes, tarefas e comunicação entre
   shopping, lojista e prestador.
4. **Certificação:** comprovação de que uma pessoa está apta para uma função ou
   rotina, com validade e renovação.
5. **Indicadores agregados:** leitura de cobertura, participação, treinamento,
   comunicação e recrutamento sem expor bases nominais.

Essa ordem mantém o produto simples: primeiro núcleo e serviços de comunicação,
aprendizagem e Match; depois campanhas, parceiros, certificação e operação.

## Plano de implementação incremental e mitigação de riscos

Esta é a ordem oficial de execução. Ela preserva a estrutura atual e prioriza
adaptação, isolamento e testes antes da criação de novos módulos. Nenhuma fase
deve introduzir uma segunda hierarquia para organizações, empresas, unidades,
usuários ou funções.

### Fase A — Baseline e contrato · EM EXECUÇÃO

- [x] Definir `Organization` como limite de tenant.
- [x] Definir `Membership` e audiência como autorização contextual.
- [x] Definir Bourbon Shopping, Rede Drogasil e ElectraTech como cenários demo
  isolados, cobertos pelos seeds oficiais de desenvolvimento.
- [x] Encerrar CV, candidatura formal, ranking e porta híbrida do escopo ativo.
- [x] Registrar no código um catálogo único de serviços e estados de ativação,
  já usando a estrutura canônica, sem camada de compatibilidade.
- [ ] Criar uma matriz de dependências para impedir que Recrutamento, Talk ou
  Cursos sejam acessados sem organização e escopo resolvidos.

Auditoria automática do URLconf percorreu 1.042 rotas nomeadas. Corrigidas
nesta etapa as rotas de conteúdo de módulos do Console, os endpoints de conteúdo
e matrícula da API de cursos e a API de gamificação, que não estavam associadas
ao serviço Treinamento. A matriz completa ainda inclui rotas de domínio central,
endpoints móveis com múltiplos serviços, tarefas assíncronas e callbacks; por isso o
item permanece aberto até existir cobertura e regra explícita para cada família.

**Gate:** o sistema deve iniciar com uma organização selecionada, sem dados de
outra organização na página atual, e `manage.py check` deve passar.

Validação local em 2026-10-09: `manage.py check` passou; Recrutamento passou
177 testes (3 skips existentes), `test_services` e seleção de idioma passaram
em 21 testes; os testes focados de território, QR, OTP e vínculo do seed também
passaram. `makemigrations --check --dry-run` não encontrou mudanças de modelo.
O teste antigo de
`CandidateApplication` foi removido porque validava o fluxo CV encerrado; a
cobertura atual usa Perfil, consentimento, necessidade, convite, rodadas, Match,
auditoria e isolamento.

Validação adicional desta continuação: `recruitment.tests.test_tenant_boundaries`
passou com 6 testes, incluindo respostas 404 para consulta de funções e
estimativa usando unidade de outra organização. Os testes de operação do Console
confirmam que o reset chama somente o comando canônico, exige a confirmação
literal e mantém os seeds de Recrutamento e Conteúdo separados.

O reset foi executado no banco local `matchco_dev` (`DEBUG=True`) com
`reset_matchco_development --yes --seed-recruitment --seed-content`. Bourbon,
Drogasil e ElectraTech ficaram ativos, o usuário admin recebeu Membership nos
três tenants, e o conteúdo foi confirmado nos respectivos schemas. O seed
registrou 25 unidades, 25 QRs ativos, 36 Perfis e 18 necessidades; Conteúdo
registrou cursos, publicações e documentos nos três tenants, além de uma
certificação publicada com dois requisitos de curso no Bourbon e outra na
Drogasil. O botão do Console foi corrigido para usar esse mesmo contrato; a
tela de seeds agora atualiza Recrutamento ou Conteúdo separadamente e não chama
reset legado.

Após os ajustes, 33 testes focados de tenant, seed, idioma, serviços e Help
passaram; a tela de seed também passou em 5 testes, incluindo renderização e
ações independentes. `manage.py check`, `makemigrations --check --dry-run`,
`git diff --check` e compilação `msgfmt --check` dos três catálogos passaram.
Uma execução ampla de 209 testes foi iniciada, mas interrompida durante a
criação repetida de schemas de teste; ela não conta como validação completa.

### Fase B — Núcleo organizacional · EM EXECUÇÃO

#### Cadastro canônico de unidades e lojas

O cadastro estrutural de `BusinessUnit` é único para qualquer operação: loja de rua, loja dentro de shopping, quiosque, serviço, escritório, centro de distribuição, fábrica ou parceiro. Ele registra:

- identidade: empresa, nome operacional, nome comercial, código e referência externa;
- classificação: tipo de unidade, tipo de localização e canal;
- localização: `PhysicalLocation` quando houver local físico compartilhado, shopping/empreendimento, endereço, número, complemento, bairro, cidade, UF, CEP e coordenadas;
- operação: responsável, telefone, e-mail, website e horário;
- administrativo: CNPJ e inscrição estadual quando aplicáveis;
- status: ativa ou inativa.

Uma unidade do shopping e uma unidade de rua usam o mesmo contrato, mas não compartilham endereço por conveniência. A Drogasil do Bourbon pode apontar para o local físico do shopping dentro da organização Bourbon e, ao mesmo tempo, dentro da Rede Drogasil; a representação, os usuários, os serviços e as permissões continuam isolados por organização.

Critérios de aceite: o cadastro não expõe dados fiscais ao candidato; o CEP da unidade fica disponível para territorialidade/proximidade controlada; o Match só adiciona o de-para canônico quando o serviço estiver ativo; Talk e Conteúdo continuam funcionando sem telas de recrutamento.

- [ ] Usar `Organization`, `Company`, `BusinessUnit`, `OperationalUnit`,
  `JobFunction`, `Partner` e `Membership` como fonte única.
- [x] Conectar os registros de Recrutamento às unidades, empresas e funções
  canônicas por referências verificáveis; a remoção completa dos modelos
  projetados continua pendente e não deve ser considerada concluída.
- [ ] Validar empresa controladora, parceiro lojista e prestador externo como
  papéis da mesma organização, sem duplicar identidade.
- [ ] Validar constraints de pertencimento e escopo em consultas, formulários,
  páginas e seeds.

O seed liga cada `RecruitmentStore` à `BusinessUnit` canônica por referência
interna e cada QR/necessidade usa essa unidade; a consolidação estrutural
completa segue pendente porque ainda existem modelos projetados de Recrutamento.

**Risco mitigado:** duas fontes de verdade para a mesma loja ou função.

### Fase C — Local físico e contexto · EM EXECUÇÃO

- [ ] Consolidar a localização compartilhada em um único registro neutro; hoje
  o seed mantém `PhysicalLocation` canônica e uma projeção `RecruitmentPhysicalUnit`
  com a mesma chave externa.
- [x] Permitir duas representações contextuais: Bourbon e Rede Drogasil.
- [ ] Fazer QR, necessidade, função, curso e audiência resolverem o contexto
  antes de carregar qualquer dado.
- [x] Sincronizar a organização selecionada com o tenant ativo e limpar unidade,
  empresa, Membership, audiência e porta anteriores na troca; preservar o filtro
  de empresa ao selecionar novamente a organização atual; a visão global de
  superadministrador também limpa o escopo de tenant (`test_current_configuration.py`).
- [ ] Confirmar, nas telas do Portal e do Console, que toda troca de organização
  limpa unidade, empresa, audiência e porta quando o escopo não for compatível
  (teste de sessão aprovado; validação ponta a ponta ainda pendente).

**Risco mitigado:** vazamento entre shopping e rede ou associação automática de
uma pessoa ao tenant errado.

### Fase D — Pessoas, acessos e audiências · EM EXECUÇÃO

- [x] Separar identidade global, Perfil externo e Membership interno.
- [x] Exigir convite, QR ou aprovação para criar participação interna.
- [x] Aplicar validade, revogação, aprovador, finalidade e auditoria.
- [ ] Impedir que conclusão de curso crie Membership automaticamente.
- [x] Permitir que um mesmo usuário tenha memberships independentes, sem
  herança de papel ou audiência.

**Risco mitigado:** treinamento, candidatura ou convite virarem acesso global.

### Fase E — Serviços existentes sobre o núcleo · EM EXECUÇÃO

- [x] Exibir no console somente Conteúdo, Talk, Treinamento, Certificação,
  Recrutamento, Parceiros, Operação ou Indicadores autorizados para o tenant.
- [ ] Reutilizar a estrutura atual de conteúdo, cursos, audiências e Match.
- [ ] Tratar Conteúdo e Talk como capacidades relacionadas, mas não misturar
  seus dados ou permissões.
- [ ] Tratar Treinamento e Certificação como evidências de aprendizagem, nunca
  como contratação ou ranking.
- [x] Criar `OrganizationServiceSubscription` depois de validar a matriz de
  capacidades no código atual; inicialmente a ativação pode ser configurada de
  forma compatível com os bindings existentes. A ativação e suspensão já estão disponíveis em `/console/organization/services/`.
- [x] Usar a organização como padrão de serviço e permitir exceção explícita
  por empresa, sem duplicar hierarquia, pessoas, conteúdos ou audiências.
- [x] Fazer uma suspensão por empresa prevalecer sobre o padrão ativo da
  organização e impedir fallback entre organizações.
- [x] Separar o grupo `Serviços` do grupo `Organização e estrutura` e ocultar
  itens de conteúdo, aprendizagem, análise e Match conforme o catálogo ativo.
- [x] Bloquear no servidor o acesso direto às rotas operacionais do Console
  quando a organização não tiver o serviço ativo; respeitar a exceção explícita
  por empresa e responder como não encontrado quando o serviço estiver inativo.
  O middleware compartilha o catálogo usado pelo menu e mantém a tela de
  configuração de serviços acessível para ativar o primeiro serviço.
- [x] Permitir que Feed/Wiki, cursos, documentos e mídia tenham empresa
  responsável; filtrar as listas do Console por empresa sem criar hierarquia
  paralela. Usuário com Membership empresarial fica fixado à própria empresa.
- [x] Aplicar a fronteira empresa também na leitura de conteúdo publicado,
  detalhe, arquivo, sincronização móvel e trilhas no app; conteúdo da empresa
  exige Membership correspondente (ou administração da organização), além da
  audiência. `is_staff`/grupo editorial não é autorização transversal.
- [x] Fazer a sincronização móvel aplicar Conteúdo e Treinamento por
  componente, filtrar notificações pelo tenant ativo e ignorar eventos do
  serviço correspondente quando ele estiver suspenso.
- [x] Manter conteúdo organizacional como compartilhável dentro da organização,
  sujeito à audiência; conteúdo de empresa permanece empresarial. Links de
  compartilhamento explícitos continuam sendo uma concessão separada e controlada.
- [ ] Propagar a empresa ativa a todos os relatórios, tarefas assíncronas,
  recomendações e integrações de conteúdo, validando papéis e serviços em cada
  ponto de entrada.
- [ ] Aplicar o mesmo cálculo de serviço por empresa em todas as telas
  operacionais que recebem uma unidade selecionada, além do menu global.
- [ ] Completar o mapa de serviços para cada rota e API, incluindo jobs
  assíncronos e callbacks de integrações; o middleware atual cobre as rotas
  identificadas do Console, App, Portal, APIs e páginas públicas contextuais,
  mas não substitui autorização por objeto, audiência ou Membership.

Auditoria do URLconf (1.042 padrões nomeados) encontrou ações de módulo do
Console, endpoints de conteúdo/matrícula da API de cursos e gamificação sem
exigência de Treinamento; o mapeamento e testes de regressão foram adicionados.
Ainda é necessário exercitar payloads móveis com overrides por empresa e fazer
inventário explícito de tarefas e callbacks; rotas de núcleo e páginas públicas
sem dados de serviço não devem ser classificadas artificialmente como serviço.

**Risco mitigado:** feature sprawl e mudança prematura de banco.

### Fase F — Recrutamento Match · EM EXECUÇÃO

- [x] Modelo valida que unidade e função da necessidade pertencem à mesma
  organização, mesmo quando a view é contornada ou chamada por integração.
- [x] Modelo valida que o Perfil e a oportunidade de uma Relation pertencem à
  mesma organização antes de liberar qualquer relação bilateral.
- [x] Revogação de visibilidade Match pausa a circulação do Perfil e impede
  novos convites até novo consentimento.
- [x] Necessidade da loja usa função local vinculada a uma ou mais funções
  canônicas do catálogo, com validação de organização.
- [x] QR permanece único por unidade e sem CV; a constraint do banco impede
  mais de um ponto Match ativo para a mesma unidade.
- [x] Distribuição determinística usa função, disponibilidade, início,
  território, consentimento e critérios negociáveis. Cada consentimento de
  circulação fica ligado ao QR e à organização de origem; loja exige a mesma
  unidade física, shopping exige localização canônica igual, rede exige o
  tenant identificado ou vínculo de rede ativo, e raio exige coordenadas e
  distância dentro do limite. Sem origem verificável ou geocodificação, falha
  fechado. Feed, prévia, convite e projeção canônica entre empresas usam a
  mesma autorização; a projeção entre empresas inclui somente sinais canônicos
  com finalidade de distribuição, nunca respostas privadas ou origem
  (`territory.py`; `test_territorial_consent.py`).
- [x] Consultas operacionais de funções e simulação não resolvem unidades fora
  da organização ativa; esses identificadores respondem como inexistentes
  (`test_tenant_boundaries.py`).
- [x] Convites expiram, rodadas reabrem após a espera configurada e o prazo
  de decisão da loja também expira; critérios negociáveis aceitam somente os
  campos explicitamente liberados (cobertura em `test_opportunity.py`).
- [x] A loja vê apenas quem demonstrou interesse naquela necessidade; convites
  entregues não geram projeção de Perfil (AA-6) antes do interesse da pessoa.
- [x] A leitura do Match mostra os valores da necessidade e os valores
  declarados pela pessoa, sem score ou ranking (`portal/lojista_relation.html`).

**Risco mitigado:** seleção opaca, exposição de base nominal e promessa de
compatibilidade que o sistema não consegue explicar.

### Fase G — Integrações de valor · POSTERIOR

- [ ] Parceiros e prestadores: convite, documentos, treinamento obrigatório,
  validade e escopo por unidade.
- [ ] Operação: checklists, tarefas, ocorrências e rotinas por área.
- [ ] Campanhas e pesquisas: enriquecimento contextual e consentimento.
- [ ] Indicadores agregados: cobertura, participação, treinamento, operação e
  Match sem exportar base nominal.
- [ ] Notificações por e-mail e WhatsApp/SMS somente com preferência,
  finalidade e provedor auditados.

**Risco mitigado:** ampliar o produto antes de provar o núcleo e coletar dados
sem finalidade operacional.

### Fase H — Console e experiência operacional · EM EXECUÇÃO

- [ ] Consolidar Tailwind compilado localmente e Flowbite via NPM como única
  fundação do Console; remover Tailwind/Flowbite duplicados por CDN do shell.
- [ ] Criar primitives reutilizáveis para cabeçalho, botão, badge, alerta,
  estado vazio, filtros, tabela e paginação, mantendo variantes de tenant,
  claro/escuro, foco, mobile e teclado.
- [ ] Migrar Dashboard, uma lista operacional e Serviços da organização como
  piloto de densidade; reduzir espaçamento e bordas sem baixar controles abaixo
  de 14px.
- [ ] Padronizar tabelas para dados repetitivos com busca, filtros, ordenação,
  paginação, overflow responsivo, estado vazio e ações por linha; reservar
  cards para resumo e descoberta.
- [ ] Auditar e retirar folhas, scripts, Bootstrap e classes concorrentes por
  família de páginas, verificando que cada componente tenha uma única fonte.
- [ ] Medir requests, bytes de CSS/JS, regressões visuais e acessibilidade
  antes/depois; aceitar a migração somente se a leveza e a paridade funcional
  forem demonstradas.
- [ ] Manter o seletor de organização sempre visível no topo.
- [ ] Agrupar o console em: Núcleo, Comunicação, Aprendizagem, Recrutamento,
  Operação, Parceiros e Indicadores.
- [x] Esconder grupos de serviço não habilitados para a organização.
- [x] Manter reset, seeds e ledger em “Operação técnica”, restrito a
  superadministradores; seeds são separados, e o reset total exige confirmação.
- [ ] Permitir que cada página mostre o contexto atual antes de listas e ações.
- [x] Validar claro/escuro, mobile, teclado, estados vazios e links de Help nas telas estruturais revisadas.
- [x] Padronizar a lista administrativa de cursos com breadcrumb, KPIs, filtros, audiência legível, tabela responsiva e paginação preservada.
- [x] Padronizar o formulário de categorias de cursos com breadcrumb, identificação separada da referência técnica e catálogo compartilhado explicado.
- [x] Padronizar a lista e o formulário de quizzes com escopo do tenant, KPIs, busca, regras de avaliação e campos Flowbite sem CSS local sobreposto.
- [x] Alinhar rótulos do menu lateral aos títulos visíveis de avaliações, cargos, usuários, acessos, grupos e conformidade, preservando as URLs técnicas.
- [x] Padronizar trilhas, criação e atribuição com breadcrumb, filtros, KPIs, abas de formulário, escopo do tenant e estados vazios localizados.
- [x] Padronizar certificações e formulário de criação com KPIs, filtros, requisitos, validade, aprovação e escopo por organização/empresa.
- [x] Padronizar Feed e Wiki com KPIs, filtros, audiência legível, expiração, breadcrumb e formulário em abas sem CSS local concorrente.
- [x] Padronizar o cadastro de tipos de público e vínculo em lista e formulário Flowbite, com escopo da organização ativa e Help contextual.
- [x] Corrigir a ordem de ativação do idioma e unificar o seletor para que a preferência funcione no menu e em Configurações.
- [x] Fixar Português do Brasil como idioma inicial, sem autodetecção por `Accept-Language`, e aplicar a preferência salva nas próximas páginas.
- [x] Disponibilizar o seletor também nas páginas públicas, incluindo a entrada de candidato por QR antes do login.
- [x] Nas páginas públicas com cabeçalho, oferecer troca imediata e discreta (PT · EN · ES) na mesma linha das ações, sem botão “Aplicar”; páginas utilitárias sem cabeçalho mantêm a faixa auxiliar.
- [ ] Revisar mensagens ainda em inglês na interface de origem e padronizar a redação em Português do Brasil antes de iniciar traduções para outros idiomas.
- [ ] Auditar e traduzir a interface fixa por jornada (pt-BR, en, es); conteúdo autoral permanece no idioma publicado e não é traduzido automaticamente.
- [x] Revisar e traduzir a tela Serviços da organização em Português do Brasil, Inglês e Espanhol, incluindo estados, explicações e ações.
- [x] Traduzir grupos, itens e atalhos do menu lateral para inglês e espanhol como superfície de teste do seletor; as demais telas continuam em português.
- [x] Módulo Serviços da organização: marcar os textos visíveis para tradução, completar os rótulos de serviços em pt-BR e ocultar códigos técnicos da interface.
- [x] Marcar textos fixos e atributos acessíveis nos templates HTML ativos; a auditoria determinística não encontrou literais visíveis sem marcação nos templates.
- [x] Marcar rótulos, ajudas, opções estáticas e mensagens comuns de formulários/erros em Python com `gettext_lazy`, preservando valores internos e dados dinâmicos.
- [x] Marcar mensagens simples de confirmação, alerta, validação e atualização de texto via JavaScript nos templates.
- [x] Criar catálogos centrais extraídos para `pt_BR`, `en` e `es`; compilar os catálogos após a extração.
- [ ] Auditar HTML montado dinamicamente em JavaScript, conteúdo dinâmico e outros contextos Python fora de campos/formulários/mensagens comuns.
- [ ] Revisar e preencher `msgstr` de `en` e `es` por jornada; confirmar que o pt-BR não exibe mensagens de origem inglesa sem tradução.
- [ ] Completar `pt_BR` para mensagens cuja origem ainda esteja em inglês; mensagens-base em português podem permanecer com `msgstr` vazio.
- [x] Criar auditor local determinístico, sem LLM/API/tokens, para varrer templates, chamadas gettext e catálogos pt-BR; permite relatório completo e execução limitada por módulo. Guia: [`LOCALIZATION_AUDITOR.md`](tools/LOCALIZATION_AUDITOR.md).
- [ ] Validar fallback, idioma de páginas públicas, acessibilidade do seletor e cobertura dos catálogos em CI.

**Risco mitigado:** console confuso e operação no tenant errado.

### Fase I — Segurança, LGPD e go-live · OBRIGATÓRIA

- [x] Revogar visibilidade Match também pausa a circulação do Perfil no escopo
  da organização, preservando o histórico de consentimento.
- [ ] Testar isolamento em consultas, templates, APIs, exportações e tarefas.
- [x] Separar conta interna, associação de empresa/audiência, perfil de candidato e ator empregador; um usuário pode exercer mais de um papel sem herdar permissões do outro.
- [x] Bloquear o uso de `is_staff` como autorização implícita para visualizar interesses de candidatos; o console exige administrador da organização ativa ou superadministrador, e o portal exige `EmployerActor` com escopo.
- [x] Garantir que a projeção do empregador não exponha contato, respostas completas, endereço ou dados de procura antes do estado de Match autorizado.
- [x] Registrar troca de tenant, alteração de associação e cada leitura de QR em trilhas append-only separadas.
- [x] Vincular, com verificação administrativa, uma conta interna a uma identidade de candidato sem apagar ou sobrescrever os históricos existentes.
- [x] Bloquear fusão automática de contas com e-mails diferentes; contas duplicadas permanecem rastreáveis até uma decisão explícita de consolidação.
- [x] Expor a vinculação e revogação na edição de usuários do Console, com busca limitada às organizações do usuário e registro da confirmação.
- [x] Expor papéis de gestão em tela própria, com responsabilidade e escopo hierárquico explícitos; desativação preserva o histórico e limita a operação ao recorte configurado.
- [x] Localizar e explicar grupos e hierarquias adicionais, mantendo explícita a diferença entre agrupamento complementar e a estrutura canônica de empresas e unidades.
- [x] Exibir conformidade e treinamento em painel localizado, limitado a Memberships ativas da organização, com status e prazos legíveis sem substituir a evidência de LGPD.
- [x] Disponibilizar auditoria da estrutura localizada e somente leitura, filtrada pela organização ativa e com responsável, ação, recurso e motivo.
- [x] Localizar e padronizar a administração global, mantendo explícitos o acesso exclusivo da plataforma e a separação dos dados por organização.
- [x] Padronizar políticas de audiência com escopo restrito à organização ativa, status ativo/inativo legível e modo de correspondência explicado para a operação.
- [x] Localizar o simulador de audiência e manter sua prévia somente leitura, com conteúdo publicado e alcance calculados dentro do tenant autorizado.
- [x] Unificar o perfil pessoal em `/app/profile/`: sidebar e avatar não apontam mais para a tela legada; o Console permanece como edição administrativa em `/console/users/<id>/edit/`.
- [x] Exibir no console uma tela operacional consolidada para histórico de vínculos, trocas de contexto, leituras de QR e contatos liberados.
- [x] Aplicar rate limit por IP nos endpoints públicos de solicitação e
  verificação do OTP; desabilitar captura/dica do código fora de `DEBUG`.
- [x] Responder como não encontrado para consulta de unidade de outro tenant no
  Portal e testar a falha negativa, sem devolver nome, funções ou estimativa.
- [x] Resolver o IP do cliente para rate limit e auditoria sem confiar em
  `X-Forwarded-For` arbitrário; aceitar a cadeia somente quando `REMOTE_ADDR`
  pertence aos CIDRs explícitos de proxy confiável, com fallback seguro e testes.
- [ ] Configurar os CIDRs e a regra de sobrescrita do header no proxy real de
  produção; confirmar ponta a ponta que o proxy de borda não preserva valores
  fornecidos pelo cliente.
- [ ] Completar controles de autenticação: limites por identidade, proteção
  anti-enumeração e alertas;
  manter OTP com expiração, máximo de tentativas e logs sem segredo. O cooldown
  de 60 segundos por telefone e o limite de cinco tentativas já estão
  implementados e testados; permanecem os demais controles desta linha.
- [ ] Revisar minimização, finalidade, retenção, anonimização e direitos do
  titular por serviço.
- [ ] Testar falhas de permissão como casos positivos, não somente happy path.
- [ ] Executar `manage.py check`, testes de organização, permissões, Match,
  cursos, Talk, auditoria e seeds antes de cada avanço de fase.

**Gate final:** código, seeds, permissões, documentação, Help contextual e
testes devem apresentar o mesmo comportamento em Bourbon e Drogasil.

### Matriz de riscos que acompanha todas as fases

| Risco | Controle obrigatório | Evidência de aceite |
|---|---|---|
| Dados entre tenants | filtro de organização em serviço, view e template | teste Bourbon × Drogasil |
| Estrutura duplicada | fonte canônica e proibição de novos cadastros paralelos | seed e constraint |
| Console complexo | navegação por serviço ativo e contexto visível | teste por papel |
| Acesso indevido | Membership, audiência, finalidade, validade e revogação | testes negativos |
| Perfil excessivo | perguntas mínimas, finalidade e retenção | revisão LGPD |
| Match opaco | critérios declarados, sem ranking | tela “declarado/necessidade” |
| Dependência de canal | preferências e fallback auditado | teste de notificação |
| Crescimento sem controle | ativar somente serviços com limite e escopo | checklist de go-live |

### Regra de implementação

Não será criado um novo serviço apenas porque ele é comercialmente desejável.
Antes, deve existir: finalidade clara, organização responsável, escopo,
Membership ou audiência, política de dados, evento de auditoria, tela de
administração e teste de isolamento. A estrutura atual permanece a base; novas
entidades só entram quando uma necessidade comprovada não puder ser atendida
com segurança pelos modelos existentes.

## Conclusão

O desenho correto é: um QR Match permanente por unidade, um Perfil que permanece, uma
intenção específica para cada necessidade, uma projeção limitada após o interesse
da pessoa e Match somente quando os dois lados decidem continuar.

Para melhorar a leitura dos candidatos, o sistema deve organizar relações por
contexto, estado e sinais objetivos. Não deve criar ranking ou score comparativo.

Documentos operacionais que acompanham este plano:

- Biblioteca de documentos: `/console/documents/` mantém busca, filtros, miniaturas/lista e ações em lote no escopo da organização e da empresa ativa; `/console/documents/new/` usa breadcrumb e grupos de formulário para identificação, conteúdo, versão e acesso. Checkboxes de seleção em lote usam o mesmo estado visual e foco das tabelas Flowbite do Console.
- Biblioteca de mídia: `/console/media/` usa o mesmo shell visual, KPIs, filtros, alternância miniaturas/lista e checkbox compartilhado; métricas e ações permanecem limitadas ao escopo ativo.
- Nova mídia: `/console/media/new/` usa breadcrumb, organização em abas, campos Flowbite e checkbox compartilhado; upload, audiência, empresa e acesso público continuam sujeitos às regras do tenant.
- As abas de Nova mídia usam o padrão Flowbite de sublinhado; botões, controles e blocos internos evitam o formato de pílula e mantêm raios menores.
- O formulário de Nova mídia mantém os rótulos em bloco, com espaçamento vertical visível entre texto e controle, inclusive em modo escuro e em telas estreitas.
- Linha 2.1.0 de Recrutamento: preservar o Portal externo e alinhar Console, serviços e modelos ao fluxo QR → perfil → cargo/requisitos do RH → necessidade da loja → elegibilidade determinística → convite sem exposição nominal → interesse bilateral → negociação → contato protegido. A ordem de implementação deve manter compatibilidade e não remover rotas ou estados existentes.
- Nova mídia mantém o fluxo essencial visível e agrupa licença, validade, retenção, aprovação e acesso público em “Opções avançadas”; a validação de upload deve ser executada no schema do tenant ativo.
- A criação de mídia usa duas abas: “Dados principais” e “Opções avançadas”; abas de uso, visualização e histórico ficam disponíveis somente depois que a mídia existe.
- Erros de validação do upload aparecem no topo com o campo e a mensagem; imagens informam claramente que o texto alternativo é obrigatório.
- Substituição de mídia deve recalcular checksum mesmo quando o stream do upload foi fechado pelo handler; a restauração do cursor é tratada como operação best-effort.
- Upload individual e em lote materializam o arquivo recebido antes do checksum e do salvamento, evitando reutilizar um `UploadedFile` fechado pelo handler.
- Coleções e lote: `/console/media/collections/`, `/console/media/collections/new/` e `/console/media/upload/` usam o mesmo cabeçalho, breadcrumb, inputs, botões e escopo da Biblioteca de mídia.
- Edição de documentos: `/console/documents/<id>/edit/` usa abas de sublinhado no padrão Flowbite para alternar dados, conteúdo, versões, acesso e manutenção sem transformar cada seção em um botão-pílula.
- A aba de nova versão mantém o upload separado do histórico, que é exibido em tabela responsiva com comparação e validade.
- O shell do Console não usa linhas decorativas no topo, na lateral ou nos itens da navegação; a hierarquia é comunicada por recuo, estados ativos e breadcrumb discreto no formato “grupo > página”.
- O escopo visual e de dados das solicitações de cadastro é limitado à organização ativa; contagens e decisões não misturam tenants.
- Auditorias de conteúdo e da estrutura usam o grupo “Análises e auditoria” no breadcrumb, enquanto audiência, conformidade e gestão seguem seus grupos operacionais.
- Todas as telas do grupo “Gestão de pessoas e acessos” usam o mesmo primeiro nível do breadcrumb; no dark mode, o shell força contraste claro para itens, títulos e textos auxiliares do menu.
- Administração global e seus detalhes por organização seguem o mesmo padrão de breadcrumb, título único, abas Flowbite e rótulos em português.
- As telas de Audiência removem o eyebrow azul do grupo; o contexto fica somente no breadcrumb `Audiência > página`.
- As telas de Conteúdo e aprendizagem removem eyebrows de grupo; o contexto fica somente no breadcrumb `Conteúdo > página`, sem repetir o grupo acima do título.
- As páginas internas de MatchCo — Recrutamento não repetem o nome do grupo como eyebrow; a entrada pública continua sendo o único item que abre a experiência externa.
- As listas internas de Recrutamento usam o shell do Console, títulos únicos, breadcrumb `MatchCo — Recrutamento > página`, tabelas responsivas e estados vazios compartilhados; a opção pública permanece fora desse shell.
- Linhas de tabelas legadas que ainda usam `border-gray-100` são normalizadas para o token de linha do Console, evitando bordas brancas no dark mode.
- O grupo “Análises e auditoria” usa breadcrumb `Análises e auditoria > página`, título único em escala moderada e filtros/tabelas no shell compartilhado; as páginas não repetem eyebrows como “Analytics”, “Governança” ou “Support”.
- A auditoria legada em `/console/latest-changes/` não aparece mais no menu; o endereço antigo redireciona para `/console/content-audit/`, evitando duas páginas com o mesmo significado.
- Tabelas de métricas não usam mais variantes zebra que caem em fundos quase pretos no dark mode; as linhas usam a superfície e o divisor semântico do Console. As abas de edição de curso seguem o padrão Flowbite de sublinhado e estado ativo.
- As páginas de Operação técnica usam breadcrumb, título único e controles compartilhados; Dados de demonstração usa KPIs SVG, Ledger usa tabela responsiva e o reset mantém alerta destrutivo explícito e confirmação limitada ao desenvolvimento local.
- Formulários de Gestão de pessoas e acessos não repetem o grupo como eyebrow; o contexto fica no breadcrumb `Gestão de pessoas e acessos > Papéis de gestão > ação`.
- Novo curso e edição de curso usam título único, breadcrumb `Conteúdo > Cursos > ação`, abas Flowbite, superfícies neutras, campos do shell compartilhado e ações padrão; formulários não exibem KPIs, pois não são telas de resumo.
- Os editores de conteúdo (Feed/Wiki, documentos, biblioteca de mídia e cursos) usam abas com ícones SVG discretos, sublinhado Flowbite e a mesma seção neutra de `Permissões e audiência`; a hierarquia é sempre apresentada na ordem organização → empresa → unidades → canal/função, usando apenas os níveis disponíveis em cada modelo.
- A criação de documento não assume um objeto salvo antes do primeiro POST; URLs e pré-visualizações dependentes da versão ficam vazias até o documento existir.
- Na criação de documento, a aba externa de edição é omitida quando teria somente uma opção; permanecem as abas internas de Identificação, Conteúdo, Versão e Acesso. A aba externa volta na edição para separar Dados de Nova versão/arquivo.

- `matchco/docs/help/html/00_MATCHCO_CORE_STAKEHOLDER_FLOWS.html` — fluxo central
  dos dois stakeholders e separação entre jornadas;
- `matchco/docs/help/html/03_RECRUITMENT_COMMERCIAL_VALIDATION.html` — regras
  comerciais, visibilidade e LGPD;
- `matchco/docs/help/html/03_RECRUITMENT_BOURBON_JOURNEYS.html` — exemplo de
  shopping, QR, perguntas e catálogo de funções;
- `matchco/docs/help/html/03_RECRUITMENT_PHARMACY_JOURNEYS.html` — exemplo de
  expansão por segmento, campanhas e pré-onboarding;
- `matchco/docs/help/html/03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html` —
  execução técnica, jornadas externas, histórico e critérios de aceite.
- `matchco/docs/help/html/00_MATCHCO_ORGANIZATIONS_CHANNELS_AND_AUDIENCES.html`
  — organizações, canais, convites, aprovações, Talk e audiências.
