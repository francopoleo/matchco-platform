from django.utils import timezone

from .models import ContentItemProgress


def get_item_progress(user, item):
    return ContentItemProgress.objects.filter(user=user, item=item).first()


def mark_item_completed(user, item):
    progress, _ = ContentItemProgress.objects.get_or_create(user=user, item=item)
    progress.completed = True
    progress.completed_at = progress.completed_at or timezone.now()
    progress.save(update_fields=['completed', 'completed_at'])
    return progress
