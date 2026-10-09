"""Territorial consent checks shared by opportunity delivery and candidate feed.

An entry point records the origin; it does not own the candidate. A consent is
usable only with a recorded context entry and only when the destination matches
the scope explicitly selected at that entry.
"""

from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone

from .models import CandidateConsent, CandidateContextEntry


_PURPOSE_TO_SCOPE = {
    CandidateConsent.PURPOSE_CIRCULATION_STORE: 'same_store',
    CandidateConsent.PURPOSE_CIRCULATION_SHOPPING: 'same_shopping',
    CandidateConsent.PURPOSE_CIRCULATION_NETWORK: 'same_network',
    CandidateConsent.PURPOSE_CIRCULATION_RADIUS: 'radius',
}


def _normalized(value):
    return slugify(str(value or '').strip())


def _target_shopping_keys(position):
    store = position.business_unit
    if not store:
        return set()
    keys = set()
    from configuration.models import BusinessUnit as ConfigBusinessUnit
    canonical = ConfigBusinessUnit.objects.filter(pk=store.legacy_id).first() if store.legacy_id else None
    if canonical and canonical.shopping_name:
        keys.add(_normalized(canonical.shopping_name))
    return keys


def _organization_keys(organization):
    return {
        _normalized(getattr(organization, 'slug', '')),
        _normalized(getattr(organization, 'external_id', '')),
        _normalized(getattr(organization, 'pk', '')),
    } - {''}


def _matches_shopping(position, entry_point):
    scope = _normalized(entry_point.scope_shopping_id)
    if not scope:
        return False
    # Shopping circulation must be grounded in the destination unit's
    # canonical location, never in a self-declared tenant slug.
    return scope in _target_shopping_keys(position)


def _matches_network(position, entry_point):
    scope = _normalized(entry_point.scope_network_id)
    if not scope:
        return False
    target_org = position.organization
    if scope in _organization_keys(target_org):
        return True

    # A network can explicitly span organizations. The anchor is the
    # organization identified by the QR's network key; only active, declared
    # network relationships may extend that key to another tenant.
    from .domain_models import RecruitmentOrganization, RecruitmentOrganizationRelation
    anchor = RecruitmentOrganization.objects.filter(slug__iexact=scope).first()
    if anchor is None:
        anchor = RecruitmentOrganization.objects.filter(external_id__iexact=scope).first()
    if anchor is None:
        return False
    return RecruitmentOrganizationRelation.objects.filter(
        active=True,
        relation_type=RecruitmentOrganizationRelation.RELATION_NETWORK,
    ).filter(
        models_q(anchor, target_org),
    ).exists()


def models_q(anchor, target):
    """Build the two legal directions for a declared organization network."""
    from django.db.models import Q
    return (
        Q(organization=anchor, related_organization=target)
        | Q(organization=target, related_organization=anchor)
    )


def _matches_store(position, entry_point, context):
    target = position.business_unit
    source = context.business_unit or entry_point.scope_store
    if not target or not source:
        return False
    if target.pk == source.pk:
        return True
    return bool(
        target.physical_unit_id
        and source.physical_unit_id
        and target.physical_unit_id == source.physical_unit_id
    )


def _within_radius(candidate, position, entry_point):
    if not position.business_unit:
        return False
    from .geo import distance_candidate_to_store
    distance = distance_candidate_to_store(candidate, position.business_unit)
    if distance is None:
        return False
    radius_m = getattr(entry_point, 'geo_radius_m', None)
    radius_km = (float(radius_m) / 1000) if radius_m else float(
        getattr(settings, 'MATCHCO_DEFAULT_RADIUS_KM', 5.0)
    )
    return distance <= radius_km


def _scope_matches(scope, candidate, position, entry_point, context):
    if scope == 'same_store':
        return _matches_store(position, entry_point, context)
    if scope == 'same_shopping':
        return _matches_shopping(position, entry_point)
    if scope == 'same_network':
        return _matches_network(position, entry_point)
    if scope == 'radius':
        return _within_radius(candidate, position, entry_point)
    return False


def has_territorial_consent(*, candidate, position, entry_point=None, at=None):
    """Return whether a current, contextual consent covers this destination.

    Invitations use any historical QR context with a still-active consent.
    A candidate feed may pass its active QR to restrict results to that
    experience. A QR never grants consent by itself.
    """
    if not candidate.identity_id or not candidate.visibility_match:
        return False
    if candidate.circulation_state != candidate.CIRCULATION_ALLOWED:
        return False

    consents = CandidateConsent.objects.filter(
        identity_id=candidate.identity_id,
        purpose__in=_PURPOSE_TO_SCOPE,
        granted=True,
        revoked_at__isnull=True,
    )
    if at is not None:
        consents = consents.filter(granted_at__lte=at)

    for consent in consents.iterator():
        if not consent.organization_id:
            continue
        contexts = CandidateContextEntry.objects.filter(
            candidate=candidate,
            identity_id=candidate.identity_id,
            organization_id=consent.organization_id,
            entry_point__isnull=False,
            entry_point__organization_id=consent.organization_id,
        ).select_related('entry_point', 'business_unit')

        source = consent.source or ''
        if source.startswith('entry_point:'):
            source_id = source.partition(':')[2]
            contexts = contexts.filter(entry_point_id=source_id)
        elif source == 'candidato_perfil':
            # A person may adjust an existing consent in their profile; retain
            # the same territory boundary by checking only contexts presented
            # by that organization.
            pass
        else:
            # Unbound historical consents cannot authorize new delivery.
            continue

        for context in contexts.iterator():
            entry = context.entry_point
            if entry_point is not None and entry.pk != entry_point.pk:
                continue
            scope = _PURPOSE_TO_SCOPE[consent.purpose]
            if _scope_matches(scope, candidate, position, entry, context):
                return True
    return False


def has_network_consent_for_organization(*, candidate, viewer_organization, at=None):
    """Check a QR-bound network authorization before cross-tenant projection."""
    from types import SimpleNamespace

    at = at or timezone.now()
    consents = CandidateConsent.objects.filter(
        identity_id=candidate.identity_id,
        purpose=CandidateConsent.PURPOSE_CIRCULATION_NETWORK,
        granted=True, revoked_at__isnull=True,
        granted_at__lte=at,
    ).exclude(organization__isnull=True)
    target = SimpleNamespace(organization=viewer_organization, business_unit=None)
    for consent in consents.iterator():
        source = consent.source or ''
        if not source.startswith('entry_point:'):
            continue
        contexts = CandidateContextEntry.objects.filter(
            candidate=candidate, identity_id=candidate.identity_id,
            organization_id=consent.organization_id,
            entry_point_id=source.partition(':')[2],
            entry_point__organization_id=consent.organization_id,
        ).select_related('entry_point')
        if any(_matches_network(target, context.entry_point) for context in contexts.iterator()):
            return True
    return False


def classify_territory(position, entry_point):
    """Describe a destination relative to a known QR origin, without scoring."""
    if entry_point is None:
        return 'other'
    target = position.business_unit
    origin = entry_point.scope_store
    if target and origin and (
        target.pk == origin.pk
        or (target.physical_unit_id and target.physical_unit_id == origin.physical_unit_id)
    ):
        return 'same_store'
    if _matches_shopping(position, entry_point):
        return 'same_shopping'
    if _matches_network(position, entry_point):
        return 'same_network'
    return 'other'
