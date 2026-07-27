# 📌 Versioning & Release Guide

## Semantic Versioning

Este projeto usa **Semantic Versioning (SemVer)** com o formato: `MAJOR.MINOR.PATCH-PRERELEASE`

### Versão Structure
- **MAJOR**: Mudanças incompatíveis na API ou arquitetura
- **MINOR**: Novas funcionalidades compatíveis com versões anteriores
- **PATCH**: Correções de bugs
- **PRERELEASE**: alpha, beta, rc (release candidate)

### Exemplos
- `2.0.0-alpha.1` → Primeira alpha da versão 2.0
- `2.0.0-alpha.2` → Segunda alpha da versão 2.0
- `2.0.0-beta.1` → Beta release
- `2.0.0-rc.1` → Release candidate
- `2.0.0` → Versão final

## Release Workflow

### 1️⃣ Desenvolvimento
```bash
# Trabalhar normalmente em features
git commit -m "feat: sua feature"
git commit -m "fix: seu bug fix"
```

### 2️⃣ Preparar Release

#### Local
```bash
# Verificar status
git status
git log --oneline -10

# Garantir que tudo está no remoto
git push origin main
```

#### Criar Tag
```bash
# Tag anotada (com mensagem descritiva)
git tag -a v2.0.0-alpha.2 -m "Version 2.0.0-alpha.2: Descrição detalhada..."

# Fazer push da tag
git push origin v2.0.0-alpha.2

# Verificar tag
git tag -l
git show v2.0.0-alpha.2
```

### 3️⃣ Criar Release no GitHub
```bash
# Criar release (abre editor ou usa arquivo)
gh release create v2.0.0-alpha.2 --title "Title" --notes "Descrição"

# Ou criar com arquivo
gh release create v2.0.0-alpha.2 --title "Title" -F RELEASE_NOTES.md
```

### Release Notes Template
```markdown
## 🎉 Release Title

### ✨ New Features
- Feature 1
- Feature 2

### 🔧 Improvements
- Improvement 1
- Improvement 2

### 🐛 Bug Fixes
- Fix 1
- Fix 2

### 📦 Version Info
- **Version**: X.Y.Z-type.N
- **Release Type**: (Alpha/Beta/RC/Stable)
- **Branch**: main

### 🚀 Next Steps
- What's coming next
```

## Histórico de Versões

### v2.0.0-alpha.2 (Current)
- ✅ Course Editor with full content management
- ✅ Drag-and-drop for modules and content
- ✅ Auto-save on reorder
- ✅ Edit buttons for all content types

### v2.0.0-alpha.1
- Initial Course Editor implementation

## Padrões de Commit

Use conventional commits para melhor rastreamento:

```
feat: add new feature
fix: fix a bug
docs: update documentation
style: improve code formatting
refactor: refactor code
perf: improve performance
test: add tests
chore: maintenance tasks
```

## Checklist Antes de Release

- [ ] Todos os commits fizeram push para `origin/main`
- [ ] Testes passando (se houver)
- [ ] Documentação atualizada
- [ ] CHANGELOG.md atualizado (se houver)
- [ ] Tag criada localmente
- [ ] Tag fizeu push para remoto
- [ ] Release criado no GitHub
- [ ] Release notes descrevem mudanças

## Comandos Úteis

```bash
# Ver histórico de tags
git tag -l

# Ver detalhes de uma tag
git show v2.0.0-alpha.2

# Deletar tag local
git tag -d v2.0.0-alpha.2

# Deletar tag remota
git push origin --delete v2.0.0-alpha.2

# Listar releases
gh release list

# Ver release específico
gh release view v2.0.0-alpha.2

# Atualizar release
gh release edit v2.0.0-alpha.2 --notes "Nova descrição"
```

## Próxima Versão

A próxima versão será **v2.0.0-alpha.3** (ou beta.1 se funcionalidades estiverem completas).

Siga o mesmo workflow:
1. Trabalhe nas features
2. Faça push dos commits
3. Crie tag anotada
4. Faça push da tag
5. Crie release no GitHub

---

**Last Updated**: 2026-07-27
**Maintainer**: Franco
