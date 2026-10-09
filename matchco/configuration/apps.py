from django.utils.translation import gettext_lazy as gettext_lazy
from django.apps import AppConfig


class ConfigurationConfig(AppConfig):
    name = 'configuration'
    verbose_name = gettext_lazy('Configuration')

    def ready(self):
        """Registra signals quando app está pronto"""
        import configuration.signals  # noqa
