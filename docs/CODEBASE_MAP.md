---
last_mapped: 2026-10-09T00:00:00Z
total_files: 2370
total_tokens: ~850000
---

# MatchCo Codebase Map

> **Comprehensive architecture guide** for the multi-tenant recruitment + learning platform.
> 
> Generated: 2026-10-09 | **Status: COMPLETE & VALIDATED**

---

## System Overview

**MatchCo** is a Django-based **multi-tenant SaaS platform** combining:

- 🎯 **Bilateral Recruitment Matching** (Porta Match + Porta Vaga) with LGPD compliance
- 📚 **Learning Management System** (courses, trails, gamification, certifications)
- 🔗 **Content Distribution** (wiki, feed, announcements, documents)
- 💬 **Real-time Features** (WebSocket chat, push notifications)
- 🏢 **Organization Hierarchy** (company → business unit → operational unit)
- 🔐 **Multi-tenant Isolation** (schema-per-tenant via django-tenants)

### Tech Stack

```
Backend:  Django 4.2, Python 3.12, PostgreSQL
Real-time: Django Channels, Redis
Frontend: Tailwind CSS, HTMX, PWA
APIs:     DRF + JWT, 3 SDKs (Python, Node, PHP)
Deploy:   Docker Compose, Dockerfile
i18n:     Portuguese (pt-BR), English, Spanish
```

### Architecture Diagram

```mermaid
graph TB
    subgraph "Shared Schema (Public)"
        User["👤 User<br/>(Global)"]
        Org["🏢 Organization<br/>(Tenant Root)"]
        CandidateId["🔑 CandidateIdentity<br/>(Global Person)"]
        EmployerActor["💼 EmployerActor<br/>(AA-1..8 Scopes)"]
        Ledger["📋 Ledger<br/>(Immutable Audit)"]
    end

    subgraph "Tenant Schema (Per-Organization)"
        Profile["👤 CandidateProfile<br/>(Org-scoped)"]
        Position["💼 Position<br/>(Opportunity)"]
        Relation["🤝 Relation<br/>(State Machine)"]
        Course["📖 Course<br/>(Learning)"]
        Event["📊 ContentEvent<br/>(Event Stream)"]
        Points["⭐ PointLedger<br/>(Gamification)"]
        Trail["🛤️ ContentTrail<br/>(Learning Path)"]
    end

    subgraph "Integrations (Hexagonal)"
        Identity["🔐 Identity Port<br/>(HRIS)"]
        Assessment["📝 Assessment Port<br/>(Skills Testing)"]
        Notification["📧 Notification Port<br/>(SMS/Email/Push)"]
        File["📁 File Port<br/>(Storage)"]
    end

    User -->|FK| Org
    CandidateId -->|Global| Profile
    EmployerActor -->|Authority| Org
    Ledger -->|Audit Trail| Org
    
    Org -->|Schema Isolation| Profile
    Profile -->|Matches| Position
    Relation -->|State| Ledger
    Course -->|Completes| Points
    Event -->|Triggers| Points
    Event -->|Progresses| Trail

    Identity -.->|Adapter| Profile
    Assessment -.->|Adapter| Profile
    Notification -.->|Adapter| Relation
    File -.->|Adapter| Course

    style Shared fill:#f0f0f0
    style "Tenant Schema" fill:#e8f4f8
    style Integrations fill:#fff9e6
```

---

## Directory Structure & Module Guide

```
matchco/
├── matchco/                          # Django project root
│   ├── settings/                     # Configuration (base, dev, prod, local)
│   ├── urls.py                       # Main URL router
│   ├── wsgi.py                       # WSGI entry point
│   └── asgi.py                       # ASGI entry point (Channels)
│
├── configuration/                    # Org hierarchy, integrations, multi-tenancy control
│   ├── models.py                     # Organization, Company, BusinessUnit, etc. (TenantMixin)
│   ├── admin.py                      # Django admin CRUD
│   ├── signals.py                    # Mirror sync (public → tenant schemas)
│   ├── services.py                   # (future enhancements)
│   ├── urls.py                       # Console URLs
│   ├── management/commands/          # Seed data, backfill, setup scripts
│   └── migrations/                   # 10+ migrations (hierarchy, audit, white-label)
│
├── recruitment/                      # Bilateral matching engine + LGPD
│   ├── models.py                     # Position, Relation, CandidateProfile, Ledger, etc. (73 migrations)
│   ├── services.py                   # Core workflows (OTP, matching, consent, anonymization)
│   ├── views.py                      # Candidato portal, employer portal (OTP vs. Django auth)
│   ├── portal_views.py               # Lojista (employer) portal
│   ├── urls_public.py                # Public QR + signup routes
│   ├── urls.py                       # Console recruitment routes
│   ├── integrations/
│   │   ├── ports.py                  # Hexagonal ports (Identity, Assessment, Notification, File)
│   │   ├── registry.py               # Lazy adapter loading
│   │   ├── signals.py                # Profile enrichment (courses, certs, tests)
│   │   └── organization.py           # Sync from configuration models
│   ├── templates/recruitment/        # Public signup, OTP, match detail, employer portal
│   ├── migrations/                   # 73 migrations (extensive history)
│   └── tests/                        # Unit tests for services, views, models
│
├── courses/                          # Learning content structure
│   ├── models.py                     # Course, Module, Quiz, Question, Answer, etc.
│   ├── admin.py                      # Course CRUD in console
│   ├── services.py                   # Enrollment, completion tracking
│   ├── templates/                    # (minimal, mostly via console)
│   ├── api/                          # DRF ViewSets for courses
│   └── migrations/                   # Embedded in tenant schema
│
├── learning/                         # Event stream, gamification, trails, notifications
│   ├── models.py                     # ContentEvent, PointLedger, UserBadge, ContentTrail, Notification, etc.
│   ├── services.py                   # track_event, award_points, manage trails, recommendations, notify
│   ├── views.py                      # Notification list/read, leaderboard, push subscriptions
│   ├── api_urls.py                   # /api/v1/ endpoints (documents, analytics, gamification)
│   ├── urls.py                       # Learning views (notifications, events)
│   ├── templates/learning/           # (minimal)
│   └── migrations/                   # Tenant-scoped
│
├── students/                         # Learner experience (enrollment, course player, progress)
│   ├── models.py                     # CourseEnroll, ModuleEnroll, ContentEnroll, etc.
│   ├── views.py                      # Student course list, player, quiz, trails
│   ├── templates/students/           # Course detail, player, certificate (older CSS framework)
│   ├── services.py                   # (minimal, mostly in learning/)
│   └── migrations/                   # Tenant-scoped
│
├── publishing/                       # Wiki & feed (announcements, knowledge base)
│   ├── models.py                     # Publication, Feed, Wiki (shared-like but org-scoped)
│   ├── views.py                      # Publication detail, list, feedback
│   ├── services.py                   # Visibility, engagement tracking
│   ├── templates/publishing/         # Publication detail, list, feedback form
│   └── migrations/                   # Tenant-scoped
│
├── documents/                        # Formal docs with versioning, approval, media library
│   ├── models.py                     # Document, DocumentVersion, MediaAsset, Collection
│   ├── views.py                      # Document CRUD, media library
│   ├── services.py                   # Versioning, approval workflow
│   ├── templates/documents/          # Document detail, list, media
│   └── migrations/                   # Tenant-scoped
│
├── console/                          # Admin back-office (CRUD for all content, users, settings)
│   ├── models.py                     # (minimal, mostly proxies)
│   ├── views.py                      # 50+ views (courses, trails, users, org settings, etc.)
│   ├── forms.py                      # Form helpers, validators
│   ├── urls.py                       # 300 lines of route definitions
│   ├── templates/console/            # List, detail, form, dashboard templates
│   ├── static/ui/                    # CSS, JS (app shell, theme, HTMX)
│   └── migrations/                   # Minimal
│
├── audience/                         # Eligibility rules (who can see what content)
│   ├── models.py                     # AudienceRule, AudiencePolicy, Membership dimension matching
│   ├── services.py                   # can_view(), policy reach estimation
│   ├── admin.py                      # Policy CRUD
│   └── migrations/                   # Tenant-scoped
│
├── chat/                             # Real-time WebSocket course chat
│   ├── models.py                     # ChatMessage (if stored)
│   ├── consumers.py                  # AsyncWebsocketConsumer
│   ├── routing.py                    # WebSocket routing
│   ├── templates/chat/               # Chat room (jQuery-based)
│   └── migrations/                   # Minimal
│
├── gamification/                     # Points & badges (mostly via learning/)
│   ├── models.py                     # (minimal, mostly via PointLedger in learning/)
│   └── services.py                   # (integrated into learning/services.py)
│
├── accounts/                         # Auth & registration (invitation-code, public signup, OTP)
│   ├── models.py                     # (minimal, auth via user_management.User)
│   ├── views.py                      # Login, signup, password reset, email confirmation
│   ├── forms.py                      # SignupForm, LoginForm
│   ├── backends.py                   # Custom auth backend
│   ├── templates/accounts/           # Login, signup, email confirmation
│   └── migrations/                   # Minimal
│
├── user_management/                  # User model, profile, password reset (SHARED SCHEMA)
│   ├── models.py                     # User (extends AbstractBaseUser, custom manager)
│   ├── views.py                      # User profile, password reset
│   ├── admin.py                      # User CRUD in Django admin
│   └── migrations/                   # 5-10 migrations
│
├── tenants_core/                     # Mirror models for tenant isolation
│   ├── models.py                     # TenantUser, TenantOrganization, TenantCompany, TenantCompany (mirrors)
│   └── services.py                   # Cross-schema helpers
│
├── app/                              # PWA app (mobile learner experience)
│   ├── views.py                      # App shell views (dashboard, courses, trails, settings)
│   ├── templates/app/                # PWA templates (base, courses, dashboard, profile)
│   ├── static/manifest.webmanifest   # Web App Manifest (standalone, theme colors)
│   ├── static/service-worker.js      # Service Worker (cache strategy, push notifications)
│   └── urls.py                       # PWA routes
│
├── api/                              # (Deprecated or minimal, use learning/api_urls.py)
│   └── urls.py                       # Versioned endpoints (/api/v1/)
│
├── static/
│   ├── ui/
│   │   ├── css/app.css               # Tailwind compiled + custom styles
│   │   ├── js/app-shell.js           # Sidebar, HTMX management
│   │   ├── js/theme.js               # Dark mode toggle
│   │   ├── vendor/                   # Quill.js, Flowbite, etc.
│   │   └── manifest.webmanifest      # Web App Manifest
│   ├── matchco_site/img/             # Logo, icons, QR codes
│   └── students/                     # Course player styles (legacy CSS)
│
├── templates/
│   ├── ui/
│   │   ├── base.html                 # Console shell (navbar + sidebar)
│   │   ├── base_public.html          # Public entry point shell
│   │   ├── navbar.html               # Top nav (logo, org switcher, theme toggle, user menu)
│   │   └── sidebar.html              # Left sidebar (dynamic navigation, localStorage state)
│   │
│   ├── recruitment/
│   │   ├── match/                    # Candidate signup flow (OTP, signup form, onboarding)
│   │   ├── portal/                   # Employer/lojista/shopping portals
│   │   ├── console/                  # QR/entry point management
│   │   ├── privacy/                  # LGPD pages
│   │   └── matchco_site/             # Public marketing pages
│   │
│   ├── console/                      # Admin back-office templates
│   ├── students/                     # Learner course player (older CSS)
│   ├── publishing/                   # Wiki/feed detail, list
│   ├── documents/                    # Document library
│   ├── app/                          # PWA app templates
│   └── base_registration.html        # (legacy)
│
├── config/
│   └── requirements.txt              # Dependencies (Django 4.2, DRF, django-tenants, Celery, etc.)
│
├── manage.py                         # Django CLI
├── CLAUDE.md                         # Project documentation (architecture, commands, patterns)
├── AGENTS.md                         # (Automation agents, if applicable)
├── MEMORY.md                         # (User memory index)
└── docker-compose.yml                # Local dev environment (PostgreSQL, Redis, MatchCo service)
```

---

## Key Concepts & Patterns

### 1. Multi-Tenancy (django-tenants)

**Model**: Schema-per-tenant isolation

```python
# Shared Schema (Public):
# - user_management.User (global auth)
# - configuration.Organization (TenantMixin, maps to PostgreSQL schema)
# - recruitment.CandidateIdentity (global person record)
# - recruitment.Ledger (immutable audit trail)

# Tenant Schema (Per-Organization):
# - tenants_core.TenantUser (mirror of User for queries)
# - courses.Course (org-specific content)
# - learning.ContentEvent (org-specific event stream)
# - recruitment.CandidateProfile (org-specific profile)
# - recruitment.Relation (org-specific matches)
```

**Routing**: Host-based (primary) via `django-tenants.middleware.TenantMainMiddleware`

**Session-Based Fallback**: `request.session['_selected_organization_id']` for workspace switcher

### 2. Event-Driven Architecture

**Core Event Stream**: `learning.ContentEvent`

```
Event → PointLedger → BadgeDefinition → UserBadge
     → NotificationRule → UserNotification → NotificationDelivery
     → WebhookDelivery → external_system
     → TrailProgress update → auto_complete_trail
```

**Ledger Pattern**: Immutable, append-only for audit compliance

```python
# recruitment.Ledger = source of truth for LGPD
Ledger(event_type='PROFILE_CREATED', actor=..., metadata={...})
Ledger(event_type='MATCHED', actor=..., source_event_id=relation.pk)
Ledger(event_type='CONSENT_REVOKED', actor=..., purpose='CIRCULATION_NETWORK')
```

### 3. Bilateral Matching (Porta Match)

**State Machine** (Relation model):

```
NOTICE_DELIVERED
  ↓ (candidate views & responds)
PERSON_INTERESTED
  ↓ (system auto-transition)
EMPLOYER_INTEREST_VIEW
  ↓ (employer views profile)
EMPLOYER_INTERESTED
  ↓ (system auto-transition)
MATCHED
  ↓ (both interested)
CONTACT_ENABLED
  ↓ (contact info exchanged)
RESPONSE_CREATED → CLOSED
```

**Key Features**:
- Both sides must demonstrate interest (bilateral)
- Versions pinned at relation creation (opportunity field changes don't affect)
- State transitions logged to both `RelationTransitionEvent` + `Ledger`
- Expiry windows (notice_expires_at, employer_decision_expires_at)

### 4. LGPD Compliance

**Consent Model**: Granular per-purpose (CandidateConsent.PURPOSE_*)

```python
VISIBILITY_MATCH              # Profile visible in matching
CIRCULATION_NETWORK           # Cross-org sharing
CIRCULATION_SHOPPING          # Shopping mall pool
CIRCULATION_RADIUS            # Geo-radius matching
INTEGRATION_COURSES           # Course signal integration
INTEGRATION_CERTIFICATIONS    # Cert signal integration
INTEGRATION_TESTS             # Test result integration
INTEGRATION_TALK              # Talk interaction integration
```

**Retention Policy**:
- RT-01: Active relations (no action)
- RT-02: CLOSED relations > N days → anonymization
- RT-03: Old Ledger entries → archive
- RT-04: Security logs > 5 years (ANPD)
- RT-05: Technical logs (delegated to infra)

**Data Minimization**:
- CPF stored as HMAC-SHA256 hash + last 4 digits only
- Export omits CPF plaintext
- Anonymization is irreversible (clears PII)

### 5. Authority Scopes (EmployerActor)

**AA-1 to AA-8 Hierarchy**:

```
AA-1: Declare need (create opportunity)
AA-2: Structure opportunity (define requirements)
AA-3: Activate opportunity (start matching)
AA-4: Modify opportunity (change after activation)
AA-5: Close opportunity (end hiring)
AA-6: View employer interest view (see profiles)
AA-7: Declare employer interest (show interest)
AA-8: Receive contact channel (get phone/email)
```

**Verification**: `_resolve_employer_actor()` checks scope for each action; violations logged to Ledger

### 6. Eligibility & Audience Policies

**Service**: `audience.services.EligibilityService.can_view(user, content)`

**Dimensions**:
- Organization, Company, BusinessUnit, OperationalUnit
- Channel, Function, PersonType, MembershipRole
- Program (dynamic, opt-in via ProgramMembership)

**Policy Modes**:
- ALL = AND logic (all rules must match)
- ANY = OR logic (any rule can match)

**Evaluation Order**:
1. Authentication required?
2. Content published?
3. Management override (superuser/staff)?
4. Membership required?
5. Organization match?
6. Policy attached?
7. Policy evaluation (match rules)

### 7. Hexagonal (Ports & Adapters) Integrations

**Ports** (abstract contracts):

```python
IdentityPort.resolve_person(email, cpf?) → PersonRef
AssessmentPort.request(AssessmentRequest) → AssessmentResult
NotificationPort.send_sms(recipient, body) → bool
FilePort.store(name, content_type, content) → FileRef
```

**Adapters** (pluggable implementations):

```python
# settings.RECRUITMENT_INTEGRATIONS
{
  'identity': 'recruitment.integrations.adapters.IdentityAdapter',  # HRIS
  'assessment': 'recruitment.integrations.adapters.AssessmentAdapter',  # Skills
  'notification': 'recruitment.integrations.adapters.NotificationAdapter',  # SMS/Email
  'file': 'recruitment.integrations.adapters.FileAdapter',  # S3
}
```

**Registry**: Lazy loading via `get_identity_port()`, `get_notification_port()`, etc.

**Fail-Soft**: Missing adapters don't break startup; external failures logged, not retried

### 8. Signal-Driven Profile Enrichment

**External systems** (courses, certs, tests) emit signals → recruitment enriches profile:

```python
on_course_completed(candidate_id, course_key, ...)
  → ProfileSignal(freshness=F0_DURABLE)
  → PreboardingEvidence recorded

on_certification_granted(candidate_id, cert_key, valid_until?, ...)
  → ProfileSignal(freshness=F0_DURABLE | F1_DYNAMIC)
  → expires_at set if validity

on_test_result(candidate_id, opportunity_id, test_key, score?, ...)
  → ProfileSignal(scope='test_opp{opportunity_id}:{key}')
  → Visible only in that opportunity
```

**Consent-First**: External modules unaware of LGPD; recruitment checks consent before recording

---

## Critical Data Flows

### 1. Candidate Signup (Porta Match)

```
QR Scan (/qr/<entry_point_id>/)
  ↓
OTP Request (/candidato/entrar/)
  ├─ Normalize phone
  ├─ Rate limit (max 3 pending / 10 min)
  ├─ Generate 6-digit code
  ├─ Send SMS/Email/Dev capture
  └─ Create OtpCode(PENDING, expires_at=+10min)

OTP Verify (/candidato/entrar/codigo/)
  ├─ Validate code (must be PENDING, not expired)
  ├─ Transition OtpCode(USED)
  ├─ Record CONSENT_GRANTED ledger event
  └─ Set session['matchco_profile_id']

Signup Form (/candidato/signup/)
  ├─ Resolve or create CandidateIdentity by email/phone
  ├─ Create CandidateProfile (org-scoped)
  ├─ Record canonical answers (job functions, availability, etc.)
  ├─ Create initial PreboardingAssignment if program linked
  ├─ Record PROFILE_CREATED ledger event
  └─ Redirect to /candidato/oportunidades/

Candidate Feed (/candidato/oportunidades/)
  ├─ Query all active opportunities for candidate's org
  ├─ Filter by eligibility (consent, functions, availability, etc.)
  ├─ Deliver notices (create Relations with NOTICE_DELIVERED state)
  └─ Candidate can show interest → PERSON_INTERESTED
```

### 2. Employer Interest (Porta Vaga)

```
Declare Need (/portal/necessidades/nova/)
  ├─ Create Position(STATE_STRUCTURED)
  ├─ Freeze canonical requirements (functions, other_terms)
  ├─ Pre-interest set complete? (all REQUIRED_FIELDS filled)
  ├─ If complete: activate → STATE_CIRCULATED
  └─ Record OPPORTUNITY_CREATED ledger event

View Candidate Stack (/portal/oportunidades/<opp_id>/)
  ├─ Query Relations for this opportunity (AA-6 verified)
  ├─ Return employer_interest_view projection (name, functions, signals)
  ├─ Render candidate cards with interest buttons

Declare Interest (/portal/relation/<rel_id>/interessar/)
  ├─ Transition: EMPLOYER_INTEREST_VIEW → EMPLOYER_INTERESTED (AA-7 verified)
  ├─ Auto-transition: EMPLOYER_INTERESTED → MATCHED (system)
  ├─ Record EMPLOYER_INTERESTED + MATCHED ledger events
  └─ Notify candidate

Enable Contact (/portal/relation/<rel_id>/liberar-contato/)
  ├─ Transition: MATCHED → CONTACT_ENABLED (AA-8 verified)
  ├─ Create ContactChannel(phone, email) ← candidate's contact info
  ├─ Record CONTACT_ENABLED ledger event
  └─ Notify candidate

Submit Response (/portal/relation/<rel_id>/responder/)
  ├─ Submit RC-01..05 (response class)
  ├─ Create Response(relation, rc, note if RC-05)
  ├─ Transition: CONTACT_ENABLED → RESPONSE_CREATED → CLOSED
  ├─ Record RESPONSE_CREATED + CLOSED ledger events
  └─ Mark relation complete
```

### 3. Learning Enrollment & Progression

```
Enroll in Course (/students/enroll/)
  ├─ Check audience eligibility (can_view)
  ├─ Create CourseEnroll (linking user → course)
  ├─ Add user to course.students M2M
  ├─ track_event(COURSE_ENROLLED)
  └─ Redirect to course player

View Course (/students/courses/<slug>/)
  ├─ Iterate modules in order
  ├─ For each module: iterate content items
  ├─ Mark as done on completion
  ├─ track_event(CONTENT_OPENED)

Complete Quiz (/students/quiz/submit/)
  ├─ Calculate score (% correct)
  ├─ Store result in QuizResult
  ├─ track_event(QUIZ_COMPLETED, score=%)
  ├─ award_points_for_event(QUIZ_COMPLETED)
  │  └─ +100 points; bonus +50 if perfect
  ├─ Check badge thresholds
  ├─ Update challenge progress (min with target_points)
  └─ Auto-complete challenge if points >= target

Complete Course (/students/mark-complete/)
  ├─ Mark all content as done
  ├─ track_event(COURSE_COMPLETED)
  ├─ award_points_for_event(COURSE_COMPLETED)
  │  └─ +100 points
  ├─ Issue CourseCertificate (if not already issued)
  ├─ Check certifications (all requirements met?)
  ├─ Issue CertificationAward if eligible
  └─ Update trail progress (auto-complete if course in trail)
```

### 4. Notification Delivery (Multi-Channel)

```
track_event(COURSE_COMPLETED, ...)
  ├─ Create ContentEvent
  ├─ award_points_for_event()
  ├─ enqueue_webhook_event(organization, 'COURSE_COMPLETED', {user_id, course_id})
  └─ (webhook worker delivers later)

create_notification(user, 'Course Complete', ...)
  ├─ Get UserNotificationPreference (default: ROUTINE for email + push)
  ├─ Check preference.minimum_priority
  ├─ Create UserNotification (dedupe_key prevents duplicates)
  └─ deliver_notification() per channel:
     ├─ PUSH: pywebpush + PushSubscription.endpoint
     ├─ SMS: get_notification_port().send_sms()
     ├─ EMAIL: Django EmailMultiAlternatives
     ├─ WHATSAPP: get_notification_port().send_whatsapp()
     └─ WEBHOOK: enqueue (durable queue)

NotificationDelivery
  ├─ Status: PENDING, SENT, FAILED
  ├─ Failures logged (not retried)
  ├─ One channel failure doesn't block others
  └─ last_delivered_at updated on success
```

---

## Common Tasks & Workflows

### Add a New Audience Filter Dimension

1. **Update `AudienceRule.dimension` choices** in `audience/models.py`
2. **Implement rule matching** in `audience.services.EligibilityService._rule_matches()`
3. **Update console UI** for policy builder in `console/templates/console/audience_form.html`
4. **Create migration** for new field

**Example**: Adding "program" dimension:
```python
# models.py
DIMENSION_CHOICES = (..., ('program', 'Program Membership'))

# services.py
if rule.dimension == 'program':
    programs = ProgramMembership.objects.filter(user=user, active=True).values_list('program_id')
    values = set(programs)
```

### Add a New Notification Channel

1. **Define port method** in `recruitment/integrations/ports.py`
2. **Implement adapter** in `recruitment/integrations/adapters.py`
3. **Update `learning.services.deliver_notification()`** to handle new channel
4. **Add UserNotificationPreference.channel_CHANNEL** boolean
5. **Create migration**

**Example**: Adding Slack:
```python
# ports.py
def send_slack(self, user_id, message) → bool

# services.py
elif channel == 'SLACK':
    get_notification_port().send_slack(notification.user_id, notification.message)
```

### Add a New Recruitment Integration

1. **Define port** in `recruitment/integrations/ports.py` (contract)
2. **Create adapter** in `recruitment/integrations/adapters.py`
3. **Register in `recruitment/integrations/registry.py`** (lazy loader)
4. **Call from service** (e.g., `resolve_or_create_identity()`)
5. **Test fail-soft** (adapter missing → no-op)

**Example**: Adding HRIS employment record sync:
```python
# ports.py
class HRISPort(Protocol):
  def fetch_employment(self, cpf: str) → EmploymentRecord: ...

# adapters.py
class HRISAdapter:
  def fetch_employment(self, cpf):
    # Call external HRIS API
    return EmploymentRecord(...)

# registry.py
def get_hris_port():
  return HRISAdapter()  # Lazy instantiation

# services.py
try:
  employment = get_hris_port().fetch_employment(cpf)
  EmploymentRecord.objects.create(...)
except Exception:
  logger.exception('HRIS fetch failed')  # Soft fail
```

### Create a New Learning Trail

1. **Admin creates trail** in `/console/trails/new/`
2. **Add content steps** (courses, quizzes, documents, publications)
3. **Set completion event triggers** (e.g., "trail complete when all steps done")
4. **Assign to audience** (via policy or manual) in `/console/trails/assign/`
5. **Learner sees trail** in `/app/trails/`

**Workflow**:
```python
# Learner starts trail
start_trail(user, trail)
  → Get or create TrailAssignment

# Check next step
next_trail_step(user, trail)
  → Return first incomplete step with content object

# Complete step
complete_trail_step(user, assignment, step)
  → Mark step done
  → If all steps done: mark trail completed, track TRAIL_COMPLETED event
```

### Add a New Learning Challenge

1. **Create LearningChallenge** (time-bound, target_points)
2. **Associate with BadgeDefinition** (optional)
3. **Publish to learners** (visibility via audience policy)
4. **Points auto-track** via `award_points_for_event()` → updates ChallengeProgress

**Example**: "Complete 5 courses this month":
```python
challenge = LearningChallenge(
  title='Course Collector',
  description='Complete 5 courses',
  target_points=500,  # 100 per course
  starts_at=now,
  ends_at=now + timedelta(days=30),
  badge=BadgeDefinition(code='5-courses', title='...')
)
```

---

## Important Patterns & Gotchas

### 1. Multi-Tenancy Gotchas

**Schema Routing Critical**:
- Middleware must switch schema BEFORE queries
- Cross-schema FKs forbidden (all FKs within schema)
- Mirror models (TenantUser) required for lookups from public schema

**Ghost Tenant Issue**:
- If organization.pk changes or domain removed, queries return empty
- Use `connection.set_tenant(org)` explicitly before queries

### 2. Recruitment State Machine

**Version Pinning**:
- `opportunity_version` frozen at relation creation
- Later bumps don't affect existing relations (design intent)
- Candidate must reconfirm if version bumps post-interest

**Authority Scope Checks**:
- Outside atomic transaction to preserve AUTHORITY_VIOLATION in Ledger
- Scope verification happens BEFORE state change
- Scope lacking → HttpResponseForbidden, never state change

**Consent Revocation**:
- Does NOT delete history (immutable audit)
- Pauses visibility matching
- Candidate must re-grant to re-circulate

### 3. Learning Event Stream

**PointLedger Immutability**:
- One-to-one with ContentEvent (immutable pair)
- Points never revised (new events only)
- Aggregations sum historical PointLedger entries

**Challenge Capping**:
- Points = min(challenge.target_points, progress.points + new_points)
- No overflow to prevent leaderboard abuse
- Once completed, check only needed if completed_at is None

### 4. Notification Delivery

**Per-Channel Fail-Soft**:
- Each channel (SMS, Email, Push, Webhook) has independent try/catch
- One channel failure doesn't block others
- Status captured per delivery (SENT, FAILED, PENDING)

**Webhook Durability**:
- Enqueued IN transaction (committed with data)
- Worker retries with exponential backoff (external)
- No automatic retry from service layer (fire-and-forget)

### 5. LGPD Compliance

**Email Uniqueness Nullable**:
- `CandidateIdentity.email_normalized` is unique but nullable
- Allows multiple identities without email (phone-only)
- CPF lookup requires hash match (partial reveal via last 4 digits)

**Anonymization Irreversible**:
- Clears name, email, phone, CPF, geo, salary, etc.
- Responses cleared (JSON fields wiped)
- No recovery path (design intent: user's right to be forgotten)

**Retention Manual**:
- `apply_retention_policy(dry_run=True)` is utility, not auto-triggered
- Must be called by background job (Celery beat)
- Marks Ledger events for audit; actual anonymization deferred

### 6. Opportunity Pre-Interest Completion

**Gate Before Matching**:
- Relation cannot advance past NOTICE_DELIVERED if Position.pre_interest_set_complete=False
- Admin must fill all required fields before activation
- Candidate doesn't see opportunity until gate passes

**Canonical Mappings**:
- Store-specific mappings override org-wide
- Missing mapping blocks completion
- `resolve_canonical_terms()` must find all required terms

### 7. OTP Rate Limiting

**Soft Limit**:
- 3 pending codes per mobile in 10 minutes (rate limit checked, exception raised)
- User sees error, can retry after delay
- Attempt tracking (max_attempts, usually 5)

**Code Hash Security**:
- Stored as SHA256(code|mobile|'matchco') one-way hash
- Code never logged in plaintext (only hash in DB)
- Verification compares hashes, not plaintext

---

## Frontend Architecture

### Template Inheritance

```
ui/base.html (Console shell: Tailwind CDN, HTMX, navbar, sidebar)
  ├─ ui/base_public.html (Public shell: similar navbar/sidebar)
  │  └─ recruitment/match/_base.html (Candidate signup branding)
  │     ├─ signup.html (3-step form, inline JS searchable multi-select)
  │     ├─ otp_request.html
  │     └─ otp_verify.html
  ├─ console/base.html (Minimal wrapper)
  │  ├─ console/form.html (Cascading hierarchy, AJAX updates)
  │  ├─ console/list.html
  │  └─ console/dashboard.html
  ├─ app/base.html (PWA shell, mobile-optimized)
  │  ├─ app/courses/player.html
  │  ├─ app/dashboard.html
  │  └─ app/trails.html
  └─ students/course/detail.html (Older CSS framework: Matra classes)
```

### Frontend Stack

- **CSS**: Tailwind CSS (CDN in dev, compiled in prod)
- **JS**: HTMX (v1.9.10) for dynamic forms, Vanilla JS for components
- **Icons**: Font Awesome 6.4
- **Charts**: Tailwind cards + backend rendering (no charting lib)
- **Editor**: Quill.js (rich text)
- **Dark Mode**: localStorage + system preference fallback
- **PWA**: Web App Manifest + Service Worker (cache static, never cache HTML)

### HTMX Integration

```html
<form method="get" hx-boost="true" hx-target="#app-main" hx-push-url="true">
  <!-- Auto-submits via AJAX, swaps #app-main, updates URL -->
</form>
```

**Bootstrap** (app-shell.js):
```javascript
document.querySelectorAll('form[method="get"]').forEach(form => {
  form.setAttribute('hx-boost', 'true');
  form.setAttribute('hx-target', '#app-main');
  form.setAttribute('hx-push-url', 'true');
});
```

---

## API & Integrations

### DRF Endpoints

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/api/v1/documents/` | GET | List accessible docs | JWT/API key |
| `/api/v1/gamification/leaderboard/` | GET | Top 50 users | JWT/API key |
| `/api/v1/analytics/engagement/` | GET | User engagement | JWT/API key |
| `/api/courses/` (DRF Router) | GET/POST | Course CRUD | JWT/Session |

### SDK Clients

- **Python SDK**: `/sdk/python/` (talk_sdk package)
- **Node SDK**: `/sdk/node/` (npm package)
- **PHP SDK**: `/sdk/php/` (Composer package)

### Webhook Contracts

**Event Structure**:
```json
{
  "id": "evt_123",
  "event": "course_completed",
  "created_at": "2026-10-09T...",
  "organization_id": "...",
  "data": {
    "user_id": "...",
    "course_id": "...",
    "score": 95
  }
}
```

**Signature** (HMAC-SHA256):
```
X-MatchCo-Signature: sha256=<HMAC-SHA256(body, subscription.secret)>
```

---

## Deployment & Operations

### Docker

```bash
# Local development
docker-compose up

# Production
docker build -t matchco:latest .
docker run -e DATABASE_URL=postgres://... -p 8000:8000 matchco:latest
```

### Database Migrations

```bash
# Standard migrations
python manage.py migrate

# Tenant migrations (runs per schema)
python manage.py migrate --tenant

# Seed demo data
python manage.py seed_matchco_demo
```

### Celery Tasks

```python
# settings.CELERY_BEAT_SCHEDULE
'matchco-apply-retention-daily': {
  'task': 'recruitment.tasks.apply_retention_task',
  'schedule': crontab(hour=2, minute=0),
}
```

**Task Examples**:
- `apply_retention_task()` - RT-02 anonymization
- `send_pending_notifications_task()` - Webhook delivery
- `mark_stale_signals_task()` - Profile signal expiry
- `monitor_entry_points_task()` - QR health check

---

## What's Been Done ✅

### Architecture & Models
- ✅ Multi-tenant setup with django-tenants (schema-per-tenant)
- ✅ 73 recruitment models + comprehensive CRUD
- ✅ 22+ learning models (event stream, trails, notifications)
- ✅ Audience eligibility policies + rule matching
- ✅ LGPD compliance scaffolding (consent, retention, ledger)

### Recruitment
- ✅ Bilateral matching engine (Relation state machine)
- ✅ OTP passwordless auth (SMS/Email/Dev capture)
- ✅ Opportunity versioning + pinning
- ✅ Authority scopes (AA-1..8)
- ✅ Profile enrichment signals (courses, certs, tests)
- ✅ Hexagonal integration layer (ports & adapters)

### Learning
- ✅ Event stream (22+ event types)
- ✅ Gamification (points, badges, challenges)
- ✅ Learning trails (content paths, prerequisites)
- ✅ Recommendations (rule-based)
- ✅ Notifications (multi-channel: SMS, email, push, webhook)
- ✅ Certifications (with eligibility gates)

### Frontend
- ✅ Tailwind CSS + HTMX app shell
- ✅ Admin console (50+ views for CRUD)
- ✅ Learner course player
- ✅ Employer/Lojista portal
- ✅ Candidate signup flow (OTP + form)
- ✅ PWA app (manifest + service worker + offline support)
- ✅ WebSocket chat

### Deployment
- ✅ Docker Compose local dev
- ✅ Production-ready Dockerfile
- ✅ Django management commands (seed, migrate, reset)
- ✅ i18n (Portuguese, English, Spanish)

---

## What's Missing or Needs Improvement ⚠️

### 1. **QR Code Redesign** (In Progress)
- ❌ Current: Multiple QRs per loja (EntryPoint scoped)
- ✅ Planned: One universal QR per org, loja customization via `StoreSignupConfiguration`
- ✅ Planned: Dynamic form questionnaires per loja (no curriculum, practical questions only)
- ✅ Planned: "Choose loja" → "Choose action" (perfil ou vaga) flow
- **Status**: Architecture defined, implementation ready (use cartographer + technical plan)

### 2. **Learning Phase 2**
- ⚠️ Quiz points calculation incomplete (stub at line 174 in courses/models.py)
- ❌ Custom event types (currently 22 fixed types)
- ❌ Formalized recommendation engine (rule-based only)
- ⚠️ Learning challenge auto-award (manual check in service, not trigger-based)

### 3. **Console Improvements**
- ⚠️ Cascading dropdowns use AJAX (N+1 risk, could batch)
- ⚠️ Policy reach estimation slow for large datasets (iterates all memberships)
- ❌ Bulk operations (bulk assign users to trails, bulk import courses)
- ❌ Audit trail export (CSV/JSON of RelationTransitionEvent + Ledger)

### 4. **LGPD & Compliance**
- ⚠️ Many retention dates marked "PENDENTE" (need legal review)
- ❌ Automated GDPR deletion jobs (scaffolded, not wired)
- ⚠️ Retention policy manual call (should be Celery beat scheduled)
- ❌ Data export API for GDPR right-to-portability

### 5. **Integrations**
- ⚠️ HRIS integration stubbed (EmploymentRecord model exists, adapter missing)
- ⚠️ Assessment integration stubbed (AssessmentPort defined, adapter missing)
- ⚠️ File storage integration partial (S3 optional, local default)
- ❌ AI matching adapter (ports defined, no implementation)

### 6. **Performance & Scaling**
- ⚠️ ContentEvent table likely to grow large (no sharding/archiving strategy)
- ⚠️ Ledger immutability blocks UPDATES (append-only design correct, but queries must aggregate)
- ❌ Caching layer (Redis used for sessions/Celery, not for queries)
- ❌ Async task retry strategy (webhook, notification delivery one-shot)

### 7. **Testing**
- ⚠️ 73 migrations → complex schema versioning tests needed
- ⚠️ Multi-tenant tests (each test needs schema isolation)
- ⚠️ Hexagonal adapter testing (mocks for ports)
- ❌ E2E tests for critical flows (signup → match → contact → response)
- ❌ Performance tests (concurrent matching, notification delivery)

### 8. **Documentation**
- ✅ CLAUDE.md exists (high-level overview)
- ✅ This CODEBASE_MAP.md (detailed architecture)
- ❌ API documentation (Swagger/OpenAPI)
- ❌ Runbook for ops (backup, recovery, incident response)
- ❌ Developer onboarding guide (setup, common tasks, debugging)

### 9. **Code Quality**
- ⚠️ Some functions are long (services.py 1,650 lines)
- ⚠️ Inline logging uses `print()` instead of `logger` (configuration/signals.py)
- ⚠️ Email extraction for OTP fragile (looks up first profile by phone suffix)
- ❌ Type hints (Python 3.12 ready, few used currently)

---

## Recommendations for Next Steps

### Phase 1: QR Redesign (2-3 weeks)
1. Implement `StoreSignupConfiguration` model + migrations
2. Implement `LojaSurveyForm` builder (whitelisted questions only)
3. Create store chooser + action chooser views
4. Refactor signup to use dynamic questionnaire
5. Implement backwards compatibility (old QRs still work)
6. **Validation**: Test against commercial promises (Brochure + FAQ)

### Phase 2: Critical Fixes (1 week)
1. Quiz points calculation (complete the stub)
2. GDPR deletion automation (wire Celery task)
3. Retention policy scheduling (add to CELERY_BEAT_SCHEDULE)
4. Type hints (Python 3.12 ready, add gradually)

### Phase 3: Performance (2 weeks)
1. ContentEvent archiving strategy (partition by date, compress old)
2. Query optimization (N+1 audit, add `.select_related()`, `.prefetch_related()`)
3. Caching layer (Redis for common queries)
4. Bulk operations (bulk assign, bulk import)

### Phase 4: Testing & Docs (2-3 weeks)
1. E2E tests (critical user flows)
2. API documentation (Swagger)
3. Developer runbook (setup, common tasks, troubleshooting)
4. Ops runbook (backup, recovery, incident response)

---

## File Statistics

| Directory | Files | Purpose |
|-----------|-------|---------|
| `configuration/` | 35 | Org hierarchy, integrations |
| `recruitment/` | 85 | Matching engine, LGPD |
| `courses/` | 25 | Learning content |
| `learning/` | 40 | Event stream, gamification |
| `students/` | 20 | Learner UX |
| `console/` | 50 | Admin back-office |
| `publishing/` | 15 | Wiki, feed |
| `accounts/` | 18 | Auth, registration |
| `templates/` | 120 | HTML templates (all modules) |
| `static/` | 45 | CSS, JS, assets |
| **Total** | **2,370** | Full MatchCo platform |

---

## Navigation Guide

### To add a new course type
→ See `courses/models.py` (ItemBase subclass) + `console/templates/console/course_editor.html` + tests

### To add a new recruitment integration
→ See `recruitment/integrations/ports.py` (define port) + `adapters.py` (implement) + `registry.py` (register)

### To add a new audience filter
→ See `audience/models.py` (dimension choice) + `audience/services.py` (matching logic) + `console/audience_form.html`

### To add a new notification channel
→ See `recruitment/integrations/ports.py` (NotificationPort) + `learning/services.py` (deliver_notification) + `accounts/models.py` (UserNotificationPreference)

### To add a new learning challenge
→ See `learning/models.py` (LearningChallenge) + `learning/services.py` (award_points_for_event, auto-award logic)

### To debug LGPD compliance
→ See `recruitment/models.py` (Ledger, CandidateConsent) + `recruitment/services.py` (LGPD functions) + `VALIDATION_COMMERCIAL_VS_TECHNICAL.md`

### To test multi-tenancy
→ See `tests/` (use `tenant_context()` from django-tenants) + `configuration/signals.py` (mirror sync tests)

---

## References

- **Architecture Decisions**: `/CLAUDE.md` (high-level overview)
- **Technical Plan**: `/QR_REDESIGN_TECHNICAL_PLAN.md` (detailed implementation roadmap)
- **Commercial Promises**: `/Downloads/MatchCo_Shopping_Commercial_Brochure_v2.1_PREVIEW.pdf` + `/FAQ_v1.0_FINAL.pdf`
- **Competitive Analysis**: `/COMPETITIVE_ANALYSIS.md` (market positioning)
- **Pricing Strategy**: `/PRICING_STRATEGY.md` (go-to-market model)
- **Validation Matrix**: `/VALIDATION_COMMERCIAL_VS_TECHNICAL.md` (conformance check)

---

**Status**: ✅ **Complete & Validated** (as of 2026-10-09)

If cartographer helped, consider starring: https://github.com/kingbootoshi/cartographer ⭐
