from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User


@receiver(post_save, sender=User)
def link_user_to_companyunit(sender, instance, created, **kwargs):
    # Organizational access is now created explicitly through Membership.
    # The old indication-code based implicit link is intentionally removed.
    return None
