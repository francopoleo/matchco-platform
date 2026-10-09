"""Fase 8 — Feed territorial + freshness F0/F1/F2 + circulation state."""
from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone

from recruitment.domain_models import (
    RecruitmentOrganization, RecruitmentCompany, RecruitmentStore, RecruitmentJobFunction,
)
from recruitment.feed import build_feed
from recruitment.models import (
    CandidateConsent, CandidateIdentity, CandidateProfile, CanonicalCatalog,
    CanonicalFunctionMapping, CanonicalTerm, EntryPoint,
    FreshnessClass, OpportunityCriterion, Position as Opportunity,
    ProfileSignal, SignalOrigin,
)
from recruitment.services import record_candidate_context


class FreshnessTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(external_id='o8', slug='o8', name='O8')
        self.profile = CandidateProfile.objects.create(
            organization=self.org, first_name='F', last_name='X',
            email='f@ex.com', phone='11900001111',
        )

    def test_f0_never_stale(self):
        s = ProfileSignal.objects.create(
            profile=self.profile, key='experience_atendimento',
            freshness_class=FreshnessClass.F0_DURABLE,
            confirmed_at=timezone.now() - timedelta(days=365),
        )
        self.assertFalse(s.is_stale())
        self.assertIsNone(s.expires_at)

    def test_f1_stales_after_90_days(self):
        s = ProfileSignal.objects.create(
            profile=self.profile, key='availability',
            freshness_class=FreshnessClass.F1_DYNAMIC,
            confirmed_at=timezone.now() - timedelta(days=91),
        )
        self.assertTrue(s.is_stale())

    def test_f1_not_stale_before_90_days(self):
        s = ProfileSignal.objects.create(
            profile=self.profile, key='availability',
            freshness_class=FreshnessClass.F1_DYNAMIC,
            confirmed_at=timezone.now() - timedelta(days=30),
        )
        self.assertFalse(s.is_stale())

    def test_f2_stales_after_30_days(self):
        s = ProfileSignal.objects.create(
            profile=self.profile, key='start_available',
            freshness_class=FreshnessClass.F2_HIGHLY_DYNAMIC,
            confirmed_at=timezone.now() - timedelta(days=31),
        )
        self.assertTrue(s.is_stale())

    def test_expires_at_computed_on_save(self):
        s = ProfileSignal.objects.create(
            profile=self.profile, key='k',
            freshness_class=FreshnessClass.F2_HIGHLY_DYNAMIC,
        )
        self.assertIsNotNone(s.expires_at)
        self.assertLess(s.expires_at - s.confirmed_at, timedelta(days=31))


class FeedTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(external_id='o8f', slug='o8f', name='O')
        self.comp = RecruitmentCompany.objects.create(organization=self.org, name='C')
        self.store_a = RecruitmentStore.objects.create(organization=self.org, company=self.comp, name='A')
        self.store_b = RecruitmentStore.objects.create(organization=self.org, company=self.comp, name='B')
        self.func = RecruitmentJobFunction.objects.create(
            organization=self.org, company=self.comp, name='F',
        )
        catalog = CanonicalCatalog.objects.create(
            code='feed-catalog', name='Feed', version=1,
            status=CanonicalCatalog.STATUS_PUBLISHED,
        )
        term = CanonicalTerm.objects.create(
            catalog=catalog, term_type=CanonicalTerm.TYPE_FUNCTION,
            code='feed-f', label='F', normalized_label='f',
        )
        CanonicalFunctionMapping.objects.create(
            term=term, job_function=self.func, organization=self.org,
        )
        self.identity = CandidateIdentity.objects.create(email_normalized='cand@ex.com')
        self.cand = CandidateProfile.objects.create(
            organization=self.org, identity=self.identity,
            first_name='C', last_name='X',
            email='cand@ex.com', phone='11900001111',
        )
        self.cand.job_functions.add(self.func)
        self.entry_point = EntryPoint.objects.create(
            organization=self.org, kind=EntryPoint.KIND_STORE,
            scope_store=self.store_a, label='QR loja A',
            canonical_destination_url='https://matchco.test/qr/store-a',
        )
        record_candidate_context(candidate=self.cand, entry_point=self.entry_point)
        CandidateConsent.objects.create(
            identity=self.identity, organization=self.org,
            purpose=CandidateConsent.PURPOSE_CIRCULATION_STORE,
            granted=True, policy_version='v1',
            source=f'entry_point:{self.entry_point.pk}',
        )

    def _make_opp(self, store, **kwargs):
        defaults = dict(
            organization=self.org, business_unit=store, job_function=self.func,
            title=f'Opp {store.name}', workplace='W', schedule='S',
            work_format=Opportunity.FORMAT_FIXO, starts_at=date(2026, 12, 1),
            tag=Opportunity.TAG_PRECISA, mode=Opportunity.MODE_MATCH,
            state=Opportunity.STATE_ACTIVATED, pre_interest_set_complete=True,
        )
        defaults.update(kwargs)
        opp = Opportunity.objects.create(**defaults)
        OpportunityCriterion.objects.create(
            opportunity=opp, label='X', weight=OpportunityCriterion.WEIGHT_REQUIRED,
        )
        return opp

    def test_paused_candidate_gets_empty_feed(self):
        self._make_opp(self.store_a)
        self.cand.circulation_state = CandidateProfile.CIRCULATION_PAUSED
        self.cand.save()
        self.assertEqual(build_feed(self.cand), [])

    def test_only_match_mode_is_considered(self):
        self._make_opp(self.store_a, mode=Opportunity.MODE_MATCH)
        self._make_opp(self.store_b, mode=Opportunity.MODE_MATCH)
        feed = build_feed(self.cand)
        titles = [i['title'] for i in feed]
        self.assertNotIn(f'Opp {self.store_b.name}', titles)

    def test_incomplete_pre_interest_excluded(self):
        self._make_opp(self.store_a, pre_interest_set_complete=False)
        self.assertEqual(build_feed(self.cand), [])

    def test_feed_returns_no_score_field(self):
        self._make_opp(self.store_a)
        feed = build_feed(self.cand)
        for item in feed:
            for forbidden in ('score', 'match_score', 'ranking', '_weight'):
                self.assertNotIn(forbidden, item)

    def test_consent_denial_excludes_opportunity(self):
        CandidateConsent.objects.filter(identity=self.identity).update(
            granted=False, revoked_at=timezone.now(),
        )
        self._make_opp(self.store_a)
        feed = build_feed(self.cand, entry_point=self.entry_point)
        titles = [i['title'] for i in feed]
        self.assertNotIn(f'Opp {self.store_a.name}', titles)
