from django.utils.translation import gettext_lazy as gettext_lazy
from django.apps import AppConfig


class RecruitmentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recruitment'
    verbose_name = gettext_lazy('Recruitment')

    def ready(self):
        """Register signals when app is ready."""
        import recruitment.signals  # noqa
