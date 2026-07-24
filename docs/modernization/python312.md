# Preparação para Python 3.12

## Estado atual

- Python alvo validado: 3.12.10.
- Django alvo validado: 4.2.30.
- Wagtail e Puput foram removidos do código/configuração ativos.
- O `/admin/` usa Django Admin.
- O Docker está preparado para `python:3.12-slim-bookworm`.

## Alvo técnico

1. Python 3.12.
2. Django 4.2 LTS como primeiro salto controlado.
3. Channels 4 e `channels-redis` 4.
4. Psycopg 2.9 como adapter atual.
5. Django Admin e páginas próprias como única camada administrativa.

## Ordem de migração

1. Remover usos de APIs removidas do Django 4 (`ugettext_lazy`, `django.conf.urls.url` e APIs antigas de Wagtail).
2. Migrar telas de usuário, home, busca e alterações recentes para Django genérico/Admin.
3. Criar o baseline de migrações sem Wagtail conforme [migration-reset.md](migration-reset.md).
4. Criar ambiente limpo com Python 3.12 e instalar as versões alvo.
5. Executar `check`, migrações e testes em banco novo.
6. Repetir o build Docker com o daemon ativo e validar PostgreSQL/Channels.
7. Adotar HTMX progressivamente nos componentes de UX, mantendo fallback server-side.

## Critérios de teste por etapa

- `python manage.py check` sem erros ou warnings novos.
- Carregamento de `/course-list/`, `/students/course/3/`, `/wiki/`, `/feed/` e `/admin/`.
- Testes de elegibilidade, publicação, matrícula, progresso, quiz e gamificação.
- `makemigrations --check` sem alterações pendentes.
- Build limpo do Docker usando a versão alvo.
- Interações HTMX funcionando com resposta parcial e fallback HTML.

## Validação executada

- `manage.py check`: aprovado.
- Todas as migrações: aplicadas com sucesso em SQLite temporário.
- `makemigrations --check --dry-run`: sem alterações pendentes.
- 11 testes de audience, learning, library e publishing: aprovados.
- 4 testes de configuration: aprovados.
- 3 testes de user_management: aprovados.
- Build Docker: pendente de inicialização do daemon local.
