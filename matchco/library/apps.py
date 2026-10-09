from django.utils.translation import gettext_lazy as gettext_lazy
from django.apps import AppConfig


class LibraryConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'library'
    verbose_name = gettext_lazy('Content library')
