"""Seleção dinâmica de provider MatchCo baseada em env vars."""
import os


def get_sms_provider():
    """Retorna adapter SMS ativo com base em MATCHCO_SMS_PROVIDER.

    Aceita: twilio, awssns, whatsapp. Retorna None se nenhum configurado.
    """
    choice = os.getenv('MATCHCO_SMS_PROVIDER', '').lower()

    if choice == 'twilio':
        from .sms_twilio import TwilioSmsAdapter
        adapter = TwilioSmsAdapter()
    elif choice == 'awssns':
        from .sms_awssns import AwsSnsSmsAdapter
        adapter = AwsSnsSmsAdapter()
    elif choice == 'whatsapp':
        from .whatsapp_meta import WhatsAppMetaAdapter
        adapter = WhatsAppMetaAdapter()
    else:
        return None

    return adapter if adapter.is_configured() else None
