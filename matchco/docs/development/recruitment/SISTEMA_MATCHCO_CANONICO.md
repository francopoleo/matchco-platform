# Sistema MatchCo — Referência Canônica

Documento técnico de referência única para a **Porta Match**.
Fonte de verdade a partir dos congelamentos DR01–DR24, OQ14–OQ31, CH3/CH4 e
da arquitetura do site v1.1.

Este documento é normativo. Contradições no código são bugs a corrigir,
não licença para reinterpretar.

Data: 2026-11-19
Versão de revisão: 2.1.0 — contrato único de fluxo, catálogo e respostas
Escopo: somente a Porta Match para necessidades operacionais de alto giro.

Este é o documento único de revisão do fluxo de Recrutamento. A documentação
de ajuda em HTML e o auxílio contextual resumem esta referência; não devem
criar regras divergentes.

---

## 1. Princípios inegociáveis (congelamento)

Estes princípios governam qualquer decisão de projeto. Se uma funcionalidade
os viola, a funcionalidade está errada.

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
   base pesquisável. Nenhuma consulta livre. Nenhuma exportação.
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
15. **Sinais do Perfil têm atualidade explícita.** Desatualizado ≠ ruim.

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
mode                       # match (único modo ativo; sem CV e sem modo híbrido)
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
| `CandidateScore`, `CandidatePosition`, `ScoringRuleSet`, `rank_candidates` | **Removidos** do código e do schema pela migração `0075`; a distribuição Match usa elegibilidade e interesse, sem ranking. |
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

## 19. Contrato de produto e domínio — Recrutamento 2.1.0

Esta seção transforma a jornada Match em um contrato de implementação para
varejo, franquias e shopping. Ela não cria uma segunda hierarquia nem altera
as regras de privacidade anteriores; apenas fixa quem cadastra cada informação,
qual informação é reutilizável e quais respostas o sistema pode oferecer.

### 19.1 Vocabulário obrigatório

| Termo | Significado | Quem mantém |
|---|---|---|
| **Cargo** | Papel oficial da empresa, com descrição, remuneração, benefícios e requisitos de RH. Ex.: `Consultor de Vendas Drogasil`. | RH/empresa |
| **Função canônica** | Atividade padronizada usada para ligar cargo e Perfil. Ex.: `Vendedor de loja`, `Operador de caixa`. | MatchCo |
| **Unidade** | Loja, quiosque, loja dentro de shopping, CD ou outra operação física. | Organização/empresa |
| **Necessidade** | Demanda local declarada por uma unidade para uma quantidade de pessoas. | Gerente, com cargo aprovado pelo RH |
| **Oportunidade** | Necessidade ativada e apresentada a pessoas elegíveis. | Sistema |
| **Perfil** | Dados estruturados, reutilizáveis e controlados pela pessoa candidata. | Candidato |
| **Requisito** | Critério ligado a uma função/cargo, classificado como obrigatório, desejável ou negociável. | RH; condição local pelo gerente |
| **Match** | Interesse da pessoa + interesse da unidade. Não é contratação nem nota. | Sistema |

O produto deve preferir “necessidade” e “oportunidade” no fluxo sem currículo.
“Vaga” pode aparecer como explicação para o público, mas não deve criar um
cadastro paralelo de candidatura ou currículo.

### 19.2 Autoridade de cada participante

1. **MatchCo** mantém a taxonomia, os nomes canônicos, os chips, o significado
   das perguntas e as regras determinísticas. Ninguém cria sinônimos livres
   para participar do match.
2. **RH da empresa** cria e revisa o Cargo, escolhe funções canônicas, define
   descrição, remuneração, benefícios e requisitos. RH também decide o que é
   obrigatório, desejável ou negociável.
3. **Gerente da unidade** escolhe um Cargo já aprovado e declara a necessidade
   local: quantidade, dias, período, início, formato, unidade e condições
   específicas. Ele não cria outro Cargo nem altera a definição corporativa.
4. **Candidato** informa seu Perfil reutilizável, escolhe funções e autoriza
   onde pode aparecer. Disponibilidade e intenção são sinais atuais, não
   promessas permanentes.
5. **Sistema** compara somente respostas estruturadas, explica o resultado e
   libera cada etapa da relação conforme o consentimento e o estado.

### 19.3 Catálogo de respostas prontas (chips)

Os chips abaixo são o vocabulário inicial de demonstração e produção. A busca
é por catálogo publicado, permite múltipla seleção e não aceita texto livre
como resposta canônica. Novos chips devem ser versionados e revisados.

**Funções — selecionar as atividades, não a categoria:**

| Grupo | Chips iniciais |
|---|---|
| Vendas | Consultor de vendas; Vendedor de loja; Promotor de vendas; Atendimento comercial |
| Atendimento | Atendimento ao cliente; Recepção; Concierge de shopping; SAC presencial |
| Caixa | Operador de caixa; Frente de caixa; Fiscal de caixa |
| Estoque | Auxiliar de estoque; Repositor; Conferente; Separador de pedidos; Expedição |
| Loja | Visual merchandising; Organização de loja; Inventário; Delivery/omnichannel |
| Liderança | Líder de loja; Subgerente; Gerente de loja; Supervisor de operações |
| Alimentação e serviços | Atendente de alimentação; Barista; Auxiliar de cozinha; Recepcionista de serviços |

**Segmentos conhecidos:** Varejo; Farmácia; Moda; Alimentação; Eletrônicos;
Beleza; Casa e decoração; Esportes; Serviços; Atacado/atacarejo; Franquias;
Logística e distribuição.

**Ambientes de trabalho:** Shopping; Loja de rua; Quiosque; Loja âncora;
Franquia; Praça de alimentação; Centro de distribuição; Escritório; Operação
de serviços. Ambiente não substitui segmento: uma farmácia pode estar em um
shopping, e uma loja de moda pode ser franquia.

**Experiências e evidências declaradas:** Atendimento ao público; Vendas;
Caixa; Abertura e fechamento de caixa; Estoque; Reposição; Inventário;
Recebimento de mercadorias; Separação de pedidos; Visual merchandising;
Entrega; CRM/WhatsApp; Rotina de shopping; Rotina de franquia;
Liderança de equipe.

**Intenção para cada função:** Já trabalhei com isso; Tenho alguma experiência;
Quero trabalhar com isso; Aceito aprender.

**Disponibilidade:** Segunda, terça, quarta, quinta, sexta, sábado, domingo;
Manhã, tarde, noite, madrugada, qualquer período; início imediato ou data;
Fixo; Temporário; Fixo ou temporário; Intermitente/diária quando a política
da empresa permitir.

**Circulação autorizada:** Loja que iniciou o cadastro; Outras lojas do mesmo
shopping; Outras unidades da mesma rede; Lojas próximas do meu bairro;
Receber avisos por SMS/e-mail.

### 19.4 O que fica no Perfil e o que fica na necessidade

O primeiro cadastro deve ser curto e reaproveitável: identidade mínima,
funções de interesse, experiência/segmentos/ambientes, intenção, dias e
períodos disponíveis, formato, data de início, região/CEP de referência e
autorizações de circulação. O CEP serve para proximidade e nunca é exibido à
loja antes da etapa autorizada.

O Perfil não deve guardar como verdade permanente uma escala de uma loja,
quantidade de vagas, salário de uma oportunidade, endereço da unidade ou
perguntas inventadas por um empregador. Dias, períodos, formato e início têm
atualidade F1/F2 e podem ser confirmados quando uma oportunidade chegar.

O Cargo/necessidade guarda a descrição oficial, salário/faixa, benefícios,
função, unidade, quantidade, dias, período, início, formato e requisitos. Cada
requisito deve declarar:

- **Obrigatório:** falha impede elegibilidade;
- **Desejável:** explica relevância, mas não bloqueia;
- **Negociável:** pode ser confirmado ou ajustado depois do interesse;
- **Pode aprender:** vira convite para treinamento/integração, não reprovação.

Perguntas gerais de “já trabalhou com atendimento?” não são criadas pelo RH
como texto isolado. MatchCo cadastra a pergunta e seus chips; RH apenas escolhe
quais respostas canônicas são relevantes para o Cargo. Assim a resposta do
Perfil continua reutilizável entre empresas, sem expor histórico desnecessário.

### 19.4.1 Questionário único do candidato

Esta é a especificação do formulário que nasce no QR e pode ser reutilizado em
outras oportunidades. A pessoa responde uma vez e pode revisar os sinais
dinâmicos antes de demonstrar interesse.

| Ordem | Pergunta apresentada | Tipo de resposta | Obrigatório |
|---:|---|---|:---:|
| 1 | Como podemos chamar você? | Nome e sobrenome | Sim |
| 2 | Qual é seu celular? | Celular + confirmação OTP | Sim |
| 3 | Qual é seu e-mail? | E-mail | Não |
| 4 | Você tem 18 anos ou mais? | Sim / Não | Sim |
| 5 | Onde consegue trabalhar? | Bairros/região + CEP de referência | Sim |
| 6 | Em quais funções você teria interesse? | Funções canônicas, múltipla escolha | Sim |
| 7 | Onde você já trabalhou ou teve contato? | Segmentos e ambientes, múltipla escolha | Não |
| 8 | Quais experiências você reconhece em si? | Chips de experiência, múltipla escolha | Sim |
| 9 | Como você se relaciona com cada função escolhida? | Intenção por função | Sim |
| 10 | Em quais dias consegue trabalhar? | Dias da semana, múltipla escolha | Sim |
| 11 | Em qual período consegue trabalhar? | Manhã, tarde, noite, madrugada ou qualquer | Sim |
| 12 | Quando pode começar? | Hoje / data | Sim |
| 13 | Qual formato aceita? | Fixo, temporário, ambos ou política vigente | Sim |
| 14 | Para quem você quer aparecer? | Autorizações de circulação | Sim |
| 15 | Aceita avisos compatíveis? | Sim / Não para SMS/e-mail | Não |

**Respostas da pergunta 6 — funções de interesse:** a pessoa seleciona
`Caixa`, `Caixa de loja`, `Operador de caixa`, `Frente de caixa` ou outro
termo publicado. Se houver apelidos de busca, eles apontam para o mesmo termo
canônico; o apelido não vira um novo item. No catálogo inicial, “caixa” pode ser
um grupo de busca amigável, mas o valor salvo deve ser o termo canônico
publicado pela MatchCo.

**Respostas da pergunta 7 — segmentos e ambientes:**

- segmentos: `Varejo`, `Farmácia`, `Moda`, `Alimentação`, `Eletrônicos`,
  `Beleza`, `Casa e decoração`, `Esportes`, `Serviços`, `Atacado/atacarejo`,
  `Franquias`, `Logística e distribuição`;
- ambientes: `Shopping`, `Loja de rua`, `Quiosque`, `Loja âncora`, `Franquia`,
  `Praça de alimentação`, `Centro de distribuição`, `Escritório`, `Operação
  de serviços`.

**Respostas da pergunta 8 — experiências:** `Atendimento ao público`,
`Vendas`, `Caixa`, `Abertura e fechamento de caixa`, `Estoque`, `Reposição`,
`Inventário`, `Recebimento de mercadorias`, `Separação de pedidos`, `Organização
visual`, `Entrega`, `CRM/WhatsApp`, `Rotina de shopping`,
`Rotina de franquia`, `Liderança de equipe`.

**Respostas da pergunta 9 — intenção por função:**

| Chip | Significado usado no Match |
|---|---|
| Já trabalhei com isso | Experiência declarada diretamente relacionada |
| Tenho alguma experiência | Contato parcial ou experiência não aprofundada |
| Quero trabalhar com isso | Interesse atual, sem afirmar experiência |
| Aceito aprender | Não conhece ainda; aceita treinamento/integração |

**Respostas de disponibilidade:** dias `segunda` a `domingo`; períodos
`manhã`, `tarde`, `noite`, `madrugada`, `qualquer período`; início `imediato`
ou uma data; formato `fixo`, `temporário`, `fixo ou temporário` ou outro
formato habilitado pela política. O candidato pode marcar mais de um dia e
período.

**Respostas de circulação:** `Aparecer para a loja que escaneei`, `Aparecer
para outras lojas do mesmo shopping`, `Aparecer para outras unidades da mesma
rede`, `Aparecer para lojas próximas do meu bairro` e `Aceito receber avisos
por SMS/e-mail`. Cada opção é um consentimento separado e revogável.

### 19.4.2 Formulário de Cargo mantido pelo RH

O RH não cadastra um questionário novo para cada empresa. Ele preenche o Cargo
oficial e seleciona itens do catálogo MatchCo. O formulário deve ser revisado
na seguinte ordem:

**A. Identificação do Cargo**

- nome oficial interno: ex. `Caixa de loja sênior`;
- nome público compreensível;
- empresa responsável e situação `rascunho`, `publicado` ou `arquivado`;
- descrição curta da rotina;
- descrição detalhada das atividades;
- segmento e ambientes em que o cargo pode existir.

**B. Funções canônicas ligadas ao Cargo**

- uma ou mais funções canônicas do catálogo MatchCo;
- ordem de relevância;
- se a função é principal ou complementar;
- apelidos somente para busca, nunca para criar uma nova resposta;
- compatibilidade de cada função com a unidade e o segmento.

**C. Requisitos estruturados**

Para cada requisito, o RH escolhe uma pergunta MatchCo, seus chips válidos e
uma classe:

| Classe | Exemplo | Efeito |
|---|---|---|
| Obrigatório | Experiência `Caixa` | Sem a resposta correspondente, não elegível |
| Desejável | Experiência `Abertura e fechamento de caixa` | Exibido como ponto positivo, não bloqueia |
| Negociável | Disponibilidade `sábado` | Pode ser confirmado na relação |
| Pode aprender | `Rotina de shopping` | Permite convite para treinamento |

**D. Operação e contratação**

- faixa salarial e periodicidade;
- benefícios e adicionais;
- tipo de contratação e formato aceito;
- jornada de referência;
- dias e períodos possíveis;
- data mínima de início;
- local/empresa/unidade que poderá usar o Cargo;
- quantidade de pessoas somente na Necessidade, não no Cargo;
- campos que podem ser negociados, com limite e mensagem.

**E. Publicação**

- revisão do texto público;
- revisão dos requisitos e suas classes;
- prévia com exemplos de respostas aceitas;
- versão do Cargo e data de publicação;
- aprovação do RH antes de o gerente poder selecionar o Cargo.

### 19.4.3 Exemplo obrigatório — “Caixa de loja sênior”

O RH da empresa cadastra:

```text
CARGO OFICIAL
Nome: Caixa de loja sênior
Empresa: Drogasil
Segmento: Farmácia / Varejo
Ambiente: Shopping, loja de rua

FUNÇÕES CANÔNICAS
Principal: Caixa de loja
Também compatível: Operador de caixa, Frente de caixa

REQUISITOS
Obrigatório: experiência ou intenção na função Caixa de loja
Desejável: Abertura e fechamento de caixa
Desejável: Atendimento ao público
Desejável: Rotina de farmácia
Pode aprender: Rotina específica da loja e sistemas internos

CONDIÇÕES DO CARGO
Formato: Fixo
Períodos: manhã, tarde ou noite
Benefícios e remuneração: definidos pelo RH
```

No cadastro do candidato, as respostas possíveis continuam sendo somente as
do catálogo MatchCo:

```text
Função de interesse: Caixa de loja
Função de interesse: Operador de caixa
Experiência: Caixa
Experiência: Abertura e fechamento de caixa
Segmento: Varejo ou Farmácia
Ambiente: Shopping ou Loja de rua
Intenção: Já trabalhei com isso / Quero trabalhar com isso / Aceito aprender
```

“Caixa de loja sênior” não aparece como uma nova função do candidato. `Sênior`
é uma característica do Cargo definida pelo RH e pode exigir experiência,
responsabilidades ou remuneração diferentes. O de-para é:

```text
Caixa de loja sênior
  → Caixa de loja
  → Operador de caixa
  → Frente de caixa
```

O sistema pode aceitar `caixa`, `caixa de loja` e `operador de caixa` na busca
do candidato, mas resolve os três para termos canônicos conhecidos. O RH
escolhe quais desses termos são compatíveis com o Cargo. Se o Cargo exigir
experiência sênior como obrigatória, isso deve ser expresso por um requisito
estruturado — não pelo texto do título e não por uma nota oculta.

### 19.4.4 Dados que o gerente preenche ao criar a Necessidade

Depois de escolher `Caixa de loja sênior`, o gerente não repete o cadastro de
RH. Ele informa apenas a situação da unidade:

- unidade e responsável;
- quantidade de pessoas;
- dias reais da escala;
- período/turno e horário de referência;
- data de início;
- duração, quando temporário;
- confirmação ou ajuste dos campos negociáveis;
- observações operacionais curtas, sem criar novo requisito;
- prazo da rodada e quantidade de convites.

O servidor copia para a versão da Oportunidade a descrição, requisitos,
remuneração e funções publicadas pelo Cargo. Se RH alterar o Cargo depois, a
necessidade já publicada não muda silenciosamente: uma nova versão exige
revisão e reconfirmação.

### 19.4.5 Resultado esperado para o candidato

Para o candidato, a oportunidade deve responder com o mínimo necessário:

```text
Função: Caixa de loja
Empresa: Drogasil
Local: unidade Drogasil · Bourbon
Escala: sábado e domingo, tarde
Início: 10/12/2026
Formato: fixo

Você atende: função Caixa de loja, varejo e experiência em caixa.
Para confirmar: disponibilidade aos sábados.
Você pode aprender: rotina específica da farmácia.
```

O sistema não mostra uma porcentagem como se fosse uma avaliação pessoal. Se a
interface precisar resumir, use apenas os estados `Compatível`, `Compatível
com negociação`, `Precisa confirmar disponibilidade` e `Não elegível`, sempre
com os critérios por extenso.

### 19.5 Fluxo completo e contrato de dados

```text
RH publica Cargo + funções + requisitos
  → gerente escolhe Cargo e declara Necessidade local
  → MatchCo valida conjunto mínimo e cria versão da Oportunidade
  → sistema filtra Perfis por critérios obrigatórios e consentimento
  → convites circulam sem revelar lista nominal
  → candidato lê o conjunto completo e demonstra interesse
  → unidade vê apenas a projeção autorizada e demonstra interesse
  → MATCHED libera contato
  → somente campos negociáveis podem ser confirmados/negociados
  → unidade encerra com resposta RC-01..RC-05
```

Ao publicar ou alterar materialmente uma oportunidade, o sistema congela uma
versão contendo cargo, função, descrição, unidade, remuneração, escala,
requisitos, critérios negociáveis e prazo. Alteração material exige nova versão
e reconfirmação da pessoa; não altera silenciosamente uma relação existente.

### 19.6 Match determinístico, sem avaliação numérica

O serviço deve retornar um parecer explicável, não uma pontuação persistida:

```texto
{
  "elegivel": true,
  "percentual": 100,
  "obrigatorios": ["função", "dias", "período", "formato", "início"],
  "atendidos": ["função", "dias", "período", "formato", "início"],
  "ausentes": [],
  "negociaveis": []
}
```

`100%` significa somente que todos os critérios obrigatórios publicados foram
atendidos. Não é qualidade, classificação, probabilidade de contratação ou nota da
pessoa. Se apenas um critério negociável divergir, o resultado é **Compatível
com negociação**; se um obrigatório divergir, é **Não elegível**. A ordem da
rodada deve usar proximidade aproximada e desempate estável, nunca pontuação,
recência, “melhor candidato” ou nota oculta.

### 19.7 Negociação e respostas da MatchCo

Depois do interesse da pessoa, a tela deve responder em linguagem direta:

| Situação | Resposta exibida |
|---|---|
| Todos os obrigatórios atendidos | “Você atende aos critérios principais desta oportunidade.” |
| Só negociáveis divergem | “Você é compatível. A unidade precisa confirmar: {campos}.” |
| Obrigatório ausente | “Esta oportunidade exige {critério}. Ela não será enviada nesta rodada.” |
| Perfil desatualizado | “Confirme seus dias, período e início para continuar.” |
| Interesse registrado | “Seu interesse foi enviado. A unidade só verá seu perfil autorizado se revisar esta relação.” |
| Interesse dos dois lados | “Deu Match. O contato será liberado conforme a autorização.” |
| Sem interesse da unidade | “A unidade não avançou nesta relação. Seu Perfil continua sob seu controle.” |
| Necessidade encerrada | “Esta necessidade foi encerrada: {motivo}.” |

Chips de encerramento obrigatórios: **Seguir com esta pessoa** (RC-01);
**Seguir com outra pessoa** (RC-02); **Adiar ou cancelar a necessidade**
(RC-03); **Mudar o perfil procurado** (RC-04); **Outro motivo** (RC-05, com
nota curta). O sistema não deve usar “não se encaixa” sem explicar o critério
ou a classe de encerramento.

### 19.8 Exemplos estruturais oficiais

**Rede Drogasil:** Organização `Rede Drogasil` → empresa `Drogasil` → unidades
`Drogasil · Lapa`, `Drogasil · Perdizes`, `Drogasil · Bourbon` e CD. O RH
publica cargos como `Atendente de farmácia`, `Operador de caixa` e `Auxiliar
de estoque`; cada loja declara apenas sua necessidade local.

**Bourbon Shopping:** Organização `Bourbon Shopping` → empresa/estrutura
administrativa `Administração Bourbon` → unidades administrativas, segurança,
limpeza e manutenção; empresas lojistas como `Drogasil`, `Centauro` e outras
possuem suas lojas como unidades próprias. O shopping administra o shopping e
seus prestadores, mas não vira dono do Perfil ou dos candidatos das lojas.

### 19.9 Critérios de aceite deste contrato

- Um Cargo aprovado pelo RH é reutilizado por várias unidades sem duplicar o
  catálogo canônico.
- O gerente escolhe um Cargo e completa somente a necessidade local.
- A mesma resposta estruturada do candidato pode participar de oportunidades
  em empresas diferentes, respeitando consentimento e circulação.
- O match exibe critérios atendidos, ausentes e negociáveis; não exibe pontuação.
- A rodada usa elegibilidade + proximidade, sem classificação nominal.
- O contato só aparece após interesse bilateral e autorização.
- Shopping, rede, empresa e unidade veem apenas seu escopo.
- Toda resposta de encerramento usa um chip RC-01..RC-05.

### 19.10 Contrato de paridade entre o servidor, o Console e o Portal

O Portal e o Console são duas interfaces do mesmo domínio. O Portal não pode
ter uma regra própria de elegibilidade, estado ou permissão, e o Console não
pode criar uma necessidade que o Portal não consiga apresentar com o mesmo
significado. Ambos devem chamar os mesmos serviços de domínio e receber os
mesmos objetos versionados.

| Etapa | Servidor único | Portal candidato/lojista | Console operacional |
|---|---|---|---|
| Cadastro | `CandidateProfile`, catálogo e consentimentos | Cadastro por QR, OTP e Perfil reutilizável | Consulta/auditoria autorizada |
| Cargo/função | `JobFunction`, `CanonicalTerm`, de-para e requisitos | Apenas exibe o nome compreensível | RH configura; gerente escolhe cargo aprovado |
| Necessidade | `Position`/`Opportunity` versionada | Lojista declara a necessidade pelo fluxo público | Console declara, revisa ou acompanha a necessidade |
| Elegibilidade | Um serviço determinístico | Recebe “compatível”, “negociável” ou não disponível | Mostra critérios e contagem, sem ranking |
| Convite | `Relation` e rodada | Pessoa recebe, aceita ou recusa | Unidade acompanha interesses |
| Match | Interesse bilateral e autorização | Pessoa vê estado e contato quando liberado | Unidade responde, negocia campos permitidos e libera contato |
| Encerramento | RC-01..RC-05 no Ledger | Recebe o resultado explicado | Registra a resposta obrigatória |

Os pontos de entrada do servidor devem ser a fonte de verdade para as duas experiências:

- `candidate_is_eligible_for_position` e o futuro parecer determinístico não
  podem ser duplicados em JavaScript, template ou view alternativa;
- `open_invitation_round`, `person_interested`, `employer_interested`,
  `request_negotiation`, `respond_negotiation` e `create_response` devem ser
  usados pelo Portal e pelo Console;
- representações e projeções devem aplicar a mesma lista autorizada, organização,
  consentimento
  e versão da Oportunidade em ambas as interfaces;
- um teste de contrato deve executar cada transição por Portal e Console e
  comparar estado, eventos, critérios, mensagens e permissões;
- diferenças de texto podem existir para o papel (“Você recebeu” versus “Você
  recebeu interesse”), mas não diferenças de regra ou de dado exposto.

O Portal pode simplificar a apresentação para o candidato/gerente, mas não pode
remover uma confirmação obrigatória, aceitar um requisito que o servidor rejeita,
mostrar contato antes de `CONTACT_ENABLED` ou salvar uma resposta fora do
catálogo canônico. O Console pode expor auditoria e explicações adicionais,
mas não pode operar fora da mesma máquina de estados.

## 20. O que este documento não cobre

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
