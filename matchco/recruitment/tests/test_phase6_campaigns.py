"""Fase 6 — cobertura insuficiente e campanhas sem ranking."""

from django.test import TestCase

from recruitment.domain_models import RecruitmentCompany, RecruitmentJobFunction, RecruitmentOrganization, RecruitmentStore
from recruitment.models import (
    CandidateConsent, CandidateIdentity, CandidateProfile, CanonicalCatalog,
    CanonicalFunctionMapping, CanonicalTerm, EntryPoint,
    CoverageGap, EnrichmentCampaign, EnrichmentInvite, Position,
)
from recruitment.services import (
    change_enrichment_campaign_status, create_enrichment_invite,
    evaluate_coverage_gap, record_enrichment_response, record_candidate_context,
)


class CoverageCampaignTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(
            external_id='phase-6-org', slug='phase-6-org', name='Phase 6',
        )
        company = RecruitmentCompany.objects.create(organization=self.org, name='Rede')
        store = RecruitmentStore.objects.create(
            organization=self.org, company=company, name='Unidade',
        )
        function = RecruitmentJobFunction.objects.create(
            organization=self.org, company=company, name='Atendente',
        )
        catalog = CanonicalCatalog.objects.create(code='phase-6-catalog', name='Varejo', version=1, status=CanonicalCatalog.STATUS_PUBLISHED)
        term = CanonicalTerm.objects.create(catalog=catalog, term_type=CanonicalTerm.TYPE_FUNCTION, code='atendente', label='Atendente', normalized_label='atendente')
        CanonicalFunctionMapping.objects.create(term=term, job_function=function, organization=self.org)
        self.position = Position.objects.create(
            organization=self.org, business_unit=store, job_function=function,
            title='Atendente', mode=Position.MODE_MATCH,
        )
        self.candidate = CandidateProfile.objects.create(
            organization=self.org, first_name='Ana', email='phase6@example.com',
            visibility_match=True,
        )
        self.candidate.job_functions.add(function)
        identity = CandidateIdentity.objects.create(email_normalized='phase6@example.com')
        self.candidate.identity = identity
        self.candidate.save(update_fields=['identity', 'updated_at'])
        qr = EntryPoint.objects.create(
            organization=self.org, kind=EntryPoint.KIND_STORE,
            scope_store=store, label='QR fase 6',
            canonical_destination_url='https://matchco.test/qr/phase6',
        )
        record_candidate_context(candidate=self.candidate, entry_point=qr)
        CandidateConsent.objects.create(
            identity=identity, organization=self.org,
            purpose=CandidateConsent.PURPOSE_CIRCULATION_STORE,
            granted=True, policy_version='phase6', source=f'entry_point:{qr.pk}',
        )
        self.gap = CoverageGap.objects.create(
            position=self.position, organization=self.org,
            minimum_eligible=2, minimum_interested=1,
        )
        self.campaign = EnrichmentCampaign.objects.create(
            organization=self.org, coverage_gap=self.gap, position=self.position,
            name='Disponibilidade Atendente', status=EnrichmentCampaign.STATUS_ACTIVE,
        )

    def test_gap_counts_eligible_people_without_ordering_them(self):
        evaluate_coverage_gap(coverage_gap=self.gap)
        self.gap.refresh_from_db()
        self.assertEqual(self.gap.eligible_count, 1)
        self.assertEqual(self.gap.interested_count, 0)
        self.assertEqual(self.gap.state, CoverageGap.STATE_OPEN)

    def test_campaign_invite_and_response_are_versioned_and_optional(self):
        invite = create_enrichment_invite(campaign=self.campaign, candidate=self.candidate)
        response = record_enrichment_response(
            invite=invite, responses={'availability': ['weekends']}, consented_at=self.candidate.created_at,
        )
        self.assertEqual(response.campaign_id, self.campaign.pk)
        self.assertEqual(response.responses['availability'], ['weekends'])
        invite.refresh_from_db()
        self.assertEqual(invite.state, EnrichmentInvite.STATE_COMPLETED)

    def test_pause_revokes_open_invites(self):
        invite = create_enrichment_invite(campaign=self.campaign, candidate=self.candidate)
        change_enrichment_campaign_status(
            campaign=self.campaign, status=EnrichmentCampaign.STATUS_PAUSED,
        )
        invite.refresh_from_db()
        self.assertEqual(invite.state, EnrichmentInvite.STATE_REVOKED)
