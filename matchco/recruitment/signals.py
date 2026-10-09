"""Signals de versionamento e compatibilidade histórica.

CandidateScore não é mais recalculado automaticamente nem participa do fluxo
Match. Os registros antigos permanecem disponíveis apenas para auditoria.
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import (
    CandidateProfileSurveyResponse,
    CandidateCourseCompletion,
    Position,
    OpportunityVersionHistory,
)

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CandidateProfileSurveyResponse)
def recalculate_on_survey_response(sender, instance, created, **kwargs):
    """Legacy hook intentionally disabled; answers enrich the profile only."""
    logger.debug('Legacy CandidateScore recalculation skipped for survey response %s', instance.pk)


@receiver(post_save, sender=CandidateCourseCompletion)
def recalculate_on_course_completion(sender, instance, created, **kwargs):
    """Legacy hook intentionally disabled; completion is profile evidence."""
    logger.debug('Legacy CandidateScore recalculation skipped for course completion %s', instance.pk)


# ---------------------------------------------------------------------------
# Porta Match — versionamento de Opportunity (SISTEMA_MATCHCO_CANONICO §2.3)
# ---------------------------------------------------------------------------

_OPPORTUNITY_SNAPSHOT_ATTR = '_matchco_material_snapshot'


@receiver(pre_save, sender=Position)
def snapshot_material_fields(sender, instance, **kwargs):
    """Snapshot dos campos materiais antes de salvar, para detectar mudança."""
    if not instance.pk:
        setattr(instance, _OPPORTUNITY_SNAPSHOT_ATTR, None)
        return
    try:
        current = Position.objects.get(pk=instance.pk)
    except Position.DoesNotExist:
        setattr(instance, _OPPORTUNITY_SNAPSHOT_ATTR, None)
        return
    snapshot = {f: getattr(current, f) for f in Position.MATERIAL_FIELDS}
    snapshot['_version'] = current.version
    setattr(instance, _OPPORTUNITY_SNAPSHOT_ATTR, snapshot)


@receiver(post_save, sender=Position)
def bump_version_on_material_change(sender, instance, created, **kwargs):
    """Se algum campo material mudou pós-ativação, bump version + histórico."""
    snapshot = getattr(instance, _OPPORTUNITY_SNAPSHOT_ATTR, None)
    if created or snapshot is None:
        return

    # Só versiona depois de ativada (STRUCTURED aceita edição sem bump).
    if snapshot['_version'] != instance.version:
        # Bump já foi feito manualmente; nada a fazer aqui.
        return
    if instance.state == Position.STATE_STRUCTURED:
        return

    changed = [
        f for f in Position.MATERIAL_FIELDS
        if snapshot[f] != getattr(instance, f)
    ]
    if not changed:
        return

    from_version = instance.version
    to_version = from_version + 1
    # Update sem disparar signal recursivo.
    Position.objects.filter(pk=instance.pk).update(version=to_version)
    instance.version = to_version

    OpportunityVersionHistory.objects.create(
        opportunity=instance,
        from_version=from_version,
        to_version=to_version,
        changed_fields=changed,
    )
    logger.info(
        f"Opportunity {instance.pk} bumped v{from_version}→v{to_version}: {changed}"
    )


# ---------------------------------------------------------------------------
# C3 — bridge com courses: quiz aprovado → sinal MatchCo
# ---------------------------------------------------------------------------

try:
    from courses.models import UserQuizAttempt as _CoursesQuizAttempt
except Exception:
    _CoursesQuizAttempt = None


if _CoursesQuizAttempt is not None:
    @receiver(post_save, sender=_CoursesQuizAttempt)
    def bridge_course_completion_to_matchco(sender, instance, created, **kwargs):
        """Quiz aprovado → chama on_course_completed no MatchCo (fail-soft)."""
        if not getattr(instance, 'passed', None):
            return
        from .models import CandidateProfile
        try:
            user_email = getattr(instance.user, 'email', None)
        except Exception:
            user_email = None
        if not user_email:
            return
        profile = CandidateProfile.objects.filter(email=user_email).first()
        if profile is None:
            return
        try:
            quiz = instance.quiz
            course_key = f'quiz-{quiz.pk}'
            course_name = getattr(quiz, 'title', None) or f'Quiz {quiz.pk}'
        except Exception:
            return
        try:
            from .integrations.signals import on_course_completed
            from .services import resolve_platform_context
            platform_context = resolve_platform_context(organization=profile.organization)
            on_course_completed(
                candidate_id=profile.pk,
                course_key=course_key,
                course_name=course_name,
                platform_context=platform_context if platform_context['platform_organization_ids'] else None,
            )
        except Exception:
            logger.exception('bridge_course_completion falhou para %s', profile.pk)
