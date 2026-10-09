# Sincronização: Cartographer + Claude Code + Documentação

**Objetivo**: Manter arquivos atualizados quando trabalhando em paralelo (Cartographer + code editing)

---

## 📁 Estrutura de Documentação (Sync Point)

```
matchco-platform/
├── docs/
│   ├── CODEBASE_MAP.md              ← 🔵 SOURCE OF TRUTH (Arquitetura)
│   ├── APP_PWA_ARCHITECTURE.md      ← Frontend PWA
│   └── install.md                   ← Setup guide
│
├── CLAUDE.md                        ← 📌 High-level overview (update refs)
├── AGENTS.md                        ← Automation scripts (if any)
├── MEMORY.md                        ← User memory index (if any)
│
├── QR_REDESIGN_TECHNICAL_PLAN.md    ← 🟡 Implementation detail
├── VALIDATION_COMMERCIAL_VS_TECHNICAL.md ← 🟡 Conformance check
├── COMPETITIVE_ANALYSIS.md          ← 🟡 Market positioning
├── PRICING_STRATEGY.md              ← 🟡 Go-to-market
├── MAPPING_SUMMARY.md               ← 🟡 Validation recap
└── SYNCHRONIZATION_GUIDE.md         ← THIS FILE (How to keep synced)
```

### Legenda
- 🔵 **SOURCE OF TRUTH** - Ler primeiro, atualizar frequentemente
- 🟡 **REFERENCE DOCS** - Consultar durante implementação
- 📌 **PROJECT DOCS** - Manter atualizados com links

---

## 🔄 Fluxo de Sincronização

### Quando Alterar Código

1. **Ler CODEBASE_MAP.md** (context)
   ```bash
   # Buscar secção relevante (ex: "Recruitment Service Layer")
   grep -n "recruitment/services.py" docs/CODEBASE_MAP.md
   ```

2. **Editar código** no IDE
   ```bash
   # Fazer mudanças normalmente
   # Commit com mensagem clara (include file paths)
   git commit -m "feat(recruitment): add billing_limit to Position

   - Add max_openings field to prevent overbooking
   - Update Position model + migration
   - See docs/CODEBASE_MAP.md line XXX for context"
   ```

3. **Atualizar doc se mudança é "arquitetura"**
   ```bash
   # Se mudança é grande (novo campo, novo model, novo service):
   # Editar CODEBASE_MAP.md, seção relevante
   # Ex: docs/CODEBASE_MAP.md → "Recruitment Service Layer" → Position model table
   ```

4. **Verificar comercial alignment**
   - Se mudança afeta recruitment flows → verificar VALIDATION_COMMERCIAL_VS_TECHNICAL.md
   - Certificar que não quebra promessas comerciais

5. **Commit doc change**
   ```bash
   git add docs/CODEBASE_MAP.md
   git commit -m "docs: update Position model (added max_openings field)"
   ```

---

## 📊 Quando Atualizar Qual Documento

| Tipo de Mudança | Arquivo | Ação |
|---|---|---|
| **Novo model** | CODEBASE_MAP.md | Add table em "Module Guide" section |
| **New service function** | CODEBASE_MAP.md | Add entry em "Key Service Functions" |
| **Bug fix** | NÃO ATUALIZAR | (internal implementation) |
| **Feature + comercial impact** | VALIDATION_COMMERCIAL_VS_TECHNICAL.md | Verificar conformance |
| **New URL route** | CODEBASE_MAP.md | Update "URL Routing Structure" |
| **New migration** | CODEBASE_MAP.md | Note em "Migrations Strategy" |
| **Performance change** | CODEBASE_MAP.md | Update relevant section |
| **LGPD/Compliance change** | CODEBASE_MAP.md + VALIDATION | Ambos |

---

## 🎯 Checklist: Manter Sincronizado

### Weekly (Sexta-feira)
- [ ] Review PRs opened this week
- [ ] Check if CODEBASE_MAP.md needs updates (new models? new flows?)
- [ ] Check if VALIDATION_COMMERCIAL_VS_TECHNICAL.md still aligned
- [ ] Update CLAUDE.md if big architecture change
- [ ] Commit doc updates together with code

### Before Release
- [ ] Run through CODEBASE_MAP.md "Navigation Guide" (ensure still accurate)
- [ ] Update version number in docs
- [ ] Verify all critical flows documented
- [ ] Check MAPPING_SUMMARY.md "90-day roadmap" (update what's done)

### When Adding Feature
- [ ] Update CODEBASE_MAP.md before starting (plan it!)
- [ ] Update MAPPING_SUMMARY.md "What's Missing" section
- [ ] If recruitment-related: verify VALIDATION_COMMERCIAL_VS_TECHNICAL.md
- [ ] Update QR_REDESIGN_TECHNICAL_PLAN.md if related

---

## 💡 Best Practices

### 1. Use CODEBASE_MAP as Living Document
```bash
# Before starting feature work:
nano docs/CODEBASE_MAP.md
# Read relevant section
# Decide where code will live
# Make notes
```

### 2. Link Code to Documentation
```python
# In your code comments, reference docs:
class MatchcoSignupView(View):
    """
    Recruitment signup flow.
    
    See docs/CODEBASE_MAP.md → "Candidate Signup" section.
    Validates against VALIDATION_COMMERCIAL_VS_TECHNICAL.md conformance.
    """
```

### 3. Update Docs in Same PR as Code
```bash
git log --oneline
# Output should show code + doc commits close together
# NOT: 5 code commits, then 1 doc commit 3 weeks later
```

### 4. Version Docs with Code
```bash
# In migration comments or commit:
"""
Migration 0074_recruitment_position_billing_limit.py

See docs/CODEBASE_MAP.md line 485 (Position model table)
Updated: max_openings field added to prevent overbooking
Deadline: Commercial requirement for enterprise tier
"""
```

---

## 🔍 Common Scenarios

### Scenario 1: Add New Audience Filter Dimension

1. **Read**: CODEBASE_MAP.md → "Key Concepts" → "Eligibility & Audience Policies"
2. **Code**: 
   - Update `audience/models.py` (add dimension choice)
   - Update `audience/services.py` (implement matching)
   - Update console template
3. **Doc**:
   - Update CODEBASE_MAP.md → "Audience Eligibility" section
   - Add new row to "Dimensions" table
4. **Commit**: `git add audience/ docs/CODEBASE_MAP.md && git commit`

### Scenario 2: Fix GDPR Compliance Issue

1. **Read**: CODEBASE_MAP.md → "LGPD Compliance Patterns"
2. **Read**: VALIDATION_COMMERCIAL_VS_TECHNICAL.md → "SEGURANÇA" section
3. **Code**: Fix the issue
4. **Doc**: 
   - Update VALIDATION_COMMERCIAL_VS_TECHNICAL.md (mark as fixed)
   - Update MAPPING_SUMMARY.md (move from "Missing" to "Done")
5. **Commit**: `git add recruitment/ docs/CODEBASE_MAP.md VALIDATION_COMMERCIAL_VS_TECHNICAL.md MAPPING_SUMMARY.md`

### Scenario 3: Implement QR Redesign

1. **Read**: 
   - QR_REDESIGN_TECHNICAL_PLAN.md (implementation steps)
   - CODEBASE_MAP.md (current system)
   - VALIDATION_COMMERCIAL_VS_TECHNICAL.md (must pass conformance)
2. **Code**: Follow TECHNICAL_PLAN.md step-by-step
3. **Doc**:
   - Update CODEBASE_MAP.md → "Entry Points & QR" section
   - Update VALIDATION_COMMERCIAL_VS_TECHNICAL.md → check off items
   - Update MAPPING_SUMMARY.md → move QR redesign to "Done"
4. **Commit**: PR with code + doc updates

---

## 📌 Rules

### ✅ DO

- ✅ Reference CODEBASE_MAP.md in commit messages
- ✅ Update docs in same PR as code (if architecture change)
- ✅ Use CODEBASE_MAP.md to plan new features
- ✅ Verify commercial alignment before implementation
- ✅ Keep MAPPING_SUMMARY.md roadmap updated
- ✅ Commit docs changes together with code (not separately)

### ❌ DON'T

- ❌ Leave CODEBASE_MAP.md outdated (it's your map, don't lose it)
- ❌ Implement without reading CODEBASE_MAP.md first
- ❌ Break commercial promises without updating VALIDATION doc
- ❌ Commit code without updating related docs
- ❌ Use CLAUDE.md for implementation details (use CODEBASE_MAP.md instead)

---

## 🚀 Quick Reference

### Find Something
```bash
# "How do I add a new notification channel?"
grep -n "Add a new notification" docs/CODEBASE_MAP.md
# Output: Line XXX in "Common Tasks" section

# "What does OtpVerifyView do?"
grep -n "OtpVerifyView" docs/CODEBASE_MAP.md
# Output: Line XXX in "Frontend & Templates" section
```

### Update Architecture
```bash
# 1. Edit code
# 2. Update docs
nano docs/CODEBASE_MAP.md
# 3. Commit both
git add matchco/recruitment/views.py docs/CODEBASE_MAP.md
git commit -m "feat(recruitment): add otp verify bypass flag

- See docs/CODEBASE_MAP.md line 1234 (OtpVerifyView)"
```

### Verify Conformance
```bash
# Before shipping feature:
grep -n "QR" VALIDATION_COMMERCIAL_VS_TECHNICAL.md
# Ensure all commercial promises still held
```

---

## 📞 Who Edits What

| Person | Edits | Reads |
|--------|-------|-------|
| **Backend Dev** | Code + CODEBASE_MAP.md (if arch change) | CODEBASE_MAP.md, TECHNICAL_PLAN.md |
| **Frontend Dev** | Code + CODEBASE_MAP.md (template section) | CODEBASE_MAP.md, COMPETITIVE_ANALYSIS.md |
| **QA Lead** | VALIDATION_COMMERCIAL_VS_TECHNICAL.md | All (conformance check) |
| **Product Manager** | MAPPING_SUMMARY.md (roadmap) | All docs |
| **DevOps/Ops** | (new) Operations Runbook | CODEBASE_MAP.md, MAPPING_SUMMARY.md |

---

## 🎯 Goal

**One source of truth (CODEBASE_MAP.md) + Implementation guides (TECHNICAL_PLAN.md) + Validation docs (CONFORMANCE, COMMERCIAL) = Aligned execution**

---

**Last Updated**: 2026-10-09  
**Maintainer**: Team (see git blame for specific docs)
