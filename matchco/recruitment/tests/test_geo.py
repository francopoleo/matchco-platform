"""C2 — Geografia real (haversine + feed com distância)."""
from datetime import date
from django.test import TestCase

from recruitment.domain_models import (
    RecruitmentCompany, RecruitmentJobFunction, RecruitmentOrganization, RecruitmentStore,
)
from recruitment.feed import build_feed
from recruitment.geo import distance_candidate_to_store, haversine_km
from recruitment.models import (
    CandidateConsent, CandidateIdentity, CandidateProfile, CanonicalCatalog,
    CanonicalFunctionMapping, CanonicalTerm,
    EntryPoint, OpportunityCriterion, Position as Opportunity,
)
from recruitment.services import record_candidate_context


class HaversineTests(TestCase):
    def test_same_point_zero(self):
        self.assertAlmostEqual(haversine_km(-23.5, -46.6, -23.5, -46.6), 0.0, places=3)

    def test_known_distance_sp_rj(self):
        # São Paulo ↔ Rio de Janeiro ≈ 360 km
        d = haversine_km(-23.55, -46.63, -22.90, -43.20)
        self.assertGreater(d, 350)
        self.assertLess(d, 380)

    def test_missing_coord_returns_none(self):
        self.assertIsNone(haversine_km(None, None, -22.9, -43.2))


class FeedDistanceTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(external_id='og', slug='og', name='O')
        self.comp = RecruitmentCompany.objects.create(organization=self.org, name='C')
        self.func = RecruitmentJobFunction.objects.create(organization=self.org, company=self.comp, name='F')
        catalog = CanonicalCatalog.objects.create(code='geo-catalog', name='Geo', version=1, status=CanonicalCatalog.STATUS_PUBLISHED)
        term = CanonicalTerm.objects.create(catalog=catalog, term_type=CanonicalTerm.TYPE_FUNCTION, code='geo-f', label='F', normalized_label='f')
        CanonicalFunctionMapping.objects.create(term=term, job_function=self.func, organization=self.org)

        # Loja perto (500m) e loja longe (10 km)
        self.store_near = RecruitmentStore.objects.create(
            organization=self.org, company=self.comp, name='Perto',
            latitude=-23.560, longitude=-46.650,
        )
        self.store_far = RecruitmentStore.objects.create(
            organization=self.org, company=self.comp, name='Longe',
            latitude=-23.650, longitude=-46.650,
        )

        # Candidato
        self.identity = CandidateIdentity.objects.create(email_normalized='g@ex.com')
        self.cand = CandidateProfile.objects.create(
            organization=self.org, identity=self.identity,
            first_name='G', last_name='X', email='g@ex.com', phone='11900',
            latitude=-23.560, longitude=-46.650,
            preferred_work_format=Opportunity.FORMAT_FIXO,
            available_from=date(2026, 1, 1),
        )
        self.cand.job_functions.add(self.func)
        self.entry_point = EntryPoint.objects.create(
            organization=self.org, kind=EntryPoint.KIND_STORE,
            scope_store=self.store_near, geo_radius_m=5000,
            label='QR loja perto',
            canonical_destination_url='https://matchco.test/qr/near',
        )
        record_candidate_context(candidate=self.cand, entry_point=self.entry_point)
        for p in (CandidateConsent.PURPOSE_CIRCULATION_STORE,
                  CandidateConsent.PURPOSE_CIRCULATION_RADIUS):
            CandidateConsent.objects.create(
                identity=self.identity, organization=self.org,
                purpose=p, granted=True, policy_version='v1',
                source=f'entry_point:{self.entry_point.pk}',
            )

    def _opp(self, store):
        opp = Opportunity.objects.create(
            organization=self.org, business_unit=store, job_function=self.func,
            title=f'Opp {store.name}', workplace='W', schedule='S',
            work_format=Opportunity.FORMAT_FIXO, starts_at=date(2026, 12, 1),
            tag=Opportunity.TAG_PRECISA, mode=Opportunity.MODE_MATCH,
            state=Opportunity.STATE_ACTIVATED, pre_interest_set_complete=True,
        )
        OpportunityCriterion.objects.create(
            opportunity=opp, label='X', weight=OpportunityCriterion.WEIGHT_REQUIRED,
        )
        return opp

    def test_distance_exposed_in_feed(self):
        self._opp(self.store_near)
        items = build_feed(self.cand)
        self.assertIsNotNone(items[0]['distance_km'])
        self.assertLess(items[0]['distance_km'], 1)

    def test_nearer_store_ranks_higher(self):
        self._opp(self.store_far)
        self._opp(self.store_near)
        items = build_feed(self.cand)
        self.assertEqual(items[0]['title'], 'Opp Perto')

    def test_radius_only_consent_filters_far_store(self):
        # Retira STORE e SHOPPING, deixa só RADIUS (5km default)
        CandidateConsent.objects.filter(identity=self.identity).exclude(
            purpose=CandidateConsent.PURPOSE_CIRCULATION_RADIUS,
        ).delete()
        self._opp(self.store_far)  # ~10 km
        self._opp(self.store_near)
        titles = [i['title'] for i in build_feed(self.cand)]
        self.assertIn('Opp Perto', titles)
        self.assertNotIn('Opp Longe', titles)

    def test_distance_helper_direct(self):
        d = distance_candidate_to_store(self.cand, self.store_near)
        self.assertLess(d, 1)
