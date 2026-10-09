"""Feed territorial da Porta Match (SISTEMA_MATCHCO_CANONICO §8).

Ordenação efêmera: proximidade + recência + tag. **Nenhum score persistido**
no candidato. Nada é ranqueado. Só listagem contextual.
"""
from django.utils import timezone

from .models import (
    CandidateConsent, EntryPoint, Position as Opportunity, Relation,
)


# Peso de ordenação por origem territorial.
_TERRITORY_WEIGHT = {
    'same_store': 100,
    'same_shopping': 50,
    'same_network': 40,
    'same_city': 10,
    'other': 1,
}

# Peso por tag da necessidade.
_TAG_WEIGHT = {
    Opportunity.TAG_PRECISA: 30,
    Opportunity.TAG_SERIA_BOM: 20,
    Opportunity.TAG_PODE_APRENDER: 15,
}


def _territory_class(opp, entry_point):
    """Classifica territorialidade da opp vs. ponto de entrada."""
    if entry_point is None:
        return 'other'
    if entry_point.scope_store_id and opp.business_unit_id == entry_point.scope_store_id:
        return 'same_store'
    if entry_point.scope_shopping_id and opp.business_unit and getattr(
        opp.business_unit, 'shopping_id', None,
    ) == entry_point.scope_shopping_id:
        return 'same_shopping'
    if entry_point.scope_network_id and opp.business_unit and getattr(
        opp.business_unit.company, 'network_id', None,
    ) == entry_point.scope_network_id:
        return 'same_network'
    return 'other'


def _has_scope_consent(candidate, territory_class):
    """Só circula se o candidato consentiu com o escopo territorial."""
    purpose_map = {
        'same_store': CandidateConsent.PURPOSE_CIRCULATION_STORE,
        'same_shopping': CandidateConsent.PURPOSE_CIRCULATION_SHOPPING,
        'same_network': CandidateConsent.PURPOSE_CIRCULATION_NETWORK,
        'other': CandidateConsent.PURPOSE_CIRCULATION_RADIUS,
        'same_city': CandidateConsent.PURPOSE_CIRCULATION_RADIUS,
    }
    purpose = purpose_map.get(territory_class)
    if purpose is None:
        return False
    if candidate.identity_id is None:
        return True  # sem Identity ainda; consentimento gerenciado no signup
    return candidate.identity.consents.filter(
        purpose=purpose, granted=True, revoked_at__isnull=True,
    ).exists()


def build_feed(candidate, *, entry_point=None, limit=20, now=None):
    """Constrói feed ordenado (efêmero) para o candidato.

    Nunca persiste ordenação. Nunca calcula score guardado. Se candidato está
    PAUSED, retorna vazio.
    """
    from .models import CandidateProfile

    if candidate.circulation_state == CandidateProfile.CIRCULATION_PAUSED:
        return []
    # Segregação de portas (Fase 9): feed Match só para candidatos opt-in.
    if not candidate.visibility_match:
        return []

    now = now or timezone.now()

    active_relations = Relation.objects.filter(candidate=candidate).exclude(
        state__in=list(Relation.TERMINAL_STATES) + [Relation.STATE_NOTICE_DELIVERED]
    )
    qs = Opportunity.objects.filter(
        state__in=[Opportunity.STATE_ACTIVATED, Opportunity.STATE_CIRCULATED],
        pre_interest_set_complete=True,
        mode=Opportunity.MODE_MATCH,
    ).exclude(
        # Não mostra Opportunity para a qual já existe Relation não-terminal.
        pk__in=active_relations.values('opportunity_id'),
    ).select_related('business_unit', 'business_unit__company', 'organization')

    from .geo import distance_candidate_to_store

    items = []
    from .services import candidate_is_eligible_for_position
    for opp in qs:
        current_relation = Relation.objects.filter(
            candidate=candidate, opportunity=opp, opportunity_version=opp.version,
        ).first()
        invitation_round_exists = Relation.objects.filter(
            opportunity=opp, opportunity_version=opp.version,
        ).exists()
        # Rodadas abertas são privadas: só aparece quem recebeu o convite.
        if (invitation_round_exists or opp.state == Opportunity.STATE_CIRCULATED) and current_relation is None:
            continue
        if current_relation and current_relation.state != Relation.STATE_NOTICE_DELIVERED:
            continue
        if not candidate_is_eligible_for_position(candidate=candidate, position=opp, at=now):
            continue
        territory = _territory_class(opp, entry_point)
        if not _has_scope_consent(candidate, territory):
            continue

        distance_km = None
        if opp.business_unit:
            distance_km = distance_candidate_to_store(candidate, opp.business_unit)

        # Filtro de raio consentido — se candidato só tem RADIUS e distância > raio, exclui.
        max_radius_km = _max_consented_radius_km(candidate)
        if max_radius_km is not None and distance_km is not None and distance_km > max_radius_km:
            # Aceita mesmo assim se territorialidade explícita (loja/shopping/rede) valeu.
            if territory == 'other':
                continue

        recency_hours = max(1, (now - opp.updated_at).total_seconds() / 3600.0)
        distance_score = 0
        if distance_km is not None:
            # Perto = mais peso; 0km ≈ 30 pontos, 10km ≈ 0.
            distance_score = max(0, 30 - distance_km * 3)

        weight = (
            _TERRITORY_WEIGHT.get(territory, 1)
            + _TAG_WEIGHT.get(opp.tag, 0)
            + distance_score
            - min(50, recency_hours / 24.0)
        )
        items.append({
            'opportunity_id': opp.pk,
            'title': opp.title,
            'workplace': opp.workplace,
            'tag': opp.tag,
            'schedule': opp.schedule,
            'work_format': opp.work_format,
            'starts_at': opp.starts_at,
            'territory': territory,
            'distance_km': round(distance_km, 1) if distance_km is not None else None,
            '_weight': weight,
        })

    items.sort(key=lambda it: it['_weight'], reverse=True)
    for it in items:
        it.pop('_weight', None)
    return items[:limit]


# Raio configurável no futuro; hoje padrão de 5km para CIRCULATION_RADIUS.
_DEFAULT_RADIUS_KM = 5.0


def _max_consented_radius_km(candidate):
    """Retorna raio máximo se candidato tem só consent RADIUS (sem STORE/SHOPPING/NETWORK)."""
    from django.conf import settings as _s
    if candidate.identity_id is None:
        return None
    consents = candidate.identity.consents.filter(
        granted=True, revoked_at__isnull=True,
    ).values_list('purpose', flat=True)
    if any(p in consents for p in (
        CandidateConsent.PURPOSE_CIRCULATION_STORE,
        CandidateConsent.PURPOSE_CIRCULATION_SHOPPING,
        CandidateConsent.PURPOSE_CIRCULATION_NETWORK,
    )):
        return None  # sem limite de raio; outros escopos concedidos
    if CandidateConsent.PURPOSE_CIRCULATION_RADIUS in consents:
        return getattr(_s, 'MATCHCO_DEFAULT_RADIUS_KM', _DEFAULT_RADIUS_KM)
    return None
