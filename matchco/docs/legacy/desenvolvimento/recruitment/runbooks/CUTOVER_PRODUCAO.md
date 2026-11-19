# Runbook — Cutover para produção real

Aplicável quando sair de piloto convidado para produção aberta com
Perfis reais. Sem passar por todos os passos, não sobe.

## Pré-requisitos legais (bloqueiam)

- [ ] Nome legal + CNPJ do controlador em `MATCHCO_CONTROLLER_NAME`.
- [ ] DPO real nomeado (`MATCHCO_DPO_NAME`, `MATCHCO_DPO_EMAIL`).
- [ ] Canal de e-mail de direitos ativo (`MATCHCO_RIGHTS_EMAIL`).
- [ ] Canal de incidente ativo (`MATCHCO_INCIDENT_EMAIL`).
- [ ] Provedores contratados (OTP/SMS, e-mail transacional, WhatsApp
      opcional) com DPA assinado.
- [ ] `MATCHCO_PROCESSOR_REGISTER` populado com nomes, países, DPA refs
      reais (sem `PENDENTE`).
- [ ] RT-02, RT-03, RT-05 revistos com jurídico e configurados.

## Pré-requisitos técnicos

- [ ] `python manage.py pig_check --strict` retorna PASS.
- [ ] Cada `EntryPoint` produtivo passa PIAG (`can_activate()==True`).
- [ ] `apply_retention_task` agendado no Celery beat.
- [ ] `send_pending_notifications_task` agendado.
- [ ] `monitor_entry_points_task` agendado.
- [ ] Backup do Postgres cifrado + deleção-aware (restore respeita
      registros anonimizados).
- [ ] TLS válido no `canonical_destination_url` das QRs.
- [ ] Rate limit no `POST /auth/otp-request` (5/min por IP).
- [ ] Alerta de infra para `LedgerAppendOnlyError` no log.

## Pré-requisitos operacionais

- [ ] Equipe de suporte treinada nos 4 runbooks.
- [ ] Playbook comercial: quando dizer não à Porta Match (rever cânone §1).
- [ ] Piloto piloto sem incidente por N semanas.
- [ ] Métricas do `/ops/metrics/` estáveis.
- [ ] Auditoria externa do Ledger (opcional mas recomendado).

## Sequência de deploy

1. **T-14d**: pig_check --strict passa em staging + freeze de código.
2. **T-7d**: comunicado interno + treinamento de suporte.
3. **T-3d**: staging com dados sintéticos reflete produção.
4. **T-1d**: backup completo, plano de rollback documentado.
5. **T-0**: cutover — apontar DNS/proxy; primeiro EntryPoint ACTIVE.
6. **T+1h**: fumaça manual (signup + feed + match + resposta).
7. **T+24h**: revisão de métricas + Ledger.
8. **T+7d**: pós-cutover review + retrospectiva.

## Rollback

- DNS/proxy volta para versão anterior.
- **Perfis criados no janela**: **NÃO deletar** — Ledger obriga preservação
  mínima. Apenas suspender via `circulation_state='paused'` até estabilizar.
- Comunicar titulares afetados por e-mail.
