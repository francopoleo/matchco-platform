# Runbook — Atendimento de RightsCase (LGPD)

Canal oficial: `MATCHCO_RIGHTS_EMAIL`. Prazo legal: **15 dias úteis** a
partir da verificação de identidade.

## Tipos de pedido

- `access` — acesso aos dados.
- `correction` — correção.
- `deletion` — exclusão (anonimização no ativo + Ledger mínimo retido).
- `blocking` — bloqueio (pausa circulação).
- `objection` — oposição a legítimo interesse.
- `portability` — portabilidade.

## Fluxo

### 1. Ingresso (T+0)

Titular escreve para `MATCHCO_RIGHTS_EMAIL`. Operador cria caso:

```bash
python manage.py shell -c "
from recruitment.services import open_rights_case
from recruitment.models import RightsCase
c = open_rights_case(
    requester_email='titular@x.com',
    request_type=RightsCase.TYPE_ACCESS,
    notes='pedido via e-mail YYYY-MM-DD',
)
print(c.case_ref)
"
```

Responder ao titular com o `case_ref` em até 48h.

### 2. Verificação de identidade (T+0 a T+3d)

Comprovação por:
- E-mail cadastrado + código OTP no mobile cadastrado.
- Documento oficial (aceito apenas quando outros meios falham; descartar
  cópia após verificação — RT-06).

Atualiza `verification_state='verified'` no admin.

### 3. Execução (T+3d a T+15d)

**Access:** exportar JSON completo dos dados do titular (Perfil,
consents, Relations, ProfileSignals, Ledger scoped). Anexar ao caso.

**Correction:** aplicar mudança no Perfil; grava `CORRECTION` no Ledger.

**Deletion:** rodar `anonymize_identity`:
```bash
python manage.py shell -c "
from recruitment.models import CandidateIdentity
from recruitment.services import anonymize_identity
identity = CandidateIdentity.objects.get(email_normalized='...')
anonymize_identity(identity=identity, reason='LGPD deletion request')
"
```
Preserva Ledger mínimo (RT-03 = 5 anos) — obrigação legal.

**Blocking:** setar `CandidateProfile.circulation_state='paused'` +
revogar consents.

**Objection:** revogar consent do purpose específico.

**Portability:** mesmo export do `access` em formato interoperável.

### 4. Fechamento

Atualizar `action_state='done'` + `closed_at`. Comunicar titular por
e-mail com resumo do executado.

## Prorrogação

Se caso complexo excede 15 dias úteis: aviso ao titular com nova ETA e
justificativa, antes do vencimento original. Máximo mais 15 dias.

## Rejeição

Se pedido não puder ser atendido (ex.: obrigação legal impede exclusão
total), responder ao titular com motivo específico + referência legal.
Atualizar `verification_state='rejected'` se falha na verificação.
