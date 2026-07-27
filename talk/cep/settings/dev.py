from .base import *

try:
    from .base import *
except ImportError:
    pass

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameBackend',
]
