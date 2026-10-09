from django.conf import settings
from django.db import models


class TalkInteraction(models.Model):
    """Minimal audit event for Talk; message content is never persisted here."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    platform_organization_id = models.PositiveIntegerField(db_index=True)
    room_key = models.CharField(max_length=160)
    topic_key = models.CharField(max_length=160, default='talk')
    message_length = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['platform_organization_id', 'created_at']),
        ]

# Create your models here.
