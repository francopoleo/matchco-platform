"""Métricas do funil MatchCo — derivadas do Relation + Ledger.

Nenhum agregado persistido. Tudo calculado em query. Se o volume crescer,
promover para materialized view / tabela agregada por dia.

Ver ROADMAP_CONFORMIDADE §Métricas.
"""
from datetime import timedelta

from django.db.models import Avg, Count, ExpressionWrapper, F, fields
from django.utils import timezone

from .models import Ledger, Relation, RightsCase


def _window(days=30, now=None):
    now = now or timezone.now()
    return now - timedelta(days=days), now


def funnel_counts(*, organization=None, business_unit=None, days=30):
    """Contagem de Relations por estado no período."""
    since, now = _window(days)
    qs = Relation.objects.filter(created_at__gte=since)
    if organization is not None:
        qs = qs.filter(opportunity__organization=organization)
    if business_unit is not None:
        qs = qs.filter(opportunity__business_unit=business_unit)
    counts = dict(qs.values_list('state').annotate(n=Count('id')))
    # Ordena canônico para exibição.
    order = [
        Relation.STATE_NOTICE_DELIVERED,
        Relation.STATE_PERSON_INTERESTED,
        Relation.STATE_EMPLOYER_INTEREST_VIEW,
        Relation.STATE_EMPLOYER_INTERESTED,
        Relation.STATE_MATCHED,
        Relation.STATE_CONTACT_ENABLED,
        Relation.STATE_RESPONSE_CREATED,
        Relation.STATE_CLOSED,
        Relation.STATE_DECLINED,
        Relation.STATE_NO_EMPLOYER_INTEREST,
    ]
    return [{'state': s, 'count': counts.get(s, 0)} for s in order]


def _avg_seconds(qs, start_field, end_field):
    duration = ExpressionWrapper(
        F(end_field) - F(start_field),
        output_field=fields.DurationField(),
    )
    result = qs.exclude(**{f'{end_field}__isnull': True}).exclude(
        **{f'{start_field}__isnull': True}
    ).aggregate(avg=Avg(duration))
    avg = result['avg']
    return avg.total_seconds() if avg else None


def avg_time_person_to_match(*, organization=None, business_unit=None, days=30):
    since, _ = _window(days)
    qs = Relation.objects.filter(matched_at__gte=since)
    if organization is not None:
        qs = qs.filter(opportunity__organization=organization)
    if business_unit is not None:
        qs = qs.filter(opportunity__business_unit=business_unit)
    return _avg_seconds(qs, 'person_interested_at', 'matched_at')


def avg_time_match_to_response(*, organization=None, business_unit=None, days=30):
    since, _ = _window(days)
    qs = Relation.objects.filter(response_created_at__gte=since)
    if organization is not None:
        qs = qs.filter(opportunity__organization=organization)
    if business_unit is not None:
        qs = qs.filter(opportunity__business_unit=business_unit)
    return _avg_seconds(qs, 'matched_at', 'response_created_at')


def _fmt_duration(seconds):
    if seconds is None:
        return None
    hours = seconds / 3600
    if hours < 24:
        return f'{hours:.1f}h'
    return f'{hours / 24:.1f}d'


def rights_case_summary(*, days=30):
    since, _ = _window(days)
    qs = RightsCase.objects.filter(received_at__gte=since)
    return {
        'total': qs.count(),
        'by_type': dict(qs.values_list('request_type').annotate(n=Count('id'))),
        'open': qs.filter(action_state=RightsCase.ACTION_OPEN).count(),
    }


def ledger_alerts(*, days=7):
    """Contadores de eventos que exigem atenção."""
    since, _ = _window(days)
    qs = Ledger.objects.filter(occurred_at__gte=since)
    return {
        'authority_violations': qs.filter(event_type='AUTHORITY_VIOLATION').count(),
        'point_compromised': qs.filter(event_type='POINT_COMPROMISED').count(),
        'rights_requests': qs.filter(event_type='RIGHTS_REQUEST').count(),
    }


def dashboard(*, organization=None, business_unit=None, days=30):
    return {
        'days': days,
        'funnel': funnel_counts(organization=organization, business_unit=business_unit, days=days),
        'avg_person_to_match_seconds':
            avg_time_person_to_match(organization=organization, business_unit=business_unit, days=days),
        'avg_person_to_match_human':
            _fmt_duration(avg_time_person_to_match(organization=organization, business_unit=business_unit, days=days)),
        'avg_match_to_response_seconds':
            avg_time_match_to_response(organization=organization, business_unit=business_unit, days=days),
        'avg_match_to_response_human':
            _fmt_duration(avg_time_match_to_response(organization=organization, days=days)),
        'rights_cases': rights_case_summary(days=days),
        'ledger_alerts': ledger_alerts(days=7),
    }
