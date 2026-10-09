from audience.services import eligibility


def filter_entries(entries, user):
    """Apply the centralized enterprise audience decision to a collection."""
    return [entry for entry in entries if eligibility.can_view(user, entry).allowed]
