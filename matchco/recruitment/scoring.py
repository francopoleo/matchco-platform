"""Flexible, rule-based scoring engine for recruitment candidates."""

from django.db import transaction
from django.utils import timezone
from typing import Dict, Tuple
import logging

from .models import (
    ScoringRuleSet,
    ScoringCriteria,
    WeightedQuestion,
    ScoringLog,
    CandidateScore,
    CandidateCourseCompletion,
    CandidateProfileSurveyResponse,
)

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Core scoring calculation logic - no hardcoding, all rule-driven."""

    def __init__(self, organization, candidate):
        self.organization = organization
        self.candidate = candidate
        self.rule_set = organization.scoring_rule_set if hasattr(organization, 'scoring_rule_set') else None

    def calculate_score(self) -> Tuple[int, Dict]:
        """Calculate total score and breakdown.

        Returns:
            Tuple of (total_score: int, breakdown: dict)
        """

        if not self.rule_set or not self.rule_set.is_active:
            # Fallback to legacy scoring if no rule set
            return self._legacy_score()

        breakdown = {}
        total_weighted_points = 0
        total_weight = 0

        for criteria in self.rule_set.criteria.filter(is_active=True):
            points = self._score_criteria(criteria)
            breakdown[criteria.name] = {
                'points': points,
                'max_points': criteria.max_points,
                'weight': criteria.weight,
                'type': criteria.criteria_type,
            }

            # Weight the contribution (points * weight / 100)
            if criteria.max_points > 0:
                normalized = (points / criteria.max_points) * 100
                weighted_contribution = (normalized * criteria.weight) / 100
                total_weighted_points += weighted_contribution
                total_weight += criteria.weight

        # Normalize to 0-100
        if total_weight > 0:
            normalized_score = int(min(100, (total_weighted_points / total_weight) * 100))
        else:
            normalized_score = 0

        return normalized_score, breakdown

    def _score_criteria(self, criteria: ScoringCriteria) -> int:
        """Calculate points for a single criteria based on its type."""

        scorer_map = {
            ScoringCriteria.TYPE_QUESTION: self._score_question,
            ScoringCriteria.TYPE_ENGAGEMENT: self._score_engagement,
            ScoringCriteria.TYPE_COURSE: self._score_courses,
            ScoringCriteria.TYPE_CUSTOM: self._score_custom,
        }

        scorer = scorer_map.get(criteria.criteria_type)
        if not scorer:
            logger.warning(f"Unknown criteria type: {criteria.criteria_type}")
            return 0

        try:
            points = scorer(criteria)
            return min(points, criteria.max_points)
        except Exception as e:
            logger.error(f"Error scoring {criteria.name}: {e}")
            return 0

    def _score_question(self, criteria: ScoringCriteria) -> int:
        """Score based on survey response to a weighted question."""

        try:
            survey = self.candidate.profile_survey
            question_mapping = criteria.question_mapping
            response = survey.responses.get(question_mapping.question_text)

            if not response:
                return 0

            # Find matching answer choice
            for answer in question_mapping.answer_scores:
                if str(answer['choice']).lower() == str(response).lower():
                    return int(answer.get('points', 0))

            return 0
        except (CandidateProfileSurveyResponse.DoesNotExist, AttributeError):
            return 0

    def _score_engagement(self, criteria: ScoringCriteria) -> int:
        """Score based on engagement metrics."""

        config = criteria.rule_config
        metric_type = config.get('metric_type', 'days_since_signup')

        try:
            if metric_type == 'days_since_signup':
                days = (timezone.now() - self.candidate.created_at).days
                max_days = config.get('max_days', 30)
                # Linear scoring up to max_days
                return min(int((days / max_days) * criteria.max_points), criteria.max_points)

            elif metric_type == 'profile_completeness':
                # Score based on filled fields
                fields_filled = sum([
                    bool(self.candidate.phone),
                    bool(self.candidate.bio),
                    bool(self.candidate.linkedin_url),
                    self.candidate.experience_years > 0,
                ])
                return int((fields_filled / 4) * criteria.max_points)

            return 0
        except Exception as e:
            logger.error(f"Error scoring engagement: {e}")
            return 0

    def _score_courses(self, criteria: ScoringCriteria) -> int:
        """Score based on completed courses."""

        config = criteria.rule_config
        points_per_course = config.get('points_per_course', 5)

        try:
            completed_count = CandidateCourseCompletion.objects.filter(
                candidate=self.candidate,
                completed=True
            ).count()

            total = completed_count * points_per_course
            return min(total, criteria.max_points)
        except Exception as e:
            logger.error(f"Error scoring courses: {e}")
            return 0

    def _score_custom(self, criteria: ScoringCriteria) -> int:
        """Score using custom formula stored in rule_config."""

        config = criteria.rule_config
        formula_type = config.get('formula_type')

        try:
            if formula_type == 'experience_years':
                years = self.candidate.experience_years
                required_years = config.get('required_years', 1)
                max_years = config.get('max_years', 10)

                if years >= max_years:
                    return criteria.max_points
                elif years < required_years:
                    return 0
                else:
                    # Linear interpolation
                    progress = (years - required_years) / (max_years - required_years)
                    return int(progress * criteria.max_points)

            return 0
        except Exception as e:
            logger.error(f"Error scoring custom: {e}")
            return 0

    def _legacy_score(self) -> Tuple[int, Dict]:
        """Fallback to old calculation method."""
        try:
            survey = self.candidate.profile_survey
            responses = survey.responses or {}
            survey_score = min(len(responses) * 8, 40)
        except CandidateProfileSurveyResponse.DoesNotExist:
            survey_score = 0

        completed_courses = CandidateCourseCompletion.objects.filter(
            candidate=self.candidate,
            completed=True
        ).count()
        courses_score = min(completed_courses * 8, 40)

        days_since_signup = (timezone.now() - self.candidate.created_at).days
        engagement_score = min(days_since_signup, 20)

        overall_score = survey_score + courses_score + engagement_score

        breakdown = {
            'survey': {'points': survey_score, 'max_points': 40, 'weight': 40},
            'courses': {'points': courses_score, 'max_points': 40, 'weight': 40},
            'engagement': {'points': engagement_score, 'max_points': 20, 'weight': 20},
        }

        return overall_score, breakdown

    @transaction.atomic
    def save_score(self):
        """Calculate and save score with breakdown."""

        score, breakdown = self.calculate_score()

        candidate_score, created = CandidateScore.objects.get_or_create(
            candidate=self.candidate,
            defaults={'organization': self.organization},
        )

        candidate_score.overall_score = score
        candidate_score.scoring_breakdown = breakdown
        if self.rule_set:
            candidate_score.scoring_rule_version = self.rule_set.version
        candidate_score.calculation_method = 'rule_based' if self.rule_set else 'legacy'
        candidate_score.save()

        logger.info(f"Scored {self.candidate}: {score} (method: {candidate_score.calculation_method})")

        return score


class ScoringRuleManager:
    """Handle rule creation, updates, and versioning."""

    @staticmethod
    @transaction.atomic
    def update_rule_set(organization, rule_data: Dict) -> ScoringRuleSet:
        """Update/create scoring rule set with version increment."""

        rule_set = getattr(organization, 'scoring_rule_set', None)

        if not rule_set:
            rule_set = ScoringRuleSet.objects.create(
                organization=organization,
                max_score=rule_data.get('max_score', 100),
            )
        else:
            # Increment version on update
            rule_set.version += 1

        rule_set.name = rule_data.get('name', rule_set.name)
        rule_set.description = rule_data.get('description', rule_set.description)
        rule_set.save()

        # Update criteria
        for criteria_data in rule_data.get('criteria', []):
            ScoringRuleManager._update_criteria(rule_set, criteria_data)

        # Log the change
        ScoringLog.objects.create(
            organization=organization,
            rule_set=rule_set,
            action='rule_updated',
            changed_by=None,
            new_values=rule_data,
        )

        # Trigger recalculation for all candidates
        ScoringRuleManager.recalculate_all_scores(organization)

        logger.info(f"Updated scoring rules for {organization} (v{rule_set.version})")

        return rule_set

    @staticmethod
    def _update_criteria(rule_set: ScoringRuleSet, criteria_data: Dict):
        """Create or update a scoring criteria."""

        criteria, created = ScoringCriteria.objects.update_or_create(
            rule_set=rule_set,
            name=criteria_data['name'],
            defaults={
                'description': criteria_data.get('description', ''),
                'criteria_type': criteria_data['type'],
                'weight': criteria_data.get('weight', 10),
                'max_points': criteria_data.get('max_points', 10),
                'rule_config': criteria_data.get('config', {}),
                'rule_set_version': rule_set.version,
                'order': criteria_data.get('order', 0),
            }
        )

        # If question type, create WeightedQuestion
        if criteria_data['type'] == ScoringCriteria.TYPE_QUESTION:
            WeightedQuestion.objects.update_or_create(
                criteria=criteria,
                defaults={
                    'question_text': criteria_data.get('question_text', ''),
                    'answer_scores': criteria_data.get('answer_scores', []),
                }
            )

    @staticmethod
    @transaction.atomic
    def recalculate_all_scores(organization):
        """Recalculate scores for all candidates when rules change."""

        from .models import CandidateProfile

        candidates = CandidateProfile.objects.filter(organization=organization)

        count = 0
        for candidate in candidates:
            engine = ScoringEngine(organization, candidate)
            engine.save_score()
            count += 1

        logger.info(f"Recalculated scores for {count} candidates in {organization}")

        return count
