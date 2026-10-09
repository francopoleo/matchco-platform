from django.utils.translation import gettext_lazy as gettext_lazy
from django.apps import AppConfig


class UserManagementConfig(AppConfig):
    name = 'user_management'
    verbose_name = gettext_lazy("User Management")

    def ready(self):
        import user_management.signals

