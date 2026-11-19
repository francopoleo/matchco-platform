"""Resolution and rendering helpers for contextual candidate questionnaires.

The resolver keeps the public flow simple: a candidate sees one questionnaire,
while the organization can maintain many versions behind the same portal or QR.
"""

from .models import QuestionnaireTemplate


def _configured_market(candidate):
    """Return the market configured for the organization when available."""
    legacy_id = getattr(candidate.organization, 'legacy_id', None)
    if not legacy_id:
        return ''
    try:
        from configuration.models import Organization
        return Organization.objects.filter(pk=legacy_id).values_list('market', flat=True).first() or ''
    except Exception:
        # The recruitment app remains usable during migrations or isolated tests.
        return ''


def _entry_point_matches_org(entry_point, organization):
    if not entry_point:
        return False
    config_org_id = getattr(entry_point, 'organization_id', None)
    if config_org_id and getattr(organization, 'legacy_id', None) == config_org_id:
        return True
    # Slugs are the stable bridge for installations created after the legacy
    # migration, where RecruitmentOrganization.legacy_id can be empty.
    config_org = getattr(entry_point, 'organization', None)
    return bool(config_org and getattr(config_org, 'slug', '') == getattr(organization, 'slug', ''))


def _market_matches(template_market, configured_market):
    if not template_market:
        return True
    if template_market == configured_market:
        return True
    # Starter templates use a smaller number of operating patterns than the
    # market taxonomy: shopping follows retail operations and hospital follows
    # the same health/safety pattern as pharma.
    return {
        'retail': {'retail', 'shopping'},
        'pharma': {'pharma', 'hospital'},
    }.get(template_market, {template_market}).__contains__(configured_market)


def resolve_questionnaire(candidate, entry_point=None):
    """Pick the best published questionnaire for a candidate.

    Specificity is deterministic and documented: QR, function, unit, channel,
    audience role, market, then organization default. A newer version wins
    when two templates have the same specificity.
    """
    templates = list(
        QuestionnaireTemplate.objects.filter(
            organization=candidate.organization,
            status=QuestionnaireTemplate.STATUS_PUBLISHED,
        ).prefetch_related('questions')
    )
    if not templates:
        return None

    candidate_function_ids = set(candidate.job_functions.values_list('id', flat=True))
    store = getattr(candidate, 'preferred_store', None)
    channel_id = getattr(store, 'channel_id', None)
    audience_role = ''
    request = getattr(candidate, '_matchco_request', None)
    if request is not None:
        audience_role = request.session.get('ep_audience_role', '')
    market = _configured_market(candidate)

    ranked = []
    for template in templates:
        score = 0
        if template.entry_point_id:
            if not entry_point or template.entry_point_id != entry_point.pk:
                continue
            if not _entry_point_matches_org(entry_point, candidate.organization):
                continue
            score += 100
        elif entry_point and _entry_point_matches_org(entry_point, candidate.organization):
            # A generic template can still be selected for an organization's QR.
            score += 5

        if template.scope_job_function_id:
            if template.scope_job_function_id not in candidate_function_ids:
                continue
            score += 80
        if template.scope_store_id:
            if not store or template.scope_store_id != store.pk:
                continue
            score += 70
        if template.scope_channel_id:
            if not channel_id or template.scope_channel_id != channel_id:
                continue
            score += 60
        if template.audience_role:
            if not audience_role or template.audience_role != audience_role:
                continue
            score += 50
        if template.market:
            if not market or not _market_matches(template.market, market):
                continue
            score += 20
        if template.is_default:
            score += 10
        ranked.append((score, template.version, template.updated_at, template))

    return max(ranked, key=lambda row: (row[0], row[1], row[2]))[3] if ranked else None


def _condition_matches(condition, answers):
    if not condition:
        return True
    key = condition.get('key')
    if not key:
        return True
    value = answers.get(key)
    if 'equals' in condition:
        return value == condition['equals']
    if 'not_equals' in condition:
        return value != condition['not_equals']
    if 'contains' in condition:
        values = value if isinstance(value, list) else [value]
        return condition['contains'] in values
    return True


def questionnaire_questions(template, answers=None):
    """Return template questions in the shape expected by the public form."""
    answers = answers or {}
    if not template:
        return []
    questions = []
    for question in template.questions.filter(active=True):
        if not _condition_matches(question.conditions, answers):
            continue
        field_type = question.field_type
        # Existing template markup uses select/radio names; keep that contract.
        if field_type == 'single_choice':
            field_type = 'select'
        elif field_type == 'multiple_choice':
            field_type = 'checkbox'
        elif field_type == 'boolean':
            field_type = 'radio'
        questions.append({
            'id': question.key,
            'label': question.label,
            'help_text': question.help_text,
            'type': field_type,
            'options': question.options or [],
            'required': question.required,
        })
    return questions
