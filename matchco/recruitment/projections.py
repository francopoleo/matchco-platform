"""Projeções scopeadas de dados de candidato para atores empregadores.

Ver SISTEMA_MATCHCO_CANONICO §3.5 e §4.

**Regra de ouro**: nenhuma projeção retorna telefone, e-mail, endereço, foto
ou score enquanto a Relation não estiver em CONTACT_ENABLED. Whitelist estrita.

Uso:

    from recruitment.projections import employer_interest_view

    data = employer_interest_view(relation)

Retorna um dict serializável, seguro para render em template do lado
empregador. Nunca retorne o objeto CandidateProfile diretamente para o
empregador — sempre passe por esta função.
"""
from django.db.models import Q

from .models import (
    CandidateSignupAnswer, CanonicalTerm, OpportunityCanonicalRequirement,
    Position, Relation,
)


def _match_explanation(relation):
    """Explica a elegibilidade sem score, ranking ou exposição de dados sensíveis."""
    from .geo import distance_candidate_to_store
    from .services import canonical_terms_for_candidate

    candidate = relation.candidate
    opportunity = relation.opportunity
    candidate_terms = canonical_terms_for_candidate(candidate)
    candidate_function_ids = set(
        candidate_terms.filter(term_type=CanonicalTerm.TYPE_FUNCTION).values_list('pk', flat=True)
    )
    candidate_function_labels = list(
        candidate_terms.filter(term_type=CanonicalTerm.TYPE_FUNCTION).values_list('label', flat=True)
    )
    requirements = list(OpportunityCanonicalRequirement.objects.filter(
        position=opportunity, active=True,
        requirement=OpportunityCanonicalRequirement.REQUIRED,
    ).select_related('term'))
    required_function_terms = [item.term for item in requirements if item.term.term_type == CanonicalTerm.TYPE_FUNCTION]
    if not required_function_terms and opportunity.job_function_id:
        required_function_terms = list(CanonicalTerm.objects.filter(
            function_mappings__job_function_id=opportunity.job_function_id,
            function_mappings__active=True, active=True,
        ).filter(
            Q(function_mappings__business_unit=opportunity.business_unit) |
            Q(function_mappings__business_unit__isnull=True)
        ).distinct())
    matched_function_terms = [term for term in required_function_terms if term.pk in candidate_function_ids]

    def days_label(values):
        labels = {'mon': 'segunda', 'tue': 'terça', 'wed': 'quarta', 'thu': 'quinta', 'fri': 'sexta', 'sat': 'sábado', 'sun': 'domingo'}
        return ', '.join(labels.get(value, value) for value in values) or 'não informado'

    required_days = list(opportunity.required_days or [])
    candidate_days = set(candidate.availability_days or [])
    required_period = opportunity.get_required_period_display() if opportunity.required_period else 'qualquer período'
    candidate_period = {'morning': 'manhã', 'afternoon': 'tarde', 'evening': 'noite', 'any': 'qualquer período'}.get(candidate.availability_period, 'não informado')
    required_format = opportunity.get_work_format_display() if opportunity.work_format else 'não especificado'
    candidate_format = {'fixo': 'fixo', 'temporario': 'temporário', 'ambos': 'fixo ou temporário'}.get(candidate.preferred_work_format, 'não informado')

    criteria = [
        {
            'label': 'Função canônica',
            'required_value': ', '.join(term.label for term in required_function_terms) or 'cargo mapeado',
            'candidate_value': ', '.join(label for label in candidate_function_labels if label in {term.label for term in matched_function_terms}) or 'não informado',
        },
        {
            'label': 'Dias disponíveis',
            'required_value': days_label(required_days) if required_days else 'não especificados',
            'candidate_value': days_label(candidate.availability_days),
        },
        {
            'label': 'Período',
            'required_value': required_period,
            'candidate_value': candidate_period,
        },
        {
            'label': 'Formato',
            'required_value': required_format,
            'candidate_value': candidate_format,
        },
        {
            'label': 'Experiência',
            'required_value': opportunity.get_required_experience_display(),
            'candidate_value': f'{candidate.experience_years} ano(s) declarado(s)',
        },
    ]
    if opportunity.starts_at:
        criteria.append({
            'label': 'Início',
            'required_value': opportunity.starts_at.strftime('%d/%m/%Y'),
            'candidate_value': candidate.available_from.strftime('%d/%m/%Y') if candidate.available_from else 'não informado',
        })

    distance_km = None
    if opportunity.business_unit:
        distance_km = distance_candidate_to_store(candidate, opportunity.business_unit)
    if distance_km is not None:
        distance_label = f'{distance_km:.1f} km em linha aproximada'
    elif candidate.cep and opportunity.business_unit and getattr(opportunity.business_unit, 'postal_code', ''):
        distance_label = 'CEP do candidato e da unidade registrados; aguardando geocodificação'
    else:
        distance_label = 'distância não calculada — informe os CEPs e geocodifique as coordenadas'
    helpful = [
        f'Consentimento territorial compatível com esta oportunidade ({opportunity.business_unit.name if opportunity.business_unit else opportunity.organization.name}).',
        f'Localidade declarada: {candidate.city or "não informada"}/{candidate.state or "—"}.',
        f'Proximidade estimada: {distance_label}.',
    ]
    if candidate.preferred_store_id == opportunity.business_unit_id and opportunity.business_unit_id:
        helpful.append('A unidade desta oportunidade coincide com a unidade de origem preferida no Perfil.')

    return {
        'criteria': criteria,
        'helpful': helpful,
        'distance_km': round(distance_km, 1) if distance_km is not None else None,
        'distance_label': distance_label,
        'no_ranking': 'Esta explicação mostra os critérios atendidos. Não é uma nota nem uma posição contra outras pessoas.',
    }


def employer_interest_view(relation):
    """Projeção whitelist do Perfil para o empregador.

    Retorna nada útil se a Relation ainda não chegou a
    EMPLOYER_INTEREST_VIEW. Nunca inclui contato — isso é ContactChannel.
    """
    if relation.state == Relation.STATE_NOTICE_DELIVERED:
        # Empregador não tem direito a nada ainda.
        return None

    candidate = relation.candidate
    opp = relation.opportunity

    # Whitelist estrita — cada campo abaixo tem justificativa relacional.
    view = {
        'relation_id': str(relation.id),
        'state': relation.state,
        'opportunity_version_at_interest': relation.opportunity_version,
        'person_interested_at': relation.person_interested_at,

        # Identidade mínima (nome; sem sobrenome-só se preferir stub).
        'first_name': candidate.first_name,
        'last_name': candidate.last_name,

        # Bairro/cidade — geografia de possibilidade, não endereço.
        'city': candidate.city,
        'state_uf': candidate.state,

        # Fatos relevantes à FUNÇÃO da Opportunity.
        'experience_years': candidate.experience_years,

        # Disponibilidade — só o que for relevante ao horário da Opportunity.
        'availability_days': candidate.availability_days or [],
        'availability_start': candidate.availability_start,
        'availability_end': candidate.availability_end,

        # Interesse declarado sobre a função.
        'interest_categories': candidate.interest_categories or [],

        # Respostas a critérios REQUIRED — placeholder, ligado à Fase 8/10.
        'required_criteria_answers': [],
        'desirable_facts': [],

        # Sinais de integração (Fase 10) — sempre por extenso, escopo Opportunity.
        'integration_signals': [],
        'match_explanation': _match_explanation(relation),
    }
    # Respostas de questionário não são projetadas por padrão. Sem um
    # mapeamento explícito de pergunta → critério da oportunidade, expor o
    # JSON inteiro poderia compartilhar informação fora da finalidade. A
    # pessoa empregadora recebe os fatos acima e os critérios objetivos da
    # Relation; respostas detalhadas ficam no escopo autorizado de operação.
    view['contextual_answers'] = {}
    try:
        from .integrations.signals import signals_for_view
        view['integration_signals'] = signals_for_view(
            candidate, opportunity_id=opp.pk,
        )
    except Exception:
        # Integrations não podem quebrar a projeção principal.
        view['integration_signals'] = []
    return view


def contact_view(relation):
    """Contato do candidato — só se CONTACT_ENABLED.

    Retorna None em qualquer outro estado. Sem exceção. Sem escape.
    """
    if relation.state not in (Relation.STATE_CONTACT_ENABLED, Relation.STATE_RESPONSE_CREATED, Relation.STATE_CLOSED):
        return None

    candidate = relation.candidate
    return {
        'relation_id': str(relation.id),
        'candidate_first_name': candidate.first_name,
        'candidate_last_name': candidate.last_name,
        'candidate_mobile': candidate.phone,
        'released_at': getattr(relation, 'contact_channel', None) and relation.contact_channel.released_at,
    }
