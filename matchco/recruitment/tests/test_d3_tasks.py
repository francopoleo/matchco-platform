"""D3 — jobs periódicos executam sem erro."""
from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone

from recruitment.domain_models import (
    RecruitmentCompany, RecruitmentJobFunction, RecruitmentOrganization, RecruitmentStore,
)
from recruitment.models import (
    CandidateProfile, FreshnessClass, OpportunityCriterion,
    Position as Opportunity, ProfileSignal,
)
try:
    from recruitment.tasks import (
        apply_retention_task, expire_pending_opportunities_task, mark_stale_signals_task,
    )
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False


import unittest


@unittest.skipUnless(CELERY_AVAILABLE, 'celery not installed in this environment')
class D3TaskTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(external_id='od', slug='od', name='O')
        self.comp = RecruitmentCompany.objects.create(organization=self.org, name='C')
        self.store = RecruitmentStore.objects.create(organization=self.org, company=self.comp, name='L')
        self.func = RecruitmentJobFunction.objects.create(organization=self.org, company=self.comp, name='F')

    def test_apply_retention_dry_run(self):
        report = apply_retention_task.apply(kwargs={'commit': False}).get()
        self.assertTrue(report['dry_run'])

    def test_expire_pending_opportunities(self):
        opp = Opportunity.objects.create(
            organization=self.org, business_unit=self.store, job_function=self.func,
            title='X', workplace='W', schedule='S', work_format=Opportunity.FORMAT_FIXO,
            starts_at=date(2026, 12, 1), tag=Opportunity.TAG_PRECISA,
            state=Opportunity.STATE_ACTIVATED, pre_interest_set_complete=True,
            active_until=date.today() - timedelta(days=1),
        )
        OpportunityCriterion.objects.create(
            opportunity=opp, label='X', weight=OpportunityCriterion.WEIGHT_REQUIRED,
        )
        n = expire_pending_opportunities_task.apply().get()
        self.assertEqual(n, 1)
        opp.refresh_from_db()
        self.assertEqual(opp.state, Opportunity.STATE_CLOSED)

    def test_mark_stale_signals_runs(self):
        prof = CandidateProfile.objects.create(
            organization=self.org, first_name='S', last_name='X',
            email='s@ex.com', phone='11900',
        )
        sig = ProfileSignal.objects.create(
            profile=prof, key='k', label='X',
            freshness_class=FreshnessClass.F2_HIGHLY_DYNAMIC,
            confirmed_at=timezone.now() - timedelta(days=31),
        )
        # Não levanta.
        result = mark_stale_signals_task.apply().get()
        self.assertGreaterEqual(result, 0)
