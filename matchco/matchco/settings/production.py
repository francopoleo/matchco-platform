from .base import *

DEBUG = False

# O proxy termina TLS, mas o Django também deve exigir que a sessão e o
# CSRF só trafeguem por HTTPS. HSTS só é ativado neste módulo de produção,
# depois de confirmar que todos os subdomínios estão servidos por TLS.
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameBackend',
]

try:
    from .production import *
except ImportError:
    pass
