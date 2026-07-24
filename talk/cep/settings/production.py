from .base import *

DEBUG = False

try:
    from .production import *
except ImportError:
    pass
