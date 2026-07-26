from django import template

register = template.Library()


@register.filter
def format_seconds(seconds):
    """
    Converte segundos em um formato legível.
    Exemplos: 3661 → "1h 1m", 86400 → "1 dia", 667233 → "7 dias 17h"
    """
    if not seconds:
        return "—"

    seconds = int(seconds)

    # Constantes
    DAY = 86400
    HOUR = 3600
    MINUTE = 60

    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // MINUTE
        secs = seconds % MINUTE
        if secs == 0:
            return f"{minutes}m"
        return f"{minutes}m {secs}s"
    elif seconds < 86400:
        hours = seconds // HOUR
        remaining = seconds % HOUR
        minutes = remaining // MINUTE
        if minutes == 0:
            return f"{hours}h"
        return f"{hours}h {minutes}m"
    else:
        days = seconds // DAY
        remaining = seconds % DAY
        hours = remaining // HOUR
        if hours == 0:
            return f"{days} dia" if days == 1 else f"{days} dias"
        return f"{days} dias {hours}h"
