from django.utils.translation import gettext_lazy as gettext_lazy
from django.apps import AppConfig


class ConsoleConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'console'
    verbose_name = gettext_lazy('Management Console')
