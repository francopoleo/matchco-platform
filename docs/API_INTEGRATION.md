# Integrações enterprise do Talk

## Credenciais

Gestores criam credenciais em `POST /api/v1/integrations/credentials/` com sessão autenticada e organização ativa. A resposta exibe a chave uma única vez. O banco armazena apenas o hash SHA-256 e o prefixo para identificação.

As chamadas de parceiro usam:

```http
X-Talk-API-Key: talk_...
```

ou `Authorization: ApiKey talk_...`. A credencial é limitada à organização, pode ter escopos, expiração e rotação. A chave anterior deixa de funcionar imediatamente após a rotação.

## Recursos

- `GET /api/v1/documents/`
- `GET /api/v1/documents/{id}/`
- `PATCH /api/v1/documents/{id}/` — atualiza metadados e audiência, com escopo `documents:write`;
- `DELETE /api/v1/documents/{id}/` — arquiva logicamente sem apagar versões ou auditoria;
- `GET /api/v1/documents/{id}/downloads/`
- `POST /api/v1/documents/{id}/versions/`
- `GET /api/v1/analytics/engagement/`
- `GET /api/v1/gamification/summary/`
- `GET /api/v1/gamification/leaderboard/`
- `GET /api/v1/partner/me/`
- `GET /api/mobile/sync/`
- `POST /api/mobile/events/`

Documentos, analytics e leaderboard respeitam a organização ativa (ou a organização da API key), a política de audiência e os escopos do usuário/gestor. Histórico individual de downloads não é exposto pela API de parceiro; o endpoint retorna somente agregados para gestores.

Parceiros são entidades da organização com `PartnerMembership` por usuário (`viewer` ou `manager`). Uma credencial pode ser vinculada a um parceiro e, nesse caso, `/api/v1/partner/me/` retorna somente aquele contexto.

## Webhooks

`WebhookSubscription` registra endpoint, eventos e segredo por organização. Domínios que geram eventos criam um `WebhookDelivery` durável no outbox. O comando abaixo entrega pendências e assina o corpo com HMAC-SHA256:

```bash
python manage.py deliver_webhooks --limit 100
```

Cabeçalhos enviados:

- `X-Talk-Event`
- `X-Talk-Signature`

O worker Celery é opcional; o outbox permite começar com cron/management command e migrar para fila sem alterar os modelos ou os contratos. Quando habilitado, use `celery -A cep.celery worker -B` para processar webhooks e retentar entregas de notificação. E-mails são multipartes, com templates em texto/HTML e backend SMTP configurável.

## OpenAPI

O schema Swagger existente em `/doc/` documenta as rotas REST. O arquivo `docs/EXECUTION_PLAN.md` registra quais adaptadores ainda dependem de implantação (S3, FCM, SSO e aplicativo mobile nativo).

## Clientes SDK

Clientes mínimos, sem duplicar a lógica de audiência do servidor, estão disponíveis em:

- `sdk/python/` — pacote fonte `talk_sdk`, sem dependências externas;
- `sdk/node/` — módulo CommonJS para Node 18+ usando `fetch` nativo;
- `sdk/php/TalkClient.php` — cliente PHP com cURL.

Eles cobrem documentos, analytics de engajamento, contexto do parceiro e sincronização/eventos mobile. A distribuição em PyPI/npm/Packagist fica deliberadamente separada da publicação do produto e requer nome, versão, licença e credenciais dos respectivos registries.
