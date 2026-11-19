# Centro de Documentação - Talk / MatchCo

**Idioma**: Português  
**Última atualização**: 2026-10-02  
**Versão**: 1.0 - Consolidação Completa

---

## Bem-vindo!

Este é o centro centralizado de documentação para o projeto Talk/MatchCo. Toda a informação de produto, arquitetura, operações e guias de usuário está aqui, organizada por categoria.

**Comece aqui**: [INDEX.md](INDEX.md) para navegação completa.

---

## Estrutura da Documentação

### 📋 01 - INÍCIO RÁPIDO
Documentação para setup inicial e referência rápida de operações.

- **[01_ADMIN_SETUP_QUICK_REFERENCE.md](01_ADMIN_SETUP_QUICK_REFERENCE.md)** — Cartão de referência: 20 minutos para onboard um novo tenant

### 🏗️ 02 - ARQUITETURA
Decisões técnicas, padrões, multi-tenancy, segurança.

- **[02_ARCHITECTURE_MULTITENANT.md](02_ARCHITECTURE_MULTITENANT.md)** — Análise completa de subdomain vs path-based routing, implementação atual, setup por setor

### 📚 03 - FEATURES
Documentação detalhada por módulo: recruitment, courses, integrations.

- **[03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.md](03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.md)** — Checklist de 14 fases com 400+ items de aceite
- **[03_COURSES_IMPLEMENTATION_CHECKLIST.md](03_COURSES_IMPLEMENTATION_CHECKLIST.md)** — Checklist de cursos: progressão, player, relatórios, compliance
- Futuro: Modelos de dados detalhados por feature

### 04 - RELEASE & VERSIONING
Versionamento semântico, processos de release, changelog.

- **[04_VERSIONING_GUIDE.md](04_VERSIONING_GUIDE.md)** — Guia SemVer, workflow de release, checklist
- **[04_CHANGELOG.md](04_CHANGELOG.md)** — Histórico de versões e mudanças

### 👥 05 - USUÁRIOS
Guias por função: admin, RH, lojista, candidato.

- **[05_ADMIN_GUIDE_BY_SECTOR.md](05_ADMIN_GUIDE_BY_SECTOR.md)** — Setup por setor (Shopping, Hospital, Farmácia), funções típicas, fluxos

### 🛠️ 06 - OPERAÇÕES
Backup, disaster recovery, monitoring, troubleshooting.

- **[06_OPERATIONS_TROUBLESHOOTING.md](06_OPERATIONS_TROUBLESHOOTING.md)** — Problemas comuns, verificações, soluções, checklist de diagnóstico

### 📱 07 - INTEGRAÇÃO
Contratos de APIs internas, ports, adapters.

- **[07_INTEGRATION_PORTS.md](07_INTEGRATION_PORTS.md)** — Arquitetura desacoplada: identity, learning, notifications, files, AI, organization ports

### 📊 08 - DADOS
Relatórios, exports, compliance, auditoria.

- Futuro: Guias de relatórios, dashboards, compliance

---

## Busca por Objetivo

### "Preciso configurar um novo tenant/organização"
1. Ler: [01_ADMIN_SETUP_QUICK_REFERENCE.md](01_ADMIN_SETUP_QUICK_REFERENCE.md) (20 min)
2. Ler: [02_ARCHITECTURE_MULTITENANT.md](02_ARCHITECTURE_MULTITENANT.md) - seção correspondente ao setor
3. Ler: [05_ADMIN_GUIDE_BY_SECTOR.md](05_ADMIN_GUIDE_BY_SECTOR.md) para checklist de compliance

### "Preciso implementar uma feature de recrutamento"
1. Ler: [03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.md](03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.md)
2. Verificar status das fases e decidir qual implementar
3. Referência: [02_ARCHITECTURE_MULTITENANT.md](02_ARCHITECTURE_MULTITENANT.md) para contexto

### "Estou debugging um problema de tenant isolation"
1. Ler: [06_OPERATIONS_TROUBLESHOOTING.md](06_OPERATIONS_TROUBLESHOOTING.md) - seção "Problemas de Isolamento"
2. Seguir checklist de diagnóstico
3. Referência: [02_ARCHITECTURE_MULTITENANT.md](02_ARCHITECTURE_MULTITENANT.md) para implementação

### "Preciso adicionar uma nova integração"
1. Ler: [07_INTEGRATION_PORTS.md](07_INTEGRATION_PORTS.md)
2. Seguir seção "Adicionando Nova Integração"
3. Implementar Port abstrato e Null Adapter

### "Preciso fazer release de uma versão"
1. Ler: [04_VERSIONING_GUIDE.md](04_VERSIONING_GUIDE.md)
2. Seguir "Release Workflow"
3. Usar template de "Release Notes"

### "Preciso entender como funciona [feature]"
1. Consultar [INDEX.md](INDEX.md) - seção "Busca Rápida por Tópico"
2. Ler documento específico

---

## Convenções Usadas

### Checklist Status
- `[ ]` Pendente
- `[-]` Em progresso / Parcialmente completo
- `[x]` Concluído e validado
- `[!]` Bloqueado ou aguardando decisão

### Code Blocks
- **Python**: `python manage.py shell`
- **Bash**: `bash` commands
- **SQL**: `sql` queries
- **Config**: `python` settings files

### Admonições
- ✅ Sucesso / Implementado
- ❌ Falha / Não implementado
- ⚠️ Aviso / Cuidado
- ℹ️ Informação / Nota
- 🚀 Feature / Próximo passo

---

## Contribuindo à Documentação

### Como Atualizar

1. **Editar arquivo correspondente**: Todos em `docs/`
2. **Seguir convenções**: Headings, checkboxes, code blocks
3. **Atualizar [INDEX.md](INDEX.md)** se adicionou novo documento
4. **Atualizar "Última atualização"** no footer

### Como Adicionar Nova Seção

1. **Criar arquivo**: `docs/NN_NOME.md`
2. **Adicionar a [INDEX.md](INDEX.md)** com categoria
3. **Linkar de documentos relacionados**
4. **Incluir no histórico de consolidação**

### Template para Novo Documento

```markdown
# Título do Documento

**Público**: Quem deve ler (DevOps, Product Manager, etc)  
**Última atualização**: YYYY-MM-DD

---

## Seção 1

Conteúdo...

---

## Seção 2

Conteúdo...

---

**Última Atualização**: YYYY-MM-DD  
**Referência**: Links para documentação relacionada
```

---

## Manutenção da Documentação

| Artefato | Frequência | Responsável | Status |
|---|---|---|---|
| INDEX.md | Trimestral | Franco | ✅ |
| Checklists | A cada entrega | Responsável da fase | ✅ |
| Troubleshooting | Conforme problemas | DevOps / Suporte | ✅ |
| Guides | Semestral | Product Manager | ✅ |
| Versioning/Changelog | A cada release | Responsável release | ✅ |

---

## Histórico de Consolidação

| Data | Ação | Versão | Documentos |
|---|---|---|---|
| 2026-10-02 | Consolidação inicial | 1.0 | 8 arquivos base |

### Arquivos Originais Consolidados

| Original | Consolidado em | Status |
|---|---|---|
| MATCHCO_MULTITENANT_ARCHITECTURE.md | 02_ARCHITECTURE_MULTITENANT.md | ✅ |
| ADMIN_QUICK_SETUP_REFERENCE.md | 01_ADMIN_SETUP_QUICK_REFERENCE.md | ✅ |
| RECRUTAMENTO_ENTERPRISE_IMPLEMENTACAO.md | 03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.md | ✅ |
| CURSOS_ENTERPRISE_IMPLEMENTACAO.md | 03_COURSES_IMPLEMENTATION_CHECKLIST.md | ✅ |
| VERSIONING.md | 04_VERSIONING_GUIDE.md | ✅ |
| CHANGELOG.md | 04_CHANGELOG.md | ✅ |

---

## Mapa de Cobertura

### Coberto (100%)
- Multi-tenant architecture
- Admin setup & onboarding
- Release management
- Troubleshooting básico
- Integration contracts

### Parcialmente Coberto (50%)
- User guides (apenas admin por setor)
- Feature implementation (apenas recruitment & courses)
- Operations (apenas troubleshooting)

### Não Coberto (0%)
- API documentation detalhada
- Data models (diagrama ER)
- Security policies completas
- Performance tuning
- Disaster recovery procedures
- Dashboard/analytics guides

---

## Roadmap de Documentação

### Q4 2026
- [ ] Adicionar data model diagrams (Recruitment, Courses)
- [ ] Criar security policies document
- [ ] Expandir operations com backup/recovery procedures
- [ ] Criar API reference (auto-gerado via Swagger)

### Q1 2027
- [ ] Guia de candidato (signup, candidatura, onboarding)
- [ ] Guia de lojista (pipeline, comunicação)
- [ ] Guia de RH (pool, consolidado, relatórios)
- [ ] Performance tuning guide

### Q2 2027
- [ ] Migrar para ferramenta de docs (Confluence / MkDocs)
- [ ] Implementar full-text search
- [ ] Versioning de documentação (v1.0, v2.0, etc)
- [ ] Auto-geração de docs a partir de docstrings

---

## Perguntas Frequentes (FAQ)

### Onde encontro a checklist de features de recruitment?
[03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.md](03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.md)

### Como configuro um novo tenant?
[01_ADMIN_SETUP_QUICK_REFERENCE.md](01_ADMIN_SETUP_QUICK_REFERENCE.md)

### Qual é a diferença entre subdomain e path-based routing?
[02_ARCHITECTURE_MULTITENANT.md](02_ARCHITECTURE_MULTITENANT.md) - Seção "Análise: Subdomain vs Path-Based"

### Como faço uma release?
[04_VERSIONING_GUIDE.md](04_VERSIONING_GUIDE.md)

### Estou recebendo erro 404 no console, o que fazer?
[06_OPERATIONS_TROUBLESHOOTING.md](06_OPERATIONS_TROUBLESHOOTING.md) - "404 em `/candidato/signup`"

---

## Contatos & Suporte

- **Product Owner**: Franco (franco@example.com)
- **Tech Lead**: [Tech Lead Name]
- **DevOps**: [DevOps Name]
- **Documentation**: Franco

---

## Licença & Atribuição

- Documentação: Colaboração entre Franco e Claude Code
- Projeto Talk: https://github.com/francopoleo/matchco
- Última geração: 2026-10-02

---

**Comece navegando pelo [INDEX.md](INDEX.md)**
