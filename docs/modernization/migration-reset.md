# Inicialização limpa do banco

As migrações de `courses`, `students`, `gamification`, `videos` e `library` foram recriadas a partir do estado atual dos modelos. Elas não são compatíveis com o histórico antigo que dependia do Wagtail.

Para uma instalação nova:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

Com Docker e sem necessidade de preservar o volume legado:

```bash
docker compose down -v
docker compose build --no-cache
docker compose up
```

O volume antigo não deve ser reutilizado com o novo conjunto de migrações. O banco atual não foi apagado automaticamente.
