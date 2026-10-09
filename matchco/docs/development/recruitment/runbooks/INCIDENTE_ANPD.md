# Runbook — Incidente de segurança com dados pessoais (ANPD)

Base legal: LGPD art. 48. Prazo de comunicação à ANPD: **razoável**
(interpretado como até 2 dias úteis para incidentes com risco relevante).

---

## 1. Detecção (T+0)

Fontes de disparo:
- Alerta de `LedgerAppendOnlyError` no log da aplicação.
- Alerta de `AUTHORITY_VIOLATION` no `/ops/metrics/` (> 0 em 7 dias).
- Reporte via `MATCHCO_INCIDENT_EMAIL`.
- Reporte de titular via `MATCHCO_RIGHTS_EMAIL`.
- Comportamento anômalo (ex.: emissão de contato antes de MATCH).

**Ação imediata:** anotar timestamp, quem detectou, canal.

## 2. Contenção (T+0 a T+2h)

- Isolar componente afetado (pausar Celery beat, revogar EntryPoint,
  suspender EmployerActor comprometido).
- Congelar Ledger relevante — se necessário, snapshot manual.
- Rotacionar credenciais dos provedores comprometidos (OTP/SMS/e-mail/DB).
- **Não delete evidência**: Ledger é append-only. Retire acesso, não apague.

Comandos úteis:

```bash
# Suspende EmployerActor
python manage.py shell -c "
from recruitment.models import EmployerActor
EmployerActor.objects.filter(user__email='X').update(active=False)
"

# Revoga EntryPoint suspeito
python manage.py shell -c "
from recruitment.models import EntryPoint
EntryPoint.objects.filter(id='...').update(state='revoked')
"
```

## 3. Avaliação (T+2h a T+24h)

Registrar no `RightsCase` interno:
- Categoria de dados afetados (identificação, contato, geografia, ledger).
- Volume estimado de titulares.
- Duração da exposição.
- Provedor terceiro envolvido (se houver).
- Risco material ao titular (Sim/Não + justificativa).

## 4. Comunicação (T+24h a T+48h)

**Se risco relevante:**
1. Comunicar ANPD via canal oficial (comunicado.dpo.gov.br).
2. Comunicar titulares afetados via e-mail cadastrado.
3. Publicar aviso público em `/privacidade/` se escala exigir.

Modelo de mensagem ao titular:

> Prezado(a) [nome], em [data] identificamos um incidente que pode ter
> afetado seus dados na plataforma MatchCo. [descrição]. Tomamos as
> seguintes ações: [lista]. Você pode exercer seus direitos escrevendo
> para {rights_email}. — DPO {dpo_name}.

## 5. Erradicação (T+48h a T+7d)

- Fix técnico do vetor.
- Adicionar teste de regressão que reproduz o cenário.
- Atualizar `pig_check` se necessário.

## 6. Pós-morte (T+7d a T+14d)

Documento em `docs/development/recruitment/postmortems/YYYY-MM-DD-slug.md`:
- Timeline.
- Causa raiz.
- Ações preventivas.
- Referências no Ledger (event_id).

Nunca reescrever o passado. O Ledger é fonte da verdade.
