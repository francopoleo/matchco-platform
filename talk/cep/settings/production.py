from .base import *

DEBUG = False

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameBackend',
]

try:
    from .production import *
except ImportError:
    pass
