# Providers MatchCo — configuração por env var

Todos opcionais. Sem env vars, sistema usa **fallback de e-mail via Django**
(SMTP configurado no projeto) e o `dev_capture` da sessão em modo dev.

---

## E-mail (obrigatório em prod, já funciona no projeto)

O projeto já usa Django SMTP configurado em `matchco/settings/base.py`. OTP e
todas as notificações caem nesse canal quando o SMS não está ativo.

Variáveis (já existem no projeto):
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.seuprovedor.com
EMAIL_HOST_USER=user
EMAIL_HOST_PASSWORD=senha
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=MatchCo <noreply@matchco.br>
```

Em dev: `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`
imprime o e-mail no terminal.

---

## SMS — escolha um provider

Ative um dos três:

### Opção A — Twilio SMS

```
MATCHCO_SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+5511987654321
```

Instalação: `pip install twilio`

Signup: https://www.twilio.com/try-twilio

### Opção B — AWS SNS

```
MATCHCO_SMS_PROVIDER=awssns
AWS_SNS_REGION_NAME=sa-east-1
AWS_ACCESS_KEY_ID=AKIAxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxx
AWS_SNS_SENDER_ID=MatchCo
```

Instalação: `pip install boto3`

Nota: SMS transacional no Brasil via SNS exige registro prévio de sender ID
com a operadora (Pré-registro na ANATEL / carrier). Custa mais caro que
Twilio para volumes baixos.

### Opção C — WhatsApp Business (Meta)

```
MATCHCO_SMS_PROVIDER=whatsapp
WA_PHONE_NUMBER_ID=1234567890
WA_ACCESS_TOKEN=EAAxxxxxxxxxxxx
WA_TEMPLATE_OTP=matchco_otp
WA_TEMPLATE_LANG=pt_BR
```

Sem lib adicional (usa urllib).

Pré-requisitos:
1. Conta Meta Business Manager.
2. Número WhatsApp Business verificado.
3. Template aprovado pela Meta com uma variável `{{1}}` para o código:

```
Seu código MatchCo é {{1}}. Válido por 10 minutos.
```

Docs: https://developers.facebook.com/docs/whatsapp/cloud-api

---

## DPO / LGPD

```
MATCHCO_CONTROLLER_NAME=Nome legal do controlador
MATCHCO_CONTROLLER_CNPJ=00.000.000/0000-00
MATCHCO_DPO_NAME=Nome do DPO
MATCHCO_DPO_EMAIL=dpo@matchco.br
MATCHCO_RIGHTS_EMAIL=direitos@matchco.br
MATCHCO_INCIDENT_EMAIL=incidentes@matchco.br
```

---

## Parâmetros de negócio

```
MATCHCO_RESPONSE_SLA_DAYS=14
MATCHCO_DEFAULT_RADIUS_KM=5
MATCHCO_RETENTION_RT02_DAYS=365
MATCHCO_RETENTION_RT03_DAYS=1825
MATCHCO_RETENTION_RT05_DAYS=180
```

---

## Verificar configuração

```
python manage.py pig_check
```

Retorna PASS quando todos os itens legais estão preenchidos e providers
prontos. `--strict` faz exit 1 em CI.
