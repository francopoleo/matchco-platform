from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.test import SimpleTestCase


class RankingRemovalTests(SimpleTestCase):
    def test_legacy_candidate_scoring_models_are_not_registered(self):
        removed_models = {
            'CandidatePosition', 'CandidateScore', 'CandidateCourseEnroll',
            'CandidateCourseCompletion', 'ScoringRuleSet', 'ScoringCriteria',
            'WeightedQuestion', 'ScoringLog',
        }
        registered = {model.__name__ for model in apps.get_app_config('recruitment').get_models()}
        self.assertTrue(removed_models.isdisjoint(registered))

    def test_candidate_score_and_ranking_engines_are_not_available(self):
        recruitment_path = Path(settings.BASE_DIR) / 'recruitment'
        self.assertFalse((recruitment_path / 'scoring.py').exists())
        self.assertFalse((recruitment_path / 'matching.py').exists())
