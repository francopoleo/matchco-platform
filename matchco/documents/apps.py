from django.utils.translation import gettext_lazy as gettext_lazy
from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'documents'
    verbose_name = gettext_lazy('Documentos')
