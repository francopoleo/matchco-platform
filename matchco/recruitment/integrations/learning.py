"""Optional assessment/learning integration.

Recruitment stores only an assessment snapshot and never imports a Course or
Quiz model. A learning provider can implement ``AssessmentPort`` and be
configured through ``RECRUITMENT_INTEGRATIONS['assessment']``.
"""

from .defaults import NullAssessmentAdapter
from .ports import AssessmentPort

__all__ = ['AssessmentPort', 'NullAssessmentAdapter']
