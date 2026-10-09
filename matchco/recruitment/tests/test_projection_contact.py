"""Fase 5 — EmployerInterestView (whitelist) + ContactChannel."""
from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from recruitment.domain_models import (
    RecruitmentOrganization, RecruitmentCompany, RecruitmentStore, RecruitmentJobFunction,
)
from recruitment.models import (
    AuthorityScope, CandidateProfile, ContactChannel, EmployerActor,
    OpportunityCriterion, Position as Opportunity, Relation,
)
from recruitment.projections import contact_view, employer_interest_view
from recruitment.services import (
    deliver_opportunity_notice, employer_interested, enable_contact, person_interested,
)

User = get_user_model()


class Setup:
    def _setup(self):
        self.org = RecruitmentOrganization.objects.create(external_id='o5', slug='o5', name='O5')
        self.company = RecruitmentCompany.objects.create(organization=self.org, name='C')
        self.store = RecruitmentStore.objects.create(organization=self.org, company=self.company, name='L')
        self.func = RecruitmentJobFunction.objects.create(organization=self.org, company=self.company, name='F')
        self.candidate = CandidateProfile.objects.create(
            organization=self.org, first_name='Bia', last_name='Souza',
            email='bia@ex.com', phone='11988887777',
            address='Rua Detalhada 500', city='São Paulo', state='SP',
            experience_years=3, availability_days=['mon', 'tue'],
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
        self.user = User.objects.create_user(username='u5', password='x', email='u5@ex.com')
        self.actor = EmployerActor.objects.create(
            user=self.user, organization=self.org, business_unit=self.store,
            authority_scopes=[
                AuthorityScope.AA6_VIEW_EMPLOYER_INTEREST_VIEW,
                AuthorityScope.AA7_DECLARE_EMPLOYER_INTEREST,
                AuthorityScope.AA8_RECEIVE_CONTACT_CHANNEL,
            ],
            human_verified_at=timezone.now(),
        )


class EmployerInterestViewProjectionTests(Setup, TestCase):
    def setUp(self):
        self._setup()

    def test_returns_none_before_person_interested(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        self.assertIsNone(employer_interest_view(rel))

    def test_returns_whitelist_after_person_interested(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        person_interested(relation=rel)
        v = employer_interest_view(rel)
        self.assertIn('first_name', v)
        self.assertIn('experience_years', v)
        self.assertEqual(v['first_name'], 'Bia')

    def test_never_leaks_forbidden_fields(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        person_interested(relation=rel)
        v = employer_interest_view(rel)
        for forbidden in ('phone', 'email', 'address', 'salary_expectation',
                          'resume_text', 'linkedin_url', 'score', 'overall_score'):
            self.assertNotIn(forbidden, v, f'Vazamento: {forbidden}')


class ContactViewGatingTests(Setup, TestCase):
    def setUp(self):
        self._setup()

    def test_returns_none_before_contact_enabled(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        person_interested(relation=rel)
        employer_interested(relation=rel, actor=self.user)
        # MATCHED, mas ainda não CONTACT_ENABLED.
        self.assertIsNone(contact_view(rel))

    def test_returns_contact_after_enable(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        person_interested(relation=rel)
        employer_interested(relation=rel, actor=self.user)
        enable_contact(relation=rel, actor=self.user)
        v = contact_view(rel)
        self.assertEqual(v['candidate_mobile'], '11988887777')

    def test_contact_channel_materialized(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        person_interested(relation=rel)
        employer_interested(relation=rel, actor=self.user)
        enable_contact(relation=rel, actor=self.user)
        cc = ContactChannel.objects.get(relation=rel)
        self.assertEqual(cc.candidate_mobile, '11988887777')
        self.assertEqual(cc.released_to_actor, self.user)

    def test_enable_contact_idempotent(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        person_interested(relation=rel)
        employer_interested(relation=rel, actor=self.user)
        enable_contact(relation=rel, actor=self.user)
        self.assertEqual(ContactChannel.objects.filter(relation=rel).count(), 1)