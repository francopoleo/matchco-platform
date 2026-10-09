"""Fase 7 — Response RC-01..05 obrigatório no encerramento."""
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from recruitment.domain_models import (
    RecruitmentOrganization, RecruitmentCompany, RecruitmentStore, RecruitmentJobFunction,
)
from recruitment.models import (
    AuthorityScope, CandidateProfile, EmployerActor, OpportunityCriterion,
    Position as Opportunity, Relation, Response, ResponseClass, ResponseValidationError,
)
from recruitment.services import (
    can_declare_new_opportunity, create_response, deliver_opportunity_notice,
    employer_interested, enable_contact, pending_response_relations, person_interested,
)

User = get_user_model()


class Setup:
    def _setup(self):
        self.org = RecruitmentOrganization.objects.create(external_id='o7', slug='o7', name='O7')
        self.company = RecruitmentCompany.objects.create(organization=self.org, name='C')
        self.store = RecruitmentStore.objects.create(organization=self.org, company=self.company, name='L')
        self.func = RecruitmentJobFunction.objects.create(organization=self.org, company=self.company, name='F')
        self.candidate = CandidateProfile.objects.create(
            organization=self.org, first_name='C', last_name='X',
            email='c@ex.com', phone='11900000000',
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
        self.user = User.objects.create_user(username='u7', password='x', email='u7@ex.com')
        self.actor = EmployerActor.objects.create(
            user=self.user, organization=self.org, business_unit=self.store,
            authority_scopes=[
                AuthorityScope.AA5_CLOSE_OPPORTUNITY,
                AuthorityScope.AA7_DECLARE_EMPLOYER_INTEREST,
                AuthorityScope.AA8_RECEIVE_CONTACT_CHANNEL,
            ],
            human_verified_at=timezone.now(),
        )

    def _matched(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        person_interested(relation=rel)
        employer_interested(relation=rel, actor=self.user)
        enable_contact(relation=rel, actor=self.user)
        rel.refresh_from_db()
        return rel


class ResponseValidationTests(Setup, TestCase):
    def setUp(self):
        self._setup()

    def test_rc01_accepted(self):
        rel = self._matched()
        resp = create_response(relation=rel, actor=self.user, response_class='RC-01')
        rel.refresh_from_db()
        self.assertEqual(rel.state, Relation.STATE_CLOSED)
        self.assertEqual(resp.response_class, 'RC-01')

    def test_rc05_requires_note(self):
        rel = self._matched()
        with self.assertRaises(ResponseValidationError):
            create_response(relation=rel, actor=self.user, response_class='RC-05', note='')

    def test_rc05_with_note_ok(self):
        rel = self._matched()
        resp = create_response(
            relation=rel, actor=self.user,
            response_class='RC-05', note='Reestruturamos a área',
        )
        self.assertEqual(resp.note, 'Reestruturamos a área')

    def test_invalid_class_rejected(self):
        rel = self._matched()
        with self.assertRaises(ResponseValidationError):
            create_response(relation=rel, actor=self.user, response_class='RC-99')

    def test_response_creates_row_and_closes_relation(self):
        rel = self._matched()
        create_response(relation=rel, actor=self.user, response_class='RC-02')
        self.assertTrue(Response.objects.filter(relation=rel).exists())
        rel.refresh_from_db()
        self.assertTrue(rel.is_terminal())


class SlaGatingTests(Setup, TestCase):
    def setUp(self):
        self._setup()

    def test_can_declare_new_when_no_pending(self):
        self.assertTrue(can_declare_new_opportunity(organization=self.org))

    def test_pending_relations_block_new_declaration(self):
        rel = self._matched()
        # Simula MATCHED antigo (> SLA).
        Relation.objects.filter(pk=rel.pk).update(
            matched_at=timezone.now() - timedelta(days=30),
        )
        self.assertFalse(can_declare_new_opportunity(organization=self.org))
        self.assertEqual(pending_response_relations(organization=self.org).count(), 1)

    def test_response_removes_from_pending(self):
        rel = self._matched()
        Relation.objects.filter(pk=rel.pk).update(
            matched_at=timezone.now() - timedelta(days=30),
        )
        rel.refresh_from_db()
        create_response(relation=rel, actor=self.user, response_class='RC-01')
        self.assertTrue(can_declare_new_opportunity(organization=self.org))
