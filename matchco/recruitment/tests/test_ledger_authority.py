"""Fase 4 — Ledger append-only + EmployerActor AA-1..8."""
from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from recruitment.domain_models import (
    RecruitmentOrganization, RecruitmentCompany, RecruitmentStore, RecruitmentJobFunction,
)
from recruitment.models import (
    AuthorityError, AuthorityScope,
    CandidateProfile, EmployerActor,
    Ledger, LedgerAppendOnlyError,
    OpportunityCriterion,
    Position as Opportunity,
    Relation,
)
from recruitment.services import (
    deliver_opportunity_notice,
    employer_interested,
    enable_contact,
    ledger_record,
    person_interested,
)

User = get_user_model()


class LedgerAppendOnlyTests(TestCase):
    def test_create_ok(self):
        ev = ledger_record(Ledger.EVENT_PROFILE_CREATED, actor_type='system',
                           metadata={'k': 'v'})
        self.assertIsNotNone(ev.event_id)
        self.assertEqual(Ledger.objects.count(), 1)

    def test_update_via_save_blocked(self):
        ev = ledger_record(Ledger.EVENT_PROFILE_CREATED)
        ev.event_type = 'HACKED'
        with self.assertRaises(LedgerAppendOnlyError):
            ev.save()

    def test_queryset_update_blocked(self):
        ledger_record(Ledger.EVENT_PROFILE_CREATED)
        with self.assertRaises(LedgerAppendOnlyError):
            Ledger.objects.all().update(event_type='HACKED')

    def test_queryset_delete_blocked(self):
        ledger_record(Ledger.EVENT_PROFILE_CREATED)
        with self.assertRaises(LedgerAppendOnlyError):
            Ledger.objects.all().delete()

    def test_instance_delete_blocked(self):
        ev = ledger_record(Ledger.EVENT_PROFILE_CREATED)
        with self.assertRaises(LedgerAppendOnlyError):
            ev.delete()

    def test_correction_is_new_event(self):
        original = ledger_record(Ledger.EVENT_PROFILE_CREATED, metadata={'k': 'v1'})
        correction = ledger_record(Ledger.EVENT_CORRECTION,
                                    metadata={'corrects': str(original.event_id), 'new_k': 'v2'})
        self.assertNotEqual(original.event_id, correction.event_id)
        self.assertEqual(Ledger.objects.count(), 2)


class EmployerActorScopeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', password='x', email='u@ex.com')
        self.org = RecruitmentOrganization.objects.create(
            external_id='o', slug='o', name='O',
        )

    def test_has_scope_true_when_listed(self):
        actor = EmployerActor.objects.create(
            user=self.user, organization=self.org,
            authority_scopes=[AuthorityScope.AA1_DECLARE_NEED],
        )
        self.assertTrue(actor.has_scope(AuthorityScope.AA1_DECLARE_NEED))
        self.assertFalse(actor.has_scope(AuthorityScope.AA7_DECLARE_EMPLOYER_INTEREST))

    def test_aa7_requires_human_verified(self):
        actor = EmployerActor.objects.create(
            user=self.user, organization=self.org,
            authority_scopes=[AuthorityScope.AA7_DECLARE_EMPLOYER_INTEREST],
        )
        self.assertFalse(actor.has_scope(AuthorityScope.AA7_DECLARE_EMPLOYER_INTEREST))

        actor.human_verified_at = timezone.now()
        actor.save()
        self.assertTrue(actor.has_scope(AuthorityScope.AA7_DECLARE_EMPLOYER_INTEREST))

    def test_aa8_requires_human_verified(self):
        actor = EmployerActor.objects.create(
            user=self.user, organization=self.org,
            authority_scopes=[AuthorityScope.AA8_RECEIVE_CONTACT_CHANNEL],
        )
        self.assertFalse(actor.has_scope(AuthorityScope.AA8_RECEIVE_CONTACT_CHANNEL))
        actor.human_verified_at = timezone.now()
        actor.save()
        self.assertTrue(actor.has_scope(AuthorityScope.AA8_RECEIVE_CONTACT_CHANNEL))

    def test_inactive_actor_has_no_scope(self):
        actor = EmployerActor.objects.create(
            user=self.user, organization=self.org, active=False,
            authority_scopes=[AuthorityScope.AA1_DECLARE_NEED],
        )
        self.assertFalse(actor.has_scope(AuthorityScope.AA1_DECLARE_NEED))

    def test_require_scope_raises(self):
        actor = EmployerActor.objects.create(
            user=self.user, organization=self.org, authority_scopes=[],
        )
        with self.assertRaises(AuthorityError):
            actor.require_scope(AuthorityScope.AA1_DECLARE_NEED)


class LedgerIntegrationWithRelationTests(TestCase):
    """Fluxo completo grava eventos canônicos no Ledger."""

    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(external_id='o', slug='o', name='O')
        self.company = RecruitmentCompany.objects.create(organization=self.org, name='C')
        self.store = RecruitmentStore.objects.create(
            organization=self.org, company=self.company, name='L',
        )
        self.func = RecruitmentJobFunction.objects.create(
            organization=self.org, company=self.company, name='Rep',
        )
        self.candidate = CandidateProfile.objects.create(
            organization=self.org, first_name='A', last_name='B',
            email='a@ex.com', phone='11999',
        )
        self.opp = Opportunity.objects.create(
            organization=self.org, business_unit=self.store, job_function=self.func,
            title='X', workplace='W', schedule='S',
            work_format=Opportunity.FORMAT_FIXO, starts_at=date(2026, 12, 1),
            tag=Opportunity.TAG_PRECISA, state=Opportunity.STATE_ACTIVATED,
            pre_interest_set_complete=True,
        )
        OpportunityCriterion.objects.create(
            opportunity=self.opp, label='X', weight=OpportunityCriterion.WEIGHT_REQUIRED,
        )
        self.user = User.objects.create_user(username='u', password='x', email='u@ex.com')
        self.actor = EmployerActor.objects.create(
            user=self.user, organization=self.org, business_unit=self.store,
            authority_scopes=[
                AuthorityScope.AA7_DECLARE_EMPLOYER_INTEREST,
                AuthorityScope.AA8_RECEIVE_CONTACT_CHANNEL,
            ],
            human_verified_at=timezone.now(),
        )

    def test_full_flow_writes_ledger_events(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        person_interested(relation=rel)
        employer_interested(relation=rel, actor=self.user)
        enable_contact(relation=rel, actor=self.user)

        types = list(Ledger.objects.filter(relation=rel).values_list('event_type', flat=True))
        for expected in ('NOTICE_DELIVERED', 'PERSON_INTERESTED', 'EMPLOYER_INTERESTED',
                         'MATCHED', 'CONTACT_ENABLED'):
            self.assertIn(expected, types, f'Ledger missing {expected}')

    def test_authority_violation_logged(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        person_interested(relation=rel)
        # Novo user sem EmployerActor.
        rogue = User.objects.create_user(username='rogue', password='x', email='r@ex.com')
        with self.assertRaises(AuthorityError):
            employer_interested(relation=rel, actor=rogue)
        self.assertTrue(
            Ledger.objects.filter(event_type='AUTHORITY_VIOLATION', actor=rogue).exists()
        )

    def test_unverified_actor_denied_aa7(self):
        rel = deliver_opportunity_notice(candidate=self.candidate, opportunity=self.opp)
        person_interested(relation=rel)
        self.actor.human_verified_at = None
        self.actor.save()
        with self.assertRaises(AuthorityError):
            employer_interested(relation=rel, actor=self.user)