# TALK — Plano Executivo Detalhado

**Data**: 2026-07-24  
**Versão**: 2.0 (Progressive Growth Strategy)  
**Status**: Pronto para Execução

## POSICIONAMENTO DO PRODUTO

**Talk** é uma **Plataforma de Comunicação e Engajamento Operacional**.  
Slogan: **Menos ruído. Mais aderência à operação.**

O frontend autenticado apresenta somente a marca Talk. “Talk Learning” fica restrito ao contexto de cursos e aprendizagem; a plataforma como um todo também cobre Feed, Wiki, audiência, comunicação e melhoria contínua.

---

## 🚀 ESTRATÉGIA CORE: "PROGRESSIVE GROWTH"

### O Problema com Plataformas Tradicionais

Docebo, SAP, Moodle fracassam no dia 1 porque:
- ❌ Oferecem 500 features, usuário se perde em 20
- ❌ Sistema fica vazio por semanas enquanto admin configura
- ❌ Ciclo de implementação: 6+ meses
- ❌ Adoption: 40-50% (resto abandona)

### A Solução Talk: "Start Lean, Grow Intentional"

**Cada cliente começa com apenas o que PRECISA USAR no dia 1:**

```
SEMANA 1: 5 features essenciais + 75% adoption
SEMANA 2-3: 1-2 features novas despertam naturalmente
SEMANA 4: Sistema tem 12 features, completamente customizado
MÊS 2: 85% adoption, ROI visível
MÊS 3+: Cliente pede expansão (not abandonment)
```

**Diferença**: Docebo espera você usar (e desiste), Talk cresce conforme você usa (e quer mais).

### Impacto na Venda

| Métrica | Docebo | Talk |
|---------|--------|------|
| Tempo até ROI | 6+ meses | 30 dias |
| Adoption | 40% | 85% |
| Ciclo de vendas | 120+ dias | 21 dias |
| CAC Payback | 9+ meses | 5-10 dias |
| Net Retention | 85% | 130%+ |

---

## 📋 ÍNDICE

1. [Plano de Desenvolvimento (Sprints)](#plano-de-desenvolvimento)
2. [Estratégia Progressive Growth (Implementação)](#estratégia-progressive-growth-implementação)
3. [Plano de Marketing & GTM](#plano-de-marketing)
4. [Modelo de Negócio](#modelo-de-negócio)
5. [Arquitetura de Integração](#arquitetura-de-integração)
6. [Estratégia de Vendas](#estratégia-de-vendas)
7. [Feedback e Aderência](#feedback-e-aderência)
8. [Inteligência de Conteúdo e Trilhas](#inteligência-de-conteúdo-e-trilhas)

---

## FEEDBACK E ADERÊNCIA

Feedback é uma capacidade estratégica do Talk para medir se a informação realmente ajudou a operação. Não será um mural público: será um sinal privado, contextual e controlado.

### MVP recomendado

- Pergunta contextual: **“Esta informação ajudou?”**
- Respostas: sim, parcialmente ou não.
- Motivo opcional para respostas parcial/negativa.
- Permissão por organização, unidade, função e canal.
- Inbox privado para o responsável pelo conteúdo.
- Métricas por conteúdo, versão e audiência.

### Critério de priorização

```text
prioridade = alcance × taxa de não utilidade × criticidade operacional
```

O indicador evita transformar feedback em volume de comentários. O objetivo é localizar conteúdos muito acessados que ainda não ajudam e corrigir sua causa.

### Evolução

Depois do MVP, entram casos com status, SLA, comparação entre versões, resposta privada, integração com suporte e relatórios de aderência/ROI. A especificação completa está em [FEEDBACK_AND_ADHERENCE_PLAN.md](FEEDBACK_AND_ADHERENCE_PLAN.md).

## INTELIGÊNCIA DE CONTEÚDO E TRILHAS

Esta frente conecta comunicação, conhecimento, aprendizagem e evidência operacional. O plano detalhado e o checklist completo estão em [CONTENT_INTELLIGENCE_ANALYTICS_PLAN.md](CONTENT_INTELLIGENCE_ANALYTICS_PLAN.md).

### Estado atual

- [x] Eventos unificados para conteúdo e aprendizagem.
- [x] Trilhas versionadas com etapas, dependências, audiência e progresso.
- [x] Recomendações elegíveis na Home.
- [x] Editor e atribuição de trilhas no Console.
- [x] Relatório inicial de progresso e funil de aderência.

### Ordem obrigatória das próximas entregas

1. expansão de audiência para usuários elegíveis;
2. página Minhas trilhas e progresso no frontend;
3. recomendações contextuais após leitura, busca e feedback;
4. analytics avançado de abandono, versões e utilidade;
5. cursos, quizzes, certificados e evidências;
6. notificações internas, e-mail e push controlado;
7. ROI, privacidade, exportação e auditoria.

Não avançar para recomendações automáticas ou push amplo sem preservar a elegibilidade de audiência, a explicação do motivo e os limites de privacidade.

---

## 🚀 PLANO DE DESENVOLVIMENTO

### Visão Geral
**Tempo Total**: 18 meses (6 fases, 18 sprints)  
**Investimento**: ~$1.5M  
**Team**: 8-10 pessoas  
**MVP Versão**: 3-4 meses (com Progressive Growth ativo)
**Diferencial**: Cada cliente começa enxuto, cresce conforme necessário

---

### FASE 1: MVP (Sprint 1-6, Semanas 1-12)

#### Módulo documental entregue no núcleo do Talk

- [x] Documento lógico separado de suas versões físicas/textuais.
- [x] Audiência por organização e política de acesso.
- [x] Histórico de versões, vigência, expiração, resumo de alteração e arquivamento.
- [x] Visualização, download, tempo ativo e auditoria por usuário/versão.
- [x] Console de gestão e biblioteca documental no frontend.
- [x] Integração de documentos vinculados na criação/edição de Feed e Wiki.
- [x] Integração de documentos vinculados na criação/edição de cursos.
- [x] Integração de documentos vinculados na criação/edição de módulos.

#### Sprint 1-2 (Semanas 1-4): Infra & Documentos Básico

**Objetivo**: Document Management MVP

**Backend**:
- [x] Model: Document (title, description, file, version, category)
- [x] Model: DocumentVersion (track changes)
- [x] Model: DocumentPermission (who can view/download)
- [x] Upload handler (PDF, IMG, DOC, VIDEO)
- [x] S3/storage integration: adapter `django-storages` configurável por `TALK_STORAGE_BACKEND=s3`; credenciais/bucket permanecem deployment-specific
- [x] Search API (endpoint autenticado de documentos por título/código; Elasticsearch continua como adapter opcional de escala)
- [x] Audit log (quem fez o quê quando)

**Frontend**:
- [x] Upload widget (drag-drop com feedback de nome e suporte a teclado)
- [x] Document library page (list view)
- [x] Version history view
- [x] Download tracking
- [x] Share dialog (set permissions)

**Banco de Dados**:
```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY,
  title VARCHAR(255),
  description TEXT,
  category_id FK,
  created_by FK,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  expires_at TIMESTAMP,
  status ENUM('draft', 'published', 'archived')
);

CREATE TABLE document_versions (
  id UUID PRIMARY KEY,
  document_id FK,
  file_url TEXT,
  version_number INT,
  changelog TEXT,
  created_at TIMESTAMP
);

CREATE TABLE document_permissions (
  id UUID PRIMARY KEY,
  document_id FK,
  user_id FK / group_id FK,
  permission ENUM('view', 'download', 'edit', 'delete'),
  expires_at TIMESTAMP
);

CREATE TABLE document_downloads (
  id UUID PRIMARY KEY,
  document_id FK,
  user_id FK,
  downloaded_at TIMESTAMP,
  ip_address VARCHAR(255),
  device_info TEXT
);
```

**Deliverables**:
- Demo: Upload documento → compartilhar com grupo → download rastreado
- API: POST /documents, GET /documents, GET /documents/{id}/downloads
- Admin: Ver histórico de downloads por documento

Implementação atual: além da interface web, o contrato autenticado está disponível em `/api/v1/documents/`, `/api/v1/documents/{id}/downloads/` e `/api/v1/documents/{id}/versions/`. A API respeita a audiência e limita o histórico detalhado a gestores.

---

#### Sprint 3-4 (Semanas 5-8): Notificações & Analytics Básico

**Objetivo**: Smart notifications + Analytics dashboard simples

**Backend - Notifications**:
- [x] Celery setup opcional: `cep/celery.py`, tarefas de webhook/retry em `learning/tasks.py`, configuração de broker/beat e fallback por management command
- [x] Templates de e-mail versionados em texto/HTML (`learning/templates/learning/emails/`), com envio multipart e auditoria de entrega
- [x] Notification models: UserNotification, entrega por canal, preferências e NotificationRule declarativa com condições e ação auditável
  ```python
  class Notification:
    - type: (new_doc, doc_updated, course_expired, urgent_alert)
    - trigger: (manual, automatic via rule)
    - recipient: (user, group, everyone)
    - scheduled_at (send agora ou agendar)
    - status (pending, sent, failed)
  ```
- [x] Rules engine: regras de publicação/atualização/arquivamento de documentos avaliadas contra categoria, prioridade, audiência e organização
  ```python
  # Exemplo de regra
  IF document uploaded AND category = "Urgent"
  THEN notify group "Managers" via email + push
  AND add to mobile app notification center
  ```
- [ ] Push notifications (Firebase Cloud Messaging) (Web Push VAPID implementado; FCM mobile permanece futuro)
- [x] In-app notification center (bell icon)
- [x] Unsubscribe/preference management

**Frontend - Analytics**:
- [x] Dashboard básico: Console com resumo de usuários, conteúdos, cursos, regras, atividade e métricas agregadas
  ```
  [Total users: 0]  [Active this week: 0]
  [Documents viewed: 0]  [Courses completed: 0%]
  
  Recent activity:
  - John completed "Safety Training" (2h ago)
  - New doc: "Price List v2.1" (4h ago)
  - Maria downloaded "Manual.pdf" (1d ago)
  ```
- [x] User engagement report: métricas de acesso, leitores, tempo ativo, retorno, abandono, feedback, dúvidas e ações operacionais
  - Last login
  - Docs viewed
  - Courses completed
  - Time spent
- [x] Document stats: visualizações, leitores, downloads, tempo ativo, uso por versão e vencimentos/arquivamento
  - Downloads count
  - Views count
  - Most downloaded
  - Expiring soon

**Banco de Dados**:
```sql
CREATE TABLE notifications (
  id UUID PRIMARY KEY,
  type VARCHAR(50),
  title TEXT,
  message TEXT,
  recipient_id FK / group_id FK,
  created_by FK,
  scheduled_at TIMESTAMP,
  sent_at TIMESTAMP,
  status ENUM('pending', 'sent', 'failed'),
  created_at TIMESTAMP
);

CREATE TABLE notification_rules (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  trigger_type VARCHAR(50),
  condition JSON, -- {"documentCategory": "urgent", "userGroup": "managers"}
  action JSON, -- {"type": "email", "template": "new_doc"}
  enabled BOOLEAN,
  created_by FK
);

CREATE TABLE user_notification_preferences (
  id UUID PRIMARY KEY,
  user_id FK,
  notification_type VARCHAR(50),
  via_email BOOLEAN,
  via_push BOOLEAN,
  via_inapp BOOLEAN
);

CREATE TABLE analytics_events (
  id UUID PRIMARY KEY,
  event_type VARCHAR(50), -- 'document_viewed', 'document_downloaded', 'course_completed'
  user_id FK,
  object_id FK, -- document_id ou course_id
  object_type VARCHAR(50),
  properties JSON,
  timestamp TIMESTAMP
);
```

**Deliverables**:
- Demo: Criar documento → Notifica grupo automaticamente
- Admin pode criar regras de notificação
- Dashboard mostra "João completou X, 50% da turma já fez"
- API: POST /notifications/rules, GET /analytics/engagement

---

#### Sprint 5-6 (Semanas 9-12): Partner Portal & Auth Melhorado

**Objetivo**: Suportar múltiplos públicos (internos, parceiros, clientes)

**Backend**:
- [x] Role-based access control (RBAC) melhorado: grupos content_manager/audience_manager, atribuições de gestão por audiência e mixin de proteção do Console
  ```python
  roles = [
    'admin', 'content_manager', 'partner_manager',
    'partner_viewer', 'internal_user', 'customer', 'guest'
  ]
  
  permissions = {
    'admin': ['all'],
    'content_manager': ['create_doc', 'edit_doc', 'manage_users'],
    'partner_manager': ['view_partners', 'edit_partner', 'view_partner_analytics'],
    'partner_viewer': ['view_own_content', 'download', 'view_own_analytics'],
    'internal_user': ['view_internal', 'complete_courses', 'download'],
    'customer': ['view_public', 'download_public'],
    'guest': ['view_public_only']
  }
  ```
- [ ] SSO/SAML (Google, Azure AD, SAML genérico)
- [x] Partner portal models: `Partner` e `PartnerMembership` por organização, função viewer/manager, status, gestor responsável e metadata; métricas são calculadas a partir dos eventos auditáveis
  ```python
  class Partner:
    - name
    - company
    - email
    - status (active/inactive)
    - assigned_manager_id
    - metadata (custom fields)
    - created_at
    
  class PartnerAnalytics:
    - documents_downloaded (count)
    - courses_completed (count)
    - last_activity (timestamp)
    - engagement_score (%)
  ```
- [x] API key generation (credenciais por organização, hash SHA-256, escopos, expiração, rotação e revogação)

**Frontend**:
- [x] Partner portal home: `/partner/` e `GET /api/v1/partner/me/` com recursos elegíveis, cursos matriculados, conclusões, pontos e última atividade
  ```
  [Welcome João - Oficina XYZ]
  [Documents: 15]  [Completed Courses: 3/5]  [Last Login: 2h]
  
  Your Resources:
  - Manuais de procedimento (5 docs)
  - Tabela de preços (1 doc, updated 2d ago)
  - Vídeos de treinamento (3 videos)
  
  Your Performance:
  - Documents downloaded: 24
  - Courses completed: 60%
  - Chat support: 2 pending messages
  ```
- [x] Permission-based UI (oculta recursos fora da membership/audiência do parceiro)
- [x] Analytics privada (o portal e a API retornam apenas atividade do usuário/parceiro autenticado)

**Banco de Dados**:
```sql
CREATE TABLE partners (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  company VARCHAR(255),
  email VARCHAR(255),
  api_key VARCHAR(255) UNIQUE,
  role_id FK,
  assigned_manager_id FK,
  status ENUM('active', 'inactive', 'suspended'),
  metadata JSON,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE partner_analytics (
  id UUID PRIMARY KEY,
  partner_id FK,
  documents_downloaded INT DEFAULT 0,
  courses_completed INT DEFAULT 0,
  last_activity TIMESTAMP,
  total_time_spent INT, -- em minutos
  engagement_score FLOAT, -- 0-100
  updated_at TIMESTAMP
);

CREATE TABLE api_keys (
  id UUID PRIMARY KEY,
  partner_id FK,
  key VARCHAR(255) UNIQUE,
  secret VARCHAR(255),
  name VARCHAR(255),
  last_used TIMESTAMP,
  created_at TIMESTAMP,
  expires_at TIMESTAMP
);
```

**Deliverables**:
- Demo: 3 tipos de usuários acessam portais diferentes
- Partner vê só seu conteúdo
- Admin controla quem vê o quê via permissões
- API key para partners integrarem

---

### FASE 2: Funcionalidades Críticas (Sprint 7-12, Semanas 13-24)

#### Sprint 7-8 (Semanas 13-16): Mobile App MVP

**Tecnologia**: React Native (ambos iOS + Android)

**Features**:
- [ ] Autenticação (biométrico + password)
- [ ] Offline mode:
  - Baixa documentos/cursos pra visualizar offline
  - Sincroniza quando conecta (background)
  - Rastreia downloads offline (marca como "viewed" quando sync)
- [ ] Push notifications (sistema nativo)
- [x] Document viewer (PDF, imagens e conteúdo textual), com registro de versão, tempo ativo, download e auditoria
- [ ] Cursos modo learning (offline-capable)
- [ ] Status bar (engajamento, próximas ações)
- [ ] Feedback widget (screenshot + message)

**Backend - Sync API**:
```
GET /api/mobile/sync?last_sync=2026-07-24T10:00:00Z

Response:
{
  "documents": [{id, title, updated_at, file_url, version}],
  "courses": [{id, title, progress}],
  "notifications": [{id, message, read}],
  "sync_complete_at": "2026-07-24T10:05:00Z"
}

POST /api/mobile/events
{
  "events": [
    {type: "document_viewed", document_id: "x", timestamp: "2026-07-24T09:00:00Z"},
    {type: "course_completed", course_id: "y", score: 95, timestamp: "2026-07-24T10:00:00Z"}
  ]
}
```

**UI Pattern**:
```
Tab 1: Home
  - "Boas-vindas João"
  - Cards de próximas ações
  - Documentos recentes
  - Cursos em progresso

Tab 2: Documentos
  - Lista com busca
  - Categorias
  - Downloads (com indicador offline)

Tab 3: Cursos
  - Progress bar
  - Próximas aulas

Tab 4: Notifications
  - Bell icon
  - Centro de notificações
  - Mark as read

Tab 5: Perfil
  - Info pessoal
  - Certificados
  - Histórico
  - Logout
```

**Deliverables**:
- App funcional iOS + Android
- Offline-first experience
- Sync automático quando volta online

Contrato de backend já disponível para o cliente mobile: `/api/mobile/sync/` e `/api/mobile/events/`. O app React Native, biometria e armazenamento offline são entregas de cliente fora deste repositório.

O frontend web também é instalável como PWA: `/service-worker.js` fornece cache do shell, fallback offline e entrega Web Push; o manifest está em `static/ui/manifest.webmanifest`.

---

#### Sprint 9-10 (Semanas 17-20): API Robusta & Integrações

**Objetivo**: Parceiros conseguem integrar Talk com seus sistemas

**API REST**:
```
Authentication:
  POST /api/v1/auth/login          (username + password)
  POST /api/v1/auth/oauth/google   (OAuth)
  POST /api/v1/auth/saml           (SAML SSO)
  
Documents:
  GET    /api/v1/documents
  POST   /api/v1/documents
  GET    /api/v1/documents/{id}
  PUT    /api/v1/documents/{id}
  DELETE /api/v1/documents/{id}
  POST   /api/v1/documents/{id}/versions
  GET    /api/v1/documents/{id}/downloads
  
Courses:
  GET    /api/v1/courses
  POST   /api/v1/courses/{id}/enroll
  POST   /api/v1/courses/{id}/complete
  
Users:
  GET    /api/v1/users
  POST   /api/v1/users
  GET    /api/v1/users/{id}
  PUT    /api/v1/users/{id}
  
Analytics:
  GET    /api/v1/analytics/engagement
  GET    /api/v1/analytics/documents
  GET    /api/v1/analytics/courses
```

**Webhooks** (Partner → Talk):
```
POST https://talk.com/webhooks/events

Events:
- user.created
- user.updated
- document.viewed
- document.downloaded
- course.completed
- notification.sent
```

**Webhooks** (Talk → Partner ERP):
```
Partner configura:
  POST https://erp.cliente.com/webhooks/talk

Quando Talk recebe:
  - Document uploaded
  - Course completed
  - User engagement milestone
  
Envia pro ERP do parceiro para logging/sync
```

**SDKs**:
- [x] Python SDK source client em `sdk/python/`, cobrindo documentos, analytics, partner portal e sincronização mobile
- [x] Node.js SDK source client em `sdk/node/`, compatível com `fetch` do Node 18+
- [x] PHP SDK source client em `sdk/php/`, baseado em cURL
- [x] OpenAPI/Swagger docs: schema existente em /doc/ e contratos REST v1 para documentos, analytics e sincronização mobile

**Deliverables**:
- Documentação OpenAPI completa
- 3 SDKs funcionais
- Exemplos de integrações
- API rate limiting (100 req/min for partners)

---

#### Sprint 11-12 (Semanas 21-24): Gamification & Community

**Objetivo**: Aumentar engajamento 30-50%

**Gamification**:
- [x] Points system: ledger imutável derivado de eventos, com pontuação para leitura, conclusão, quiz, trilha e ação operacional
  ```python
  points_for = {
    'course_completed': 100,
    'document_read': 10,
    'quiz_perfect_score': 50,
    'community_answer': 25,
    'badge_achieved': 50
  }
  ```
- [x] Badges: definições configuráveis e concessão automática por limiar de pontos
  ```
  - "Primeira aula" (complete any course)
  - "Leitor assíduo" (50 docs read)
  - "Expert" (100 points)
  - "Semana perfeita" (no absences)
  - "Mentor" (ajudou 10 colegas)
  ```
- [x] Leaderboard privado por organização, com pontuação derivada do ledger, ranking interno e API `GET /api/v1/gamification/leaderboard/`.
  - Top 10 por departamento/semana
  - "João está #3 essa semana"
  - Badges visíveis no perfil
- [x] Challenges: desafios semanais/mensais com progresso e conclusão por usuário
  - "Complete 3 cursos essa semana"
  - "Leia 5 manuais"
  - Duração: 1 semana, 1 mês, trimestral

**Community**:
- [ ] Forums por departamento/tema
- [ ] Q&A (Stack Overflow style)
- [ ] Reputation system
- [ ] Moderation tools (block spam)

**Banco de Dados**:
```sql
CREATE TABLE user_points (
  id UUID PRIMARY KEY,
  user_id FK,
  points_total INT DEFAULT 0,
  points_this_week INT DEFAULT 0,
  points_this_month INT DEFAULT 0,
  updated_at TIMESTAMP
);

CREATE TABLE badges (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  icon_url TEXT,
  description TEXT,
  condition JSON, -- {type: "courses_completed", value: 10}
  created_at TIMESTAMP
);

CREATE TABLE user_badges (
  id UUID PRIMARY KEY,
  user_id FK,
  badge_id FK,
  achieved_at TIMESTAMP
);

CREATE TABLE leaderboards (
  id UUID PRIMARY KEY,
  user_id FK,
  rank INT,
  points INT,
  period VARCHAR(50), -- 'week', 'month', 'all_time'
  scope VARCHAR(50), -- 'department', 'company', 'global'
  updated_at TIMESTAMP
);
```

**Deliverables**:
- Leaderboard funcional
- 10 badges definidas
- Forums com moderação
- Points rastreados

---

### FASE 3: Escalabilidade & AI (Sprint 13-18, Semanas 25-36)

#### Sprint 13-14 (Semanas 25-28): Integrações com ERPs

**Objetivo**: Sincronizar dados do cliente (pacientes, clientes, documentos) com Talk

**Padrão de Integração**:
```
┌─────────────────────────────────────────────────┐
│ CUSTOMER ERP (TASY, SAP, etc.)                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ Patients/Clientes: João Silva (ID: 123)   │ │
│ │ Documentos: Manuais, Recibos                │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
           ↑                     ↓
    API / Webhook         Sync via Talk API
           ↓                     ↑
┌─────────────────────────────────────────────────┐
│ TALK PLATFORM                                  │
│ ┌─────────────────────────────────────────────┐ │
│ │ User: João Silva (externalId: ERP:123)     │ │
│ │ Documents: Manuais, Recibos                 │ │
│ │ Metadata: {erp_id: 123, erp_source: TASY}  │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**Tipos de Integrações**:

1. **Sync de Usuários**:
   ```
   TASY Patient: {id: 123, name: "João", email: "joao@email.com"}
   ↓
   Talk User: {
     username: "tasy_patient_123",
     full_name: "João",
     email: "joao@email.com",
     external_id: "tasy:123",
     role: "patient",
     metadata: {erp_source: "TASY", erp_id: 123}
   }
   ```

2. **Sync de Documentos**:
   ```
   ERP Document: {
     id: "doc_456",
     title: "Manual de Procedimento",
     url: "https://erp.cliente.com/docs/456"
   }
   ↓
   Talk Document: {
     title: "Manual de Procedimento",
     file_url: "https://erp.cliente.com/docs/456", // URL externa
     external_id: "erp_doc_456",
     sync_status: "synced",
     sync_at: "2026-07-24T10:00:00Z"
   }
   ```

3. **Sync de Eventos**:
   ```
   TASY Event: Patient completed appointment
   ↓
   Talk Event: User marked course as complete / viewed notification
   ↓
   Analytics updated
   ```

**Implementação - Connector Framework**:
```python
# talk/integrations/connectors/base.py
class ERPConnector:
    def __init__(self, config):
        self.api_key = config['api_key']
        self.base_url = config['base_url']
    
    def sync_users(self) -> List[User]:
        """Busca usuários do ERP e cria/atualiza em Talk"""
        erp_users = self.get_users_from_erp()
        
        for erp_user in erp_users:
            talk_user = User.objects.get_or_create(
                external_id=f"{self.connector_type}:{erp_user['id']}",
                defaults={
                    'username': erp_user['email'],
                    'full_name': erp_user['name'],
                    'email': erp_user['email'],
                    'role': self.map_role(erp_user['type']),
                    'metadata': {'erp_source': self.connector_type}
                }
            )
        
        return talk_user
    
    def sync_documents(self) -> List[Document]:
        """Busca documentos do ERP"""
        pass
    
    def sync_events(self, event) -> None:
        """Recebe webhooks do ERP"""
        pass
    
    def get_users_from_erp(self):
        """Abstract - implementado por subclasses"""
        raise NotImplementedError

# talk/integrations/connectors/tasy.py
class TASYConnector(ERPConnector):
    connector_type = 'TASY'
    
    def get_users_from_erp(self):
        response = requests.get(
            f"{self.base_url}/api/patients",
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        return response.json()['patients']
    
    def map_role(self, tasy_type):
        mapping = {
            'patient': 'patient',
            'doctor': 'doctor',
            'admin': 'admin'
        }
        return mapping.get(tasy_type, 'patient')

# talk/integrations/connectors/sap.py
class SAPConnector(ERPConnector):
    connector_type = 'SAP'
    
    def get_users_from_erp(self):
        # Implementação específica SAP
        pass
```

**Admin Interface para Setup**:
```
┌─────────────────────────────────────────┐
│ Integrações > Add New Integration       │
├─────────────────────────────────────────┤
│                                         │
│ Tipo: [ TASY ▼ ]                       │
│                                         │
│ Configuração:                          │
│ Base URL: [https://tasy.cliente.com/]  │
│ API Key: [••••••••••••••••]             │
│ Sync Interval: [Every 1 hour ▼]        │
│                                         │
│ Sync Settings:                         │
│ ☑ Sync Users                           │
│ ☑ Sync Documents                       │
│ ☑ Sync Events                          │
│                                         │
│ [ Test Connection ]  [ Save ]           │
└─────────────────────────────────────────┘
```

**Modelo de Dados**:
```sql
CREATE TABLE integrations (
  id UUID PRIMARY KEY,
  company_id FK,
  connector_type VARCHAR(50), -- 'TASY', 'SAP', 'ORACLE'
  base_url TEXT,
  api_key VARCHAR(255) ENCRYPTED,
  status ENUM('active', 'inactive', 'error'),
  last_sync TIMESTAMP,
  last_error TEXT,
  sync_frequency VARCHAR(50), -- 'hourly', 'daily', 'realtime'
  config JSON, -- custom fields by connector
  created_at TIMESTAMP
);

CREATE TABLE external_ids (
  id UUID PRIMARY KEY,
  talk_object_type VARCHAR(50), -- 'user', 'document'
  talk_object_id FK,
  external_id VARCHAR(255),
  external_source VARCHAR(50), -- 'TASY', 'SAP'
  last_synced TIMESTAMP,
  UNIQUE(external_id, external_source)
);

CREATE TABLE sync_logs (
  id UUID PRIMARY KEY,
  integration_id FK,
  sync_type VARCHAR(50), -- 'users', 'documents', 'events'
  status ENUM('success', 'partial', 'failed'),
  records_processed INT,
  records_created INT,
  records_updated INT,
  errors TEXT,
  started_at TIMESTAMP,
  completed_at TIMESTAMP
);
```

**Webhooks Recebidos do ERP**:
```python
# talk/integrations/webhooks.py
@webhook_handler
def handle_tasy_webhook(request):
    event = request.json
    
    if event['type'] == 'patient.created':
        # Cria usuário em Talk
        user = User.objects.create(
            username=f"tasy_{event['patient_id']}",
            full_name=event['patient_name'],
            external_id=f"tasy:{event['patient_id']}"
        )
        
        # Notifica admin
        send_notification(
            user_id=None,  # para admins
            title="Novo paciente sincronizado",
            message=f"{event['patient_name']} foi adicionado"
        )
    
    elif event['type'] == 'appointment.completed':
        # Marca algo como completo em Talk
        user = User.objects.get(external_id=f"tasy:{event['patient_id']}")
        mark_user_achievement(user, 'appointment_completed')
```

**Deliverables**:
- Connector framework pronto
- 2 integrações implementadas (TASY + SAP)
- Admin UI para setup
- Webhook system funcionando
- Sync logs rastreados

---

#### Sprint 15-16 (Semanas 29-32): AI Features

**Objetivo**: Recomendações inteligentes, search melhorado, chatbot

**Features**:
1. **Smart Recommendations**:
   ```
   "Você pode gostar de..."
   - Docs similares ao que tá lendo
   - Cursos baseado em progresso
   - "Colegas no seu time completaram..."
   
   Usando: Collaborative filtering + content-based
   ```

2. **Search Inteligente**:
   ```
   Busca semântica (não só keyword matching)
   - "como fazer checklist" → retorna doc "Checklist de procedimento"
   - "drivers nvidia" → retorna doc "GPU Drivers v2.1"
   
   Usando: Embeddings (Sentence-BERT ou similar)
   ```

3. **Chatbot FAQ**:
   ```
   "Qual é a política de cobertura para acidente?"
   Bot responde com chunk do documento relevante
   Se não souber, escala para humano
   
   Usando: RAG (Retrieval Augmented Generation)
   ```

**Implementação**:
```python
# talk/ai/recommendations.py
class RecommendationEngine:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def get_recommendations_for_user(self, user_id, num=5):
        """Retorna documentos/cursos recomendados"""
        user_history = UserActivity.objects.filter(user_id=user_id)
        
        # Documentos que user já viu
        viewed_docs = Document.objects.filter(
            id__in=user_history.values_list('object_id')
        )
        
        # Embeddings dos docs que viu
        viewed_embeddings = self.model.encode([doc.title for doc in viewed_docs])
        
        # Todos os outros docs
        all_docs = Document.objects.exclude(id__in=user_history.values_list('object_id'))
        all_embeddings = self.model.encode([doc.title for doc in all_docs])
        
        # Similaridade (cosine)
        similarities = cosine_similarity(viewed_embeddings, all_embeddings)
        top_similar = np.argsort(similarities[0])[::-1][:num]
        
        return [all_docs[i] for i in top_similar]

# talk/ai/search.py
class SemanticSearch:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def search(self, query, num_results=10):
        """Busca semântica em documentos"""
        query_embedding = self.model.encode(query)
        
        # Busca em Elasticsearch/Weaviate (já tem embeddings)
        results = search_engine.search(
            vector=query_embedding,
            top_k=num_results
        )
        
        return results

# talk/ai/chatbot.py
class FAQChatbot:
    def __init__(self):
        self.llm = OpenAI(api_key=settings.OPENAI_KEY)
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    def answer_question(self, question, user_id):
        """Responde pergunta usando docs como contexto"""
        # Busca docs relevantes
        docs = Document.objects.filter(user_accessible=True)
        doc_texts = [doc.content for doc in docs]
        
        # Embeddings
        doc_embeddings = self.embedder.encode(doc_texts)
        question_embedding = self.embedder.encode(question)
        
        # Top 3 docs relevantes
        similarities = cosine_similarity([question_embedding], doc_embeddings)[0]
        top_indices = np.argsort(similarities)[::-1][:3]
        
        context = "\n".join([doc_texts[i] for i in top_indices])
        
        # LLM responde usando contexto
        prompt = f"""
        Contexto (documentos da empresa):
        {context}
        
        Pergunta do usuário: {question}
        
        Responda usando o contexto acima. Se não sabe, diga "Não encontrei essa informação nos documentos. Por favor contate suporte."
        """
        
        response = self.llm.completion(prompt)
        
        return {
            'answer': response,
            'source_docs': [docs[i].id for i in top_indices],
            'confidence': max(similarities[top_indices])
        }
```

**Deliverables**:
- Recomendações funcionando
- Search semântico no banco
- Chatbot respondendo FAQs

---

### Timeline Resumido

```
Sprint 1-2  (Sem 1-4):     Document Management
Sprint 3-4  (Sem 5-8):     Notifications + Analytics
Sprint 5-6  (Sem 9-12):    Partner Portal
─────────────────────────────────────────
Sprint 7-8  (Sem 13-16):   Mobile App
Sprint 9-10 (Sem 17-20):   API Robusta
Sprint 11-12(Sem 21-24):   Gamification
─────────────────────────────────────────
Sprint 13-14(Sem 25-28):   ERP Integrations
Sprint 15-16(Sem 29-32):   AI Features
Sprint 17-18(Sem 33-36):   Scale + Polishing
```

---

## ⚙️ ESTRATÉGIA PROGRESSIVE GROWTH - IMPLEMENTAÇÃO TÉCNICA

### Como Cada Feature "Desbloqueia" Automaticamente

**Baseado em**: Métricas de uso real (não opinião)

#### Feature Unlock Rules

```python
# Sistema que detecta quando cliente está pronto pra novo feature

FEATURE_UNLOCK_MATRIX = {
    'analytics_dashboard': {
        'trigger': lambda m: m.doc_view_rate > 0.5,
        'description': 'Quando >50% de documentos foram visualizados',
        'unlock_message': 'Analytics disponível - seus docs estão sendo lidos!',
        'monthly_cost': 300,
        'deploy_sprint': 3,  # Sprint 3-4 é quando fica pronto
    },
    
    'advanced_search': {
        'trigger': lambda m: m.search_queries_per_week > 20,
        'description': 'Quando usuários fazem >20 buscas/semana',
        'unlock_message': 'Pesquisa avançada em PDFs agora disponível',
        'monthly_cost': 0,  # Incluído
        'deploy_sprint': 3,
    },
    
    'compliance_dashboard': {
        'trigger': lambda m: m.has_compliance_requests,
        'description': 'Quando cliente menciona compliance/auditoria',
        'unlock_message': 'Dashboard de compliance & auditoria disponível',
        'monthly_cost': 500,
        'deploy_sprint': 4,
    },
    
    'gamification': {
        'trigger': lambda m: m.engagement_score > 0.6 and m.days_active > 14,
        'description': 'Quando engagement é alto e sistema é usado regularmente',
        'unlock_message': 'Badges & leaderboards disponíveis pra motivar sua equipe',
        'monthly_cost': 200,
        'deploy_sprint': 6,
    },
    
    'community_forums': {
        'trigger': lambda m: m.feedback_messages_per_week > 5,
        'description': 'Quando usuários estão conversando entre si',
        'unlock_message': 'Fóruns & comunidade abertos pra peer support',
        'monthly_cost': 200,
        'deploy_sprint': 6,
    },
    
    'mobile_app': {
        'trigger': lambda m: m.mobile_traffic_ratio > 0.4,
        'description': 'Quando >40% do acesso é mobile',
        'unlock_message': 'App mobile disponível pra iOS/Android',
        'monthly_cost': 1000,
        'deploy_sprint': 8,
    },
    
    'api_access': {
        'trigger': lambda m: m.integration_requests_count > 0,
        'description': 'Quando cliente pede integração ou dados customizados',
        'unlock_message': 'API REST & webhooks disponíveis',
        'monthly_cost': 500,
        'deploy_sprint': 9,
    },
}
```

#### Workflow de Unlock

```
1. WEEKLY CRON JOB:
   ├─ Calcular métricas do cliente (aggregar eventos da semana)
   ├─ Comparar contra cada FEATURE_UNLOCK_RULE
   ├─ Se trigger ativado E feature não está enabled:
   │  ├─ Enable feature
   │  ├─ Enviar email ao admin: "New feature available: X"
   │  ├─ Update billing (adicionar custo mensal)
   │  └─ Log no adoption_journey
   └─ Retry next week se trigger não mais é true (cleanup)

2. ADMIN NOTIFICAÇÃO:
   ├─ Email com: "Sua equipe está engajada! Confira X feature"
   ├─ Link direto pro novo feature
   └─ CTA: "Ativar agora?" ou "Saber mais?"

3. BILLING AUTOMÁTICO:
   ├─ $300 pra Analytics? Somar na fatura de próximo mês
   ├─ Transparente (não surpresa)
   ├─ Admin pode recusar: "Não quer analytics por $300? Tudo bem."
   └─ Se recusar, não reclama de novo por 30 dias
```

### Progressive UI: Interface Muda Conforme Adoção

```html
<!-- Modo "INBOX" - Semana 1 (adoção < 30%) -->
<!-- Apenas: Notificações + Busca + Dashboard minimalista -->

<!-- Modo "DISCOVERY" - Semana 2-3 (adoção 30-70%) -->
<!-- Adiciona: Documentos + Cursos + Analytics básico -->

<!-- Modo "FULL FEATURED" - Mês 2+ (adoção > 70%) -->
<!-- Tudo: Sidebar completo, Analytics avançado, Community, Integrações -->
```

### Impacto no Roadmap

**Sprint 1-2** (Semana 1-4):
- ✅ Infra de Progressive Growth (feature flagging backend)
- ✅ Métrica collection setup
- ✅ Document Management MVP
- ✅ Modo "INBOX" UI (simples)
- **Resultado**: Cliente dia 1 com sistema funcional, limpo

**Sprint 3-4** (Semana 5-8):
- ✅ Notificações + Analytics (features que provavelmente serão desbloqueadas)
- ✅ Modo "DISCOVERY" UI
- ✅ Feature unlock automation
- **Resultado**: Sistema cresce naturalmente, sem parecer "vazio"

**Sprint 5-6** (Semana 9-12):
- ✅ Compliance tracking (preparado pra desbloquear)
- ✅ Gamification engine (preparado pra desbloquear)
- **Resultado**: Features esperando pelo trigger do cliente

### Exemplos Reais de Progression por Industria

#### Seguradora - Primeira 30 dias

```
DIA 1 GO-LIVE:
├─ 150 oficinas, 25 despachantes
├─ 1 documento (Manual de Procedimentos)
├─ 1 notificação (Leia em 24h)
├─ Dashboard minimalista (5 KPIs)
├─ Adoption: 75% em 24h
└─ Sistema NÃO está vazio ✅

SEMANA 2:
├─ Admin adiciona 3 documentos novos
├─ Sistema detecta: "doc_view_rate > 0.5" ✅
├─ Analytics desbloqueia AUTOMATICAMENTE
├─ Admin recebe email: "Analytics disponível, 150 docs visualizados!"
└─ Adoption: 85%

SEMANA 3-4:
├─ Admin atualiza documentos 3x (versioning pain)
├─ Usuários fazem 45 buscas (>20 por semana) ✅
├─ Advanced search desbloqueia
├─ Gestor quer "quem leu o quê" (compliance request) ✅
├─ Compliance dashboard desbloqueia
├─ ROI comprovado: 20h/semana economizadas
└─ Adoption: 88%

DIA 30:
├─ Cliente vê: Adoption ↑, Economia ↑, Features cresceram naturalmente
├─ Proposta: "Quer mobile app pra oficinas?" → +$1k/mês
└─ Cliente: "SIM, quanto antes"
```

#### Fabricante - Primeira 30 dias

```
DIA 1:
├─ 50 revendedores, 200 técnicos, 5k clientes
├─ 1 folder + 1 guia + drivers pra download
├─ Notificação: "Novo firmware disponível"
├─ Dashboard: "200 downloads em 24h"
└─ Adoption: 80%

SEMANA 2:
├─ 200 técnicos já usam (mobile traffic ↑)
├─ Revendedores fazem 50+ buscas
├─ Advanced search + Analytics desbloqueia
└─ Revendedores veem: "Portal pessoal com stats"

SEMANA 3:
├─ Técnicos começam responder uns aos outros (feedback)
├─ Community desbloqueia
├─ Revendedores pedem integração (API requests ↑)
├─ API desbloqueia (preparado no sprint 9, mas oferece early access)
└─ Adoption: 86%

MÊS 2:
├─ Proposta: "Mobile app" → SIM
├─ Proposta: "Gamification" → SIM
├─ Proposta: "ERP integration" → SIM
└─ Contract cresce de $2k/mês → $8k/mês
```

### KPIs de Sucesso da Progressive Growth

```
Adoção dia 1:          > 75% (vs Docebo 40%)
Adoption semana 2:     > 85% (vs Docebo 50%)
Engagement semana 4:   > 60% weekly active (vs Docebo 35%)
ROI dia 30:            > 10x (vs Docebo 3x)
Features desbloqueadas mês 1: 3-5 (conforme natural)
Customer churn:        < 5% (vs Docebo 15%)
Net retention:         > 130% (vs Docebo 110%)
```

---

## 📊 PLANO DE MARKETING

### Fase 1: Pre-Launch (Months 1-3)

#### Objetivo
Entender mercado, validar problema, criar buzz

#### Atividades

**1. Market Research**:
- [ ] Entrevistar 20-30 prospects (ERPs, fabricantes, seguros, saúde)
- [ ] Análise de concorrentes (Docebo, Moodle, SAP)
- [ ] Pesquisa de preço ($25, $50, $100/user/mês?)
- [ ] Validar positioning ("Docebo 50% mais barato")

**2. Content & Thought Leadership**:
- [ ] Blog: "5 problemas com Docebo que Talk resolve"
- [ ] Ebook: "Guia de LMS para Empresas com Múltiplos Públicos"
- [ ] LinkedIn: Posts sobre integração com ERPs
- [ ] Webinar: "Como sincronizar dados do seu ERP com plataforma de learning"

**3. Early Access Program**:
- [ ] Recrutar 5-10 beta customers (fornecedor de serviço, fabricante, seguradora)
- [ ] Oferecer grátis em troca de feedback
- [ ] Case studies (publicar depois)
- [ ] Video testimonials

**4. Website & SEO**:
- [ ] Landing page focada em "ERP Integration"
- [ ] Blog posts para SEO:
  - "TASY + Learning Management"
  - "Sincronizar SAP com plataforma de conhecimento"
  - "Document management para seguradoras"
- [ ] FAQ schema markup (Google snippets)

**Investimento**: $20k-40k  
**Resultado esperado**: 50-100 leads qualificados

---

### Fase 2: Launch (Months 4-6)

#### Objetivo
Lançar produto, conquistar primeiros clientes, criar momentum

#### Argumentos de Venda

**Posicionamento**:
```
"Talk é Docebo + SharePoint integrados,
feito para empresas brasileiras com múltiplos públicos.
50% mais barato, 10x mais rápido de implementar,
com API nativa para sincronizar seu ERP."
```

**Para Quem**:
- Seguradoras (com oficinas, despachantes, clientes)
- Fabricantes de eletrônicos (com revendedores)
- Redes de saúde (com pacientes, enfermeiros)
- Bancos (com filiais, terceirizados)
- Telcos (com técnicos, parceiros)

**Pain Points Abordados**:
```
❌ Problema: "Compartilhamos docs via email/WhatsApp"
✅ Solução: "Talk centraliza, versiona, rastreia"

❌ Problema: "Não sabemos quem leu o treinamento"
✅ Solução: "Dashboard mostra engagement de cada pessoa"

❌ Problema: "Duplicar dados (ERP + plataforma learning)"
✅ Solução: "Sincronização automática via API"

❌ Problema: "Implementação de 6 meses em SAP"
✅ Solução: "Live em 2 semanas com Talk"

❌ Problema: "Caro ($100+/user/mês)"
✅ Solução: "Talk custa $10-50/user/mês"
```

#### Go-to-Market Channels

**1. Direct Sales** (50% do effort):
- [ ] Contratar 1-2 Enterprise sales reps
- [ ] Listar em Capterra, G2, GetApp
- [ ] LinkedIn outreach (CIOs, CHROs)
- [ ] Eventos (HR Summit, Retail Summit)
- [ ] Partnership com consultoras (Deloitte, Accenture)

**2. Self-Service** (20% do effort):
- [ ] Website com free trial (7 dias)
- [ ] Pricing transparente
- [ ] Demo automática (Calendly)
- [ ] Onboarding self-serve (primeiros 100 users)

**3. Partners** (30% do effort):
- [ ] Resellers (empresas de consultoria)
- [ ] Integradores de ERP
- [ ] Agências de marketing/comunicação
- [ ] Comissão: 20-30% ou revenue share

#### PR & Press

- [ ] Press release: "Talk lança plataforma integrada com ERP"
- [ ] Pitch para jornalistas (TechCrunch Brasil, Exame, Época Negócios)
- [ ] Award applications (Startup Brasil, inovação em RH)
- [ ] Entrevistas em podcasts

**Investimento**: $100k-150k  
**Resultado esperado**: 5-10 clientes pagos, $10k-30k MRR

---

### Fase 3: Growth (Months 7-12)

#### Objetivo
Acelerar vendas, expandir para outros segmentos, construir reputação

#### Estratégias

**1. Product-Led Growth (PLG)**:
- [ ] Free tier com limite: 100 docs, 10 users
- [ ] Upgrade para Pro ($50/mês) quando atinge limite
- [ ] Free API key para developers
- [ ] Marketplace de integrações (parceiros constroem conectores)

**2. Content Marketing**:
- [ ] 2 blog posts/semana
- [ ] Monthly webinar (com parceiros)
- [ ] Ebook atualizado (novos segmentos)
- [ ] Case studies (publicar 3-4)
- [ ] YouTube: "How to" videos de integrações

**3. Community**:
- [ ] Slack community (1k+ members)
- [ ] GitHub (publicar examples, SDKs)
- [ ] Community Discord/Forum
- [ ] Super Users program (free Pro tier em troca de feedback)

**4. Partnerships**:
- [ ] Integração com Zapier (automações simples)
- [ ] Marketplace (encontrar conectores TASY, SAP, ORACLE)
- [ ] Partner program (revenue share)
- [ ] Reseller channels (agências de consultoria)

**Investimento**: $200k-300k  
**Resultado esperado**: 20-50 clientes, $50k-150k MRR

---

### Segmentação por Indústria

#### Seguradoras
```
Pain Point: Comunicar com 500+ oficinas sobre políticas
Solução: "Talk Seguradora" (template pre-built)
- Templates de documentos (apólices, procedimentos)
- Partner portal (oficinas fazem login)
- Notificações automáticas (mudança de política)
- Compliance tracking (quem viu a politica nova?)

Preço: $20k/mês para 10k usuários (oficinas + interno)
GTM: Vender para 3-5 big seguradoras (Bradesco, Itaú, Porto)
```

#### Fabricantes
```
Pain Point: Distribuir drivers, manuais para revendedores
Solução: "Talk para Fabricantes"
- Versionamento de drivers (track compatibility)
- Revendedor portal (vê sales, leads, margins)
- Notificação automática (nova versão)
- Analytics (quem fez download de qual versão?)

Preço: $15k/mês para 5k usuários (internos + 500+ revendedores)
GTM: Samsung, LG, Positivo, Dell, HP
```

#### Redes de Saúde
```
Pain Point: Sincronizar pacientes do TASY, protocolos clínicos, educação
Solução: "Talk Healthcare"
- HIPAA compliant
- Integração TASY (sync pacientes)
- Protocolos clínicos (atualizar versão)
- Educação para pacientes (pré e pós-alta)
- Enfermeiro → Paciente messaging (segura)

Preço: $30k/mês para clínica 500 camas
GTM: Rede São Camilo, Sírio Libanês, América
```

---

### Métricas de Sucesso

```
Month 1-3 (Pre-Launch):
- 50+ qualified leads
- 10 beta customers
- 2 case studies
- 10k website visitors

Month 4-6 (Launch):
- 10+ paying customers
- $20k+ MRR
- 50k website visitors
- 30% MoM growth

Month 7-12 (Scale):
- 50+ paying customers
- $100k+ MRR
- 500k website visitors
- Net retention >110%
```

---

## 💰 MODELO DE NEGÓCIO

### Opção A: SaaS (Recomendado)

**Preço**:
```
Tier Starter:    $500/mês        (até 100 users)
Tier Pro:        $2,000/mês      (até 1k users)
Tier Enterprise: $10,000+/mês    (custom)

Exemplo:
Empresa 500 pessoas = Pro tier = $2k/mês = $24k/ano
Empresa 5k pessoas = Enterprise = $15k-20k/mês = $180k-240k/ano
```

**Modelo**:
```
Revenue = Customers × Average MRR

Year 1 target:
- 20 customers
- Average $8k/mês = $160k MRR
- ARR = $1.92M
```

**Advantage**:
- ✅ Recurring revenue (previsível)
- ✅ Baixa implementação (SaaS)
- ✅ Easy scale (não precisa IR in-house)
- ✅ Customer lifetime value alto

**Disadvantage**:
- ❌ Sensível à mudança de preço
- ❌ Churn se não entregar valor

---

### Opção B: On-Premise

**Preço**:
```
Licença Perpétua: $100k (até 1k users)
Suporte/Ano: $15k

Exemplo:
Empresa 500 pessoas = $100k (one-time) + $15k/ano
Total Year 1: $115k
```

**Advantage**:
- ✅ Privacy/compliance (dados on-premise)
- ✅ Revenue imediata (não recurring)
- ✅ Atrai grandes empresas (governo, fintech)

**Disadvantage**:
- ❌ Implementação lenta (precisa devs on-site)
- ❌ Support intenso (bugs no cliente)
- ❌ Revenue incerta (project-based)

---

### Opção C: Híbrido (Melhor dos 2 mundos)

**Preço**:
```
SaaS (Cloud Public):    $50/user/mês  (default)
SaaS (VPC Privada):     $100/user/mês (data isolation)
On-Premise:             $100k (perpetua) + $15k/ano

Escolha do cliente:
- Startup/PME → Cloud público ($50/user)
- Mid-market → VPC privada ($100/user) 
- Enterprise → On-premise ($100k + $15k)
```

**Strategy**:
- 80% de customers em Cloud
- 20% em On-Premise (Enterprise)
- VPC = intermediate option

---

### CONFIDENCIALIDADE & SEGURANÇA

#### Comparação: Cloud vs On-Premise

```
┌─────────────────────────────────────────────────┐
│                    CLOUD PUBLIC                 │
├─────────────────────────────────────────────────┤
│ Security:       SOC2, HIPAA, GDPR compliant    │
│ Encryption:     TLS in-transit, AES-256 rest   │
│ Data Location:  AWS us-east-1 (or Brazil)      │
│ Backup:         Diário + geo-redundant         │
│ DPA:            SIM (Data Processing Agreement) │
│ Uptime:         99.99%                         │
│ Cost:           $50/user/mês                   │
│                                                │
│ Confiável para: Maioria (não-sensível)        │
│ Não para:       Dados muito sensíveis (PII)   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│                   CLOUD PRIVADA (VPC)           │
├─────────────────────────────────────────────────┤
│ Security:       Mesma que Cloud + Isolation    │
│ Encryption:     Mesma + Private network        │
│ Data Location:  AWS VPC privada                │
│ Network:        Sem acesso internet (NAT)      │
│ Backup:         Mesmo padrão                   │
│ DPA:            SIM + BAA (Business Associate) │
│ Uptime:         99.99%                         │
│ Cost:           $100/user/mês                  │
│                                                │
│ Confiável para: HIPAA, PII, dados sensíveis    │
│ Ideal para:     Healthcare, Finance, Gov       │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│                  ON-PREMISE (Cliente)           │
├─────────────────────────────────────────────────┤
│ Security:       Cliente é responsável          │
│ Encryption:     Cliente configura              │
│ Data Location:  Data center do cliente         │
│ Network:        Isolado completamente          │
│ Backup:         Cliente responsável            │
│ DPA:            Não aplicável                  │
│ Uptime:         Depende do cliente             │
│ Cost:           $100k (perpetua) + $15k/ano    │
│                                                │
│ Confiável para: Máxima segurança/compliance    │
│ Ideal para:     Governo, Military, Finance     │
└─────────────────────────────────────────────────┘
```

#### Recomendação

**Para Brasil**:
```
Tier 1: SaaS Cloud Público ($50/user/mês)
  └─ Startup, PME, departamentos não-críticos

Tier 2: SaaS VPC Privada ($100/user/mês)
  └─ Mid-market, healthcare, finance

Tier 3: On-Premise ($100k + $15k/ano)
  └─ Enterprise, governo, compliance extremo
```

**Por que VPC é melhor que On-Premise**:
```
✅ Segurança igual ou melhor (isolamento de network)
✅ Custo 50% menor (não precisa manter infra)
✅ Uptime melhor (AWS manages)
✅ Suporte melhor (Talk responsável por patches)
❌ On-Premise: Cliente precisa devs, suporte 24/7
```

---

## 🔌 ARQUITETURA DE INTEGRAÇÃO

### Problema Específico: TASY + Talk

**Cenário**:
```
Hospital tem 500 pacientes no TASY
Precisa que cada paciente acesse materiais de educação no Talk
Sem duplicar cadastro

Exemplo:
TASY Paciente: João Silva (ID: 12345)
↓
Talk User: João Silva (vinculado ao TASY:12345)
↓
Acessa conteúdo de "Educação Pós-Alta"
```

### Arquitetura de Integração

```
┌─────────────────────────────────────────────────┐
│ TASY Hospital                                  │
│ ├─ Pacientes: 500                             │
│ ├─ Consultórios: 20                           │
│ ├─ Procedimentos: 1000/dia                    │
│ └─ API: HTTP REST (disponível em 2023+)       │
└─────────────────────────────────────────────────┘
           ↓ (Sync Bidirectional)
┌─────────────────────────────────────────────────┐
│ Talk Integration Service                       │
│ ├─ Connector TASY (Python)                     │
│ ├─ Sync Worker (Celery)                        │
│ ├─ Event Handler (Webhooks)                    │
│ └─ Mapping Engine                              │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│ Talk Platform                                  │
│ ├─ Users (vinculados via external_id)          │
│ ├─ Documents (vinculados via external_id)      │
│ ├─ Groups (mapeado de departamentos TASY)      │
│ └─ Analytics (sincronizado)                    │
└─────────────────────────────────────────────────┘
```

### Padrão de Sincronização

#### 1. Primeiro Setup (One-Time)

```python
# Admin Talk acess integração > TASY
# 1. Insere: Base URL do TASY, API Key
# 2. Sistema Talk faz GET /api/tasy/patients

GET https://tasy.cliente.com/api/v1/pacientes
Response:
{
  "pacientes": [
    {
      "id": 12345,
      "nome": "João Silva",
      "email": "joao@email.com",
      "departamento": "Cardio",
      "role": "paciente"
    }
  ]
}

# 3. Talk cria Users em lote
POST /api/talk/users (batch)
{
  "users": [
    {
      "external_id": "tasy:12345",
      "username": "tasy_patient_12345",
      "full_name": "João Silva",
      "email": "joao@email.com",
      "group": "Cardio-Patients",
      "role": "patient"
    }
  ]
}
```

#### 2. Sync Contínuo (Incremental)

```python
# A cada 1 hora, Talk chama:
GET https://tasy.cliente.com/api/v1/pacientes?last_sync=2026-07-24T09:00:00Z

Response:
{
  "changed": [
    {
      "action": "updated",
      "id": 12345,
      "name": "João Silva - UPDATED",
      "email": "joao.silva@newemail.com"
    },
    {
      "action": "created",
      "id": 12346,
      "name": "Maria Santos",
      "email": "maria@email.com"
    },
    {
      "action": "deleted",
      "id": 12347
      # (paciente deletado do TASY)
    }
  ]
}

# Talk atualiza banco (merge)
for change in response['changed']:
    if change['action'] == 'updated':
        user = User.objects.get(external_id=f"tasy:{change['id']}")
        user.full_name = change['name']
        user.email = change['email']
        user.save()
    
    elif change['action'] == 'created':
        User.objects.create(
            external_id=f"tasy:{change['id']}",
            full_name=change['name'],
            email=change['email']
        )
    
    elif change['action'] == 'deleted':
        user = User.objects.get(external_id=f"tasy:{change['id']}")
        user.deactivate()  # soft delete
```

#### 3. Webhooks do TASY → Talk

```python
# TASY envia notificação quando algo muda
POST https://talk.com/webhooks/tasy

{
  "event": "patient.created",
  "timestamp": "2026-07-24T10:30:00Z",
  "data": {
    "patient_id": 12345,
    "patient_name": "João Silva",
    "email": "joao@email.com"
  }
}

# Talk Handler
@webhook_handler('/webhooks/tasy', method='POST')
def handle_tasy_event(request):
    event = request.json
    
    if event['event'] == 'patient.created':
        user = User.objects.create(
            external_id=f"tasy:{event['data']['patient_id']}",
            full_name=event['data']['patient_name'],
            email=event['data']['email']
        )
        
        # Auto-enrolar em curso de educação
        course = Course.objects.get(slug='pacient-education-onboarding')
        course.students.add(user)
        
        # Notificar
        send_notification(
            user_id=user.id,
            title="Bem-vindo ao Hospital XYZ",
            message="Acesse materiais de educação na aba Cursos"
        )
```

### Mapping de Papéis (TASY → Talk)

```
TASY Role               → Talk Role    → Talk Permissions
─────────────────────────────────────────────────────────
doctor                  → doctor       → view_patient_docs, create_care_plan
nurse                   → nurse        → view_patient_docs, update_checklist
patient                 → patient      → view_own_docs, read_education
admin                   → admin        → manage_all
receptionist            → staff        → view_patient_directory
```

### Mapeamento de Grupos (Departamentos)

```
TASY Departamento       → Talk Group
─────────────────────────────────────
Cardiology              → group_cardio
Oncology                → group_onco
Emergency               → group_er
ICU                     → group_icu

Acesso a docs:
- "Cardio Protocols" → visible only to group_cardio + admins
- "General Guidelines" → visible to all
- "Salary Info" → visible only to admin
```

### Sincronização de Documentos

```
┌─────────────────────────────┐
│ TASY Document Store         │
│ ├─ Manuais de procedimento  │
│ ├─ Protocolos clínicos      │
│ ├─ Formulários              │
│ └─ Attachments              │
└─────────────────────────────┘
           ↓
┌─────────────────────────────┐
│ Talk Document Management    │
│ ├─ File cache (S3)          │
│ ├─ Metadata sync            │
│ ├─ Permissions              │
│ └─ Analytics (views)        │
└─────────────────────────────┘

Modelo:
Document {
  title: "Cardio Protocol v3.2"
  file_url: "https://tasy.com/docs/cardio-v3.2.pdf"
  external_id: "tasy_doc_456"
  sync_status: "synced"
  last_synced: "2026-07-24T10:00:00Z"
  version: 3.2
  visible_to_groups: ["group_cardio", "group_admin"]
}
```

### Event Tracking (Talk → TASY Analytics)

```
Talk event: User completed course
→ Send to TASY via webhook (optional)
→ TASY logs in patient medical record

Example:
POST https://tasy.com/webhooks/talk
{
  "event": "patient_completed_course",
  "patient_id": 12345,
  "course": "Educação Pós-Alta",
  "completed_at": "2026-07-24T11:00:00Z",
  "score": 95
}

TASY stores in patient record:
Patient 12345 history:
- 2026-07-24: Completed education course "Pós-Alta" (95%)
```

### Arquitetura Técnica (Talk)

```
talk/integrations/
├── __init__.py
├── models.py
│   ├── Integration (config, status, last_sync)
│   ├── ExternalID (maps user to erp_id)
│   ├── SyncLog (auditoria)
│   └── IntegrationEvent (webhook history)
│
├── connectors/
│   ├── base.py (abstract ERPConnector)
│   ├── tasy.py (TASYConnector)
│   ├── sap.py (SAPConnector)
│   ├── oracle.py (OracleConnector)
│   └── generic.py (Generic REST)
│
├── tasks.py (Celery tasks)
│   ├── sync_users.py
│   ├── sync_documents.py
│   ├── handle_webhook.py
│   └── retry_failed_syncs.py
│
├── webhooks/
│   ├── tasy_webhook.py
│   ├── sap_webhook.py
│   └── generic_webhook.py
│
├── admin.py
│   └── IntegrationAdmin (setup UI)
│
└── tests/
    ├── test_tasy_connector.py
    ├── test_sync_logic.py
    └── test_webhook_handler.py
```

### Configuration Example (Admin UI)

```
Settings > Integrations > Add New

┌──────────────────────────────────────┐
│ Integration Setup                    │
├──────────────────────────────────────┤
│                                      │
│ System Type:      [TASY ▼]          │
│                                      │
│ Base URL:         [_______________]  │
│ API Key:          [•••••••••••••••]  │
│ Webhook URL:      (auto-generated)    │
│                                      │
│ Sync Settings:                       │
│ ├─ ☑ Sync Users (every 1h)          │
│ ├─ ☑ Sync Documents (every 4h)      │
│ ├─ ☑ Listen Webhooks (realtime)     │
│ └─ ☑ Auto-enroll courses            │
│                                      │
│ Field Mapping:                       │
│ ├─ TASY Role → Talk Role:            │
│ │  medico    → doctor                │
│ │  paciente  → patient               │
│ └─ TASY Group → Talk Group:          │
│    cardiology → group_cardio         │
│                                      │
│ Advanced:                            │
│ ├─ Retry failed syncs: [24 hours ▼] │
│ ├─ Delete users in Talk if deleted   │
│ │  in TASY: [Yes/No]                │
│ └─ Log all events: [Enabled]         │
│                                      │
│ [ Test Connection ] [ Save ]         │
└──────────────────────────────────────┘
```

---

## 🎯 ESTRATÉGIA DE VENDAS

### Segmentação

#### Persona 1: CHO (Chief HR Officer) / VP Pessoas
```
Tamanho empresa: 500+ people
Problema: "Temos documentos espalhados, não sabemos quem leu"
Decision time: 30-60 dias
Ciclo de venda: Discovery → Demo → Trial (30d) → Negotiation → Sell
Decision influencers: CIO, RH manager, Compliance
Preço sensibilidade: Média
```

#### Persona 2: CIO / VP Technology
```
Tamanho empresa: 500-5k
Problema: "Sistemas desconectados, difícil integração"
Decision time: 60-120 dias
Ciclo de venda: RFP → Technical demo → POC (30d) → Negotiation → Sell
Decision influencers: COO, Security, Architecture
Preço sensibilidade: Alta (precisa justi...
```

#### Persona 3: Director of Operations (Redes saúde, Seguradoras)
```
Tamanho empresa: 1k-10k
Problema: "Compliance, rastreamento de treinamento"
Decision time: 90-180 dias
Ciclo de venda: RFP → Demo → Full POC (60d) → Negotiation → Sell
Decision influencers: Compliance, Finance, Legal
Preço sensibilidade: Alta + Compliance requirements
```

### Sales Playbook

#### Opening Email
```
Subject: [Company Name] - Como [Seguro/Fab/Healthcare] tá sincronizando TASY com plataforma de aprendizagem

Hi [Name],

Vi que [Company] tem 500+ [oficinas/revendedores/pacientes].
Muitos players estão fazendo isso:
- Sincronizar dados do [TASY/SAP] automáticamente
- Centralizar documentos (manuais, políticas, protocolos)
- Rastrear quem completou treinamento

A Talk faz isso por $50/user/mês (vs $100+ de Docebo).

Faria sentido a gente marcar um café de 15min essa semana?

[Your name]
```

#### Discovery Call (15min)
```
1. Warm-up (2min)
   "Qual é o maior pain point com distribuição de conhecimento?"

2. Diagnosis (8min)
   - Quantos users?
   - Quais sistemas usa? (ERP, learning platforms)
   - Tracking atual? (compliance, engagement)
   - Budget?

3. Propose (3min)
   "Podemos fazer POC em 2 semanas. Sincronizar seu [TASY/SAP], centralizar docs, mostrar analytics."

4. Close
   "Agende com meu colega para demo technique"
```

#### Technical Demo (30min)
```
1. Login demo (2min)
2. Document upload & permissions (5min)
3. User sync from TASY (5min)
4. Analytics dashboard (5min)
5. Mobile app (3min)
6. API para integrações (5min)
7. Pricing & Logistics (3min)
8. Next steps
```

#### POC Terms (30 days)
```
- Setup: Talk covers (free)
- Data migration: Talk covers (free)
- Support: 1 dedicated person
- Success metric: Onboard 100 users, show 50% engagement
- Cost: Free for 30 days

After 30 days:
- If happy: Annual contract ($X)
- If unhappy: No hard feelings, walk
```

---

### Preço & Packaging

```
┌─────────────────────────────────┬────────────┬─────────────────┐
│ Tier                            │ User Range │ Price/User/mo   │
├─────────────────────────────────┼────────────┼─────────────────┤
│ Starter                         │ <100       │ $50             │
│ Growing                         │ 100-500    │ $40             │
│ Pro                             │ 500-2k    │ $35             │
│ Enterprise                      │ 2k+       │ Custom (20-30)  │
│                                                                │
│ Add-ons:                                                       │
│ + Custom Integrations (TASY)   │            │ +$2k/mo         │
│ + VPC Private (compliance)      │            │ +$15/user/mo    │
│ + On-Premise (self-hosted)      │            │ $100k + $15k/y  │
│ + Premium Support (24/7)        │            │ +$1k/mo         │
│ + Data Migration (one-time)     │            │ $5k-50k         │
└─────────────────────────────────┴────────────┴─────────────────┘

Examples:
- Startup 50 people:        50 × $50 = $2,500/mo = $30k/year
- Mid-market 500 people:    500 × $35 + $2k integr = $19.5k/mo = $234k/year
- Enterprise 2k people:     2k × $25 + $2k integr + premium = $52k+/mo
```

---

## 📊 ROADMAP EXECUTIVO

```
Q3 2026 (Jul-Sep):   MVP Docs + Notifications
├─ Document Management (upload, share, version)
├─ Basic Notifications (email, in-app)
├─ Analytics Dashboard (simples)
├─ Partner Portal (template)
└─ 3 beta customers

Q4 2026 (Oct-Dec):   Mobile + API
├─ Mobile App (iOS/Android MVP)
├─ API REST v1
├─ 5 paying customers
└─ $10k MRR target

Q1 2027 (Jan-Mar):   Integrations + Scale
├─ TASY Connector (live)
├─ SAP Connector (live)
├─ 15 paying customers
└─ $50k MRR target

Q2-Q3 2027:         AI + Community
├─ Smart recommendations
├─ Chatbot FAQ
├─ Forums/Q&A
├─ 50+ paying customers
└─ $100k+ MRR target
```

---

## 🎓 CONCLUSÃO

**Talk tem oportunidade REAL** se seguir esse plano:

1. **MVP em 3 meses** (Document Mgmt + Notifications)
2. **Mobile + API em 6 meses** (power integrations)
3. **ERP connectors em 9 meses** (product-market fit)
4. **AI + Scale em 12-18 meses** (differentiation)

**Modelo de negócio**: SaaS + VPC privada + On-premise (30/70 split)

**Go-to-market**: Direct sales + partners + content marketing

**Posicionamento**: "Docebo brasileiro com ERP integration, 50% mais barato"

**Investimento**: $1.5M over 18 months

### Estado de implementação no repositório Talk (25/07/2026)

O núcleo executável do roadmap está implementado e validado no código: documentos enterprise, versões, permissões, visualizador, auditoria, anexos, Feed/Wiki, notificações, regras declarativas, analytics, trilhas, recomendações, feedback, gamificação e leaderboard, APIs REST v1 com CRUD lógico de documentos, credenciais de integração por organização/parceiro, outbox/assinatura de webhooks, contrato de sincronização mobile, portal privado de parceiros, SDKs-fonte Python/Node/PHP e schema Swagger. As rotas principais são `/api/v1/documents/`, `/api/v1/analytics/engagement/`, `/api/v1/gamification/summary/`, `/api/v1/gamification/leaderboard/`, `/api/v1/integrations/credentials/`, `/api/v1/partner/me/`, `/api/mobile/sync/` e `/api/mobile/events/`.

Permanecem explicitamente dependentes de implantação ou de outro produto: credenciais/bucket de storage S3, broker/worker Celery em produção, FCM nativo, aplicativo React Native/offline, SSO/SAML, publicação dos SDKs em registries oficiais e ações comerciais. O código de Celery, tarefas e fallback já está no repositório; falta somente disponibilizar o broker/worker no ambiente alvo. Os clientes-fonte dos SDKs já estão no repositório e precisam apenas do processo de empacotamento/publicação versionada. Fóruns públicos não foram ativados porque a estratégia aprovada do Talk privilegia feedback privado, dúvidas controladas e comunicação sem exposição de comentários.

**ROI esperado**: $1.92M ARR (Year 1), $5M+ (Year 2)

---

**Pronto para executar?** 🚀
