from django.test import SimpleTestCase, override_settings

from recruitment.integrations import (
    get_assessment_port,
    get_file_port,
    get_identity_port,
    get_notification_port,
)
from recruitment.integrations.contracts import AssessmentRequest, NotificationRequest
from recruitment.services import normalize_cpf


class RecruitmentIntegrationBoundaryTests(SimpleTestCase):
    """Optional products must not be required for the recruitment core."""

    @override_settings(RECRUITMENT_INTEGRATIONS={})
    def test_default_adapters_are_available_without_optional_apps(self):
        self.assertIsNotNone(get_identity_port().register_candidate(candidate_id=1, email='a@example.com'))
        self.assertEqual(
            get_assessment_port().request(AssessmentRequest(candidate_id=1, assessment_id='screening')).status,
            'not_configured',
        )
        # NullNotificationAdapter agora usa Django e-mail como fallback:
        # em teste com backend locmem retorna True (não trava a build).
        get_notification_port().send(
            NotificationRequest(recipient='a@example.com', subject='x', body='x')
        )
        self.assertEqual(get_file_port().store(name='cv.txt', content_type='text/plain', content=b'x').name, 'cv.txt')

    @override_settings(RECRUITMENT_INTEGRATIONS={
        'assessment': 'recruitment.tests.test_integrations.FakeAssessmentAdapter',
    })
    def test_adapter_is_loaded_lazily_from_configuration(self):
        result = get_assessment_port().request(AssessmentRequest(candidate_id=4, assessment_id='quiz'))
        self.assertEqual(result.status, 'completed')

    def test_cpf_validation_normalizes_only_valid_values(self):
        self.assertEqual(normalize_cpf('529.982.247-25'), '52998224725')
        with self.assertRaises(ValueError):
            normalize_cpf('111.111.111-11')


class FakeAssessmentAdapter:
    def request(self, request):
        from recruitment.integrations.contracts import AssessmentResult
        return AssessmentResult(assessment_id=request.assessment_id, status='completed', score=100)
