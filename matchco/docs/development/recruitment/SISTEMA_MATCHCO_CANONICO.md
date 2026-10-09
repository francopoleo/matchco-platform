# Sistema MatchCo — Referência Canônica

Documento técnico de referência única para a **Porta Match**.
Fonte de verdade a partir dos freezes DR01–DR24, OQ14–OQ31, CH3/CH4 e
Site Architecture v1.1.

Este documento é normativo. Contradições no código são bugs a corrigir,
não licença para reinterpretar.

Data: 2026-09-29
Escopo: somente a Porta Match para necessidades operacionais de alto giro.

---

## 1. Princípios inegociáveis (freeze)

Estes princípios governam qualquer decisão de design. Se uma feature os
viola, a feature está errada.

1. **Sem currículo.** Perfil estruturado, não texto livre.
2. **Sem lista de vagas.** Candidato não pesquisa; a necessidade circula.
3. **Sem ranking.** Nenhuma pontuação persistida no candidato.
4. **Match ≠ contratação.** Match = interesse dos dois lados registrado;
   entrevista e decisão ficam fora.
5. **Interesse merece resposta.** Encerramento obrigatório com uma das 5
   classes de resposta (RC-01..05).
6. **Perfil persiste; inatividade não pausa circulação.** Só o próprio
   candidato pausa; empregador/shopping nunca reativa.
7. **Empregador não vê candidato antes de `PERSON_INTERESTED`.** Nenhuma
   base pesquisável. Nenhum browse. Nenhum export.
8. **Contato só após `MATCHED` + AA-8.** Nunca antes.
9. **Shopping/rede não é recrutador.** Só dados agregados, sem pessoa
   nominal.
10. **Dados do candidato não são ativo do shopping.** Não migram, não são
    vendidos, não fazem parte da carteira do shopping.
11. **Menor de 18 não cria Perfil (v1).** Gate antes da criação; sem
    retenção.
12. **Consentimento não é universal.** Base legal por finalidade.
13. **Telemetria de transporte ≠ empregabilidade.** GPS contínuo, wifi,
    rota nunca alimentam decisão.
14. **Toda decisão do lojista é explicável por extenso.** Nunca score
    isolado.
15. **Sinais do Perfil têm freshness explícita.** Estale ≠ ruim.

---

## 2. Máquina de estados canônica

### 2.1 Lado candidato

```
[AGE_ELIGIBLE_FOR_V1]
      │
      ▼
[PROFILE_CREATED]
      │
      ▼
[CIRCULATION_ALLOWED] ⇄ [CIRCULATION_PAUSED]     (só o candidato alterna)
      │
      ▼
[OPPORTUNITY_NOTICE_DELIVERED]
      │
      ├──► [DECLINED]  (silêncio ou toque em "não")
      │
      └──► [PERSON_INTERESTED]
                │
                ▼
        [EMPLOYER_INTEREST_VIEW_PROJECTED]  (loja passa a ver Perfil-projeção)
                │
                ├──► [NO_EMPLOYER_INTEREST] → [CLOSURE_RC-02/03/04/05]
                │
                └──► [EMPLOYER_INTERESTED]
                          │
                          ▼
                      [MATCHED]
                          │
                          ▼
                    [CONTACT_ENABLED]         (requer AA-8 do lado empregador)
                          │
                          ▼
                    (conversa externa)
                          │
                          ▼
                    [RESPONSE_CREATED]  → RC-01..05
                          │
                          ▼
                    [CLOSURE]
```

### 2.2 Lado empregador

```
[NEED_DECLARED]  → tag: PRECISA | SERIA_BOM | PODE_APRENDER
      │
      ▼
[OPPORTUNITY_STRUCTURED]  → Pre-Interest Decision Set completo
      │
      ▼
[OPPORTUNITY_ACTIVATED]   → gera versão v1
      │
      ▼
[ELIGIBLE_POOL_GENERATED] → efêmero, não persiste ranking
      │
      ▼
[OPPORTUNITY_CIRCULATED]
      │
      ▼
[PERSON_INTERESTED_RECEIVED]  (fila por Opportunity)
      │
      ▼
[EMPLOYER_INTEREST_VIEW_DELIVERED]
      │
      ├──► [NO_EMPLOYER_INTEREST]
      │
      └──► [EMPLOYER_INTERESTED]  (requer AA-7 humano)
                │
                ▼
            [MATCHED]
                │
                ▼
        [CONTACT_ENABLED]  (requer AA-8 humano)
                │
                ▼
        (conversa/entrevista externas)
                │
                ▼
        [OPPORTUNITY_CLOSED]  → RC-01..05 obrigatório
                │
                ▼
        [RESPONSE_DELIVERED_TO_PARTICIPANTS]
```

### 2.3 Regras de transição

- `PERSON_INTERESTED` só depois do candidato ver o **Pre-Interest Decision
  Set completo** (empregador, função, local, horário, tipo, remuneração,
  critérios REQUIRED materiais).
- `EMPLOYER_INTERESTED` só com **AA-7 confirmado** (ator humano
  identificado; nunca automação; nunca sponsor substituindo).
- `MATCHED` = conjunção `PERSON_INTERESTED` ∧ `EMPLOYER_INTERESTED` para o
  mesmo `(candidate_id, opportunity_id, opportunity_version)`.
- `CONTACT_ENABLED` só com **AA-8 confirmado** (destinatário autorizado).
- **Mudança material** na Opportunity (empregador, função, local, horário,
  tipo, remuneração, duração, início, critério REQUIRED) → `OPPORTUNITY_VERSION+1`
  e **reconfirmação obrigatória** do candidato. Interesse anterior fica
  vinculado à versão antiga.

---

## 3. Modelo de dados canônico

Nomes de tabela são sugestivos; o que importa é o agregado e as invariantes.

### 3.1 `CandidateProfile`

```
id (uuid)
mobile_verified            # validated mobile endpoint (não vira contato até MATCHED)
first_name, last_name
functions_of_interest[]    # taxonomia MatchCo
prior_activities[]         # ou first_job=true
geography_possibility      # raio/bairros — não é endereço detalhado
availability[day][period]  # matriz semanal
modality                   # enum: fixo | temporario | ambos
start_available_at         # data
circulation_state          # enum: ALLOWED | PAUSED
age_gate_passed_at         # timestamp; sob-18 nunca chega aqui
created_at, updated_at
```

**Não coletar por default:** CPF completo, RG, endereço detalhado, foto,
pretensão salarial, histórico com datas, empregador atual, LinkedIn URL.

### 3.2 Sinais com freshness

Cada sinal do Perfil carrega metadata própria:

```
Signal
  key                        # ex: geography_possibility
  value                      # payload
  origin                     # enum: SELF_DECLARED | COURSE_COMPLETION | CERTIFICATION | ...
  confirmed_at               # timestamp da última confirmação
  freshness_class            # enum: F0 | F1 | F2
```

**Classes de freshness:**
- **F0 durável** — sem expiração periódica (ex: experiência prévia).
- **F1 dinâmico** — expira em 90 dias (dias/turnos, geografia, formato).
- **F2 muito dinâmico** — expira em 30 dias (disponibilidade de início).

Stale ≠ ruim. Stale = **não confirmado**. Sistema pergunta antes de usar
como fato corrente em Opportunity real.

### 3.3 `Opportunity`

```
id
employer_id
version                    # inicia em 1; +1 a cada mudança material
function
workplace
schedule
type                       # fixo | temporario | ambos
compensation
tag                        # PRECISA | SERIA_BOM | PODE_APRENDER
criteria[]                 # cada um: REQUIRED | DESIRABLE | CAN_LEARN
starts_at
active_until
pre_interest_set_complete  # bool; não circula sem estar True
state                      # STRUCTURED | ACTIVATED | CIRCULATED | CLOSED
activated_at, closed_at
```

**Invariante:** `state=ACTIVATED` só com `pre_interest_set_complete=True`.

### 3.4 `Relation` (candidato × oportunidade)

Agregado central. Toda transição vive aqui.

```
id
candidate_id
opportunity_id
opportunity_version        # bind à versão específica
state                      # NOTICE_DELIVERED | PERSON_INTERESTED |
                           #   EMPLOYER_INTEREST_VIEW_PROJECTED |
                           #   EMPLOYER_INTERESTED | MATCHED |
                           #   CONTACT_ENABLED | RESPONSE_CREATED | CLOSED
person_interested_at
employer_interested_at
matched_at
contact_enabled_at
closed_at
response_class             # RC-01..05
response_note              # texto curto opcional (RC-05)
```

**Invariantes:**
- Uma `Relation` por `(candidate_id, opportunity_id, opportunity_version)`.
- Transição estritamente crescente; sem retorno.
- `MATCHED` só quando ambos `*_interested_at` estão preenchidos.

### 3.5 `EmployerInterestView` — projeção whitelist

Projeção calculada, não persistida como cópia. Regra estrita de campos:

**Inclui:**
- `first_name`, `last_name`
- Experiência/atividade **relevante à função da Opportunity**
- Disponibilidade **relevante ao horário da Opportunity**
- Respostas a critérios **REQUIRED** da Opportunity
- Fatos **DESIRABLE** relevantes

**Nunca inclui:**
- Telefone, e-mail, endereço, foto.
- Experiência não-relacionada.
- Outras Opportunities do candidato.
- Score, ranking, aderência numérica.
- Empregador atual do candidato.
- Sinais F1/F2 stale sem marca de "não confirmado".

### 3.6 `ContactChannel`

Emitido só em `CONTACT_ENABLED`. Contém endpoint móvel verificado de cada
lado. Emitido individualmente para o ator AA-8 confirmado.

### 3.7 `Ledger` — append-only

```
event_id
event_type                 # PROFILE_CREATED, PERSON_INTERESTED, EMPLOYER_INTERESTED,
                           #   MATCHED, CONTACT_ENABLED, RESPONSE_CREATED, CLOSED,
                           #   OPPORTUNITY_VERSION_BUMP, CONSENT_GRANTED, CONSENT_REVOKED,
                           #   RIGHTS_REQUEST, POINT_ACTIVATED, POINT_COMPROMISED, ...
actor_id
actor_type                 # CANDIDATE | EMPLOYER_ACTOR | OPS | SYSTEM
authority_scope            # AA-1..AA-8 quando aplicável
relation_id                # quando aplicável
opportunity_id + version   # quando aplicável
policy_version             # versão da política vigente
ip_address, user_agent
metadata (jsonb)
occurred_at                # timestamp imutável
```

**Regras:**
- **Append-only.** Nenhum UPDATE, nenhum DELETE. Correções são novos eventos
  do tipo `CORRECTION`.
- Sem PII no metadata quando evitável (usar IDs).
- Retenção RT-03 aplicada em job separado (ver §6).

### 3.8 `EntryPoint` (QR / ponto físico)

```
id
kind                       # STORE | SHOPPING | NETWORK | STANDALONE | CORPORATE_PAGE
scope_store_id
scope_shopping_id
scope_network_id
geo_lat, geo_lng
mode                       # match | vaga | hybrid  (sugestão inicial)
canonical_destination_url
tamper_evidence_hash       # binding com artefato físico
activation_tested_at
state                      # DRAFT | TESTED | ACTIVE | COMPROMISED | REVOKED
managed_by_actor_id
created_at
```

**Invariante:** `state=ACTIVE` só depois de `activation_tested_at` preenchido
e PIAG passado (ver §7).

### 3.9 `EmployerActor` e escopos de autoridade

```
EmployerActor
  id
  human_verified_at
  operation_id             # loja/rede/unidade que o ator representa
  authority_scopes[]       # subset de {AA-1..AA-8}
```

**Escopos AA:**
- **AA-1** declarar necessidade
- **AA-2** estruturar Opportunity
- **AA-3** ativar Opportunity
- **AA-4** modificar Opportunity
- **AA-5** encerrar Opportunity
- **AA-6** visualizar `EmployerInterestView`
- **AA-7** declarar `EMPLOYER_INTERESTED`
- **AA-8** receber `ContactChannel` no `MATCHED`

Cada evento no Ledger cita o `authority_scope` usado. Ação sem escopo
falha e é registrada como violação.

### 3.10 `Consent`

Granular por finalidade da circulação Match.

```
Consent
  candidate_id
  purpose                  # CIRCULATION_STORE | CIRCULATION_NETWORK |
                           #   CIRCULATION_SHOPPING | CIRCULATION_RADIUS |
                           #   VISIBILITY_MATCH |
                           #   INTEGRATION_COURSES | INTEGRATION_WIKI |
                           #   INTEGRATION_TESTS | INTEGRATION_CERTIFICATIONS |
                           #   TRANSACTIONAL_MESSAGING | ...
  policy_version
  granted_at
  revoked_at (nullable)
```

Revogação nunca é histórica: gera evento no Ledger e passa a valer daqui
para frente.

### 3.11 `RightsCase`

Canal de direitos LGPD por e-mail (fora do app).

```
RightsCase
  case_ref                 # público, curto
  requester_email
  request_type             # ACCESS | CORRECTION | DELETION | BLOCKING |
                           #   OBJECTION | PORTABILITY
  verification_state       # PENDING | VERIFIED | REJECTED
  action_state             # OPEN | IN_PROGRESS | DONE | ARCHIVED
  evidence[]               # anexos/notas
  received_at, closed_at
```

---

## 4. Escopos de acesso — matriz canônica

| Ator            | Antes de PERSON_INTERESTED | Em PERSON_INTERESTED   | Em CONTACT_ENABLED     | No fechamento        |
|-----------------|----------------------------|------------------------|------------------------|----------------------|
| Candidato       | Próprio Perfil + notificações mínimas | + `EmployerInterestView` da relação (nome do empregador, fatos relevantes) | + ContactChannel do empregador | Próprio resultado + resposta |
| Empregador AA-6+| **Nada.** Nenhum browse.   | `EmployerInterestView` (whitelist §3.5) | + `ContactChannel` do candidato | Resposta obrigatória RC-01..05 |
| Shopping/Rede   | Agregados anônimos autorizados | Idem — sem pessoa nominal | Idem                  | Idem, agregado       |
| MatchCo Ops     | Need-based; auditado       | Idem                   | Idem                   | Idem                 |

**Violações típicas a bloquear no código:**
- Empregador tenta listar candidatos sem `PERSON_INTERESTED` para aquela
  Opportunity → 403 + evento no Ledger.
- Qualquer endpoint que retorne `phone`, `email` ou `address` sem
  `CONTACT_ENABLED` na relação daquele solicitante → 403.
- Query cross-Opportunity → 403.
- Shopping tenta ver `EmployerInterestView` → 403.

---

## 5. Autoridade — AA-1..AA-8 (detalhado)

Cada ação abaixo exige o escopo respectivo. Falta de escopo = 403 + Ledger.

| Escopo | Ação                                             | Requer                         |
|--------|--------------------------------------------------|--------------------------------|
| AA-1   | Declarar `NEED_DECLARED`                         | Ator humano + operação         |
| AA-2   | Estruturar Opportunity (Pre-Interest Set)        | AA-1                           |
| AA-3   | `OPPORTUNITY_ACTIVATED`                          | AA-2 + Pre-Interest completo   |
| AA-4   | Modificar Opportunity (material → version+1)     | AA-3                           |
| AA-5   | Encerrar Opportunity                             | AA-1                           |
| AA-6   | Ler `EmployerInterestView` da relação            | Vínculo com a operação         |
| AA-7   | Marcar `EMPLOYER_INTERESTED`                     | Humano confirmado; nunca bot   |
| AA-8   | Receber `ContactChannel` em `MATCHED`            | Humano confirmado individualmente |

**Regra CH-3:** AA-7 e AA-8 **nunca** podem ser substituídos por sponsor,
plataforma ou automação. Ator humano identificável e autenticado.

---

## 6. LGPD — implementação técnica (OQ-14)

### 6.1 Bases legais por finalidade

Cada finalidade tem base legal declarada. Vazias abaixo dependem de
revisão jurídica (bloqueia PIG — ver §9).

| Finalidade                                | Base legal                       |
|-------------------------------------------|----------------------------------|
| Criação de Perfil                         | `TBD_LEGAL_REVIEW`               |
| Circulação de Opportunity                 | `TBD_LEGAL_REVIEW`               |
| Autenticação/segurança                    | `TBD_LEGAL_REVIEW` (leg. interesse esperado) |
| Divulgação ao empregador (pós-interesse)  | `TBD_LEGAL_REVIEW`               |
| Ledger/auditoria                          | `TBD_LEGAL_REVIEW`               |
| Comunicação transacional                  | Execução de contrato / consentimento |
| Integração cursos/wiki/testes/certificações | Consentimento explícito        |

### 6.2 Classes de retenção (RT-01..RT-06)

Prazos numéricos sob revisão jurídica. **Princípios frozen:**

| Classe | Escopo                                         | Prazo               |
|--------|------------------------------------------------|---------------------|
| RT-01  | Relação ativa                                  | Enquanto ativa      |
| RT-02  | Pós-encerramento (para resposta/auditoria)     | `LEGAL_REVIEW`      |
| RT-03  | Ledger/auditoria mínima                        | `LEGAL_REVIEW`      |
| RT-04  | Log de incidente de segurança                  | ≥ 5 anos (ANPD)     |
| RT-05  | Logs técnicos operacionais                     | `TECH+LEGAL_REVIEW` |
| RT-06  | Tentativa reprovada no gate de idade           | **Sem retenção**    |

**Implementação:** job periódico que aplica cada classe por tabela.
Deleção-aware backup: restore não pode "ressuscitar" Perfil deletado
legalmente (marker de exclusão persiste).

### 6.3 Direitos do titular

Canal principal: **e-mail** (não depende do app).

- **Acesso** — gera export completo (JSON + PDF humano-legível).
- **Correção** — corrige e registra `CORRECTION` no Ledger.
- **Exclusão** — anonimiza no ativo, mantém mínimo de auditoria em RT-03.
- **Bloqueio** — pausa circulação, mantém dados.
- **Oposição** — revoga base de legítimo interesse específica.
- **Portabilidade** — export em formato interoperável.

Cada pedido cria um `RightsCase`. Endpoint no app é atalho, não o canal
oficial.

### 6.4 DPIA — quando disparar

Nova finalidade de processamento; transferência internacional; coleta de
dado sensível; decisão automatizada afetando interesse; novo processador
com escopo material.

### 6.5 Registro de processadores/subprocessadores

Público. Cada linha:
- Nome do provedor + país
- Categoria de dado tratada
- Mecanismo de transferência (se cross-border)
- DPA vigente (referência + versão)
- Capacidade de deleção comprovada
- Cadeia de subprocessadores

Sem registro completo, PIG não passa.

### 6.6 Idade — gate 18+

Auto-declaração aceita. Reprovado: **sem** Perfil, **sem** waiting list,
**sem** circulação, **sem** retenção da tentativa (RT-06). Log de
segurança separado se necessário.

---

## 7. PIAG — Point Integrity Acceptance Gate

Antes de qualquer `EntryPoint` virar `ACTIVE` em produção:

1. **Destino canônico registrado** em domínio MatchCo com HTTPS.
2. **Binding QR ↔ EntryPoint** com hash tamper-evident.
3. **Teste de ativação** — humano escaneia e confirma destino.
4. **Detecção de compromisso** — monitoramento de destino resolvido.
5. **Canal de incidente** — recebe reporte de QR adulterado.
6. **Procedimento de recuperação** — reemissão + revogação.
7. **Ator autenticado** para manutenção — não basta ter telefone/WhatsApp.
8. **Vínculo evidenciado** entre ator e operação/campanha.
9. **Autoridade** — só ator autorizado modifica.
10. **Revogação** — QR comprometido vai para `COMPROMISED`; destino passa
    a servir página de aviso.
11. **Reconstrução via Ledger** — histórico auditável do ponto.

**Ator autêntico ≠ ator com autoridade.** Ter telefone da loja não dá
poder de mudar o QR. Introduzido pelo shopping não é confirmação.

---

## 8. Semântica de disponibilidade (OQ-22B / ON02)

Três dimensões **independentes**:

1. **`PROFILE_EXISTS`** — booleano.
2. **`circulation_state`** — `ALLOWED` | `PAUSED`. Só o candidato altera.
   Inatividade **nunca** move para `PAUSED`. Empregador/shopping **nunca**
   move para `ALLOWED`.
3. **Freshness dos sinais** — F0/F1/F2 por sinal.

**Stale ≠ pausado. Stale ≠ ruim. Stale ≠ prioridade menor.** Stale =
"precisa confirmar antes de usar em Opportunity real".

Não introduzir estado público "Pausado", "Inativo", "Frio" no Perfil sem
reconciliação formal (essa taxonomia é reservada).

---

## 9. PIG — Privacy Implementation Gate

**Primeiro Perfil real bloqueado** até todos os itens abaixo:

- Mapa de fluxo de dados produtivo bate com arquitetura aprovada.
- Aviso de privacidade em camadas publicado.
- Matriz papel × base legal aprovada por jurídico.
- Canal de direitos operacional (§6.3).
- Retenção RT-01..06 executável em produção.
- Prevenção de reativação pós-restore de Perfil deletado.
- Controle de acesso evidenciado (auditoria por relação).
- Registro de processadores completo (§6.5).
- Mapa de canais externos documentado.
- Baseline de segurança evidenciado (TLS, secrets, backup cifrado).
- Procedimento de incidente operacional (ANPD).
- Transferência internacional mapeada (se aplicável).
- Gate de idade 18+ ativo.
- Telemetria de transporte minimizada.

**PIG não passa → produção não sobe.** Piloto convidado admite escopo
reduzido, PIG completo antes de escala.

---

## 10. SLOs (OQ-31)

MatchCo contrata só o que controla.

| Serviço                         | Status  |
|---------------------------------|---------|
| Disponibilidade do fluxo de entrada | SC-0 (designed) |
| Reconhecimento/contenção de incidente | SC-0 |
| Recuperação de exceção          | SC-0    |
| Manuseio de incidente de Ponto  | SC-0    |
| Criação de Resposta ao participante | SC-1 (piloto) |
| Governança de resposta do empregador | SC-1 (mecanismo) |

**Não contratáveis:** garantia de match, garantia de contratação, tempo
de resposta de empregador/candidato, entrevista, ausência de falha.

Números só a partir de dados de piloto. Contratos comerciais nunca citam
SC-2 antes de evidência.

---

## 11. Stack v1 — declaração

**Dentro do v1:**
- Django + Postgres (compute + DB primária).
- Ledger como tabela append-only no mesmo Postgres.
- Autenticação passwordless (mobile + OTP).
- Provedor de OTP/SMS/WhatsApp (`TBD_VENDOR`).
- E-mail transacional próprio (`TBD_VENDOR`).
- TLS + edge (`TBD_VENDOR`).
- Backup gerenciado cifrado com deleção-aware restore.

**Fora do v1:**
- App nativo.
- Push notification.
- Analytics de produto.
- BI para sponsor.
- Integração ATS terceiro.
- Parser de CV.
- Vendor de ranking/score.
- Background check.
- IA em produção.
- Survey externo.

**Região BR:** obrigatória para dados de titular. Cross-border só com
mecanismo ANPD explícito.

---

## 12. Rotas canônicas (do site copy v1.1)

### 12.1 Público
- `GET /`
- `GET /como-funciona`
- `GET /?point={POINT_ID}` (resolução QR)
- `GET /privacidade`
- `GET /privacidade/direitos`

### 12.2 Candidato
- `GET|POST /entrar` (OTP)
- `POST /auth/otp-request`
- `POST /auth/otp-verify`
- `GET|POST /perfil`
- `GET /oportunidades`
- `GET /candidato/oportunidades/{id}` (Pre-Interest Decision Set)
- `POST /candidato/oportunidades/{id}/interesse` → `PERSON_INTERESTED`
- `GET /matches`
- `GET /matches/{id}/contato` (só se `CONTACT_ENABLED`)
- `GET /respostas`

### 12.3 Empregador
- `POST /empregador/entrar`
- `GET /empregador/operacoes`
- `GET|POST /empregador/operacoes/{op}/oportunidades`
- `POST /empregador/operacoes/{op}/oportunidades/{id}/ativar`
- `GET /empregador/operacoes/{op}/oportunidades/{id}/interesse` (lista `EmployerInterestView`)
- `POST /empregador/operacoes/{op}/oportunidades/{id}/interesse/{rel}/responder` → `EMPLOYER_INTERESTED`
- `GET /empregador/matches`
- `GET /empregador/matches/{id}/contato` (AA-8)
- `POST /empregador/operacoes/{op}/oportunidades/{id}/encerrar` → RC-01..05

### 12.4 Ops
- `GET /ops/points`
- `GET /ops/ledger` (restrito)
- `GET /ops/rights-cases`
- `POST /ops/incidents`

### 12.5 Aplicação autenticada (PWA /app/)

Progressive Web App para usuários autenticados com organização selecionada.
Requer autenticação + `selected_organization` no contexto da sessão.

**Dashboard & Perfil:**
- `GET /app/` (dashboard principal)
- `GET /app/profile/` (visualizar perfil)
- `GET|POST /app/profile/edit/` (editar perfil)
- `GET /app/settings/` (configurações da conta)

**Cursos & Aprendizado:**
- `GET /app/courses/` (lista de cursos do usuário)
- `GET /app/courses/{id}/` (detalhes do curso)
- `GET /app/courses/{id}/play/` (player de vídeo)
- `GET /app/courses/{id}/progress/` (progresso do curso)

**Conteúdo & Comunidade:**
- `GET /app/feed/` (feed de notícias — publications com kind='feed')
- `GET /app/trails/` (minhas trilhas de aprendizado — TrailAssignment)
- `GET /app/wiki/` (base de conhecimento — publications com kind='wiki')

**Conexões & Recrutamento:**
- `GET /app/matches/` (lista de matches/conexões)
- `GET /app/matches/{id}/` (detalhe de match + chat)
- `GET /app/recruitment/` (dashboard de recrutamento)
- `GET /app/recruitment/candidates/` (lista de candidatos)
- `GET /app/recruitment/positions/` (vagas abertas)

**Ajuda & Notificações:**
- `GET /app/help/` (centro de ajuda)
- `GET /app/help/{topic}/` (tópico específico)
- `GET /app/notifications/` (centro de notificações)
- `POST /app/notifications/{id}/read/` (marcar notificação como lida)

**Roteamento inteligente:**
- Usuário não autenticado → `/login/`
- Usuário autenticado sem organização → `/select-organization/`
- Admin (is_staff) → `/console/`
- Usuário com organização → `/app/` (dashboard)

---

## 13. Integrações — contrato

Integração com **Cursos, Wiki, Testes, Certificações** é opcional e via
`matchco/recruitment/integrations/registry.py`. Nunca import estrutural.

### 13.1 Regras

- Sinais viram tags F0/F1/F2 do Perfil, nunca score.
- Cada integração exige consentimento explícito (`Consent.purpose`
  correspondente).
- Sempre exibidas por extenso na `EmployerInterestView` — nome do curso,
  data, expiração da certificação.
- Sem cálculo automático de "qualidade" agregada.
- Sinal expira e some do card sozinho (F1/F2). Candidato é lembrado antes.

### 13.2 Portas
- `integrations/courses.py` — `on_course_completed(user, course)`
- `integrations/wiki.py` — apenas leitura, não altera Perfil
- `integrations/tests.py` — `on_test_result(user, test, result)` (escopo:
  aquela Opportunity, não Perfil)
- `integrations/certifications.py` — `on_certification_granted(user, cert, valid_until)`

---

## 14. Ledger — invariantes de código

- **INSERT-only.** Nenhum ORM UPDATE. Nenhum DELETE. Correção = novo evento.
- Chave imutável: `(event_id UUID, occurred_at)`.
- Índices: por `actor_id`, `relation_id`, `opportunity_id`, `event_type`,
  `occurred_at`.
- Retenção RT-03 aplicada por job de arquivamento (não DELETE do vivo —
  export cifrado + purga programada com dupla verificação).
- Nenhuma PII em `metadata` quando referenciável por ID.
- Todo endpoint mutativo grava evento antes do commit.

---

## 15. RC-01..RC-05 — classes de resposta

Encerramento sem RC é bug bloqueante.

| Classe | Significado                                    |
|--------|------------------------------------------------|
| RC-01  | Seguirei com esta pessoa                       |
| RC-02  | Seguirei com outra pessoa                      |
| RC-03  | Adiei/cancelei a necessidade                   |
| RC-04  | Mudou o perfil que preciso                     |
| RC-05  | Outro motivo (nota curta obrigatória, honesta) |

**Motivos inventados/genéricos** ("não se encaixa no perfil" sem
qualificação) são rejeitados no formulário.

Silêncio prolongado após `MATCHED` bloqueia novas declarações do
empregador até resposta gerada.

---

## 16. Gaps concretos vs. código atual

| Área                          | Ação                                            |
|-------------------------------|-------------------------------------------------|
| `CandidateScore`, `match_score`, `rank_candidates` | **Remover**; a distribuição Match usa elegibilidade e interesse, sem ranking. |
| `resume_text`                 | **Remover.**                                    |
| Listagem pública de vagas     | **Remover** da Porta Match.                    |
| `Position`                    | Renomear para `Opportunity` + adicionar version + tag + criteria taxonomy |
| `CandidateApplication`        | Remover; o fluxo atual usa `Relation` com máquina de estados |
| `RecruitmentAuditEvent`       | Refatorar para `Ledger` append-only + policy_version + authority_scope |
| Ausência de `EntryPoint`      | **Criar** + PIAG + roteamento QR                |
| Ausência de AA-1..8           | **Criar** `EmployerActor` + escopos + guard em cada action |
| Ausência de `EmployerInterestView` | **Criar** projeção whitelist + endpoint scopeado |
| Ausência de `ContactChannel`  | **Criar** + liberação só em `CONTACT_ENABLED`   |
| Ausência de RC-01..05         | **Criar** + form obrigatório no encerramento    |
| Ausência de gate de idade     | **Criar** antes de `PROFILE_CREATED`            |
| Consentimento genérico        | Refatorar para `Consent.purpose` granular       |
| Ausência de `RightsCase`      | **Criar** + inbox de e-mail + workflow          |
| Ausência de RT-01..06 executável | **Criar** job periódico com testes             |
| Ausência de freshness F0/F1/F2 | **Adicionar** ao modelo de sinais              |
| Falta de registro de processadores | **Criar** página pública + gestão interna    |
| Falta de página de privacidade | **Criar** `GET /privacidade` em camadas        |

---

## 17. Blocking gates para produção

Ordem de barreiras. Nenhum Perfil real cadastrado até tudo passar.

1. **PIG** — §9 completo.
2. **PIAG** — §7 completo, para cada `EntryPoint` produtivo.
3. **AA-7/AA-8 humano** — nenhum atalho para automação.
4. **Ledger append-only** com testes garantindo ausência de UPDATE/DELETE.
5. **Rights channel** operacional (§6.3).
6. **RT-01..06** com job rodando.
7. **RC-01..05** obrigatório no encerramento.
8. **Registro de processadores** publicado.
9. **DPO** identificado.
10. **Página de privacidade** publicada.

---

## 18. O que este documento não cobre

- UI/UX detalhado — cabe ao design system.
- Textos de copy — cabe ao site copy v1.1.
- Modelo comercial/pricing — cabe ao master estratégico.
- SLOs numéricos — cabe a decisão pós-piloto.

Contradições entre este documento e código: código está errado.
Contradições entre este documento e freeze/DR/OQ/CH originais: freeze
vence, atualizar este documento.

---

*Última revisão: 2026-09-29.
Fonte primária: `/Users/franco/Downloads/AI/` — DR01–DR24, OQ14–OQ31,
CH3/CH4, `FREEZE_Mestre_Sistema_Candidato_v1.0`, `FREEZE_Shopping_Center_v0.2`,
`Strategic_Decisions_Master_v1.1`, `Site_Architecture_and_Copy_v1.1`.*
