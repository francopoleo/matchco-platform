"""Adapter Twilio SMS. Opcional; ativa só se TWILIO_ACCOUNT_SID estiver definido.

Env vars:
    TWILIO_ACCOUNT_SID    — obrigatório
    TWILIO_AUTH_TOKEN     — obrigatório
    TWILIO_FROM_NUMBER    — obrigatório, formato E.164 (ex: +5511987654321)

Instalação:
    pip install twilio

Docs: https://www.twilio.com/docs/sms/quickstart/python
"""
import logging
import os

logger = logging.getLogger(__name__)


class TwilioSmsAdapter:
    def __init__(self):
        self.sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_FROM_NUMBER')
        self._client = None

    def is_configured(self):
        return all([self.sid, self.token, self.from_number])

    def _client_lazy(self):
        if self._client is None:
            from twilio.rest import Client  # requires: pip install twilio
            self._client = Client(self.sid, self.token)
        return self._client

    def send_sms(self, *, recipient, body):
        """recipient em formato E.164 ou local BR (11987654321)."""
        if not self.is_configured():
            return False
        if not recipient.startswith('+'):
            digits = ''.join(c for c in recipient if c.isdigit())
            recipient = f'+55{digits}' if not digits.startswith('55') else f'+{digits}'
        try:
            msg = self._client_lazy().messages.create(
                body=body, from_=self.from_number, to=recipient,
            )
            logger.info('Twilio SMS sent sid=%s to=***%s', msg.sid, recipient[-4:])
            return True
        except Exception:
            logger.exception('Twilio SMS failed')
            return False
