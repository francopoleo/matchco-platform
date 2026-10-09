"""Deterministic matching compatibility services.

The active MatchCo distribution flow is relation-based: an opportunity is
delivered to eligible people and the person's interest is the gate for the
employer view.  It must never sort or expose people by a quality score.
"""

from django.db import transaction

from .models import CandidatePosition


@transaction.atomic
def calculate_match(*, candidate, position):
    match, _ = CandidatePosition.objects.get_or_create(candidate=candidate, position=position)
    match.calculate_match()
    return match


def rank_candidates(*, position, organization, limit=50):
    """Fail loudly if legacy comparative ranking is invoked.

    Kept as a compatibility shim so an old worker or integration cannot
    silently reintroduce ranking into Match.  ``CandidatePosition`` and its
    score remain historical data until their retention policy is decided.
    """
    raise RankingRemovedError(
        'O ranking comparativo foi removido do fluxo Match; use a distribuição '
        'por elegibilidade e interesse da pessoa.'
    )


class RankingRemovedError(RuntimeError):
    """Raised when legacy candidate ranking is requested."""
