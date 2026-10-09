# MatchCo Platform

**Plataforma SaaS multiempresa para recrutamento, aprendizagem e comunicação**

Plataforma de aprendizado corporativo com suporte a cursos, quizzes, rastreamento de conclusão e compartilhamento de conteúdo.

---

## 📊 Status

**Phase 3.3B:** ✅ COMPLETE (Production Ready)
- Generic hierarchy system
- Quiz v2.0 with editor
- Organization-based access control
- Course management console
- 66 tests passing

**Phase 2:** 🚀 IN PROGRESS (28 issues)
- Content Sharing System
- Completion Tracking (3 levels)
- Video Strategy & Security
- Analytics & Reporting

---

## 🏗️ Architecture

```
MatchCo Platform (Django + templates)
├── Core: Multi-tenant organization system
├── Learning Management: Courses, modules, quizzes
├── Console: Manager UI for content management
├── Student Portal: Course player with progress tracking
├── Content Sharing: Manager → Student distribution system
└── Compliance: LGPD/HIPAA audit trails & certificates
```

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+
- PostgreSQL 13+

### Setup

```bash
# 1. Clone repository
git clone https://github.com/francopoleo/matchco-platform.git
cd matchco-platform

# 2. Create environment file
cp .env.example .env
# Edit .env with your settings

# 3. Start containers
docker-compose up -d

# 4. Run migrations & setup
docker exec matchco-app ./setup.sh

# 5. Access application
# Console (Manager): http://localhost:8000/console/
# Student Portal: http://localhost:8000/
# Admin: http://localhost:8000/admin/
```

---

## 📁 Project Structure

```
matchco/
├── matchco/                      # Django project root
│   ├── matchco/               # Django settings, URLs, WSGI e core
│   ├── console/               # Manager console (CRUD)
│   ├── courses/               # Course models & views
│   ├── students/              # Student portal
│   ├── learning/              # Learning management
│   ├── configuration/         # Organizations & permissions
│   ├── publishing/            # Course publishing workflow
│   ├── accounts/              # User authentication
│   └── templates/             # Django templates
├── docs/                      # Documentation
│   ├── 1_GETTING_STARTED/     # Onboarding guides
│   ├── 2_ARCHITECTURE/        # System design
│   ├── 3_LEARNING_MANAGEMENT/ # Quiz, completion tracking
│   ├── 4_MEDIA_MANAGEMENT/    # Video strategy
│   ├── 5_FEATURES/            # Content sharing design
│   ├── 6_OPERATIONS/          # Deployment, monitoring
│   ├── 7_COMPLIANCE/          # LGPD, HIPAA
│   ├── 8_BUSINESS/            # Marketing, sales
│   ├── _META_DOCS/            # Documentation index
│   └── archive/               # Deprecated files
├── .github/                   # GitHub configuration and automation
└── docker-compose.yml         # Docker configuration
```

---

## 🎯 Core Features

### ✅ Implemented (Phase 1 & 3)
- **User Management:** Email signup, multi-organization, RBAC
- **Course System:** CRUD, modules hierarchy, publishing workflow
- **Quiz System v2.0:** Multiple question types, editor, student interface
- **Completion Tracking Level 1:** Basic progress tracking (text/video/quiz)
- **Organization-Based Access Control:** User isolation by org
- **Console UI:** Manager interface with Flowbite design system
- **Student Portal:** Course player with responsive design

### 🚀 In Development (Phase 2)
- **Content Sharing:** Manager shares courses/modules to users
- **Completion Tracking Level 2:** Time tracking, customizable requirements
- **Completion Tracking Level 3:** Certificates, audit logs, retraining schedules
- **Video Strategy:** S3 storage, presigned URLs, DRM
- **Analytics:** Completion rates, user learning paths

---

## 📊 Desenvolvimento

O roadmap atual e seus critérios de aceite estão no
[plano mestre](matchco/docs/development/MATCHCO_MASTER_PLAN.md) e no
[plano de validação](matchco/docs/development/MATCHCO_VALIDATION_PLAN.md).

---

## 📚 Documentation

- **[MATCHCO_MASTER_PLAN.md](matchco/docs/development/MATCHCO_MASTER_PLAN.md)** - visão consolidada, fases e decisões
- **[MATCHCO_CARTOGRAPHER.md](matchco/docs/development/MATCHCO_CARTOGRAPHER.md)** - mapa único da documentação
- **[Central de documentação](matchco/docs/help/html/README.html)** - Help e documentação do produto
- **[FLOWBITE_DESIGN_SYSTEM.md](matchco/docs/development/REFERENCES/FLOWBITE_DESIGN_SYSTEM.md)** - UI/UX standards
- **[GUIA_RAPIDO_NAVEGACAO.html](matchco/docs/help/html/GUIA_RAPIDO_NAVEGACAO.html)** - Guia de navegação

---

## 🛠️ Tech Stack

- **Backend:** Django 4.2+, Python 3.12+
- **Database:** PostgreSQL 13+
- **Frontend:** Django templates, Tailwind CSS, Flowbite components
- **Authentication:** Email-based with multi-tenant org switching
- **Deployment:** Docker, AWS (EC2 + RDS + S3)
- **Compliance:** LGPD, HIPAA compliance measures

---

## 🧪 Testing

O ambiente Python local oficial é `.venv312`, com Python 3.12. O antigo
`.venv` (Python 3.8/Django 3) foi descontinuado e não deve ser recriado.

```bash
# Project checks
./.venv312/bin/python matchco/manage.py check

# Recruitment and configuration tests
./.venv312/bin/python matchco/manage.py test recruitment.tests configuration.tests

# Run a specific app
./.venv312/bin/python matchco/manage.py test courses

# Run with coverage
./.venv312/bin/python -m coverage run --source='matchco' matchco/manage.py test recruitment.tests
coverage report
```

**Current Status:**
- ✅ Recruitment and configuration suites: 137 tests passing (3 skipped)
- ✅ Configuration tests use the current organization/membership model and do not create tenant schemas.

---

## 🔐 Security & Compliance

- **Authentication:** Session-based with organization context
- **Authorization:** Role-based access control (RBAC)
- **Data Isolation:** Organization-level filtering on all queries
- **LGPD Compliance:** Right-to-be-forgotten, data retention policies
- **HIPAA Compliance:** Audit trails, access controls, encryption

---

## 📋 Development Workflow

### Branching Strategy
```
main (production)
├── develop (integration)
├── feature/* (new features)
├── bugfix/* (bug fixes)
└── hotfix/* (production fixes)
```

### Commit Conventions
```
feat: Add new feature
fix: Fix bug
chore: Maintenance (docs, deps)
test: Test additions
docs: Documentation changes
```

### Pull Requests
1. Create feature branch from `develop`
2. Implement & test changes
3. Create PR with description
4. Code review approval
5. Merge to `develop`
6. Release to `main` when ready

---

## 🚀 Deployment

### Development
```bash
docker-compose up
```

### Production
```bash
# Build and deploy to AWS
docker build -t matchco:latest .
# Push to ECR and deploy via AWS
```

See [03_DEPLOYMENT.md](matchco/docs/development/GUIDES/03_DEPLOYMENT.md) for details.

---

## 🤝 Contributing

1. Review the [Master Plan](matchco/docs/development/MATCHCO_MASTER_PLAN.md) for current work
2. Pick an issue and assign yourself
3. Create feature branch
4. Implement with tests
5. Submit PR linked to issue

---

## 📞 Support & Questions

- **Documentation:** See `matchco/docs` folder
- **Roadmap:** Check `matchco/docs/development/MATCHCO_MASTER_PLAN.md`
- **Master Plan:** `matchco/docs/development/MATCHCO_MASTER_PLAN.md`
- **Validation Plan:** `matchco/docs/development/MATCHCO_VALIDATION_PLAN.md`

---

**Last Updated:** 2026-07-27  
**Version:** 2.0 - Phase 3.3B Complete, Phase 2 In Progress  
**License:** Proprietary
