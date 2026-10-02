# Índice Central de Documentação - Talk / MatchCo
**Data**: 2026-10-02 | **Versão**: 1.0 | **Idioma**: Português

---

## Navegação Rápida

### 📋 Guias de Início Rápido
- **[Setup Rápido para Novos Tenants](01_ADMIN_SETUP_QUICK_REFERENCE.md)** — 20 minutos para onboarding completo
- **[Checklist de Configuração da Arquitetura Multi-Tenant](01_MATCHCO_SETUP_ARCHITECTURE.md)** — Decisões, padrões e infraestrutura

### 🏗️ Arquitetura & Design
- **[Arquitetura Multi-Tenant com Subdomain Routing](02_ARCHITECTURE_MULTITENANT.md)** — Análise completa: subdomain vs path-based, implementação atual
- **[Decisões de Arquitetura Enterprise](02_ARCHITECTURE_DECISIONS.md)** — User management, multi-company, session context

### 📚 Documentação de Features

#### Recrutamento
- **[Recrutamento Enterprise - Checklist Completa](03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.md)** — 14 fases, 400+ items de aceite
- **[Modelo de Dados de Recrutamento](03_RECRUITMENT_DATA_MODEL.md)** — CandidateIdentity, Application, scoring, consentimento
- **[Sistema de Consentimento & Privacidade](03_RECRUITMENT_PRIVACY_LGPD.md)** — CPF, LGPD, compartilhamento entre lojas

#### Cursos & Learning
- **[Cursos Enterprise - Checklist de Implementação](03_COURSES_IMPLEMENTATION_CHECKLIST.md)** — 15 fases: progressão, player, relatórios
- **[Motor de Aprendizagem](03_COURSES_ENGINE.md)** — Access control, progresso, conteúdo, evidências

#### Versionamento & Release
- **[Guia de Versionamento Semântico](04_VERSIONING_GUIDE.md)** — SemVer, workflow de release, tags, GitHub releases
- **[Changelog do Projeto](04_CHANGELOG.md)** — Histórico de versões, features, bug fixes

### 👥 Guias de Usuário
- **[Guia do Administrador - Setup por Setor](05_ADMIN_GUIDE_BY_SECTOR.md)** — Shopping, Hospital, Farmácia
- **[Guia do RH - Pool e Candidaturas](05_RH_GUIDE_CANDIDATE_POOL.md)** — Visibilidade, compartilhamento, prioridade

### 🛠️ Operações & Administração
- **[Troubleshooting & Problemas Comuns](06_OPERATIONS_TROUBLESHOOTING.md)** — DNS, tenant detection, domínios, reset
- **[Backup, Restauração & Disaster Recovery](06_OPERATIONS_BACKUP.md)** — Procedimentos, scripts, checklist

### 📱 APIs & Integração
- **[Contratos de Integração (Ports)](07_INTEGRATION_PORTS.md)** — Identity, Learning, Notifications, Files, AI

### 📊 Relatórios & Analytics
- **[Relatórios Enterprise](08_REPORTS.md)** — Recruitment funnel, courses, compliance, exports

---

## Sumário por Arquivo

| Arquivo Original | Categoria | Documentação Consolidada | Status |
|---|---|---|---|
| MATCHCO_MULTITENANT_ARCHITECTURE.md | Arquitetura | [02_ARCHITECTURE_MULTITENANT.md](02_ARCHITECTURE_MULTITENANT.md) | ✅ |
| ADMIN_QUICK_SETUP_REFERENCE.md | Quick Start | [01_ADMIN_SETUP_QUICK_REFERENCE.md](01_ADMIN_SETUP_QUICK_REFERENCE.md) | ✅ |
| RECRUTAMENTO_ENTERPRISE_IMPLEMENTACAO.md | Recruitment | [03_RECRUITMENT_*](03_RECRUITMENT_*.md) (5 arquivos) | ✅ |
| CURSOS_ENTERPRISE_IMPLEMENTACAO.md | Courses | [03_COURSES_*](03_COURSES_*.md) (2 arquivos) | ✅ |
| VERSIONING.md | Release | [04_VERSIONING_GUIDE.md](04_VERSIONING_GUIDE.md) | ✅ |
| CHANGELOG.md | Release | [04_CHANGELOG.md](04_CHANGELOG.md) | ✅ |

---

## Estrutura de Categorias

### 01 - INÍCIO RÁPIDO (Quick Start & Reference)
Documentação para setup inicial e operações diárias.

### 02 - ARQUITETURA (Architecture & Design)
Decisões técnicas, padrões, multi-tenant, segurança.

### 03 - FEATURES (Implementation Details)
Documentação detalhada por módulo: recruitment, courses, integrations.

### 04 - OPERAÇÕES (Release & Operations)
Versioning, changelog, deployment, troubleshooting.

### 05 - USUÁRIOS (User Guides)
Guias por função: admin, RH, lojista, candidato.

### 06 - INFRAESTRUTURA (Operations & DevOps)
Backup, disaster recovery, monitoring, scripts.

### 07 - INTEGRAÇÃO (APIs & External Systems)
Contratos, ports, adapters, external services.

### 08 - DADOS (Reports & Analytics)
Relatórios, exports, compliance, auditoria.

---

## Busca Rápida por Tópico

### Setup & Deployment
- Setup rápido: [01_ADMIN_SETUP_QUICK_REFERENCE.md](01_ADMIN_SETUP_QUICK_REFERENCE.md)
- Multi-tenant: [02_ARCHITECTURE_MULTITENANT.md](02_ARCHITECTURE_MULTITENANT.md)
- Por setor: [05_ADMIN_GUIDE_BY_SECTOR.md](05_ADMIN_GUIDE_BY_SECTOR.md)

### Recruitment
- Implementação completa: [03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.md](03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.md)
- Modelo de dados: [03_RECRUITMENT_DATA_MODEL.md](03_RECRUITMENT_DATA_MODEL.md)
- Privacidade LGPD: [03_RECRUITMENT_PRIVACY_LGPD.md](03_RECRUITMENT_PRIVACY_LGPD.md)
- Pool & candidaturas: [05_RH_GUIDE_CANDIDATE_POOL.md](05_RH_GUIDE_CANDIDATE_POOL.md)

### Courses & Learning
- Implementação: [03_COURSES_IMPLEMENTATION_CHECKLIST.md](03_COURSES_IMPLEMENTATION_CHECKLIST.md)
- Motor: [03_COURSES_ENGINE.md](03_COURSES_ENGINE.md)

### Release & Versioning
- Versionamento: [04_VERSIONING_GUIDE.md](04_VERSIONING_GUIDE.md)
- Changelog: [04_CHANGELOG.md](04_CHANGELOG.md)

### Operações
- Troubleshooting: [06_OPERATIONS_TROUBLESHOOTING.md](06_OPERATIONS_TROUBLESHOOTING.md)
- Backup/Recovery: [06_OPERATIONS_BACKUP.md](06_OPERATIONS_BACKUP.md)

---

## Histórico de Consolidação

| Data | Ação | Responsável |
|---|---|---|
| 2026-10-02 | Leitura e consolidação de 6 arquivos base | Claude Code |
| 2026-10-02 | Criação deste índice e reorganização em 8 categorias | Claude Code |

---

## Próximos Passos

1. Revisar índice com equipe
2. Validar links e cross-references
3. Adicionar conteúdo expandido conforme necessário
4. Criar busca global (ferramentas de site)

---

**Última Atualização**: 2026-10-02 · **Mantido por**: Franco · **Repositório**: https://github.com/francopoleo/talk
