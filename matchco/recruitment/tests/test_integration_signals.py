"""Fase 10 — Integrações Cursos/Certificações/Testes como sinais opcionais."""
from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone

from recruitment.domain_models import (
    RecruitmentOrganization, RecruitmentCompany, RecruitmentStore, RecruitmentJobFunction,
)
from recruitment.integrations.signals import (
    on_certification_granted, on_course_completed, on_test_result, on_talk_interaction,
    signals_for_view,
)
from recruitment.models import (
    CandidateConsent, CandidateIdentity, CandidateProfile,
    FreshnessClass, OpportunityCriterion, Position as Opportunity,
    ProfileSignal, Relation,
)
from recruitment.projections import employer_interest_view
from recruitment.services import deliver_opportunity_notice, person_interested


class ConsentGateTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(external_id='oi', slug='oi', name='O')
        self.identity = CandidateIdentity.objects.create(email_normalized='p@ex.com')
        self.profile = CandidateProfile.objects.create(
            organization=self.org, identity=self.identity,
            first_name='P', last_name='X',
            email='p@ex.com', phone='11900',
        )

    def _consent(self, purpose):
        CandidateConsent.objects.create(
            identity=self.identity, purpose=purpose, granted=True, policy_version='v1',
        )

    def test_course_without_consent_is_noop(self):
        on_course_completed(candidate_id=self.profile.pk, course_key='atendimento',
                            course_name='Atendimento Básico')
        self.assertFalse(ProfileSignal.objects.filter(profile=self.profile).exists())

    def test_course_with_consent_creates_signal(self):
        self._consent(CandidateConsent.PURPOSE_INTEGRATION_COURSES)
        sig = on_course_completed(candidate_id=self.profile.pk, course_key='atd',
                                   course_name='Atendimento Básico')
        self.assertIsNotNone(sig)
        self.assertEqual(sig.freshness_class, FreshnessClass.F0_DURABLE)
        self.assertIn('Atendimento Básico', sig.label)

    def test_certification_with_validity_gets_f1_and_expires_at(self):
        self._consent(CandidateConsent.PURPOSE_INTEGRATION_CERTIFICATIONS)
        valid = timezone.now() + timedelta(days=365)
        sig = on_certification_granted(
            candidate_id=self.profile.pk, cert_key='nr35', cert_name='NR-35',
            valid_until=valid,
        )
        self.assertEqual(sig.freshness_class, FreshnessClass.F1_DYNAMIC)
        self.assertIsNotNone(sig.expires_at)

    def test_certification_without_validity_is_f0(self):
        self._consent(CandidateConsent.PURPOSE_INTEGRATION_CERTIFICATIONS)
        sig = on_certification_granted(
            candidate_id=self.profile.pk, cert_key='k', cert_name='Vitalícia',
        )
        self.assertEqual(sig.freshness_class, FreshnessClass.F0_DURABLE)
        self.assertIsNone(sig.expires_at)

    def test_test_result_is_scoped_to_opportunity(self):
        self._consent(CandidateConsent.PURPOSE_INTEGRATION_TESTS)
        sig = on_test_result(
            candidate_id=self.profile.pk, opportunity_id=42,
            test_key='math_basic', test_name='Matemática básica',
            score=8, passed=True,
        )
        self.assertTrue(sig.key.startswith('test_opp42:'))

    def test_upsert_replaces_same_key(self):
        self._consent(CandidateConsent.PURPOSE_INTEGRATION_COURSES)
        s1 = on_course_completed(candidate_id=self.profile.pk, course_key='k',
                                  course_name='V1')
        s2 = on_course_completed(candidate_id=self.profile.pk, course_key='k',
                                  course_name='V1 (atualizado)')
        self.assertEqual(s1.pk, s2.pk)
        self.assertIn('atualizado', s2.label)

    def test_platform_binding_capability_is_required_for_external_course(self):
        self._consent(CandidateConsent.PURPOSE_INTEGRATION_COURSES)
        sig = on_course_completed(
            candidate_id=self.profile.pk, course_key='k', course_name='Curso',
            platform_context={'capabilities': ['talk']},
        )
        self.assertIsNone(sig)

    def test_talk_signal_requires_consent_and_capability(self):
        self._consent(CandidateConsent.PURPOSE_INTEGRATION_TALK)
        sig = on_talk_interaction(
            candidate_id=self.profile.pk, topic_key='atendimento', topic_name='Atendimento',
            platform_context={'capabilities': ['talk']},
        )
        self.assertIsNotNone(sig)
        self.assertEqual(sig.origin, 'talk_interaction')

    def test_talk_signal_includes_message_length_and_course_id(self):
        self._consent(CandidateConsent.PURPOSE_INTEGRATION_TALK)
        sig = on_talk_interaction(
            candidate_id=self.profile.pk, topic_key='course-42:room-1',
            topic_name='Talk: Atendimento Básico', message_length=150,
            platform_context={'capabilities': ['talk']},
        )
        self.assertIsNotNone(sig)
        self.assertEqual(sig.value.get('message_length'), 150)
        self.assertIn('course-42', sig.key)
        self.assertEqual(sig.label, 'Talk: Atendimento Básico')


class SignalsForViewTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(external_id='oi2', slug='oi2', name='O')
        self.identity = CandidateIdentity.objects.create(email_normalized='q@ex.com')
        self.profile = CandidateProfile.objects.create(
            organization=self.org, identity=self.identity,
            first_name='Q', last_name='X',
            email='q@ex.com', phone='11900',
        )
        for purpose in [
            CandidateConsent.PURPOSE_INTEGRATION_COURSES,
            CandidateConsent.PURPOSE_INTEGRATION_TESTS,
            CandidateConsent.PURPOSE_INTEGRATION_CERTIFICATIONS,
        ]:
            CandidateConsent.objects.create(
                identity=self.identity, purpose=purpose, granted=True, policy_version='v1',
            )

    def test_test_signals_only_appear_for_matching_opportunity(self):
        on_test_result(candidate_id=self.profile.pk, opportunity_id=1,
                       test_key='t', test_name='Test', passed=True)
        on_course_completed(candidate_id=self.profile.pk, course_key='c',
                            course_name='Curso X')

        # opp 1: vê o teste + curso
        v1 = signals_for_view(self.profile, opportunity_id=1)
        keys1 = {s['key'] for s in v1}
        self.assertIn('test_opp1:t', keys1)
        self.assertIn('course:c', keys1)

        # opp 2: NÃO vê o teste da opp 1
        v2 = signals_for_view(self.profile, opportunity_id=2)
        keys2 = {s['key'] for s in v2}
        self.assertNotIn('test_opp1:t', keys2)
        self.assertIn('course:c', keys2)

        # sem opp: só o durável
        v_none = signals_for_view(self.profile, opportunity_id=None)
        keys_none = {s['key'] for s in v_none}
        self.assertNotIn('test_opp1:t', keys_none)

    def test_stale_signals_omitted(self):
        on_course_completed(candidate_id=self.profile.pk, course_key='c',
                            course_name='Curso X')
        # Torna F1 stale
        sig = ProfileSignal.objects.get(profile=self.profile, key='course:c')
        sig.freshness_class = FreshnessClass.F1_DYNAMIC
        sig.confirmed_at = timezone.now() - timedelta(days=200)
        sig.save()

        out = signals_for_view(self.profile, opportunity_id=None)
        self.assertFalse(any(s['key'] == 'course:c' for s in out))


class ProjectionIncludesSignalsTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(external_id='oi3', slug='oi3', name='O')
        self.comp = RecruitmentCompany.objects.create(organization=self.org, name='C')
        self.store = RecruitmentStore.objects.create(organization=self.org, company=self.comp, name='L')
        self.func = RecruitmentJobFunction.objects.create(
            organization=self.org, company=self.comp, name='F',
        )
        self.identity = CandidateIdentity.objects.create(email_normalized='r@ex.com')
        self.cand = CandidateProfile.objects.create(
            organization=self.org, identity=self.identity,
            first_name='R', last_name='X',
            email='r@ex.com', phone='11900',
        )
        CandidateConsent.objects.create(
            identity=self.identity, purpose=CandidateConsent.PURPOSE_INTEGRATION_COURSES,
            granted=True, policy_version='v1',
        )
        self.opp = Opportunity.objects.create(
            organization=self.org, business_unit=self.store, job_function=self.func,
            title='X', workplace='W', schedule='S', work_format=Opportunity.FORMAT_FIXO,
            starts_at=date(2026, 12, 1), tag=Opportunity.TAG_PRECISA,
            state=Opportunity.STATE_ACTIVATED, pre_interest_set_complete=True,
        )
        OpportunityCriterion.objects.create(
            opportunity=self.opp, label='X', weight=OpportunityCriterion.WEIGHT_REQUIRED,
        )
        on_course_completed(candidate_id=self.cand.pk, course_key='atd',
                            course_name='Atendimento')

    def test_projection_includes_integration_signals_by_extenso(self):
        rel = deliver_opportunity_notice(candidate=self.cand, opportunity=self.opp)
        person_interested(relation=rel)
        v = employer_interest_view(rel)
        self.assertIn('integration_signals', v)
        labels = [s['label'] for s in v['integration_signals']]
        self.assertTrue(any('Atendimento' in l for l in labels))
