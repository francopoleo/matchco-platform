"""Application services for recruitment use cases.

This module is deliberately independent from courses, learning, students and
console. Adapters are invoked only at the edge and never during import.
"""

from django.utils.translation import gettext_lazy as gettext_lazy

import logging
import re
import hashlib
import hmac
import uuid
import unicodedata
import secrets
from datetime import timedelta
from datetime import date
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError

from .integrations import get_identity_port
from .models import (
    CandidateAssessment,
    CandidateConsent,
    CandidateIdentity,
    CandidateContextEntry,
    CandidateProfile,
    RecruitmentPolicy,
    EmploymentEvent,
    EmploymentRecord,
    RecruitmentAuditEvent,
)
from .integrations.contracts import AssessmentRequest
from .integrations import get_assessment_port

logger = logging.getLogger(__name__)


class IdentityConflict(Exception):
    """The supplied contacts identify two different people."""


class AccessApprovalError(Exception):
    """A controlled-access decision cannot be applied safely."""


def normalize_identity_email(value):
    return (value or '').strip().lower()


def normalize_identity_phone(value):
    return re.sub(r'\D', '', value or '')


def normalize_canonical_label(value):
    """Normalize labels for exact deterministic alias lookup only."""
    value = unicodedata.normalize('NFKD', value or '')
    value = ''.join(char for char in value if not unicodedata.combining(char))
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', value.lower())).strip()


def resolve_canonical_terms(*, catalog, value):
    """Resolve an exact canonical label/alias; this deliberately is not an LLM."""
    from .models import CanonicalTerm, CanonicalTermAlias
    normalized = normalize_canonical_label(value)
    if not normalized:
        return CanonicalTerm.objects.none()
    terms = CanonicalTerm.objects.filter(
        catalog=catalog, active=True, normalized_label=normalized,
    )
    if terms.exists():
        return terms
    return CanonicalTerm.objects.filter(
        catalog=catalog, active=True,
        aliases__normalized_alias=normalized,
        aliases__active=True,
    ).distinct()


@transaction.atomic
def record_canonical_response(*, candidate, term, scope, purpose, origin,
                              organization=None, business_unit=None, position=None,
                              segment_term=None,
                              value=None, consented_at=None, valid_until=None,
                              source_reference=''):
    """Store a scoped, version-pinned answer without changing global profile text."""
    from .models import CandidateCanonicalResponse
    organization = organization or candidate.organization
    if candidate.organization_id != organization.pk:
        raise ValueError('Candidate and response organization must match')
    response = CandidateCanonicalResponse(
        candidate=candidate, term=term, organization=organization,
        segment_term=segment_term, business_unit=business_unit, position=position, scope=scope,
        purpose=purpose, origin=origin, catalog_version=term.catalog.version,
        value=value or {}, consented_at=consented_at, valid_until=valid_until,
        source_reference=source_reference,
    )
    response.full_clean()
    response.save()
    return response


def project_shared_canonical_terms(*, candidate, viewer_organization, at=None):
    """Return only canonical labels authorized for another organization.

    The projection intentionally omits origin, source reference, raw answer and
    source organization. Cross-organization circulation requires explicit
    network consent; without it the viewer receives no profile terms.
    """
    from .models import CandidateCanonicalResponse
    at = at or timezone.now()
    if candidate.organization_id != viewer_organization.pk:
        from .territory import has_network_consent_for_organization
        allowed = has_network_consent_for_organization(
            candidate=candidate, viewer_organization=viewer_organization, at=at,
        ) if candidate.identity_id else False
        if not allowed:
            return []
    responses = CandidateCanonicalResponse.objects.filter(
        candidate=candidate, revoked_at__isnull=True,
        purpose=CandidateCanonicalResponse.PURPOSE_DISTRIBUTION,
        valid_from__lte=at,
    ).filter(Q(valid_until__isnull=True) | Q(valid_until__gte=at)).select_related('term', 'segment_term')
    return [
        {
            'code': response.term.code,
            'label': response.term.label,
            'term_type': response.term.term_type,
            'catalog_version': response.catalog_version,
            'scope': response.scope,
        }
        for response in responses
    ]


def canonical_terms_for_candidate(candidate, *, at=None):
    """Return active canonical terms from structured functions and valid answers."""
    from .models import CandidateCanonicalResponse
    at = at or timezone.now()
    mapped = candidate.job_functions.filter(
        canonical_mappings__active=True,
        canonical_mappings__term__active=True,
    ).values_list('canonical_mappings__term_id', flat=True)
    answered = CandidateCanonicalResponse.objects.filter(
        candidate=candidate, revoked_at__isnull=True,
        valid_from__lte=at,
    ).filter(Q(valid_until__isnull=True) | Q(valid_until__gte=at)).values_list('term_id', flat=True)
    from .models import CanonicalTerm
    return CanonicalTerm.objects.filter(Q(pk__in=mapped) | Q(pk__in=answered), active=True).distinct()


def candidate_is_eligible_for_position(*, candidate, position, at=None, entry_point=None):
    """Deterministic gate for a need; filters only, never scores or ranks."""
    from .models import (
        CanonicalTerm, CandidateCanonicalResponse, OpportunityCanonicalRequirement,
        Position,
    )
    at = at or timezone.now()
    from .territory import has_territorial_consent
    if not has_territorial_consent(
        candidate=candidate, position=position, entry_point=entry_point, at=at,
    ):
        return False
    terms = set(canonical_terms_for_candidate(candidate, at=at).values_list('pk', flat=True))
    requirements = list(OpportunityCanonicalRequirement.objects.filter(
        position=position, active=True,
        requirement=OpportunityCanonicalRequirement.REQUIRED,
    ).select_related('term'))
    function_terms = {item.term_id for item in requirements if item.term.term_type == CanonicalTerm.TYPE_FUNCTION}
    other_required_terms = {item.term_id for item in requirements if item.term.term_type != CanonicalTerm.TYPE_FUNCTION}
    if not function_terms and position.job_function_id:
        function_terms = set(CanonicalTerm.objects.filter(
            function_mappings__job_function_id=position.job_function_id,
            function_mappings__active=True, active=True,
        ).filter(
            Q(function_mappings__business_unit=position.business_unit) |
            Q(function_mappings__business_unit__isnull=True)
        ).values_list('pk', flat=True))
    # Um cargo local pode apontar para várias formas canônicas equivalentes
    # (OR); habilidades/segmentos adicionais continuam sendo obrigatórios
    # individualmente (AND).
    if not function_terms or not (function_terms & terms):
        return False
    if not other_required_terms.issubset(terms):
        return False

    # Disponibilidade declarada é um filtro obrigatório quando a loja informa
    # dias/período estruturados. Texto livre de schedule não participa desta
    # decisão.
    required_days = set(position.required_days or [])
    candidate_days = set(candidate.availability_days or [])
    if required_days and not required_days.issubset(candidate_days):
        return False
    if position.required_period and position.required_period != 'any':
        if candidate.availability_period not in (position.required_period, 'any') and 'period' not in (position.negotiable_fields or []):
            return False
    if position.work_format not in ('', Position.FORMAT_AMBOS):
        if candidate.preferred_work_format not in (position.work_format, Position.FORMAT_AMBOS) and 'work_format' not in (position.negotiable_fields or []):
            return False
    position_start = position.starts_at
    if isinstance(position_start, str):
        try:
            position_start = date.fromisoformat(position_start)
        except ValueError:
            return False
    if position_start:
        if candidate.available_from is None and 'start_date' not in (position.negotiable_fields or []):
            return False
        if candidate.available_from and candidate.available_from > position_start and 'start_date' not in (position.negotiable_fields or []):
            return False

    # Experiência e segmentos são sinais flexíveis do Perfil. A ausência de
    # informação só bloqueia quando a loja marcou experiência/contexto como
    # obrigatório; critérios desejáveis ficam para leitura humana.
    if position.required_experience != Position.EXPERIENCE_ANY:
        experience_values = set()
        context_values = set()
        responses = CandidateCanonicalResponse.objects.filter(
            candidate=candidate,
            purpose=CandidateCanonicalResponse.PURPOSE_DISTRIBUTION,
            revoked_at__isnull=True,
        ).order_by('-created_at')
        for response in responses:
            value = response.value or {}
            if value.get('experience'):
                experience_values.add(value['experience'])
            context_values.update(value.get('experience_contexts') or [])
        has_experience = candidate.experience_years > 0 or bool(
            experience_values.intersection({'some', 'experienced'})
        )
        if position.required_experience in (Position.EXPERIENCE_SIMILAR, Position.EXPERIENCE_AREA) and not has_experience:
            return False
        if position.required_experience == Position.EXPERIENCE_AREA and 'experienced' not in experience_values and not (
            not experience_values and candidate.experience_years >= 1
        ):
            return False
    required_contexts = set(position.required_experience_contexts or [])
    if required_contexts:
        context_values = set()
        responses = CandidateCanonicalResponse.objects.filter(
            candidate=candidate,
            purpose=CandidateCanonicalResponse.PURPOSE_DISTRIBUTION,
            revoked_at__isnull=True,
        ).only('value')
        for response in responses:
            context_values.update((response.value or {}).get('experience_contexts') or [])
        if not required_contexts.intersection(context_values):
            return False
    return True


def estimate_candidate_pool(*, organization, business_unit, job_function=None,
                            required_days=None, required_period='any',
                            work_format='', required_experience='any', at=None):
    """Conta elegíveis para a prévia da loja, usando os mesmos filtros do convite."""
    from .models import Position
    preview = Position(
        organization=organization,
        business_unit=business_unit,
        job_function=job_function,
        required_days=list(required_days or []),
        required_period=required_period or Position.PERIOD_ANY,
        work_format=work_format or '',
        required_experience=required_experience or Position.EXPERIENCE_ANY,
    )
    return eligible_candidate_count_for_position(position=preview, at=at)


def eligible_candidate_count_for_position(*, position, at=None):
    """Count all eligible Profiles, including other tenants with consent.

    Invitation rounds already search this shared pool and apply the precise
    organization-consent gate in ``candidate_is_eligible_for_position``. The
    employer preview and coverage indicators must use that same population.
    """
    from .models import CandidateProfile
    candidates = CandidateProfile.objects.filter(
        visibility_match=True,
        circulation_state=CandidateProfile.CIRCULATION_ALLOWED,
    )
    return sum(
        1 for candidate in candidates.iterator()
        if candidate_is_eligible_for_position(candidate=candidate, position=position, at=at)
    )


@transaction.atomic
def evaluate_coverage_gap(*, coverage_gap):
    """Count deterministic eligibility and interest; never ranks candidates."""
    from .models import CoverageGap, Relation
    eligible_count = eligible_candidate_count_for_position(position=coverage_gap.position)
    interested_count = Relation.objects.filter(
        opportunity=coverage_gap.position,
        state__in=[
            Relation.STATE_PERSON_INTERESTED,
            Relation.STATE_EMPLOYER_INTEREST_VIEW,
            Relation.STATE_EMPLOYER_INTERESTED,
            Relation.STATE_MATCHED,
        ],
    ).values('candidate_id').distinct().count()
    coverage_gap.eligible_count = eligible_count
    coverage_gap.interested_count = interested_count
    coverage_gap.last_evaluated_at = timezone.now()
    if coverage_gap.state != CoverageGap.STATE_PAUSED:
        coverage_gap.state = (
            CoverageGap.STATE_RESOLVED
            if eligible_count >= coverage_gap.minimum_eligible and interested_count >= coverage_gap.minimum_interested
            else CoverageGap.STATE_OPEN
        )
    coverage_gap.save(update_fields=['eligible_count', 'interested_count', 'last_evaluated_at', 'state', 'updated_at'])
    return coverage_gap


@transaction.atomic
def create_enrichment_invite(*, campaign, candidate, expires_at=None):
    from .models import EnrichmentCampaign, EnrichmentInvite
    if campaign.status != EnrichmentCampaign.STATUS_ACTIVE:
        raise ValueError('Campaign must be active to invite a candidate')
    if candidate.organization_id != campaign.organization_id:
        raise ValueError('Candidate and campaign organization must match')
    invite, created = EnrichmentInvite.objects.get_or_create(
        campaign=campaign, candidate=candidate,
        defaults={
            'token': secrets.token_urlsafe(48),
            'expires_at': expires_at or (timezone.now() + timedelta(days=14)),
        },
    )
    return invite


@transaction.atomic
def record_enrichment_response(*, invite, responses, consented_at=None):
    from .models import EnrichmentCampaign, EnrichmentInvite, EnrichmentResponse
    if invite.state in (EnrichmentInvite.STATE_REVOKED, EnrichmentInvite.STATE_DECLINED, EnrichmentInvite.STATE_EXPIRED):
        raise ValueError('Campaign invitation is no longer available')
    if invite.campaign.status != EnrichmentCampaign.STATUS_ACTIVE:
        raise ValueError('Campaign is not active')
    if invite.expires_at < timezone.now():
        invite.state = EnrichmentInvite.STATE_EXPIRED
        invite.save(update_fields=['state'])
        raise ValueError('Campaign invitation expired')
    template = invite.campaign.questionnaire_template
    response = EnrichmentResponse.objects.create(
        invite=invite, candidate=invite.candidate, campaign=invite.campaign,
        questionnaire_template=template,
        questionnaire_version=template.version if template else 1,
        responses=responses or {}, consented_at=consented_at,
    )
    invite.state = EnrichmentInvite.STATE_COMPLETED
    invite.responded_at = timezone.now()
    invite.save(update_fields=['state', 'responded_at'])
    return response


@transaction.atomic
def change_enrichment_campaign_status(*, campaign, status):
    from .models import EnrichmentCampaign
    if status not in dict(EnrichmentCampaign.STATUS_CHOICES):
        raise ValueError('Unknown enrichment campaign status')
    campaign.status = status
    campaign.save(update_fields=['status', 'updated_at'])
    if status in (EnrichmentCampaign.STATUS_PAUSED, EnrichmentCampaign.STATUS_REVOKED, EnrichmentCampaign.STATUS_CLOSED):
        campaign.invites.filter(state__in=[
            'invited', 'started',
        ]).update(state='revoked')
    return campaign


@transaction.atomic
def create_preboarding_assignment(*, candidate, organization=None, segment_term=None,
                                  company=None, business_unit=None, program=None,
                                  position=None, relation=None, tag=None,
                                  course_ids=None, required_evidence=None,
                                  requires_approved_access=True, created_by=None,
                                  starts_at=None, expires_at=None):
    """Create a contextual assignment; it never computes a candidate score."""
    from .models import PreboardingAssignment
    organization = organization or candidate.organization
    if tag is None:
        tag = getattr(position, 'tag', PreboardingAssignment.TAG_PRECISA)
    assignment = PreboardingAssignment(
        candidate=candidate, organization=organization, segment_term=segment_term,
        company=company, business_unit=business_unit, program=program,
        position=position, relation=relation, tag=tag,
        course_ids=course_ids or [], required_evidence=required_evidence or [],
        requires_approved_access=requires_approved_access, created_by=created_by,
        starts_at=starts_at, expires_at=expires_at,
    )
    assignment.full_clean()
    assignment.save()
    return assignment


@transaction.atomic
def record_preboarding_evidence(*, assignment, evidence_type, evidence_key,
                                provider='', metadata=None, recorded_by=None,
                                completed_at=None, valid_until=None):
    """Record completion evidence and transition only assignment state."""
    from .models import PreboardingAssignment, PreboardingEvidence
    if assignment.state in (PreboardingAssignment.STATE_REVOKED, PreboardingAssignment.STATE_EXPIRED):
        raise ValueError('Pre-onboarding assignment is no longer active')
    evidence, _ = PreboardingEvidence.objects.update_or_create(
        assignment=assignment, evidence_type=evidence_type, evidence_key=evidence_key,
        defaults={
            'provider': provider, 'metadata': metadata or {},
            'recorded_by': recorded_by, 'completed_at': completed_at or timezone.now(),
            'valid_until': valid_until,
        },
    )
    required = assignment.required_evidence or []
    completed = {(item.evidence_type, item.evidence_key) for item in assignment.evidence.all()}
    required_keys = {
        (item.get('type'), item.get('key')) if isinstance(item, dict) else ('manual', item)
        for item in required
    }
    assignment.state = (
        PreboardingAssignment.STATE_COMPLETED
        if required_keys and required_keys.issubset(completed)
        else PreboardingAssignment.STATE_IN_PROGRESS
    )
    assignment.save(update_fields=['state', 'updated_at'])
    return evidence


def preboarding_access_allowed(*, assignment, user):
    """Gate contextual resources on an approved audience/Membership."""
    from django.contrib.auth import get_user_model
    from .models import ControlledAccessRequest, PreboardingAssignment
    if assignment.state in (PreboardingAssignment.STATE_REVOKED, PreboardingAssignment.STATE_EXPIRED):
        return False
    if not assignment.requires_approved_access:
        return True
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    requests = ControlledAccessRequest.objects.filter(
        user_id=user.pk,
        organization=assignment.organization,
        state=ControlledAccessRequest.STATE_ACTIVE,
    )
    if assignment.program_id:
        requests = requests.filter(program_id=assignment.program_id)
    elif assignment.business_unit_id:
        requests = requests.filter(business_unit_id=assignment.business_unit_id)
    return requests.exists()


def _access_required_level(*, program=None, company=None, business_unit=None):
    from .models import ControlledAccessRequest
    if program is not None:
        return ControlledAccessRequest.LEVEL_PROGRAM
    if business_unit is not None:
        return ControlledAccessRequest.LEVEL_UNIT
    if company is not None:
        return ControlledAccessRequest.LEVEL_COMPANY
    return ControlledAccessRequest.LEVEL_ORGANIZATION


@transaction.atomic
def create_controlled_access_request(*, organization, request_type, email=None, user=None,
                                     identity=None, program=None, company=None, business_unit=None,
                                     entry_point=None, invite=None, role='participant',
                                     scopes=None, requested_by=None, state=None):
    """Create or reuse a request; creation never grants membership."""
    from .models import ControlledAccessRequest, AccessApprovalEvent
    if identity is None and email:
        identity = resolve_or_create_identity(email=email)
    if request_type == ControlledAccessRequest.TYPE_PROGRAM and program is None:
        raise AccessApprovalError('Programa obrigatório para solicitação de programa')
    if program and program.organization_id != organization.pk:
        raise AccessApprovalError('Programa fora da organização da solicitação')
    if business_unit and business_unit.organization_id != organization.pk:
        raise AccessApprovalError('Unidade fora da organização da solicitação')
    company = company or getattr(business_unit, 'company', None)
    if company and company.organization_id != organization.pk:
        raise AccessApprovalError('Empresa/rede fora da organização da solicitação')
    required_level = _access_required_level(program=program, company=company, business_unit=business_unit)
    request_state = state or ControlledAccessRequest.STATE_PENDING_APPROVAL
    lookup = {'invite': invite} if invite is not None else None
    access_request = None
    if lookup:
        access_request = ControlledAccessRequest.objects.filter(**lookup).first()
    if access_request is None:
        access_request = ControlledAccessRequest.objects.create(
            organization=organization, request_type=request_type,
            company=company,
            business_unit=business_unit, program=program, entry_point=entry_point,
            invite=invite, identity=identity, user_id=getattr(user, 'pk', None),
            requested_by=requested_by or user, request_role=role,
            requested_scopes=scopes or [], required_level=required_level,
            state=request_state,
        )
        AccessApprovalEvent.objects.create(
            request=access_request,
            action=AccessApprovalEvent.ACTION_REQUESTED,
            level=required_level,
            actor=requested_by or user,
            scope_snapshot={
                'organization_id': str(organization.pk),
                'company_id': str(company.pk) if company else None,
                'business_unit_id': str(business_unit.pk) if business_unit else None,
                'program_id': str(program.pk) if program else None,
            },
        )
    else:
        access_request.user_id = getattr(user, 'pk', None) or access_request.user_id
        access_request.identity = identity or access_request.identity
        access_request.state = request_state
        access_request.save(update_fields=['user_id', 'identity', 'state', 'updated_at'])
    return access_request


def can_approve_controlled_access(*, access_request, actor):
    """Authorize the manager at the requested organization/unit/program scope."""
    from .models import AuthorityScope, EmployerActor
    if not actor or not actor.is_authenticated:
        return False
    if actor.is_superuser or actor.is_staff:
        return True
    actor_rows = EmployerActor.objects.filter(
        user=actor, organization=access_request.organization, active=True,
    )
    if access_request.business_unit_id:
        actor_rows = actor_rows.filter(
            Q(business_unit_id=access_request.business_unit_id) | Q(business_unit__isnull=True),
        )
    return actor_rows.filter(authority_scopes__contains=[AuthorityScope.AA3_ACTIVATE_OPPORTUNITY]).exists()


@transaction.atomic
def approve_controlled_access(*, access_request, actor, reason='', valid_until=None):
    """Approve and provision exactly the requested scope."""
    from .models import (
        AccessApprovalEvent, ControlledAccessRequest, EmployerActor,
        ProgramMembership,
    )
    from django.contrib.auth import get_user_model
    if access_request.state not in (
        ControlledAccessRequest.STATE_PENDING_APPROVAL,
        ControlledAccessRequest.STATE_REQUESTED,
        ControlledAccessRequest.STATE_APPROVED,
    ):
        raise AccessApprovalError('Solicitação não está aguardando aprovação')
    if not can_approve_controlled_access(access_request=access_request, actor=actor):
        raise AccessApprovalError('Aprovador não possui autoridade para este escopo')
    now = timezone.now()
    access_request.state = ControlledAccessRequest.STATE_APPROVED
    access_request.approved_by = actor
    access_request.approved_at = now
    access_request.approval_reason = reason or ''
    access_request.valid_until = valid_until
    access_request.save(update_fields=['state', 'approved_by', 'approved_at', 'approval_reason', 'valid_until', 'updated_at'])

    if access_request.request_type == ControlledAccessRequest.TYPE_PROGRAM and access_request.program_id:
        if not access_request.user_id:
            raise AccessApprovalError('Solicitação de programa sem usuário')
        ProgramMembership.objects.update_or_create(
            user_id=access_request.user_id, program=access_request.program,
            defaults={
                'identity': access_request.identity,
                'role': access_request.request_role,
                'active': True,
                'state': ProgramMembership.STATE_ACTIVE,
                'consented_at': now,
                'source': 'controlled_access_approval',
            },
        )
    elif access_request.request_type == ControlledAccessRequest.TYPE_EMPLOYER:
        if not access_request.user_id:
            raise AccessApprovalError('Solicitação operacional sem usuário')
        EmployerActor.objects.update_or_create(
            user_id=access_request.user_id,
            organization=access_request.organization,
            business_unit=access_request.business_unit,
            defaults={'authority_scopes': access_request.requested_scopes or [], 'active': True},
        )
        try:
            from configuration.models import Organization as ConfigOrganization, Membership
            config_org = ConfigOrganization.objects.filter(
                active=True, slug=access_request.organization.slug,
            ).first() or ConfigOrganization.objects.filter(
                active=True, name=access_request.organization.name,
            ).first()
            if config_org:
                Membership.objects.get_or_create(
                    user_id=access_request.user_id, organization=config_org,
                    defaults={'role': 'member', 'active': True, 'is_primary': True},
                )
        except Exception:
            logger.exception('Could not provision configuration membership for access request %s', access_request.pk)

    access_request.state = ControlledAccessRequest.STATE_ACTIVE
    access_request.save(update_fields=['state', 'updated_at'])
    AccessApprovalEvent.objects.create(
        request=access_request, action=AccessApprovalEvent.ACTION_APPROVED,
        level=access_request.required_level, actor=actor, reason=reason or '',
        scope_snapshot={
            'organization_id': str(access_request.organization_id),
            'company_id': str(access_request.company_id) if access_request.company_id else None,
            'business_unit_id': str(access_request.business_unit_id) if access_request.business_unit_id else None,
            'program_id': str(access_request.program_id) if access_request.program_id else None,
            'valid_until': valid_until.isoformat() if valid_until else None,
        },
    )
    return access_request


@transaction.atomic
def revoke_controlled_access(*, access_request, actor, reason=''):
    from .models import AccessApprovalEvent, ControlledAccessRequest, ProgramMembership
    if not can_approve_controlled_access(access_request=access_request, actor=actor):
        raise AccessApprovalError('Aprovador não possui autoridade para revogar este escopo')
    now = timezone.now()
    access_request.state = ControlledAccessRequest.STATE_REVOKED
    access_request.revoked_by = actor
    access_request.revoked_at = now
    access_request.revocation_reason = reason or ''
    access_request.save(update_fields=['state', 'revoked_by', 'revoked_at', 'revocation_reason', 'updated_at'])
    if access_request.program_id and access_request.user_id:
        ProgramMembership.objects.filter(user_id=access_request.user_id, program_id=access_request.program_id).update(
            active=False, state=ProgramMembership.STATE_REVOKED, revoked_at=now,
        )
    AccessApprovalEvent.objects.create(
        request=access_request, action=AccessApprovalEvent.ACTION_REVOKED,
        level=access_request.required_level, actor=actor, reason=reason or '',
    )
    return access_request


@transaction.atomic
def resolve_or_create_identity(*, email=None, phone=None):
    """Reuse one global identity without silently merging two people."""
    email = normalize_identity_email(email) or None
    phone = normalize_identity_phone(phone)
    if not email and not phone:
        raise ValueError('At least one contact is required to resolve identity')

    by_email = CandidateIdentity.objects.filter(email_normalized=email).first() if email else None
    phone_matches = list(
        CandidateIdentity.objects.filter(phone_normalized=phone)[:2]
    ) if phone else []
    by_phone = phone_matches[0] if len(phone_matches) == 1 else None
    if len(phone_matches) > 1:
        raise IdentityConflict('The phone is associated with more than one identity')
    if by_email and by_phone and by_email.pk != by_phone.pk:
        raise IdentityConflict('Email and phone identify different people')

    identity = by_email or by_phone
    if identity is None:
        identity = CandidateIdentity.objects.create(
            email_normalized=email,
            phone_normalized=phone,
        )
        return identity

    changed = []
    if email and not identity.email_normalized:
        identity.email_normalized = email
        changed.append('email_normalized')
    if phone and not identity.phone_normalized:
        identity.phone_normalized = phone
        changed.append('phone_normalized')
    if changed:
        changed.append('updated_at')
        identity.save(update_fields=changed)
    return identity


@transaction.atomic
def record_candidate_context(*, candidate, entry_point=None, metadata=None):
    """Record/reuse the QR context without duplicating the candidate profile."""
    defaults = {
        'identity': candidate.identity,
        'organization': candidate.organization,
        'business_unit': entry_point.scope_store if entry_point and entry_point.scope_store_id else None,
        'source_kind': entry_point.kind if entry_point else '',
        'campaign_name': entry_point.campaign_name if entry_point else '',
        'metadata': metadata or {},
    }
    lookup = {'candidate': candidate, 'entry_point': entry_point}
    context, created = CandidateContextEntry.objects.get_or_create(
        **lookup, defaults=defaults,
    )
    if not created:
        context.visit_count += 1
        context.metadata = {**context.metadata, **(metadata or {})}
        context.save(update_fields=['visit_count', 'metadata', 'last_seen_at'])
    return context


def resolve_platform_context(*, organization, business_unit=None, program=None):
    """Return the shared-context projection used by Talk and learning adapters.

    This is a projection only: it never grants access. Membership/audience
    services must still authorize the requested platform scope.
    """
    bindings = list(organization.platform_bindings.filter(active=True).values_list(
        'platform_organization_id', 'capabilities',
    ))
    return {
        'recruitment_organization_id': organization.pk,
        'platform_organization_ids': [item[0] for item in bindings],
        'capabilities': sorted({capability for _, values in bindings for capability in (values or [])}),
        'business_unit_id': getattr(business_unit, 'pk', None),
        'program_id': getattr(program, 'pk', None),
    }


def register_candidate(candidate, *, pool_consent=False):
    """Register the candidate in an optional identity system.

    The candidate remains valid when no identity adapter is configured or an
    external integration is unavailable. The local recruitment record is the
    source of truth for the public signup flow.
    """
    identity = resolve_or_create_identity(email=candidate.email, phone=candidate.phone)
    if candidate.identity_id != identity.pk:
        candidate.identity = identity
        candidate.save(update_fields=['identity', 'updated_at'])

    visibility_purpose = CandidateConsent.PURPOSE_VISIBILITY_MATCH
    CandidateConsent.objects.create(
        identity=identity,
        organization=candidate.organization,
        purpose=visibility_purpose,
        granted=True,
        policy_version='recruitment-match-v1',
        source='match_signup',
    )
    if pool_consent:
        CandidateConsent.objects.create(
            identity=identity,
            organization=candidate.organization,
            purpose=CandidateConsent.PURPOSE_CIRCULATION_SHOPPING,
            granted=True,
            policy_version='recruitment-v1',
        )
    try:
        return get_identity_port().register_candidate(
            candidate_id=candidate.pk,
            email=candidate.email,
        )
    except Exception:  # integrations must not break QR signup
        logger.exception('Optional identity adapter failed for candidate %s', candidate.pk)
        return None


def request_assessment(*, candidate, provider, external_id, title='', version='', context=None):
    """Request an optional assessment and persist only its provider snapshot."""
    assessment, _ = CandidateAssessment.objects.get_or_create(
        candidate=candidate,
        provider=provider,
        external_id=external_id,
        defaults={'title_snapshot': title, 'version': version},
    )
    try:
        result = get_assessment_port().request(AssessmentRequest(
            candidate_id=candidate.pk,
            assessment_id=external_id,
            context=context or {},
        ))
        assessment.status = CandidateAssessment.STATUS_COMPLETED if result.status == 'completed' else CandidateAssessment.STATUS_PENDING
        assessment.score = result.score
        assessment.result = dict(result.payload)
        if assessment.status == CandidateAssessment.STATUS_COMPLETED:
            assessment.completed_at = timezone.now()
        assessment.save(update_fields=['status', 'score', 'result', 'completed_at'])
    except Exception:
        logger.exception('Optional assessment adapter failed for candidate %s', candidate.pk)
    return assessment


def revoke_consent(*, identity, purpose, organization=None):
    """Revoke future sharing without deleting the audit history."""
    queryset = identity.consents.filter(purpose=purpose, granted=True)
    if organization is not None:
        queryset = queryset.filter(organization=organization)
    updated = queryset.update(granted=False, revoked_at=timezone.now())
    if purpose == CandidateConsent.PURPOSE_CIRCULATION_SHOPPING:
        identity.pool_opt_in = False
        identity.save(update_fields=['pool_opt_in', 'updated_at'])
    if purpose == CandidateConsent.PURPOSE_VISIBILITY_MATCH:
        profiles = identity.profiles.all()
        if organization is not None:
            profiles = profiles.filter(organization=organization)
        profiles.update(
            visibility_match=False,
            circulation_state=CandidateProfile.CIRCULATION_PAUSED,
            updated_at=timezone.now(),
        )
    return updated


def end_employment(*, employment, reason='', actor=None):
    employment.status = EmploymentRecord.STATUS_ENDED
    employment.ended_at = date.today()
    employment.save(update_fields=['status', 'ended_at'])
    EmploymentEvent.objects.create(
        employment=employment,
        event_type='ended',
        metadata={'reason': reason, 'actor_id': getattr(actor, 'pk', None)},
    )
    return employment


def audit_event(*, action, actor=None, identity=None, organization=None, request=None, object_type='', object_id='', metadata=None):
    from configuration.security import client_ip

    return RecruitmentAuditEvent.objects.create(
        actor=actor,
        identity=identity,
        organization=organization,
        action=action,
        object_type=object_type,
        object_id=str(object_id or ''),
        ip_address=client_ip(request) if request else None,
        metadata=metadata or {},
    )


def normalize_cpf(value):
    digits = re.sub(r'\D', '', value or '')
    if len(digits) != 11 or len(set(digits)) == 1:
        raise ValueError('CPF inválido')
    for length in (9, 10):
        total = sum(int(digits[index]) * (length + 1 - index) for index in range(length))
        check = (total * 10) % 11
        if check == 10:
            check = 0
        if int(digits[length]) != check:
            raise ValueError('CPF inválido')
    return digits


def set_cpf(*, identity, cpf, actor=None, request=None):
    digits = normalize_cpf(cpf)
    digest = hmac.new(settings.SECRET_KEY.encode(), digits.encode(), hashlib.sha256).hexdigest()
    identity.cpf_hash = digest
    identity.cpf_last4 = digits[-4:]
    identity.save(update_fields=['cpf_hash', 'cpf_last4', 'updated_at'])
    audit_event(action='cpf_registered', actor=actor, identity=identity, request=request, object_type='CandidateIdentity', object_id=identity.pk)
    return identity


def export_identity_data(*, identity, actor=None, request=None):
    """Return a minimised, portable export without exposing CPF plaintext."""
    profiles = list(identity.profiles.select_related('organization').values(
        'id', 'organization__name', 'first_name', 'last_name', 'email', 'phone',
        'city', 'state', 'experience_years', 'interested_in', 'created_at',
    ))
    data = {
        'identity': {'id': str(identity.pk), 'email': identity.email_normalized, 'cpf_last4': identity.cpf_last4},
        'profiles': profiles,
        'consents': list(identity.consents.values('purpose', 'granted', 'policy_version', 'granted_at', 'revoked_at')),
        'employment_history': list(identity.employment_records.values('organization__name', 'position_title', 'employment_type', 'corporate_email', 'status', 'started_at', 'ended_at')),
    }
    audit_event(action='data_exported', actor=actor, identity=identity, request=request, object_type='CandidateIdentity', object_id=identity.pk)
    return data


def anonymize_identity(*, identity, actor=None, request=None, reason='LGPD request'):
    anonymized_email = f'anonymized-{uuid.uuid4().hex}@invalid.local'
    identity.email_normalized = anonymized_email
    identity.phone_normalized = ''
    identity.cpf_hash = None
    identity.cpf_last4 = ''
    identity.pool_opt_in = False
    identity.save(update_fields=['email_normalized', 'phone_normalized', 'cpf_hash', 'cpf_last4', 'pool_opt_in', 'updated_at'])
    profiles = list(identity.profiles.all())
    for profile in profiles:
        profile.first_name = 'Candidato'
        profile.last_name = 'Anonimizado'
        profile.email = anonymized_email
        profile.phone = ''
        profile.cep = ''
        profile.address = ''
        profile.city = ''
        profile.state = ''
        profile.latitude = None
        profile.longitude = None
        profile.salary_expectation = None
        profile.permite_relocation = False
        profile.bio = ''
        profile.linkedin_url = ''
        profile.interested_in = ''
        profile.availability_days = []
        profile.availability_start = None
        profile.availability_end = None
        profile.interest_categories = []
        profile.visibility_match = False
        profile.circulation_state = CandidateProfile.CIRCULATION_PAUSED
        profile.save(update_fields=[
            'first_name', 'last_name', 'email', 'phone', 'cep', 'address',
            'city', 'state', 'latitude', 'longitude', 'salary_expectation',
            'permite_relocation', 'bio', 'linkedin_url', 'interested_in',
            'availability_days', 'availability_start', 'availability_end',
            'interest_categories', 'visibility_match',
            'circulation_state', 'updated_at',
        ])
    if profiles:
        from .models import (
            CandidateCanonicalResponse, CandidateContextEntry,
            CandidateProfileSurveyResponse, CandidateSignupAnswer,
            EnrichmentResponse, PreboardingEvidence,
        )
        profile_ids = [profile.pk for profile in profiles]
        CandidateSignupAnswer.objects.filter(
            candidate_id__in=profile_ids,
            gdpr_deletion_completed__isnull=True,
        ).update(
            responses={},
            relation=None,
            gdpr_deletion_requested=timezone.now(),
            gdpr_deletion_completed=timezone.now(),
        )
        CandidateProfileSurveyResponse.objects.filter(
            candidate_id__in=profile_ids,
        ).update(responses={})
        EnrichmentResponse.objects.filter(
            candidate_id__in=profile_ids,
        ).update(responses={})
        CandidateCanonicalResponse.objects.filter(
            candidate_id__in=profile_ids,
        ).update(value={}, source_reference='')
        CandidateContextEntry.objects.filter(
            candidate_id__in=profile_ids,
        ).update(metadata={})
        PreboardingEvidence.objects.filter(
            assignment__candidate_id__in=profile_ids,
        ).update(metadata={})
    identity.consents.filter(granted=True).update(granted=False, revoked_at=timezone.now())
    audit_event(action='identity_anonymized', actor=actor, identity=identity, request=request, object_type='CandidateIdentity', object_id=identity.pk, metadata={'reason': reason})


# ---------------------------------------------------------------------------
# Porta Match — serviços de Relation (SISTEMA_MATCHCO_CANONICO §2.3)
# ---------------------------------------------------------------------------

from django.db import transaction as _db_tx, models


def ledger_record(event_type, *, actor=None, actor_type='system', authority_scope='',
                  relation=None, opportunity=None, candidate=None, entry_point=None,
                  ip_address=None, user_agent='', metadata=None):
    """Grava evento imutável no Ledger (SISTEMA_MATCHCO_CANONICO §3.7)."""
    from .models import Ledger
    return Ledger.objects.create(
        event_type=event_type,
        actor=actor,
        actor_type=actor_type,
        authority_scope=authority_scope or '',
        relation=relation,
        opportunity=opportunity,
        opportunity_version=(opportunity.version if opportunity else None),
        candidate=candidate,
        entry_point=entry_point,
        ip_address=ip_address,
        user_agent=user_agent[:400] if user_agent else '',
        metadata=metadata or {},
    )


# Map de transição → evento canônico do Ledger.
_TRANSITION_LEDGER_EVENT = {
    'notice_delivered': 'NOTICE_DELIVERED',
    'person_interested': 'PERSON_INTERESTED',
    'employer_interested': 'EMPLOYER_INTERESTED',
    'matched': 'MATCHED',
    'contact_enabled': 'CONTACT_ENABLED',
    'response_created': 'RESPONSE_CREATED',
    'closed': 'CLOSED',
    'declined': 'DECLINED',
}


def _log_transition(relation, from_state, to_state, *, actor=None, actor_type='system', authority_scope='', metadata=None):
    from .models import RelationTransitionEvent
    RelationTransitionEvent.objects.create(
        relation=relation,
        from_state=from_state,
        to_state=to_state,
        actor=actor,
        actor_type=actor_type,
        authority_scope=authority_scope,
        metadata=metadata or {},
    )
    # Espelho canônico no Ledger para os estados materiais.
    event_type = _TRANSITION_LEDGER_EVENT.get(to_state)
    if event_type:
        ledger_record(
            event_type,
            actor=actor, actor_type=actor_type, authority_scope=authority_scope,
            relation=relation,
            opportunity=relation.opportunity,
            candidate=relation.candidate,
            metadata=metadata,
        )


def recruitment_defaults(*, organization, business_unit=None):
    """Resolve a configuração efetiva: organização, depois loja/unidade."""
    from .models import RecruitmentPolicy
    values = {
        'candidate_response_hours': 72,
        'employer_decision_hours': 120,
        'invite_batch_size': 12,
        'round_wait_hours': 24,
    }
    policy = RecruitmentPolicy.objects.filter(organization=organization, active=True).first()
    if policy:
        for key in values:
            values[key] = getattr(policy, key, values[key])
    store = business_unit
    if store:
        for key in values:
            override = getattr(store, f'{key}_override', None)
            if override:
                values[key] = override
        physical_unit = getattr(store, 'physical_unit', None)
        if physical_unit:
            for key in values:
                override = getattr(physical_unit, f'{key}_override', None)
                if override:
                    values[key] = override
    return values


def recruitment_sla(*, opportunity):
    """Retorna o SLA gravado na oportunidade, já congelado no cadastro."""
    values = recruitment_defaults(
        organization=opportunity.organization,
        business_unit=opportunity.business_unit,
    )
    # A material opportunity value wins over policy defaults when explicitly set.
    for key in ('candidate_response_hours', 'employer_decision_hours', 'invite_batch_size'):
        explicit = getattr(opportunity, key, None)
        if explicit:
            values[key] = explicit
    return values


@_db_tx.atomic
def deliver_opportunity_notice(*, candidate, opportunity):
    """Cria convite com prazo. Idempotente por candidato/oportunidade/versão."""
    from .models import Relation
    if candidate.organization_id != opportunity.organization_id:
        raise ValidationError(gettext_lazy('O Perfil e a oportunidade devem pertencer à mesma organização.'))
    if opportunity.business_unit_id and opportunity.business_unit.organization_id != opportunity.organization_id:
        raise ValidationError(gettext_lazy('A unidade da oportunidade está fora da organização.'))
    now = timezone.now()
    sla = recruitment_sla(opportunity=opportunity)
    relation, created = Relation.objects.get_or_create(
        candidate=candidate,
        opportunity=opportunity,
        opportunity_version=opportunity.version,
        defaults={
            'state': Relation.STATE_NOTICE_DELIVERED,
            'notice_expires_at': now + timedelta(hours=sla['candidate_response_hours']),
        },
    )
    if created:
        _log_transition(relation, '', Relation.STATE_NOTICE_DELIVERED, actor_type='system')
    return relation


@_db_tx.atomic
def open_invitation_round(*, opportunity, now=None):
    """Entrega uma rodada limitada, sem ordenar pessoas por qualidade."""
    from .models import CandidateProfile, CandidateConsent, Relation
    now = now or timezone.now()
    sla = recruitment_sla(opportunity=opportunity)
    last_expired = Relation.objects.filter(
        opportunity=opportunity, opportunity_version=opportunity.version,
        state=Relation.STATE_NOTICE_EXPIRED,
    ).order_by('-notice_expired_at').first()
    if last_expired and last_expired.notice_expired_at and now < last_expired.notice_expired_at + timedelta(hours=sla['round_wait_hours']):
        return {'created': 0, 'eligible': 0, 'filled': 0, 'closed': False, 'waiting': True}
    filled_states = {
        Relation.STATE_EMPLOYER_INTERESTED, Relation.STATE_MATCHED,
        Relation.STATE_CONTACT_ENABLED, Relation.STATE_RESPONSE_CREATED,
    }
    filled = Relation.objects.filter(
        opportunity=opportunity, opportunity_version=opportunity.version,
        state__in=filled_states,
    ).values('candidate_id').distinct().count()
    if filled >= opportunity.requested_slots:
        return {'created': 0, 'eligible': 0, 'filled': filled, 'closed': True}
    active = Relation.objects.filter(
        opportunity=opportunity, opportunity_version=opportunity.version,
        state=Relation.STATE_NOTICE_DELIVERED,
        notice_expires_at__gt=now,
    ).count()
    capacity = max(0, sla['invite_batch_size'] - active)
    if not capacity:
        return {'created': 0, 'eligible': 0, 'filled': filled, 'closed': False}
    existing = Relation.objects.filter(
        opportunity=opportunity, opportunity_version=opportunity.version,
    ).values_list('candidate_id', flat=True)
    candidates = CandidateProfile.objects.filter(
        visibility_match=True,
        circulation_state=CandidateProfile.CIRCULATION_ALLOWED,
    ).exclude(pk__in=existing).order_by('pk')
    created = 0
    eligible = 0
    for candidate in candidates.iterator():
        if not candidate_is_eligible_for_position(candidate=candidate, position=opportunity, at=now):
            continue
        eligible += 1
        deliver_opportunity_notice(candidate=candidate, opportunity=opportunity)
        created += 1
        if created >= capacity:
            break
    return {'created': created, 'eligible': eligible, 'filled': filled, 'closed': False}


@_db_tx.atomic
def expire_invitation_rounds(*, now=None):
    """Expira convites e prazos de decisão; devolve contagens operacionais."""
    from .models import Relation
    now = now or timezone.now()
    expired_notices = 0
    for relation in Relation.objects.filter(
        state=Relation.STATE_NOTICE_DELIVERED,
        notice_expires_at__isnull=False,
        notice_expires_at__lte=now,
    ).select_related('opportunity'):
        relation.transition(Relation.STATE_NOTICE_EXPIRED, at=now)
        expired_notices += 1
    expired_decisions = 0
    for relation in Relation.objects.filter(
        state=Relation.STATE_EMPLOYER_INTEREST_VIEW,
        employer_decision_expires_at__isnull=False,
        employer_decision_expires_at__lte=now,
    ).select_related('opportunity'):
        employer_declined(relation=relation, actor=None, reason='employer_decision_expired')
        expired_decisions += 1
    return {'expired_notices': expired_notices, 'expired_decisions': expired_decisions}


NEGOTIABLE_OPPORTUNITY_FIELDS = frozenset({'period', 'start_date', 'work_format', 'learn'})


@_db_tx.atomic
def request_negotiation(*, relation, fields, proposal, actor_type):
    """Registra uma contraproposta somente nos critérios liberados pela loja."""
    from .models import Relation, RelationStateError
    requested = {str(field) for field in fields}
    allowed = set(relation.opportunity.negotiable_fields or [])
    if not requested or not requested.issubset(NEGOTIABLE_OPPORTUNITY_FIELDS):
        raise ValueError('Critério de negociação inválido.')
    if not requested.issubset(allowed):
        raise ValueError('A proposta contém critério que a loja não marcou como negociável.')
    if relation.state not in {Relation.STATE_EMPLOYER_INTEREST_VIEW, Relation.STATE_EMPLOYER_INTERESTED}:
        raise RelationStateError('A negociação só começa depois do interesse da pessoa.')
    relation.negotiation_state = 'pending'
    relation.negotiation_fields = sorted(requested)
    relation.negotiation_proposal = dict(proposal or {})
    relation.save(update_fields=['negotiation_state', 'negotiation_fields', 'negotiation_proposal', 'updated_at'])
    return relation


@_db_tx.atomic
def respond_negotiation(*, relation, accepted, actor_type):
    """Aceita ou recusa a proposta; não altera critério fora da lista permitida."""
    if relation.negotiation_state != 'pending':
        raise ValueError('Não existe negociação pendente.')
    relation.negotiation_state = 'accepted' if accepted else 'declined'
    relation.save(update_fields=['negotiation_state', 'updated_at'])
    return relation


@_db_tx.atomic
def person_interested(*, relation, actor=None):
    """Candidato manifesta interesse. Requer Pre-Interest Set completo e versão vigente."""
    from .models import Relation, RelationStateError

    if not relation.opportunity.pre_interest_set_complete:
        raise RelationStateError(
            'Pre-Interest Decision Set incompleto — Opportunity não pode receber interesse'
        )
    if relation.opportunity_version != relation.opportunity.version:
        raise RelationStateError(
            f'Versão da Opportunity mudou (v{relation.opportunity_version} → '
            f'v{relation.opportunity.version}). Reconfirmação necessária.'
        )

    from_state = relation.state
    relation.transition(Relation.STATE_PERSON_INTERESTED)
    _log_transition(relation, from_state, Relation.STATE_PERSON_INTERESTED,
                    actor=actor, actor_type='candidate')

    # EMPLOYER_INTEREST_VIEW é projeção automática: o empregador passa a
    # ver o Perfil-projeção. Não é ato humano, é sistema.
    prev = relation.state
    relation.transition(Relation.STATE_EMPLOYER_INTEREST_VIEW)
    sla = recruitment_sla(opportunity=relation.opportunity)
    relation.employer_decision_expires_at = timezone.now() + timedelta(hours=sla['employer_decision_hours'])
    relation.save(update_fields=['employer_decision_expires_at', 'updated_at'])
    _log_transition(relation, prev, Relation.STATE_EMPLOYER_INTEREST_VIEW, actor_type='system')
    return relation


@_db_tx.atomic
def candidate_declined(*, relation, actor=None):
    from .models import Relation
    from_state = relation.state
    relation.transition(Relation.STATE_DECLINED)
    _log_transition(relation, from_state, Relation.STATE_DECLINED,
                    actor=actor, actor_type='candidate')
    return relation


def _resolve_employer_actor(user, opportunity, required_scope):
    """Encontra EmployerActor do user com escopo em opportunity + registra violação se faltar."""
    from .models import EmployerActor, AuthorityScope, AuthorityError
    if user is None:
        raise AuthorityError(f'Escopo {required_scope} requer ator humano')
    qs = EmployerActor.objects.filter(
        user=user, organization=opportunity.organization, active=True,
    ).filter(
        # aceita ator com escopo na loja específica OU na org (business_unit nulo)
        models.Q(business_unit=opportunity.business_unit) | models.Q(business_unit__isnull=True)
    )
    # loja específica > escopo organização (Python-side para clareza)
    actors = sorted(qs, key=lambda a: (a.business_unit_id is None,))
    actor = actors[0] if actors else None
    # Administrador da plataforma pode operar uma organização autorizada no
    # Portal sem receber AA-7/AA-8 manualmente. A autorização de tenant e de
    # unidade já foi validada pela camada do Portal; o EmployerActor global
    # abaixo mantém auditoria, ContactChannel e Ledger tipados corretamente.
    if user.is_superuser or user.is_staff:
        if actor is None:
            actor = EmployerActor.objects.create(
                user=user,
                organization=opportunity.organization,
                business_unit=None,
                authority_scopes=[
                    AuthorityScope.AA1_DECLARE_NEED,
                    AuthorityScope.AA2_STRUCTURE_OPPORTUNITY,
                    AuthorityScope.AA3_ACTIVATE_OPPORTUNITY,
                    AuthorityScope.AA4_MODIFY_OPPORTUNITY,
                    AuthorityScope.AA5_CLOSE_OPPORTUNITY,
                    AuthorityScope.AA6_VIEW_EMPLOYER_INTEREST_VIEW,
                    AuthorityScope.AA7_DECLARE_EMPLOYER_INTEREST,
                    AuthorityScope.AA8_RECEIVE_CONTACT_CHANNEL,
                ],
                human_verified_at=timezone.now(),
                active=True,
            )
        return actor
    if actor is None or not actor.has_scope(required_scope):
        ledger_record(
            'AUTHORITY_VIOLATION',
            actor=user, actor_type='employer_actor',
            authority_scope=required_scope,
            opportunity=opportunity,
            metadata={'attempted_scope': required_scope},
        )
        raise AuthorityError(
            f'User {user.pk} não tem escopo {required_scope} para Opportunity {opportunity.pk}'
        )
    return actor


def employer_interested(*, relation, actor, authority_scope='AA-7'):
    """Empregador manifesta interesse. Requer AA-7 humano verificado."""
    # Auth check FORA do atomic para preservar AUTHORITY_VIOLATION no Ledger.
    _resolve_employer_actor(actor, relation.opportunity, authority_scope)
    return _employer_interested_locked(relation=relation, actor=actor, authority_scope=authority_scope)


@_db_tx.atomic
def _employer_interested_locked(*, relation, actor, authority_scope):
    from .models import Relation
    from_state = relation.state
    relation.transition(Relation.STATE_EMPLOYER_INTERESTED)
    _log_transition(relation, from_state, Relation.STATE_EMPLOYER_INTERESTED,
                    actor=actor, actor_type='employer_actor', authority_scope=authority_scope)
    prev = relation.state
    relation.transition(Relation.STATE_MATCHED)
    _log_transition(relation, prev, Relation.STATE_MATCHED, actor_type='system')

    # Notifica candidato do MATCH — nunca quebra o fluxo se falhar.
    try:
        from . import notifications
        notifications.notify_match(relation=relation)
    except Exception:
        logger.exception('notify_match falhou para relation %s', relation.pk)
    return relation


@_db_tx.atomic
def employer_declined(*, relation, actor, authority_scope='AA-7', reason=''):
    from .models import Relation
    from_state = relation.state
    relation.transition(Relation.STATE_NO_EMPLOYER_INTEREST)
    _log_transition(relation, from_state, Relation.STATE_NO_EMPLOYER_INTEREST,
                    actor=actor, actor_type='employer_actor',
                    authority_scope=authority_scope,
                    metadata={'reason': reason} if reason else None)
    return relation


def enable_contact(*, relation, actor, authority_scope='AA-8'):
    """Libera ContactChannel. Requer MATCHED + AA-8 humano verificado."""
    _resolve_employer_actor(actor, relation.opportunity, authority_scope)
    return _enable_contact_locked(relation=relation, actor=actor, authority_scope=authority_scope)


@_db_tx.atomic
def _enable_contact_locked(*, relation, actor, authority_scope):
    from .models import Relation, ContactChannel
    from_state = relation.state
    relation.transition(Relation.STATE_CONTACT_ENABLED)
    _log_transition(relation, from_state, Relation.STATE_CONTACT_ENABLED,
                    actor=actor, actor_type='employer_actor',
                    authority_scope=authority_scope)
    # Materializa canal (idempotente por relation).
    cc, _created = ContactChannel.objects.get_or_create(
        relation=relation,
        defaults={
            'candidate_mobile': relation.candidate.phone,
            'released_to_actor': actor,
        },
    )
    try:
        from . import notifications
        notifications.notify_contact_enabled(relation=relation, contact_channel=cc)
    except Exception:
        logger.exception('notify_contact_enabled falhou para %s', relation.pk)
    return relation


@_db_tx.atomic
def create_response(*, relation, actor, response_class, note=''):
    """Cria Response RC-01..05 (obrigatória e validada) e fecha a Relation."""
    from .models import Relation, Response, ResponseClass, ResponseValidationError

    if response_class not in ResponseClass.ALL:
        raise ResponseValidationError(
            f'response_class inválida: {response_class}. '
            f'Aceitas: {", ".join(ResponseClass.ALL)}'
        )
    if response_class == ResponseClass.RC05_OUTRO_MOTIVO and not (note or '').strip():
        raise ResponseValidationError('RC-05 exige nota curta e honesta')

    response = Response.objects.create(
        relation=relation,
        response_class=response_class,
        note=note.strip(),
        created_by=actor,
    )

    from_state = relation.state
    relation.transition(Relation.STATE_RESPONSE_CREATED)
    _log_transition(relation, from_state, Relation.STATE_RESPONSE_CREATED,
                    actor=actor, actor_type='employer_actor',
                    metadata={'response_class': response_class, 'note': note})

    prev = relation.state
    relation.transition(Relation.STATE_CLOSED)
    _log_transition(relation, prev, Relation.STATE_CLOSED, actor_type='system')
    return response


# ---------------------------------------------------------------------------
# Bloqueio de nova Opportunity com Relations MATCHED pendentes de resposta
# ---------------------------------------------------------------------------

_RESPONSE_SLA_DAYS = 14  # SLA piloto; ajustar via settings.MATCHCO_RESPONSE_SLA_DAYS.


def pending_response_relations(*, organization, older_than_days=None):
    """Retorna Relations MATCHED/CONTACT_ENABLED sem resposta há > N dias."""
    from .models import Relation
    from django.conf import settings as _s
    days = older_than_days if older_than_days is not None else getattr(
        _s, 'MATCHCO_RESPONSE_SLA_DAYS', _RESPONSE_SLA_DAYS,
    )
    cutoff = timezone.now() - timedelta(days=days)
    return Relation.objects.filter(
        opportunity__organization=organization,
        state__in=[Relation.STATE_MATCHED, Relation.STATE_CONTACT_ENABLED],
        matched_at__lt=cutoff,
    )


def can_declare_new_opportunity(*, organization):
    """False se houver Relations MATCHED pendentes há mais que o SLA."""
    return not pending_response_relations(organization=organization).exists()


# ---------------------------------------------------------------------------
# LGPD — Age gate, RightsCase, retention (SISTEMA_MATCHCO_CANONICO §6)
# ---------------------------------------------------------------------------

from datetime import date, timedelta
import secrets


class AgeGateFailure(Exception):
    """Menor de 18 tentou criar Perfil na v1."""


def enforce_age_gate(birth_date, *, minimum_age=18):
    """Bloqueia criação de Perfil se menor de idade (v1 = 18+).

    Levanta AgeGateFailure. Registra AUTHORITY_VIOLATION no Ledger. RT-06:
    nenhum dado do requerente é retido.
    """
    if birth_date is None:
        raise AgeGateFailure('Data de nascimento obrigatória')
    today = date.today()
    age = today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )
    if age < minimum_age:
        ledger_record(
            'PROFILE_CREATED',
            actor_type='system',
            metadata={'gate_failed': True, 'reason': 'under_minimum_age',
                      'minimum_age': minimum_age},
        )
        raise AgeGateFailure(
            f'Idade mínima para criar Perfil é {minimum_age} anos (v1)'
        )
    return True


def _generate_case_ref():
    return 'RC-' + secrets.token_hex(4).upper()


@_db_tx.atomic
def open_rights_case(*, requester_email, request_type, identity=None, notes=''):
    """Cria RightsCase (SISTEMA_MATCHCO_CANONICO §6.3)."""
    from .models import RightsCase
    case = RightsCase.objects.create(
        case_ref=_generate_case_ref(),
        requester_email=requester_email,
        identity=identity,
        request_type=request_type,
        notes=notes,
    )
    ledger_record(
        'RIGHTS_REQUEST',
        actor_type='system',
        candidate=None,
        metadata={
            'case_ref': case.case_ref,
            'request_type': request_type,
            'requester_email': requester_email,
        },
    )
    return case


def apply_retention_policy(*, dry_run=True, now=None):
    """Aplica RT-01..RT-06 (SISTEMA_MATCHCO_CANONICO §6.2).

    Dry-run por default. Retorna dict com contadores por classe.
    """
    from .models import (
        Ledger, Relation, RetentionClass, RightsCase, CandidateProfile,
    )
    now = now or timezone.now()
    report = {'dry_run': dry_run, 'now': now.isoformat(), 'actions': {}}

    # RT-02: Relations CLOSED há mais de N dias → anonimizar dados sensíveis.
    days_rt02 = RetentionClass.DEFAULT_DAYS[RetentionClass.RT02_POST_CLOSURE]
    cutoff_rt02 = now - timedelta(days=days_rt02)
    rt02_qs = Relation.objects.filter(
        state=Relation.STATE_CLOSED, closed_at__lt=cutoff_rt02,
    )
    report['actions']['RT-02'] = {
        'count': rt02_qs.count(),
        'action': 'anonymize_related_candidate_pii' if not dry_run else 'noop',
    }
    if not dry_run:
        # Marca no Ledger para rastreabilidade; anonimização real fica em job
        # dedicado que roda em lote fora da transação.
        for rel in rt02_qs.iterator():
            ledger_record(
                'CORRECTION', actor_type='system',
                metadata={'retention': 'RT-02', 'relation_id': str(rel.id)},
            )

    # RT-03: Ledger antigo → arquivamento (nunca DELETE do vivo).
    days_rt03 = RetentionClass.DEFAULT_DAYS[RetentionClass.RT03_LEDGER_AUDIT]
    cutoff_rt03 = now - timedelta(days=days_rt03)
    old_ledger = Ledger.objects.filter(occurred_at__lt=cutoff_rt03).count()
    report['actions']['RT-03'] = {'count': old_ledger, 'action': 'archive_pending'}

    # RT-05: Logs técnicos — placeholder (fica no adapter da stack).
    report['actions']['RT-05'] = {'count': 0, 'action': 'delegated_to_infra'}

    # RT-04 e RT-01: nada a fazer periodicamente (RT-01 = ativa; RT-04 = 5 anos ANPD).
    report['actions']['RT-01'] = {'note': 'active relation — no periodic action'}
    report['actions']['RT-04'] = {'note': 'security incident logs — infra retained'}

    return report


# ---------------------------------------------------------------------------
# OTP passwordless (Rodada B1)
# ---------------------------------------------------------------------------

import random as _random
from datetime import timedelta as _td


class OtpError(Exception):
    pass


class OtpRateLimitError(OtpError):
    pass


class OtpInvalidError(OtpError):
    pass


def _otp_hash(code, mobile):
    return hashlib.sha256(f'{code}|{mobile}|matchco'.encode()).hexdigest()


def _normalize_mobile(mobile):
    return re.sub(r'\D', '', mobile or '')


def request_otp(*, mobile, ip_address=None, dev_capture=None, email=None):
    """Emite OTP para o mobile.

    Rate limit: no máximo 3 códigos pendentes por mobile em 10 minutos.
    Entrega: chama _deliver_otp que tenta SMS/WhatsApp e cai em e-mail se
    disponível. Se nenhum provedor real estiver ligado, retorna via
    dev_capture (usado só em dev/staging).
    """
    from .models import OtpCode
    mobile = _normalize_mobile(mobile)
    if len(mobile) < 10:
        raise OtpError('Mobile inválido')

    now = timezone.now()
    resend_cooldown = int(getattr(settings, 'OTP_RESEND_COOLDOWN_SECONDS', 60))
    latest = OtpCode.objects.filter(mobile=mobile).order_by('-created_at').first()
    if latest and latest.created_at > now - _td(seconds=resend_cooldown):
        raise OtpRateLimitError(gettext_lazy('Aguarde antes de solicitar outro código.'))
    recent = OtpCode.objects.filter(
        mobile=mobile,
        state=OtpCode.STATE_PENDING,
        created_at__gte=now - _td(minutes=10),
    ).count()
    if recent >= 3:
        raise OtpRateLimitError('Muitos códigos solicitados. Tente em alguns minutos.')

    code = f'{_random.randint(0, 999999):06d}'
    otp = OtpCode.objects.create(
        mobile=mobile,
        code_hash=_otp_hash(code, mobile),
        expires_at=now + _td(minutes=10),
        ip_address=ip_address,
    )
    ledger_record(
        'CONSENT_GRANTED',
        actor_type='system',
        ip_address=ip_address,
        metadata={'otp_id': str(otp.id), 'mobile_last4': mobile[-4:]},
    )

    # Entrega: SMS/WhatsApp se configurado; senão e-mail se conhecido.
    _deliver_otp(code=code, mobile=mobile, email=email, dev_capture=dev_capture)
    return otp, code


def _deliver_otp(*, code, mobile, email=None, dev_capture=None):
    """Entrega OTP pelo canal configurado. Fail-soft para dev_capture."""
    delivered = False

    # 1) SMS/WhatsApp via port (só se algum adapter estiver ligado).
    try:
        from .integrations import get_notification_port
        from .integrations.contracts import NotificationRequest
        port = get_notification_port()
        if port and hasattr(port, 'send_sms'):
            delivered = port.send_sms(
                recipient=mobile,
                body=f'Seu código MatchCo: {code}. Válido por 10 min.',
            )
    except Exception:
        logger.exception('SMS OTP delivery failed')

    # 2) E-mail via Django (funciona hoje com console backend em dev, SMTP em prod).
    if not delivered:
        target_email = email
        if not target_email:
            from .models import CandidateProfile
            profile = CandidateProfile.objects.filter(phone__endswith=mobile[-10:]).first()
            target_email = profile.email if profile else None
        if target_email:
            try:
                from django.core.mail import send_mail
                from django.conf import settings as _s
                send_mail(
                    subject='Seu código MatchCo',
                    message=(
                        f'Olá,\n\nSeu código de entrada no MatchCo é:\n\n'
                        f'    {code}\n\n'
                        f'Válido por 10 minutos.\n\n'
                        f'Se você não solicitou, ignore este e-mail.'
                    ),
                    from_email=getattr(_s, 'DEFAULT_FROM_EMAIL', 'noreply@matchco.example'),
                    recipient_list=[target_email],
                    fail_silently=False,
                )
                delivered = True
            except Exception:
                logger.exception('Email OTP delivery failed')

    # 3) Dev fallback — só expõe se caller pediu (nunca em produção).
    if dev_capture is not None:
        dev_capture.append(code)


def verify_otp(*, mobile, code, ip_address=None):
    """Verifica OTP. Levanta OtpInvalidError se inválido/expirado/exaurido."""
    from .models import OtpCode
    mobile = _normalize_mobile(mobile)
    now = timezone.now()
    otp = OtpCode.objects.filter(
        mobile=mobile, state=OtpCode.STATE_PENDING,
    ).order_by('-created_at').first()
    if otp is None:
        raise OtpInvalidError('Nenhum código pendente para este número.')
    if now >= otp.expires_at:
        otp.state = OtpCode.STATE_EXPIRED
        otp.save(update_fields=['state'])
        raise OtpInvalidError('Código expirado.')
    otp.attempts += 1
    if _otp_hash(code, mobile) != otp.code_hash:
        if otp.attempts >= otp.max_attempts:
            otp.state = OtpCode.STATE_FAILED
        otp.save(update_fields=['attempts', 'state'])
        raise OtpInvalidError('Código incorreto.')
    otp.state = OtpCode.STATE_USED
    otp.used_at = now
    otp.save(update_fields=['state', 'used_at', 'attempts'])
    return otp
