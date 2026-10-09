from django import template

from ..models import ContentItemProgress

register = template.Library()


@register.simple_tag
def get_library_items(module):
    return module.library_items.filter(published=True)


@register.simple_tag
def library_item_is_done(item, user):
    return ContentItemProgress.objects.filter(item=item, user=user, completed=True).exists()


@register.filter
def format_seconds(seconds):
    """Converte segundos em formato legível: 667233 → "7 dias 17h", 3661 → "1h 1m"."""
    if not seconds:
        return "—"

    seconds = int(seconds)
    DAY, HOUR, MINUTE = 86400, 3600, 60

    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes, secs = seconds // MINUTE, seconds % MINUTE
        return f"{minutes}m" if secs == 0 else f"{minutes}m {secs}s"
    elif seconds < 86400:
        hours = seconds // HOUR
        minutes = (seconds % HOUR) // MINUTE
        return f"{hours}h" if minutes == 0 else f"{hours}h {minutes}m"
    else:
        days = seconds // DAY
        hours = (seconds % DAY) // HOUR
        return f"{days} dia" if (days == 1 and hours == 0) else f"{days} dias" if hours == 0 else f"{days} dias {hours}h"
