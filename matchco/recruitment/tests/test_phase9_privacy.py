"""Fase 9 — projeção mínima, anonimização e separação de portas."""

from django.test import SimpleTestCase, TestCase
from inspect import getsource

from recruitment.domain_models import RecruitmentOrganization
from recruitment.forms import MatchcoSignupForm
from recruitment.models import CandidateIdentity, CandidateProfile
from recruitment import projections
from recruitment.services import anonymize_identity


class Phase9PrivacyContractTests(SimpleTestCase):
    def test_match_signup_does_not_collect_full_address(self):
        self.assertNotIn('address', MatchcoSignupForm.base_fields)
        # CEP é permitido como referência aproximada de território; endereço
        # completo continua fora do cadastro Match.
        self.assertIn('cep', MatchcoSignupForm.base_fields)

    def test_employer_projection_has_no_contextual_answer_payload(self):
        source = getsource(projections.employer_interest_view)
        self.assertIn("view['contextual_answers'] = {}", source)
        self.assertNotIn("view['contextual_answers'] = contextual_answer.responses", source)


class Phase9AnonymizationTests(TestCase):
    def test_anonymization_removes_profile_data_and_circulation(self):
        organization = RecruitmentOrganization.objects.create(
            external_id='phase-9-org', slug='phase-9-org', name='Phase 9',
        )
        identity = CandidateIdentity.objects.create(
            email_normalized='phase9@example.com', phone_normalized='5511999990000',
        )
        candidate = CandidateProfile.objects.create(
            organization=organization, identity=identity,
            first_name='Ana', last_name='Teste', email='phase9@example.com',
            phone='5511999990000', cep='01310-100', address='Rua Privada, 10',
            city='São Paulo', state='SP', latitude=-23.56, longitude=-46.65,
            salary_expectation=2500, interested_in='Caixa',
            availability_days=['mon'], visibility_match=True,
        )

        anonymize_identity(identity=identity)
        candidate.refresh_from_db()

        self.assertEqual(candidate.address, '')
        self.assertEqual(candidate.cep, '')
        self.assertIsNone(candidate.latitude)
        self.assertIsNone(candidate.salary_expectation)
        self.assertFalse(candidate.visibility_match)
        self.assertEqual(candidate.circulation_state, CandidateProfile.CIRCULATION_PAUSED)
