from django.apps import AppConfig


class ConfigurationConfig(AppConfig):
    name = 'configuration'
    verbose_name = 'Configuration'

    def ready(self):
        """Registra signals quando app está pronto"""
        import configuration.signals  # noqa
