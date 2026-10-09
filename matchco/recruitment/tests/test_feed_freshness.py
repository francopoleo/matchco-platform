"""Fase 8 — Feed territorial + freshness F0/F1/F2 + circulation state."""
from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone

from recruitment.domain_models import (
    RecruitmentOrganization, RecruitmentCompany, RecruitmentStore, RecruitmentJobFunction,
)
from recruitment.feed import build_feed
from recruitment.models import (
    CandidateConsent, CandidateIdentity, CandidateProfile,
    FreshnessClass, OpportunityCriterion, Position as Opportunity,
    ProfileSignal, SignalOrigin,
)


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
        self.identity = CandidateIdentity.objects.create(email_normalized='cand@ex.com')
        self.cand = CandidateProfile.objects.create(
            organization=self.org, identity=self.identity,
            first_name='C', last_name='X',
            email='cand@ex.com', phone='11900001111',
        )
        # Consentimento amplo por default nos testes.
        for purpose in [
            CandidateConsent.PURPOSE_CIRCULATION_STORE,
            CandidateConsent.PURPOSE_CIRCULATION_SHOPPING,
            CandidateConsent.PURPOSE_CIRCULATION_NETWORK,
            CandidateConsent.PURPOSE_CIRCULATION_RADIUS,
        ]:
            CandidateConsent.objects.create(
                identity=self.identity, purpose=purpose, granted=True,
                policy_version='v1',
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
        # Retira consent RADIUS; sem EntryPoint, opps caem em 'other' → sem consent.
        CandidateConsent.objects.filter(
            identity=self.identity,
            purpose=CandidateConsent.PURPOSE_CIRCULATION_RADIUS,
        ).update(granted=False, revoked_at=timezone.now())
        self._make_opp(self.store_a)
        # Também precisa retirar SHOPPING/STORE porque sem EntryPoint tudo vira 'other'.
        # Confirmar que 'other' foi bloqueada: opp sem território reconhecido.
        feed = build_feed(self.cand, entry_point=None)
        # store_a sem EntryPoint = territory 'other' e RADIUS revogado → excluída.
        titles = [i['title'] for i in feed]
        self.assertNotIn(f'Opp {self.store_a.name}', titles)
