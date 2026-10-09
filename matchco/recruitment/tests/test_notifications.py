"""B2 — Notificações."""
from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from recruitment import notifications
from recruitment.domain_models import (
    RecruitmentOrganization, RecruitmentCompany, RecruitmentStore, RecruitmentJobFunction,
)
from recruitment.models import (
    AuthorityScope, CandidateProfile, EmployerActor, OpportunityCriterion,
    Position as Opportunity,
)
from recruitment.services import (
    deliver_opportunity_notice, employer_interested, enable_contact, person_interested,
)

User = get_user_model()


class MatchNotificationTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(external_id='ob', slug='ob', name='O')
        self.comp = RecruitmentCompany.objects.create(organization=self.org, name='C')
        self.store = RecruitmentStore.objects.create(organization=self.org, company=self.comp, name='L')
        self.func = RecruitmentJobFunction.objects.create(
            organization=self.org, company=self.comp, name='F',
        )
        self.cand = CandidateProfile.objects.create(
            organization=self.org, first_name='C', last_name='X',
            email='c@ex.com', phone='11900000000',
        )
        self.opp = Opportunity.objects.create(
            organization=self.org, business_unit=self.store, job_function=self.func,
            title='Vaga X', workplace='W', schedule='S',
            work_format=Opportunity.FORMAT_FIXO, starts_at=date(2026, 12, 1),
            tag=Opportunity.TAG_PRECISA, mode=Opportunity.MODE_MATCH,
            state=Opportunity.STATE_ACTIVATED, pre_interest_set_complete=True,
        )
        OpportunityCriterion.objects.create(
            opportunity=self.opp, label='X', weight=OpportunityCriterion.WEIGHT_REQUIRED,
        )
        self.user = User.objects.create_user(username='u', password='x', email='u@ex.com')
        EmployerActor.objects.create(
            user=self.user, organization=self.org, business_unit=self.store,
            authority_scopes=[
                AuthorityScope.AA7_DECLARE_EMPLOYER_INTEREST,
                AuthorityScope.AA8_RECEIVE_CONTACT_CHANNEL,
            ],
            human_verified_at=timezone.now(),
        )

    def test_match_triggers_notify_match(self):
        rel = deliver_opportunity_notice(candidate=self.cand, opportunity=self.opp)
        person_interested(relation=rel)
        with patch.object(notifications, '_send', return_value=True) as m:
            employer_interested(relation=rel, actor=self.user)
        # Chamado ao menos uma vez com subject "MATCH"
        subjects = [call.args[1] for call in m.call_args_list]
        self.assertTrue(any('MATCH' in s for s in subjects))

    def test_contact_enable_triggers_notify_contact(self):
        rel = deliver_opportunity_notice(candidate=self.cand, opportunity=self.opp)
        person_interested(relation=rel)
        employer_interested(relation=rel, actor=self.user)
        with patch.object(notifications, '_send', return_value=True) as m:
            enable_contact(relation=rel, actor=self.user)
        subjects = [call.args[1] for call in m.call_args_list]
        self.assertTrue(any('Contato liberado' in s for s in subjects))

    def test_notification_failure_never_breaks_flow(self):
        rel = deliver_opportunity_notice(candidate=self.cand, opportunity=self.opp)
        person_interested(relation=rel)
        with patch.object(notifications, '_send', side_effect=Exception('boom')):
            # Não pode lançar
            employer_interested(relation=rel, actor=self.user)
        rel.refresh_from_db()
        self.assertEqual(rel.state, 'matched')


class NotificationContentTests(TestCase):
    def test_notify_response_sla_composes_subject(self):
        with patch.object(notifications, '_send', return_value=True) as m:
            notifications.notify_response_sla_pending(
                employer_email='e@ex.com', count=3,
            )
        self.assertTrue(m.called)
        args = m.call_args.args
        self.assertIn('3', args[1])
