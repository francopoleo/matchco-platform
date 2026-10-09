from django.utils.translation import gettext_lazy as gettext_lazy
from django.apps import AppConfig


class AudienceConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'audience'
    verbose_name = gettext_lazy('Audience')
