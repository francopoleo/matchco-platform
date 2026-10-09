"""Providers concretos MatchCo — cada arquivo é opcional e só ativa se as env vars estiverem setadas.

Registro dinâmico: settings.py lê env vars → escolhe adapter → integrations.registry
usa o adapter escolhido.

Uso:
    export MATCHCO_SMS_PROVIDER=twilio
    export TWILIO_ACCOUNT_SID=...
    export TWILIO_AUTH_TOKEN=...
    export TWILIO_FROM_NUMBER=+55...

Sem env vars → nenhum provider ativa. Sistema usa fallback de e-mail (Django) e
dev_capture para OTP.
"""
