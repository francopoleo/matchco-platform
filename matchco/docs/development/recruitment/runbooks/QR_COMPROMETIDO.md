# Runbook — QR / EntryPoint comprometido

## 1. Sinais de compromisso

- Reporte de titular: "escaneei e caiu em outra página".
- `monitor_entry_points_task` marcou `state='compromised'`.
- Divergência entre `canonical_destination_url` e destino real observado.
- Aumento anormal em `AUTHORITY_VIOLATION` de um EntryPoint.

## 2. Contenção (T+0 a T+30min)

1. Marcar EntryPoint como `COMPROMISED` no admin ou:
   ```bash
   python manage.py shell -c "
   from recruitment.models import EntryPoint
   from recruitment.services import ledger_record
   ep = EntryPoint.objects.get(id='...')
   ep.state = 'compromised'
   ep.save()
   ledger_record('POINT_COMPROMISED', actor_type='ops',
                 entry_point=ep, metadata={'reason': 'reporte manual'})
   "
   ```
2. Confirmar: acessar `/qr/<id>/` no navegador — deve retornar HTTP 409
   com a página de aviso.
3. Notificar responsável do território (lojista/shopping).

## 3. Investigação (T+30min a T+4h)

- Comparar `tamper_evidence_hash` com foto atual do QR físico.
- Verificar Ledger: `Ledger.objects.filter(entry_point=ep)`.
- Se adulteração física: buscar câmeras, remover cartaz/adesivo.
- Se sequestro digital (DNS/proxy): investigar cadeia CDN/DNS.

## 4. Erradicação

- Reimprimir QR físico com novo `EntryPoint` (UUID diferente).
- Antigo permanece `COMPROMISED` no registro (não deletar — Ledger).
- Novo entra em `DRAFT` → `TESTED` → `ACTIVE` normalmente.

## 5. Comunicação

- Titulares que escanearam nas últimas 48h recebem aviso.
- Se dados foram capturados por terceiro → seguir runbook `INCIDENTE_ANPD.md`.

## 6. Prevenção

- Rever política de acesso físico ao ponto (quem pode substituir?).
- Aumentar frequência do `monitor_entry_points_task` para 15 min naquele shopping.
- Considerar QR com holograma anti-adulteração.
