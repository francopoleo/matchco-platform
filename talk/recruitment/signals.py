"""Signals to automatically recalculate scores when data changes."""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    CandidateProfileSurveyResponse,
    CandidateCourseCompletion,
    ScoringCriteria,
    CandidateProfile,
)
from .scoring import ScoringEngine

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CandidateProfileSurveyResponse)
def recalculate_on_survey_response(sender, instance, created, **kwargs):
    """Recalculate score when candidate answers survey."""
    try:
        engine = ScoringEngine(instance.organization, instance.candidate)
        engine.save_score()
        logger.info(f"Recalculated score for {instance.candidate} (survey response)")
    except Exception as e:
        logger.error(f"Error recalculating score on survey response: {e}")


@receiver(post_save, sender=CandidateCourseCompletion)
def recalculate_on_course_completion(sender, instance, created, **kwargs):
    """Recalculate score when candidate completes course."""
    try:
        engine = ScoringEngine(
            instance.candidate.organization,
            instance.candidate
        )
        engine.save_score()
        logger.info(f"Recalculated score for {instance.candidate} (course completion)")
    except Exception as e:
        logger.error(f"Error recalculating score on course completion: {e}")


@receiver(post_save, sender=ScoringCriteria)
def recalculate_on_criteria_change(sender, instance, created, **kwargs):
    """Recalculate all candidates' scores when criteria changes."""
    if created:
        return  # Skip on creation, only recalc on update

    try:
        organization = instance.rule_set.organization
        candidates = CandidateProfile.objects.filter(organization=organization)

        count = 0
        for candidate in candidates:
            engine = ScoringEngine(organization, candidate)
            engine.save_score()
            count += 1

        logger.info(f"Recalculated scores for {count} candidates (criteria {instance.name} changed)")
    except Exception as e:
        logger.error(f"Error recalculating scores on criteria change: {e}")
