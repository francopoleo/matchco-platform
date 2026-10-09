"""Adapter WhatsApp Business Cloud API (Meta).

Env vars:
    WA_PHONE_NUMBER_ID    — obrigatório (do dashboard Meta Business)
    WA_ACCESS_TOKEN       — obrigatório (token permanente do sistema)
    WA_TEMPLATE_OTP       — opcional; default 'matchco_otp' (nome do template aprovado)
    WA_TEMPLATE_LANG      — opcional; default 'pt_BR'

Notas:
- WhatsApp Business exige templates aprovados pela Meta para mensagens
  transacionais fora da janela de 24h. Crie template no Meta Business Manager
  com uma variável {{1}} (código OTP).
- Sem env vars → não ativa.

Docs: https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages
"""
import json
import logging
import os

logger = logging.getLogger(__name__)


class WhatsAppMetaAdapter:
    def __init__(self):
        self.phone_id = os.getenv('WA_PHONE_NUMBER_ID')
        self.token = os.getenv('WA_ACCESS_TOKEN')
        self.template = os.getenv('WA_TEMPLATE_OTP', 'matchco_otp')
        self.lang = os.getenv('WA_TEMPLATE_LANG', 'pt_BR')

    def is_configured(self):
        return all([self.phone_id, self.token])

    def send_sms(self, *, recipient, body):
        """recipient em formato E.164 (+55...) ou local BR.
        `body` aqui é o texto pronto; para WhatsApp usamos template — extraímos
        o código de 6 dígitos como variável."""
        if not self.is_configured():
            return False

        import re
        import urllib.request

        m = re.search(r'\b(\d{6})\b', body)
        if not m:
            return False
        code = m.group(1)

        digits = ''.join(c for c in recipient if c.isdigit())
        to = digits if digits.startswith('55') else f'55{digits}'

        payload = {
            'messaging_product': 'whatsapp',
            'to': to,
            'type': 'template',
            'template': {
                'name': self.template,
                'language': {'code': self.lang},
                'components': [{
                    'type': 'body',
                    'parameters': [{'type': 'text', 'text': code}],
                }],
            },
        }
        url = f'https://graph.facebook.com/v18.0/{self.phone_id}/messages'
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if 200 <= resp.status < 300:
                    logger.info('WhatsApp sent to=***%s', to[-4:])
                    return True
                logger.error('WhatsApp status=%s body=%s', resp.status, resp.read())
        except Exception:
            logger.exception('WhatsApp send failed')
        return False
