"""Portas de integração — sinais opcionais no Perfil (Fase 10).

Cada handler abaixo é chamado pelo módulo externo (courses, certifications,
tests, wiki). Nunca importe modelos desses módulos aqui — o recruitment
permanece independente. Recebemos DTOs primitivos.

Regras (SISTEMA_MATCHCO_CANONICO §13):

- Sinais viram tags F0/F1/F2 do Perfil, nunca score.
- Cada integração exige `CandidateConsent` correspondente ativo.
- Sempre exibidos por extenso na EmployerInterestView.
- Sem consent, o handler é no-op silencioso (não levanta exceção — a origem
  da integração não precisa saber sobre LGPD do recruitment).
"""
from django.utils import timezone

from ..models import (
    CandidateConsent, CandidateProfile, FreshnessClass, ProfileSignal,
    SignalOrigin,
)


def _has_consent(profile, purpose):
    if profile.identity_id is None:
        return False
    return profile.identity.consents.filter(
        purpose=purpose, granted=True, revoked_at__isnull=True,
    ).exists()


def _has_capability(platform_context, capability):
    """Require an approved platform binding when an adapter supplies context."""
    if platform_context is None:
        return True
    return capability in set(platform_context.get('capabilities') or [])


def _upsert_signal(profile, key, *, value, label, origin, freshness_class,
                   confirmed_at=None):
    """Cria ou atualiza sinal com (profile, key) único."""
    confirmed_at = confirmed_at or timezone.now()
    existing = ProfileSignal.objects.filter(profile=profile, key=key).first()
    if existing:
        existing.value = value
        existing.label = label
        existing.origin = origin
        existing.freshness_class = freshness_class
        existing.confirmed_at = confirmed_at
        existing.save()
        return existing
    return ProfileSignal.objects.create(
        profile=profile, key=key, value=value, label=label,
        origin=origin, freshness_class=freshness_class,
        confirmed_at=confirmed_at,
    )


def _record_preboarding_evidence(profile, *, evidence_type, evidence_key,
                                 provider='', completed_at=None, valid_until=None):
    """Bridge a completion event to contextual assignments without scoring."""
    from ..models import PreboardingAssignment, PreboardingEvidence
    for assignment in profile.preboarding_assignments.filter(
        state__in=[PreboardingAssignment.STATE_AVAILABLE, PreboardingAssignment.STATE_IN_PROGRESS],
    ).iterator():
        required = assignment.required_evidence or []
        matches = any(
            (item.get('type') == evidence_type and item.get('key') == evidence_key)
            if isinstance(item, dict) else (item == evidence_key)
            for item in required
        )
        if not matches:
            continue
        from ..services import record_preboarding_evidence
        record_preboarding_evidence(
            assignment=assignment, evidence_type=evidence_type,
            evidence_key=evidence_key, provider=provider,
            completed_at=completed_at, valid_until=valid_until,
        )


def on_course_completed(*, candidate_id, course_key, course_name, completed_at=None,
                        platform_context=None):
    """Curso concluído vira tag F0 (durável) no Perfil.

    Chamado pelo módulo Cursos. Silencioso sem consent.
    """
    profile = CandidateProfile.objects.filter(pk=candidate_id).first()
    if profile is None:
        return None
    if not _has_capability(platform_context, 'courses'):
        return None
    if not _has_consent(profile, CandidateConsent.PURPOSE_INTEGRATION_COURSES):
        return None
    signal = _upsert_signal(
        profile,
        key=f'course:{course_key}',
        value={'course_key': course_key, 'course_name': course_name},
        label=f'Curso concluído: {course_name}',
        origin=SignalOrigin.COURSE_COMPLETION,
        freshness_class=FreshnessClass.F0_DURABLE,
        confirmed_at=completed_at,
    )
    _record_preboarding_evidence(
        profile, evidence_type='course', evidence_key=course_key,
        provider='courses', completed_at=completed_at,
    )
    return signal


def on_certification_granted(*, candidate_id, cert_key, cert_name,
                             valid_until=None, granted_at=None,
                             platform_context=None):
    """Certificação vira tag no Perfil.

    F0 se sem validade (certificação vitalícia). F1 se tem validade
    (o sistema controla expiração via `expires_at` do ProfileSignal).
    """
    profile = CandidateProfile.objects.filter(pk=candidate_id).first()
    if profile is None:
        return None
    if not _has_capability(platform_context, 'certifications'):
        return None
    if not _has_consent(profile, CandidateConsent.PURPOSE_INTEGRATION_CERTIFICATIONS):
        return None
    fc = FreshnessClass.F1_DYNAMIC if valid_until else FreshnessClass.F0_DURABLE
    sig = _upsert_signal(
        profile,
        key=f'cert:{cert_key}',
        value={'cert_key': cert_key, 'cert_name': cert_name,
               'valid_until': valid_until.isoformat() if valid_until else None},
        label=f'Certificação: {cert_name}' + (
            f' (válida até {valid_until:%d/%m/%Y})' if valid_until else ''
        ),
        origin=SignalOrigin.CERTIFICATION,
        freshness_class=fc,
        confirmed_at=granted_at,
    )
    # Sobrescreve expires_at com validade explícita da certificação.
    if valid_until:
        sig.expires_at = valid_until
        sig.save(update_fields=['expires_at'])
    _record_preboarding_evidence(
        profile, evidence_type='certification', evidence_key=cert_key,
        provider='certifications', completed_at=granted_at, valid_until=valid_until,
    )
    return sig


def on_talk_interaction(*, candidate_id, topic_key, topic_name,
                        interacted_at=None, platform_context=None):
    """Record a contextual Talk signal only with consent and binding."""
    profile = CandidateProfile.objects.filter(pk=candidate_id).first()
    if profile is None:
        return None
    if not _has_capability(platform_context, 'talk'):
        return None
    if not _has_consent(profile, CandidateConsent.PURPOSE_INTEGRATION_TALK):
        return None
    return _upsert_signal(
        profile,
        key=f'talk:{topic_key}',
        value={'topic_key': topic_key, 'topic_name': topic_name},
        label=f'Talk: {topic_name}',
        origin=SignalOrigin.TALK_INTERACTION,
        freshness_class=FreshnessClass.F1_DYNAMIC,
        confirmed_at=interacted_at,
    )


def on_test_result(*, candidate_id, opportunity_id, test_key, test_name,
                   score=None, passed=None, taken_at=None):
    """Resultado de teste. **Escopo Opportunity**, não Perfil.

    Fica registrado só para aquela Relation (via ProfileSignal com key
    prefixada por opp:), nunca vira tag global do Perfil.
    """
    profile = CandidateProfile.objects.filter(pk=candidate_id).first()
    if profile is None:
        return None
    if not _has_consent(profile, CandidateConsent.PURPOSE_INTEGRATION_TESTS):
        return None
    return _upsert_signal(
        profile,
        key=f'test_opp{opportunity_id}:{test_key}',
        value={'opportunity_id': opportunity_id, 'test_key': test_key,
               'test_name': test_name, 'score': score, 'passed': passed},
        label=(f'Teste {test_name}' +
               (f' — aprovado' if passed else '') +
               (f' (nota {score})' if score is not None else '')),
        origin=SignalOrigin.TEST_RESULT,
        freshness_class=FreshnessClass.F0_DURABLE,
        confirmed_at=taken_at,
    )


def signals_for_view(profile, *, opportunity_id=None, now=None):
    """Retorna lista serializável de sinais válidos para a EmployerInterestView.

    Filtra:
    - Sinais expirados (F1/F2 stale) são omitidos.
    - Sinais escopo Opportunity (`test_oppN:*`) só aparecem se coincide
      com opportunity_id passada; caso contrário, ficam invisíveis.

    Retorna cada sinal como dict com `label` por extenso.
    """
    now = now or timezone.now()
    out = []
    for sig in profile.signals.all():
        if sig.is_stale(now=now):
            continue
        if sig.key.startswith('test_opp'):
            if opportunity_id is None:
                continue
            if not sig.key.startswith(f'test_opp{opportunity_id}:'):
                continue
        out.append({
            'key': sig.key,
            'label': sig.label,
            'origin': sig.origin,
            'freshness_class': sig.freshness_class,
            'confirmed_at': sig.confirmed_at.isoformat(),
            'expires_at': sig.expires_at.isoformat() if sig.expires_at else None,
        })
    return out
