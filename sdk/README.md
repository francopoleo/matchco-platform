# MatchCo SDKs

Clientes mínimos e sem regras duplicadas para os contratos REST do MatchCo:

- Python: `sdk/python/` (`MatchCoClient`)
- Node.js: `sdk/node/` (`@matchco-platform/client`)
- PHP: `sdk/php/MatchCoClient.php`

Todos aceitam uma API key com o header `X-MatchCo-API-Key` e cobrem documentos, analytics, partner portal e sincronização mobile. A autenticação, escopos e audiência continuam sendo decididos pelo MatchCo.
