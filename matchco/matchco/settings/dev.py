from .base import *

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameBackend',
]

# Disable rate limiting in development
RATELIMIT_ENABLE = False
