# Auditor local de idioma da interface

O `audit_ui_localization.py` percorre templates HTML, chamadas gettext em
Python e catálogos `pt_BR`. É um verificador determinístico: não usa LLM,
rede, API externa nem chamadas que consumam tokens. Também não modifica código
nem traduz textos; aponta ocorrências para revisão humana.

## Execução

Na raiz do repositório:

```bash
./.venv312/bin/python matchco/docs/development/tools/audit_ui_localization.py
```

O modo padrão exibe apenas contagens e exemplos. Para salvar o inventário
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

## Leitura e fluxo de revisão

1. Revise textos de interface nos templates e marque conteúdo fixo com
   `{% trans %}` ou `{% blocktrans %}`. Em Python, use `gettext` ou
   `gettext_lazy` conforme o momento de avaliação.
2. Trate rótulos dinâmicos, `choices`, erros, estados vazios, placeholders e
   atributos acessíveis como parte da mesma interface.
3. A fonte atual é Português do Brasil. Uma mensagem marcada que não apareça
   no catálogo `pt_BR` pode já estar escrita em português; o relatório indica
   cobertura do catálogo, não substitui revisão linguística nem classifica
   idioma com certeza.
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
exigem triagem. Não marque conteúdo de usuário como tradução de interface.
