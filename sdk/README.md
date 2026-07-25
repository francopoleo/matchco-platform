# Talk SDKs

Clientes mínimos e sem regras duplicadas para os contratos REST do Talk:

- Python: `sdk/python/` (`TalkClient`)
- Node.js: `sdk/node/` (`@talk-platform/client`)
- PHP: `sdk/php/TalkClient.php`

Todos aceitam uma API key com o header `X-Talk-API-Key` e cobrem documentos, analytics, partner portal e sincronização mobile. A autenticação, escopos e audiência continuam sendo decididos pelo Talk.
