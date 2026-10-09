from .services import eligibility


def eligible_items(items, user, recruitment_context=None):
    """Return only items visible to ``user`` according to their policy.

    ``recruitment_context`` is optional so existing course/document callers
    keep their behavior. Approved recruitment journeys can pass the projection
    from ``resolve_platform_context`` and receive the same Audience decision.
    """
    if recruitment_context:
        return [
            item for item in items
            if eligibility.can_view_with_recruitment_context(
                user, item, recruitment_context,
            ).allowed
        ]
    return [item for item in items if eligibility.can_view(user, item).allowed]
