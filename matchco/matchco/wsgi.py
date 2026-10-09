"""
WSGI config for MatchCo.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Servidores WSGI devem iniciar com as configurações endurecidas de produção.
# O desenvolvimento local continua usando matchco.settings.dev via manage.py.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "matchco.settings.production")

application = get_wsgi_application()
