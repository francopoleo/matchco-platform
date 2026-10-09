"""D1 — Métricas do funil."""
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from recruitment.domain_models import (
    RecruitmentCompany, RecruitmentJobFunction, RecruitmentOrganization, RecruitmentStore,
)
from recruitment.metrics import (
    avg_time_match_to_response, avg_time_person_to_match, dashboard, funnel_counts,
    ledger_alerts, rights_case_summary,
)
from recruitment.models import (
    AuthorityScope, CandidateProfile, EmployerActor, OpportunityCriterion,
    Position as Opportunity, Relation, RightsCase,
)
from recruitment.services import (
    create_response, deliver_opportunity_notice, employer_interested, enable_contact,
    open_rights_case, person_interested,
)

User = get_user_model()


class MetricsTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(external_id='om', slug='om', name='O')
        self.comp = RecruitmentCompany.objects.create(organization=self.org, name='C')
        self.store = RecruitmentStore.objects.create(organization=self.org, company=self.comp, name='L')
        self.func = RecruitmentJobFunction.objects.create(organization=self.org, company=self.comp, name='F')
        self.cand = CandidateProfile.objects.create(
            organization=self.org, first_name='M', last_name='X',
            email='m@ex.com', phone='11900',
        )
        self.opp = Opportunity.objects.create(
            organization=self.org, business_unit=self.store, job_function=self.func,
            title='T', workplace='W', schedule='S', work_format=Opportunity.FORMAT_FIXO,
            starts_at=date(2026, 12, 1), tag=Opportunity.TAG_PRECISA,
            state=Opportunity.STATE_ACTIVATED, pre_interest_set_complete=True,
        )
        OpportunityCriterion.objects.create(
            opportunity=self.opp, label='X', weight=OpportunityCriterion.WEIGHT_REQUIRED,
        )
        self.user = User.objects.create_user(username='u', password='x', email='u@ex.com')
        EmployerActor.objects.create(
            user=self.user, organization=self.org, business_unit=self.store,
            authority_scopes=AuthorityScope.ALL,
            human_verified_at=timezone.now(),
        )

    def test_funnel_counts_zero_by_default(self):
        rows = funnel_counts(organization=self.org)
        self.assertEqual(sum(r['count'] for r in rows), 0)

    def test_funnel_increments_across_states(self):
        rel = deliver_opportunity_notice(candidate=self.cand, opportunity=self.opp)
        person_interested(relation=rel)
        rows = {r['state']: r['count'] for r in funnel_counts(organization=self.org)}
        self.assertEqual(rows[Relation.STATE_EMPLOYER_INTEREST_VIEW], 1)

    def test_avg_person_to_match_none_before_match(self):
        rel = deliver_opportunity_notice(candidate=self.cand, opportunity=self.opp)
        person_interested(relation=rel)
        self.assertIsNone(avg_time_person_to_match(organization=self.org))

    def test_avg_person_to_match_computed_after_match(self):
        rel = deliver_opportunity_notice(candidate=self.cand, opportunity=self.opp)
        person_interested(relation=rel)
        employer_interested(relation=rel, actor=self.user)
        avg = avg_time_person_to_match(organization=self.org)
        self.assertIsNotNone(avg)
        self.assertGreaterEqual(avg, 0)

    def test_avg_match_to_response_full_flow(self):
        rel = deliver_opportunity_notice(candidate=self.cand, opportunity=self.opp)
        person_interested(relation=rel)
        employer_interested(relation=rel, actor=self.user)
        enable_contact(relation=rel, actor=self.user)
        create_response(relation=rel, actor=self.user, response_class='RC-01')
        avg = avg_time_match_to_response(organization=self.org)
        self.assertIsNotNone(avg)

    def test_rights_case_summary_counts_open(self):
        open_rights_case(requester_email='a@ex.com', request_type=RightsCase.TYPE_ACCESS)
        open_rights_case(requester_email='b@ex.com', request_type=RightsCase.TYPE_DELETION)
        s = rights_case_summary()
        self.assertEqual(s['total'], 2)
        self.assertEqual(s['open'], 2)
        self.assertIn(RightsCase.TYPE_ACCESS, s['by_type'])

    def test_ledger_alerts_zero_by_default(self):
        a = ledger_alerts()
        self.assertEqual(a['authority_violations'], 0)

    def test_dashboard_composes_all_sections(self):
        d = dashboard(organization=self.org)
        for k in ('funnel', 'rights_cases', 'ledger_alerts',
                  'avg_person_to_match_human', 'avg_match_to_response_human'):
            self.assertIn(k, d)
