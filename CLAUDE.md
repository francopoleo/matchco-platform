# MatchCo Platform

A multi-tenant SaaS platform combining LMS (courses, learning paths, gamification), a bilateral recruitment matching engine (Porta Match + Porta Vaga), content management (wiki, feed, documents), and real-time features (chat, notifications). Built on Django + PostgreSQL with schema-per-tenant isolation via `django-tenants`.

## Stack

- **Backend:** Django 4.x, Python 3.12, PostgreSQL
- **Real-time:** Django Channels, Redis
- **Frontend:** HTML/CSS/JS (PWA app at `/app/`)
- **APIs:** DRF + JWT, three SDK clients (Python, Node, PHP)
- **Deployment:** Docker Compose (local dev), Dockerfile (production-ready)
- **Observability:** PostHog analytics, Django logging
- **i18n:** Portuguese (pt-br), English, Spanish

## Key Concepts

1. **Multi-tenant:** Organizations in public schema; tenant schemas per org (courses, publishing, gamification, etc.)
2. **Recruitment:** Bilateral matching engine with QR-driven signup, LGPD-compliant consent model, append-only audit ledger
3. **Event-driven:** `ContentEvent` stream tracks everything; `track_event()` is the central dispatcher for gamification, notifications, trail progression
4. **Eligibility:** Audience policies define who can see content (org, company, unit, role, function, program membership)
5. **Integrations:** Hexagonal architecture (ports & adapters) for HRIS, assessment, notifications, file storage

## Architecture

For detailed architecture, see **[matchco/docs/development/REFERENCES/CODEBASE_MAP.md](matchco/docs/development/REFERENCES/CODEBASE_MAP.md)** — comprehensive module guide, data flows, patterns, gotchas, and navigation.

## Running Locally

```bash
# Install dependencies
pip install -r matchco/config/requirements.txt

# Copy .env template and configure
cp .env.example .env

# Run migrations
python matchco/manage.py migrate

# Start dev server
python matchco/manage.py runserver

# (Optional) Start Celery worker in another terminal
celery -A matchco.celery worker -l info

# (Optional) Start with Docker Compose
docker-compose up
```

## Useful Commands

```bash
# Create new app
python matchco/manage.py startapp <app_name>

# Create migrations
python matchco/manage.py makemigrations [app_name]

# Apply migrations (including tenant schemas)
python matchco/manage.py migrate

# Create superuser
python matchco/manage.py createsuperuser

# Test
python matchco/manage.py test [app_name]

# Lint / Format
black matchco/
flake8 matchco/
```

## Main Apps

| App | Purpose |
|---|---|
| `configuration` | Org hierarchy, multi-tenant control, integrations |
| `recruitment` | Matching engine, candidate lifecycle, LGPD |
| `courses` | Content schema (modules, quizzes, learning items) |
| `learning` | Event stream, gamification, trails, notifications, APIs |
| `students` | Learner experience (enrollment, course player, progress) |
| `publishing` | Wiki & feed (announcements, knowledge base) |
| `documents` | Formal docs with versioning, approval, media library |
| `console` | Admin back-office (CRUD for all content, users, settings) |
| `accounts` | Auth & registration (invitation-code, public signup, email confirmation) |
| `user_management` | User model, profile, password reset |
| `audience` | Eligibility rules (who can see what content) |
| `chat` | Real-time WebSocket course chat |
| `gamification` | Points & badges |

See **[matchco/docs/development/REFERENCES/CODEBASE_MAP.md](matchco/docs/development/REFERENCES/CODEBASE_MAP.md)** for full module guide with models, views, workflows, and integrations.

## Important Patterns

- **Tenant selection:** Host-based (primary) + session-based (workspace switcher)
- **Mirror sync:** `configuration/signals.py` fans User/Org/Company changes to tenant schemas
- **Event-driven:** `learning.track_event()` is called by other apps on actions → awards points, delivers notifications, advances trails
- **Recruitment:** Hexagonal architecture with pluggable integrations (HRIS, assessment, notifications, file storage)
- **LGPD:** Consent model with immutable audit trail; append-only Ledger for recruitment events

## Common Tasks

- **Add a new course content type** → see matchco/docs/development/REFERENCES/CODEBASE_MAP.md → "Navigation Guide"
- **Add a new audience filter** → update `AudienceRule.dimension` choices and `EligibilityService.can_view()`
- **Add a new integration** → create a port in `recruitment/integrations/ports.py`, implement adapter, register in registry
- **Add a new notification channel** → update `NotificationDelivery` model and create delivery task in `learning/`
- **Add a Celery task** → create `tasks.py` in app, add to `CELERY_BEAT_SCHEDULE` if periodic

## Version

Current: `v2.1.0` (SemVer with git tags, conventional commits, GitHub releases)

## Documentation

- **Architecture & modules:** [matchco/docs/development/REFERENCES/CODEBASE_MAP.md](matchco/docs/development/REFERENCES/CODEBASE_MAP.md)
- **PWA app structure:** [matchco/docs/development/REFERENCES/APP_PWA_ARCHITECTURE.md](matchco/docs/development/REFERENCES/APP_PWA_ARCHITECTURE.md)
- **Installation:** [install.md](install.md)
- **SDK clients:** [sdk/README.md](sdk/README.md)
- **Agents/automation:** [AGENTS.md](AGENTS.md)
