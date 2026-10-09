"""Adapter AWS SNS SMS. Alternativa ao Twilio.

Env vars:
    AWS_SNS_REGION_NAME   — obrigatório (ex: us-east-1, sa-east-1)
    AWS_ACCESS_KEY_ID     — obrigatório (ou usa perfil IAM)
    AWS_SECRET_ACCESS_KEY — obrigatório
    AWS_SNS_SENDER_ID     — opcional (BR requer registro prévio)

Instalação:
    pip install boto3

Docs: https://docs.aws.amazon.com/sns/latest/dg/sms_publish-to-phone.html
"""
import logging
import os

logger = logging.getLogger(__name__)


class AwsSnsSmsAdapter:
    def __init__(self):
        self.region = os.getenv('AWS_SNS_REGION_NAME')
        self.access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.sender_id = os.getenv('AWS_SNS_SENDER_ID', 'MatchCo')
        self._client = None

    def is_configured(self):
        return bool(self.region)

    def _client_lazy(self):
        if self._client is None:
            import boto3
            self._client = boto3.client(
                'sns', region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            )
        return self._client

    def send_sms(self, *, recipient, body):
        if not self.is_configured():
            return False
        if not recipient.startswith('+'):
            digits = ''.join(c for c in recipient if c.isdigit())
            recipient = f'+55{digits}' if not digits.startswith('55') else f'+{digits}'
        try:
            resp = self._client_lazy().publish(
                PhoneNumber=recipient,
                Message=body,
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String', 'StringValue': self.sender_id,
                    },
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String', 'StringValue': 'Transactional',
                    },
                },
            )
            logger.info('SNS SMS sent msg=%s to=***%s',
                        resp.get('MessageId', '?'), recipient[-4:])
            return True
        except Exception:
            logger.exception('SNS SMS failed')
            return False
