# Auditor local de idioma da interface

O `audit_ui_localization.py` percorre templates HTML, chamadas gettext em
Python e catálogos. É um verificador determinístico: não usa LLM, rede, API
externa nem chamadas que consumam tokens. Não modifica código nem traduz
textos; aponta ocorrências para revisão humana.

## Execução

Na raiz do repositório:

```bash
./.venv312/bin/python matchco/docs/development/tools/audit_ui_localization.py
```

O modo padrão exibe apenas contagens e exemplos, incluindo mensagens únicas e
`msgstr` preenchidos em pt-BR, Inglês e Espanhol. Para salvar o inventário
completo sem despejá-lo no terminal:

```bash
./.venv312/bin/python matchco/docs/development/tools/audit_ui_localization.py \
  --output /tmp/matchco-localization-audit.json
```

Para trabalhar por módulo, limite a busca a um caminho relativo à raiz Django
(`matchco/`), por exemplo:

```bash
./.venv312/bin/python matchco/docs/development/tools/audit_ui_localization.py \
  --path console/templates/console \
  --output /tmp/matchco-console-localization.json
```

O JSON completo também pode ser enviado para stdout com `--json`. Evite isso
em uma sessão interativa quando o relatório for grande.

## Marcação e extração

`mark_ui_literals.py` marca texto estático, atributos acessíveis e mensagens
simples de `confirm`, `alert`, `textContent` e validação nos templates;
`mark_python_ui_literals.py` marca rótulos, ajudas, opções fixas e mensagens
comuns de formulários/erros. Ambos têm `--check` e `--path`; sem `--check`,
aplicam a transformação. São limitados a contextos de interface e não devem
ser usados para conteúdo editorial ou dados dinâmicos.

Depois da marcação, atualize os catálogos a partir da pasta `matchco/`:

```bash
../.venv312/bin/python manage.py makemessages --locale=en --locale=es --locale=pt_BR
msgfmt --check -o locale/en/LC_MESSAGES/django.mo locale/en/LC_MESSAGES/django.po
msgfmt --check -o locale/es/LC_MESSAGES/django.mo locale/es/LC_MESSAGES/django.po
msgfmt --check -o locale/pt_BR/LC_MESSAGES/django.mo locale/pt_BR/LC_MESSAGES/django.po
```

Os catálogos centrais em `matchco/locale/` concentram as mensagens extraídas.
A extração só prepara as entradas: preencher e revisar `msgstr` em cada idioma
continua sendo trabalho editorial separado.
Compile apenas esses três arquivos centrais para evitar percorrer e alterar os
catálogos das dependências instaladas no ambiente Python.

## Leitura e fluxo de revisão

1. Revise textos de interface nos templates e marque conteúdo fixo com
   `{% trans %}` ou `{% blocktrans %}`. Em Python, use `gettext` ou
   `gettext_lazy` conforme o momento de avaliação.
2. Trate rótulos dinâmicos, `choices`, erros, estados vazios, placeholders e
   atributos acessíveis como parte da mesma interface.
3. A fonte atual é Português do Brasil. Uma mensagem marcada sem `msgstr` em
   `pt_BR` pode já estar escrita em português; o relatório mede preenchimento,
   não classifica idioma nem substitui revisão linguística.
4. Para cada texto que esteja em outro idioma, mantenha a interface-base em
   pt-BR e adicione/compile as traduções nos catálogos dos outros idiomas.
   Não traduza conteúdo autoral de cursos, Feed, Wiki ou documentos como se
   fosse rótulo da interface.
5. Valide no contexto real, incluindo claro/escuro, mobile, acessibilidade,
   formulários, mensagens e Help contextual. Execute `manage.py check`, os
   testes do módulo e o auditor novamente.

## Limites

O scanner encontra literais visíveis e mensagens marcadas; ele não entende
intenção, branding, conteúdo vindo do banco ou se uma frase está bem traduzida.
Exemplos de dados, código, conteúdo editorial e texto gerado dinamicamente
exigem triagem. Strings que montam HTML dinamicamente em JavaScript também
precisam de auditoria própria. Não marque conteúdo de usuário como tradução de
interface.
