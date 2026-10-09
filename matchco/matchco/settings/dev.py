from .base import *

try:
    from .base import *
except ImportError:
    pass

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameBackend',
]

# Disable rate limiting in development
RATELIMIT_ENABLE = False
