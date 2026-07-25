# Prettier Setup para PyCharm

## Status: Configurado (Django Templates Ignorados)

Prettier foi instalado mas **não formata Django templates** para evitar quebra de sintaxe.

### Arquivos de Configuração

- `.prettierrc.json` — Configuração do Prettier (exclui `*.html`)
- `.prettierignore` — Ignora `talk/**/*.html` (Django templates)
- `package.json` — Scripts de formatação

## ⚠️ Importante: Django Templates Não Usam Prettier

Django templates têm sintaxe especial (`{% %}`, `{{ }}`) que Prettier pode quebrar.

**Solução:** Templates Django são formatadas manualmente durante desenvolvimento com o padrão Flowbite estabelecido.

## Para Formatar Django Templates Manualmente

Use estes atalhos no PyCharm:
- **Mac:** `Cmd + Alt + L` (Reformat Code)
- **Windows/Linux:** `Ctrl + Alt + L`

Isso mantém a indentação correta sem quebrar tags Django.

## Prettier para JavaScript/JSON

Prettier ainda funciona para arquivos `.js`, `.jsx`, `.json`:

```bash
# Formatar JS/JSON apenas
npm run format

# Verificar formatação
npm run format:check
```

## Configurar PyCharm para Usar Prettier (JS apenas)

1. **Abra PyCharm** → Preferências/Settings
2. **Navegue até:** Languages & Frameworks → JavaScript → Prettier
3. **Configure:**
   - ✓ Enable Prettier
   - Prettier package: `/Users/franco/Dev/talk/node_modules/prettier`
   - Configuration file: `.prettierrc.json`
   - Run for files: `*.js,*.jsx,*.json` (sem `*.html`)

4. **Apply** → **OK**

## Padrão de Formatação Django

Todos os templates seguem o **padrão Flowbite** estabelecido em:
- `talk/console/templates/console/course_list.html`
- `talk/console/templates/console/publication_list.html`
- `talk/console/templates/console/document_list.html`
- `talk/console/templates/console/learning_metrics.html`

## Dicas

- Use `Cmd+Alt+L` para formatar Django templates com indentação correta
- Prettier é usado apenas para código JavaScript/JSON do projeto
- Mantenha templates seguindo o padrão Flowbite visual
- Não use Prettier em arquivos `.html` com Django tags
