"""Fase 3 — Relation + máquina de estados bilateral."""
from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase

from recruitment.domain_models import (
    RecruitmentOrganization, RecruitmentCompany, RecruitmentStore, RecruitmentJobFunction,
)
from django.utils import timezone

from recruitment.models import (
    AuthorityError,
    AuthorityScope,
    CandidateProfile,
    EmployerActor,
    OpportunityCriterion,
    Position as Opportunity,
    Relation,
    RelationStateError,
    RelationTransitionEvent,
)
from recruitment.services import (
    candidate_declined,
    create_response,
    deliver_opportunity_notice,
    employer_declined,
    employer_interested,
    enable_contact,
    person_interested,
)

User = get_user_model()


class RelationSetupMixin:
    def _setup(self):
        self.org = RecruitmentOrganization.objects.create(
            external_id='org-r', slug='org-r', name='Org R',
        )
        self.company = RecruitmentCompany.objects.create(
            organization=self.org, name='C',
        )
        self.store = RecruitmentStore.objects.create(
            organization=self.org, company=self.company, name='Loja',
        )
        self.func = RecruitmentJobFunction.objects.create(
            organization=self.org, company=self.company, name='Repositor',
        )
        self.candidate = CandidateProfile.objects.create(
            organization=self.org,
            first_name='Ana', last_name='Silva',
            email='ana@ex.com', phone='11999999999',
        )
        self.opp = Opportunity.objects.create(
            organization=self.org,
            business_unit=self.store,
            job_function=self.func,
            title='Repositor',
            workplace='Loja Piso 1',
            schedule='Seg-sáb, 12h-20h',
            work_format=Opportunity.FORMAT_FIXO,
            starts_at=date(2026, 11, 1),
            tag=Opportunity.TAG_PRECISA,
            state=Opportunity.STATE_ACTIVATED,
            pre_interest_set_complete=True,
        )
        OpportunityCriterion.objects.create(
            opportunity=self.opp, label='Ficar em pé', weight=OpportunityCriterion.WEIGHT_REQUIRED,
        )
        self.employer_user = User.objects.create_user(
            username='gerente', password='x', email='ger@ex.com',
        )
        self.employer_actor = EmployerActor.objects.create(
            user=self.employer_user,
            organization=self.org,
            business_unit=self.store,
            authority_scopes=[
                AuthorityScope.AA6_VIEW_EMPLOYER_INTEREST_VIEW,
                AuthorityScope.AA7_DECLARE_EMPLOYER_INTEREST,
                AuthorityScope.AA8_RECEIVE_CONTACT_CHANNEL,
            ],
            human_verified_at=timezone.now(),
        )


class RelationStateMachineTests(RelationSetupMixin, TestCase):
    def setUp(self):
        self._setup()

    def test_notice_creates_relation_at_initial_state(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        self.assertEqual(rel.state, Relation.STATE_NOTICE_DELIVERED)
        self.assertEqual(rel.opportunity_version, self.opp.version)

    def test_notice_is_idempotent(self):
        r1 = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        r2 = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        self.assertEqual(r1.pk, r2.pk)

    def test_full_happy_path_to_matched(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        person_interested(relation=rel)
        rel.refresh_from_db()
        self.assertEqual(rel.state, Relation.STATE_EMPLOYER_INTEREST_VIEW)

        employer_interested(relation=rel, actor=self.employer_user)
        rel.refresh_from_db()
        self.assertEqual(rel.state, Relation.STATE_MATCHED)
        self.assertIsNotNone(rel.matched_at)

        enable_contact(relation=rel, actor=self.employer_user)
        rel.refresh_from_db()
        self.assertEqual(rel.state, Relation.STATE_CONTACT_ENABLED)

        create_response(relation=rel, actor=self.employer_user, response_class='RC-01')
        rel.refresh_from_db()
        self.assertEqual(rel.state, Relation.STATE_CLOSED)
        self.assertTrue(rel.is_terminal())

    def test_invalid_transition_raises(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        with self.assertRaises(RelationStateError):
            rel.transition(Relation.STATE_MATCHED)

    def test_person_interested_blocked_when_pre_interest_incomplete(self):
        self.opp.pre_interest_set_complete = False
        self.opp.save()
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        with self.assertRaises(RelationStateError):
            person_interested(relation=rel)

    def test_person_interested_blocked_when_version_changed(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        # Simula bump de versão pós-notice.
        Opportunity.objects.filter(pk=self.opp.pk).update(version=self.opp.version + 1)
        rel.opportunity.refresh_from_db()
        with self.assertRaises(RelationStateError):
            person_interested(relation=rel)

    def test_employer_interested_requires_actor(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        person_interested(relation=rel)
        with self.assertRaises(AuthorityError):
            employer_interested(relation=rel, actor=None)

    def test_employer_declined_reaches_terminal_state(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        person_interested(relation=rel)
        employer_declined(relation=rel, actor=self.employer_user, reason='Vaga adiada')
        rel.refresh_from_db()
        self.assertEqual(rel.state, Relation.STATE_NO_EMPLOYER_INTEREST)
        self.assertTrue(rel.is_terminal())

    def test_candidate_declined_terminates(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        candidate_declined(relation=rel)
        rel.refresh_from_db()
        self.assertEqual(rel.state, Relation.STATE_DECLINED)
        self.assertTrue(rel.is_terminal())

    def test_contact_before_matched_is_forbidden(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        person_interested(relation=rel)
        with self.assertRaises(RelationStateError):
            enable_contact(relation=rel, actor=self.employer_user)

    def test_uniqueness_by_candidate_opp_version(self):
        from django.db import IntegrityError
        Relation.objects.create(
            candidate=self.candidate, opportunity=self.opp,
            opportunity_version=self.opp.version,
        )
        with self.assertRaises(IntegrityError):
            Relation.objects.create(
                candidate=self.candidate, opportunity=self.opp,
                opportunity_version=self.opp.version,
            )


class RelationTransitionEventTests(RelationSetupMixin, TestCase):
    def setUp(self):
        self._setup()

    def test_events_logged_for_each_transition(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        person_interested(relation=rel)
        employer_interested(relation=rel, actor=self.employer_user)

        events = list(RelationTransitionEvent.objects.filter(relation=rel).order_by('occurred_at'))
        to_states = [e.to_state for e in events]
        self.assertIn(Relation.STATE_NOTICE_DELIVERED, to_states)
        self.assertIn(Relation.STATE_PERSON_INTERESTED, to_states)
        self.assertIn(Relation.STATE_EMPLOYER_INTEREST_VIEW, to_states)
        self.assertIn(Relation.STATE_EMPLOYER_INTERESTED, to_states)
        self.assertIn(Relation.STATE_MATCHED, to_states)

    def test_employer_transition_records_authority_scope(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        person_interested(relation=rel)
        employer_interested(relation=rel, actor=self.employer_user)
        e = RelationTransitionEvent.objects.get(
            relation=rel, to_state=Relation.STATE_EMPLOYER_INTERESTED
        )
        self.assertEqual(e.authority_scope, 'AA-7')
        self.assertEqual(e.actor_type, 'employer_actor')

    def test_contact_enable_records_aa8(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        person_interested(relation=rel)
        employer_interested(relation=rel, actor=self.employer_user)
        enable_contact(relation=rel, actor=self.employer_user)
        e = RelationTransitionEvent.objects.get(
            relation=rel, to_state=Relation.STATE_CONTACT_ENABLED
        )
        self.assertEqual(e.authority_scope, 'AA-8')