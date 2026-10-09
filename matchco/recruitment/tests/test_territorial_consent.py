"""Territorial sharing: QR is context; explicit consent authorizes scope."""

from django.test import TestCase

from recruitment.domain_models import (
    RecruitmentCompany, RecruitmentOrganization, RecruitmentStore,
)
from recruitment.models import CandidateConsent, CandidateIdentity, CandidateProfile, EntryPoint, Position
from recruitment.services import record_candidate_context
from recruitment.territory import has_territorial_consent


class TerritorialConsentTests(TestCase):
    def setUp(self):
        self.origin = RecruitmentOrganization.objects.create(
            external_id='territory-origin', slug='territory-origin', name='Origem',
        )
        self.target = RecruitmentOrganization.objects.create(
            external_id='territory-target', slug='territory-target', name='Destino',
        )
        origin_company = RecruitmentCompany.objects.create(organization=self.origin, name='Origem')
        target_company = RecruitmentCompany.objects.create(organization=self.target, name='Destino')
        self.origin_store = RecruitmentStore.objects.create(
            organization=self.origin, company=origin_company, name='Loja de origem',
            latitude=-23.55, longitude=-46.63,
        )
        self.target_store = RecruitmentStore.objects.create(
            organization=self.target, company=target_company, name='Loja de destino',
            latitude=-23.55, longitude=-46.63,
        )
        self.identity = CandidateIdentity.objects.create(email_normalized='territory@example.com')
        self.candidate = CandidateProfile.objects.create(
            organization=self.origin, identity=self.identity,
            first_name='Pessoa', email='territory@example.com',
            visibility_match=True,
        )
        self.qr = EntryPoint.objects.create(
            organization=self.origin, kind=EntryPoint.KIND_STORE,
            scope_store=self.origin_store, scope_shopping_id='territory-target',
            scope_network_id='territory-target', label='QR de origem',
            canonical_destination_url='https://matchco.test/qr/territory',
        )
        record_candidate_context(candidate=self.candidate, entry_point=self.qr)
        self.position_origin = Position.objects.create(
            organization=self.origin, business_unit=self.origin_store, title='Origem',
        )
        self.position_target = Position.objects.create(
            organization=self.target, business_unit=self.target_store, title='Destino',
        )

    def grant(self, purpose, *, source=None, organization=None):
        return CandidateConsent.objects.create(
            identity=self.identity, organization=organization or self.origin,
            purpose=purpose, granted=True, policy_version='territory-test',
            source=source or f'entry_point:{self.qr.pk}',
        )

    def test_store_consent_stays_at_scanned_physical_store(self):
        self.grant(CandidateConsent.PURPOSE_CIRCULATION_STORE)
        self.assertTrue(has_territorial_consent(
            candidate=self.candidate, position=self.position_origin,
        ))
        self.assertFalse(has_territorial_consent(
            candidate=self.candidate, position=self.position_target,
        ))

    def test_shopping_consent_allows_only_the_declared_shopping_scope(self):
        self.grant(CandidateConsent.PURPOSE_CIRCULATION_SHOPPING)
        from types import SimpleNamespace
        from unittest.mock import patch

        self.qr.scope_shopping_id = 'shopping-center'
        self.qr.save(update_fields=['scope_shopping_id'])
        self.target_store.legacy_id = 2468
        self.target_store.save(update_fields=['legacy_id'])
        with patch('configuration.models.BusinessUnit.objects.filter') as config_units:
            config_units.return_value.first.return_value = SimpleNamespace(shopping_name='Shopping Center')
            self.assertTrue(has_territorial_consent(
                candidate=self.candidate, position=self.position_target,
            ))
            unrelated = RecruitmentOrganization.objects.create(
                external_id='territory-other-shopping', slug='territory-other-shopping', name='Outro território',
            )
            company = RecruitmentCompany.objects.create(organization=unrelated, name='Outro território')
            store = RecruitmentStore.objects.create(organization=unrelated, company=company, name='Outra loja')
            position = Position.objects.create(organization=unrelated, business_unit=store, title='Outra loja')
        self.assertFalse(has_territorial_consent(
            candidate=self.candidate, position=position,
        ))

    def test_network_consent_does_not_authorize_an_unrelated_tenant(self):
        self.grant(CandidateConsent.PURPOSE_CIRCULATION_NETWORK)
        self.assertTrue(has_territorial_consent(
            candidate=self.candidate, position=self.position_target,
        ))
        unrelated = RecruitmentOrganization.objects.create(
            external_id='territory-unrelated', slug='territory-unrelated', name='Sem vínculo',
        )
        company = RecruitmentCompany.objects.create(organization=unrelated, name='Sem vínculo')
        store = RecruitmentStore.objects.create(organization=unrelated, company=company, name='Outra')
        position = Position.objects.create(organization=unrelated, business_unit=store, title='Outra')
        self.assertFalse(has_territorial_consent(candidate=self.candidate, position=position))

    def test_missing_context_wrong_source_and_revoked_consent_fail_closed(self):
        consent = self.grant(
            CandidateConsent.PURPOSE_CIRCULATION_NETWORK,
            source='old_unbound_signup',
        )
        self.assertFalse(has_territorial_consent(
            candidate=self.candidate, position=self.position_target,
        ))
        consent.source = f'entry_point:{self.qr.pk}'
        consent.granted = False
        consent.revoked_at = consent.granted_at
        consent.save(update_fields=['source', 'granted', 'revoked_at'])
        self.assertFalse(has_territorial_consent(
            candidate=self.candidate, position=self.position_target,
        ))

    def test_radius_requires_geocoded_points_and_respects_qr_limit(self):
        self.qr.geo_radius_m = 500
        self.qr.save(update_fields=['geo_radius_m'])
        self.grant(CandidateConsent.PURPOSE_CIRCULATION_RADIUS)
        self.assertFalse(has_territorial_consent(
            candidate=self.candidate, position=self.position_target,
        ))
        self.candidate.latitude = -23.55
        self.candidate.longitude = -46.63
        self.candidate.save(update_fields=['latitude', 'longitude'])
        self.assertTrue(has_territorial_consent(
            candidate=self.candidate, position=self.position_target,
        ))
        self.target_store.latitude = -23.60
        self.target_store.save(update_fields=['latitude'])
        self.assertFalse(has_territorial_consent(
            candidate=self.candidate, position=self.position_target,
        ))
