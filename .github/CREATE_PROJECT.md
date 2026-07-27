# 🎯 GitHub Project Setup (Manual)

GitHub Projects v2 requer setup via web. Leva 2 minutos.

---

## ⚡ Quick Setup

### 1. Acesse Projects
```
https://github.com/francopoleo/talk/projects
```

### 2. Click "New Project"
- Title: `Talk Phase 2 Development`
- Template: **Table** (simpler)
- Visibility: **Public** or **Private** (sua escolha)
- Click **Create project**

### 3. Configure Colunas

Delete columns padrão e crie:

```
🔴 Backlog    → Novas issues
🟡 Ready      → Críticos do sprint atual
🟠 In Progress → Trabalho em curso
🟢 Testing    → PR criada/testando
✅ Done       → Merged
```

**Como fazer:**
1. Clique em "+" para adicionar coluna
2. Nome da coluna: `🔴 Backlog` (etc)
3. **Automation:** Choose "Issue opened" → Move to Backlog

### 4. Adicione Issues

**Option A (Rápido):**
```bash
# Na coluna Backlog, clique "Add from repository"
# Selecione: Issues #001-#028
```

**Option B (Manual):**
- Abra issue #001
- Clique "Add to project" (direita)
- Selecione "Talk Phase 2 Development"
- Repeat para todas

### 5. Configure Automações

Para cada coluna, clique "..." → Automations:

| Coluna | Trigger | Action |
|--------|---------|--------|
| Backlog | Issue opened | Add to Backlog |
| Ready | Manual | (você move) |
| In Progress | Manual | (você move) |
| Testing | PR created | Add to Testing |
| Done | PR merged | Move to Done |

---

## 📋 Alternativa Rápida (Sem Automações)

Se quer algo simples agora:

1. Crie project "Talk Phase 2"
2. Adicione colunas: Backlog, In Progress, Done
3. Manualmente mova issues quando trabalhar

**Depois você refina com automações.**

---

## 🔗 Links Rápidos

- **Projects:** https://github.com/francopoleo/talk/projects
- **Issues:** https://github.com/francopoleo/talk/issues
- **Docs:** `.github/GITHUB_WORKFLOW.md`

---

**Tempo:** 2-3 minutos  
**Resultado:** Sprint board visual no GitHub
