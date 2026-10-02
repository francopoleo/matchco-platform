# Guia de Versionamento Semântico (SemVer)

**Status**: Guia operacional  
**Última atualização**: 2026-10-02

---

## Versionamento Semântico

Este projeto usa **Semantic Versioning (SemVer)** com o formato: `MAJOR.MINOR.PATCH-PRERELEASE`

### Estrutura de Versão

- **MAJOR**: Mudanças incompatíveis na API ou arquitetura
- **MINOR**: Novas funcionalidades compatíveis com versões anteriores
- **PATCH**: Correções de bugs
- **PRERELEASE**: alpha, beta, rc (release candidate)

### Exemplos

- `2.0.0-alpha.1` → Primeira alpha da versão 2.0
- `2.0.0-alpha.2` → Segunda alpha da versão 2.0
- `2.0.0-beta.1` → Beta release
- `2.0.0-rc.1` → Release candidate
- `2.0.0` → Versão final (produção)

---

## Workflow de Release

### 1. Desenvolvimento

```bash
# Trabalhar normalmente em features
git commit -m "feat: sua feature"
git commit -m "fix: seu bug fix"
```

### 2. Preparar Release

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

### 3. Criar Release no GitHub

```bash
# Criar release (abre editor ou usa arquivo)
gh release create v2.0.0-alpha.2 --title "Title" --notes "Descrição"

# Ou criar com arquivo
gh release create v2.0.0-alpha.2 --title "Title" -F RELEASE_NOTES.md
```

---

## Template de Release Notes

```markdown
## 🎉 Título da Release

### ✨ Novas Features
- Feature 1
- Feature 2

### 🔧 Melhorias
- Melhoria 1
- Melhoria 2

### 🐛 Correções de Bugs
- Fix 1
- Fix 2

### 📦 Informações de Versão
- **Versão**: X.Y.Z-type.N
- **Tipo de Release**: (Alpha/Beta/RC/Stable)
- **Branch**: main

### 🚀 Próximos Passos
- O que vem a seguir
```

---

## Padrões de Commit

Use conventional commits para melhor rastreamento:

```
feat:     Adiciona nova funcionalidade
fix:      Corrige um bug
docs:     Atualiza documentação
style:    Melhora formatação de código
refactor: Refatora código
perf:     Melhora performance
test:     Adiciona testes
chore:    Tarefas de manutenção
```

### Exemplos

```bash
git commit -m "feat: add content reordering auto-save"
git commit -m "fix: correct tenant isolation in queries"
git commit -m "docs: update multi-tenant architecture guide"
git commit -m "refactor: simplify course enrollment logic"
```

---

## Checklist Antes de Release

- [ ] Todos os commits fizeram push para `origin/main`
- [ ] Testes passando (se houver)
- [ ] Documentação atualizada
- [ ] CHANGELOG.md atualizado
- [ ] Tag criada localmente
- [ ] Tag fizeu push para remoto
- [ ] Release criado no GitHub
- [ ] Release notes descrevem mudanças
- [ ] Stakeholders notificados (se necessário)

---

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

---

## Histórico de Versões Recentes

### v2.0.0-alpha.2 (2026-07-27)
- ✅ Course Editor com gerenciamento completo de conteúdo
- ✅ Drag-and-drop para módulos e conteúdo
- ✅ Auto-save ao reordenar
- ✅ Botões de edição para todos os tipos de conteúdo

### v2.0.0-alpha.1 (2026-07-26)
- Implementação inicial do Course Editor

---

## Próxima Versão

A próxima versão será **v2.0.0-alpha.3** (ou beta.1 se funcionalidades estiverem completas).

Siga o mesmo workflow:
1. Trabalhe nas features
2. Faça push dos commits
3. Crie tag anotada
4. Faça push da tag
5. Crie release no GitHub

---

**Última Atualização**: 2026-10-02  
**Mantido por**: Franco  
**Repositório**: https://github.com/francopoleo/talk
