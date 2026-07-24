from .services import eligibility


def eligible_items(items, user):
    """Return only items visible to ``user`` according to their policy."""
    return [item for item in items if eligibility.can_view(user, item).allowed]
