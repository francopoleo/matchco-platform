# Runbooks operacionais MatchCo

Guias curtos e acionáveis para lidar com incidentes e operações
sensíveis. Ler antes de precisar.

| Runbook | Quando usar |
|---|---|
| [INCIDENTE_ANPD.md](INCIDENTE_ANPD.md) | Vazamento, comprometimento, exposição indevida de dados pessoais |
| [QR_COMPROMETIDO.md](QR_COMPROMETIDO.md) | QR físico adulterado ou destino digital sequestrado |
| [RIGHTS_CASE.md](RIGHTS_CASE.md) | Pedido LGPD (acesso, correção, exclusão, portabilidade) |
| [CUTOVER_PRODUCAO.md](CUTOVER_PRODUCAO.md) | Sair de piloto para produção aberta |

## Antes de qualquer coisa

- Ledger é fonte da verdade. **Nunca apagar** — apenas registrar novos eventos.
- Prazo ANPD: comunicação em prazo razoável (2 dias úteis para risco relevante).
- Prazo LGPD titular: 15 dias úteis a partir da verificação de identidade.
- DPO ativo obrigatório para todo comunicado externo.

## Contatos operacionais

Definidos em `settings.MATCHCO_*_EMAIL`:
- `MATCHCO_DPO_EMAIL` — DPO nomeado.
- `MATCHCO_RIGHTS_EMAIL` — canal LGPD do titular.
- `MATCHCO_INCIDENT_EMAIL` — canal de reporte interno/parceiro.
