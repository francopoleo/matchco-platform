# Prettier Setup para PyCharm

## Instalação Concluída ✓

Prettier e suas dependências foram instaladas via npm.

### Arquivos de Configuração

- `.prettierrc.json` — Configuração do Prettier
- `.prettierignore` — Arquivos a ignorar durante formatação
- `package.json` — Scripts de formatação

## Configurar PyCharm para Usar Prettier

### Opção 1: Prettier como Formatador Padrão (Recomendado)

1. **Abra PyCharm** → Preferências/Settings
2. **Navegue até:** Languages & Frameworks → JavaScript → Prettier
3. **Configure:**
   - ✓ Enable Prettier
   - Prettier package: `/Users/franco/Dev/talk/node_modules/prettier`
   - Configuration file: `.prettierrc.json`
   - Run for files: `*.html,*.jsx,*.js`

4. **Apply** → **OK**

### Opção 2: Usar File Watcher (Auto-formata ao Salvar)

1. Preferências/Settings → Tools → File Watchers
2. Clique em `+` (Add)
3. Configure:
   - Name: `Prettier HTML`
   - File type: `HTML`
   - Scope: `Project Files`
   - Program: `/Users/franco/Dev/talk/node_modules/.bin/prettier`
   - Arguments: `--write $FilePath$`
   - Check: `Auto-save edited files to trigger the watcher`

## Usar via Linha de Comando

```bash
# Formatar todos os arquivos
npm run format

# Formatar apenas templates
npm run format:templates

# Verificar formatação sem modificar
npm run format:check
```

## Comandos Úteis

```bash
# Formatar arquivo específico
npx prettier --write talk/console/templates/console/document_list.html

# Verificar sem aplicar
npx prettier --check talk/console/templates/console/*.html

# Formatar diretório inteiro
npx prettier --write talk/console/templates/
```

## Dicas

- Prettier padroniza **espaçamento, indentação e quebras de linha**
- Use `<!-- prettier-ignore -->` antes de uma seção para ignorar formatação
- A configuração respeita **comentários Django** (`{% %}` e `{{ }}`)
- Ideal para manter **consistência visual** em templates HTML/Django

## Troubleshooting

Se o Prettier não funciona no PyCharm:

1. Reinicie o PyCharm
2. Verifique se `node_modules/prettier` existe
3. Tente executar via terminal: `npx prettier --write arquivo.html`
4. Verifique se `.prettierrc.json` está válido (JSON syntax)
