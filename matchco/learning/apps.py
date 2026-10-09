from django.utils.translation import gettext_lazy as gettext_lazy
from django.apps import AppConfig


class LearningConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'learning'
    verbose_name = gettext_lazy('Learning')
