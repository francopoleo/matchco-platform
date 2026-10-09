"""Fase 7 — pré-onboarding contextual e evidências sem score."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from recruitment.domain_models import RecruitmentCompany, RecruitmentJobFunction, RecruitmentOrganization, RecruitmentStore
from recruitment.models import (
    CandidateIdentity, CandidateProfile, ControlledAccessRequest, Position,
    PreboardingAssignment, PreboardingEvidence,
)
from recruitment.services import (
    create_preboarding_assignment, preboarding_access_allowed,
    record_preboarding_evidence,
)


class PreboardingTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(
            external_id='phase-7-org', slug='phase-7-org', name='Phase 7',
        )
        company = RecruitmentCompany.objects.create(organization=self.org, name='Rede')
        self.store = RecruitmentStore.objects.create(
            organization=self.org, company=company, name='Unidade',
        )
        function = RecruitmentJobFunction.objects.create(
            organization=self.org, company=company, name='Atendente',
        )
        self.position = Position.objects.create(
            organization=self.org, business_unit=self.store, job_function=function,
            title='Atendente', tag=Position.TAG_PODE_APRENDER,
        )
        self.identity = CandidateIdentity.objects.create(email_normalized='phase7@example.com')
        self.candidate = CandidateProfile.objects.create(
            organization=self.org, identity=self.identity,
            first_name='Ana', email='phase7@example.com',
        )
        User = get_user_model()
        self.user = User.objects.create_user(username='phase7@example.com', email='phase7@example.com')

    def test_assignment_is_contextual_and_uses_position_tag(self):
        assignment = create_preboarding_assignment(
            candidate=self.candidate, position=self.position,
            business_unit=self.store, required_evidence=[{'type': 'course', 'key': 'basic-service'}],
        )
        self.assertEqual(assignment.tag, PreboardingAssignment.TAG_PODE_APRENDER)
        self.assertEqual(assignment.position_id, self.position.pk)
        self.assertEqual(assignment.state, PreboardingAssignment.STATE_AVAILABLE)

    def test_evidence_completes_assignment_without_score(self):
        assignment = create_preboarding_assignment(
            candidate=self.candidate, position=self.position,
            required_evidence=[{'type': 'course', 'key': 'basic-service'}],
        )
        record_preboarding_evidence(
            assignment=assignment, evidence_type=PreboardingEvidence.TYPE_COURSE,
            evidence_key='basic-service', provider='courses',
        )
        assignment.refresh_from_db()
        self.assertEqual(assignment.state, PreboardingAssignment.STATE_COMPLETED)
        self.assertFalse(hasattr(assignment, 'score'))

    def test_resource_release_requires_approved_access(self):
        assignment = create_preboarding_assignment(
            candidate=self.candidate, position=self.position,
            business_unit=self.store, required_evidence=[],
        )
        self.assertFalse(preboarding_access_allowed(assignment=assignment, user=self.user))
        ControlledAccessRequest.objects.create(
            request_type=ControlledAccessRequest.TYPE_EMPLOYER,
            organization=self.org, business_unit=self.store, user_id=self.user.pk,
            state=ControlledAccessRequest.STATE_ACTIVE,
        )
        self.assertTrue(preboarding_access_allowed(assignment=assignment, user=self.user))
