"""Fase 5 — catálogo canônico e respostas por escopo."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from recruitment.domain_models import RecruitmentCompany, RecruitmentJobFunction, RecruitmentOrganization, RecruitmentStore
from recruitment.models import (
    CandidateCanonicalResponse, CandidateProfile, CanonicalCatalog, CanonicalFunctionMapping,
    CanonicalTerm, CanonicalTermAlias, CandidateConsent, EntryPoint,
    OpportunityCanonicalRequirement, Position,
)
from recruitment.services import (
    candidate_is_eligible_for_position, eligible_candidate_count_for_position,
    project_shared_canonical_terms,
    record_canonical_response, resolve_canonical_terms,
    record_candidate_context,
)


class CanonicalCatalogTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(
            external_id='phase-5-org', slug='phase-5-org', name='Phase 5',
        )
        self.company = RecruitmentCompany.objects.create(organization=self.org, name='Rede')
        self.store = RecruitmentStore.objects.create(
            organization=self.org, company=self.company, name='Loja A',
        )
        self.function = RecruitmentJobFunction.objects.create(
            organization=self.org, company=self.company, name='Caixa de loja',
        )
        self.catalog = CanonicalCatalog.objects.create(
            code='retail', name='Varejo', version=1, status=CanonicalCatalog.STATUS_PUBLISHED,
        )
        self.term = CanonicalTerm.objects.create(
            catalog=self.catalog, term_type=CanonicalTerm.TYPE_FUNCTION,
            code='retail-cashier', label='Caixa de loja', normalized_label='',
        )
        CanonicalTermAlias.objects.create(term=self.term, alias='caixa')
        CanonicalFunctionMapping.objects.create(
            term=self.term, job_function=self.function, organization=self.org,
        )
        self.candidate = CandidateProfile.objects.create(
            organization=self.org, first_name='Ana', email='ana-phase5@example.com',
        )
        self.candidate.job_functions.add(self.function)
        from recruitment.services import resolve_or_create_identity
        self.identity = resolve_or_create_identity(email=self.candidate.email)
        self.candidate.identity = self.identity
        self.candidate.save(update_fields=['identity', 'updated_at'])
        self.entry_point = EntryPoint.objects.create(
            organization=self.org, kind=EntryPoint.KIND_STORE,
            scope_store=self.store, label='QR Loja A',
            canonical_destination_url='https://matchco.test/qr/a',
        )
        record_candidate_context(candidate=self.candidate, entry_point=self.entry_point)
        CandidateConsent.objects.create(
            identity=self.identity, organization=self.org,
            purpose=CandidateConsent.PURPOSE_CIRCULATION_STORE,
            granted=True, policy_version='phase5',
            source=f'entry_point:{self.entry_point.pk}',
        )
        self.position = Position.objects.create(
            organization=self.org, business_unit=self.store, job_function=self.function,
            title='Caixa de loja',
        )

    def test_alias_is_exact_and_deterministic(self):
        terms = resolve_canonical_terms(catalog=self.catalog, value='CAIXA')
        self.assertEqual(list(terms), [self.term])
        self.assertFalse(resolve_canonical_terms(catalog=self.catalog, value='caix').exists())

    def test_response_preserves_scope_and_catalog_version(self):
        response = record_canonical_response(
            candidate=self.candidate, term=self.term,
            scope=CandidateCanonicalResponse.SCOPE_UNIT,
            purpose=CandidateCanonicalResponse.PURPOSE_DISTRIBUTION,
            origin=CandidateCanonicalResponse.ORIGIN_QR,
            business_unit=self.store, consented_at=None,
            value={'available': True}, source_reference='qr-loja-a',
        )
        self.assertEqual(response.catalog_version, 1)
        self.assertEqual(response.business_unit_id, self.store.pk)
        self.assertEqual(response.value, {'available': True})

    def test_unit_scope_requires_unit(self):
        response = CandidateCanonicalResponse(
            candidate=self.candidate, term=self.term, organization=self.org,
            scope=CandidateCanonicalResponse.SCOPE_UNIT,
            purpose=CandidateCanonicalResponse.PURPOSE_PROFILE,
            origin=CandidateCanonicalResponse.ORIGIN_CANDIDATE,
            catalog_version=1,
        )
        with self.assertRaises(ValidationError):
            response.full_clean()

    def test_segment_scope_requires_segment_term(self):
        response = CandidateCanonicalResponse(
            candidate=self.candidate, term=self.term, organization=self.org,
            scope=CandidateCanonicalResponse.SCOPE_SEGMENT,
            purpose=CandidateCanonicalResponse.PURPOSE_PROFILE,
            origin=CandidateCanonicalResponse.ORIGIN_CANDIDATE,
            catalog_version=1,
        )
        with self.assertRaises(ValidationError):
            response.full_clean()

    def test_cross_organization_projection_hides_source_until_network_consent(self):
        other = RecruitmentOrganization.objects.create(
            external_id='phase-5-other', slug='phase-5-other', name='Outra rede',
        )
        self.assertEqual(project_shared_canonical_terms(candidate=self.candidate, viewer_organization=other), [])
        network_qr = EntryPoint.objects.create(
            organization=self.org, kind=EntryPoint.KIND_STORE,
            scope_store=self.store, scope_network_id=other.slug,
            label='QR compartilhamento de rede',
            canonical_destination_url='https://matchco.test/qr/shared-network',
        )
        record_candidate_context(candidate=self.candidate, entry_point=network_qr)
        CandidateConsent.objects.create(
            identity=self.identity, organization=self.org,
            purpose=CandidateConsent.PURPOSE_CIRCULATION_NETWORK, granted=True,
            policy_version='phase5', source=f'entry_point:{network_qr.pk}',
        )
        record_canonical_response(
            candidate=self.candidate, term=self.term,
            scope=CandidateCanonicalResponse.SCOPE_ORGANIZATION,
            purpose=CandidateCanonicalResponse.PURPOSE_DISTRIBUTION,
            origin=CandidateCanonicalResponse.ORIGIN_MANAGER,
            value={'internal': 'omit'}, source_reference='source-private',
        )
        record_canonical_response(
            candidate=self.candidate, term=self.term,
            scope=CandidateCanonicalResponse.SCOPE_ORGANIZATION,
            purpose=CandidateCanonicalResponse.PURPOSE_PROFILE,
            origin=CandidateCanonicalResponse.ORIGIN_CANDIDATE,
            value={'private_context': 'do not project'}, source_reference='profile-only',
        )
        projected = project_shared_canonical_terms(candidate=self.candidate, viewer_organization=other)
        self.assertEqual(len(projected), 1)
        self.assertEqual(projected[0]['label'], 'Caixa de loja')
        self.assertNotIn('source_reference', projected[0])

    def test_required_term_is_a_gate_without_ranking(self):
        OpportunityCanonicalRequirement.objects.create(
            position=self.position, term=self.term,
            requirement=OpportunityCanonicalRequirement.REQUIRED,
        )
        self.assertTrue(candidate_is_eligible_for_position(candidate=self.candidate, position=self.position))
        self.candidate.job_functions.clear()
        self.assertFalse(candidate_is_eligible_for_position(candidate=self.candidate, position=self.position))

    def test_structured_availability_is_a_hard_gate(self):
        self.position.required_days = ['sun']
        self.position.required_period = 'evening'
        self.position.work_format = Position.FORMAT_TEMPORARIO
        self.position.save(update_fields=['required_days', 'required_period', 'work_format'])
        self.candidate.availability_days = ['sat']
        self.candidate.availability_period = 'morning'
        self.candidate.preferred_work_format = Position.FORMAT_TEMPORARIO
        self.candidate.save(update_fields=['availability_days', 'availability_period', 'preferred_work_format'])
        self.assertFalse(candidate_is_eligible_for_position(candidate=self.candidate, position=self.position))
        self.candidate.availability_days = ['sat', 'sun']
        self.candidate.availability_period = 'evening'
        self.candidate.save(update_fields=['availability_days', 'availability_period'])
        self.assertTrue(candidate_is_eligible_for_position(candidate=self.candidate, position=self.position))

    def test_eligible_pool_counts_cross_organization_profiles_only_after_consent(self):
        from recruitment.services import resolve_or_create_identity

        other_org = RecruitmentOrganization.objects.create(
            external_id='phase-5-other-pool', slug='phase-5-other-pool', name='Outra rede',
        )
        other_company = RecruitmentCompany.objects.create(organization=other_org, name='Outra empresa')
        other_function = RecruitmentJobFunction.objects.create(
            organization=other_org, company=other_company, name='Operador de caixa',
        )
        CanonicalFunctionMapping.objects.create(
            term=self.term, job_function=other_function, organization=other_org,
        )
        identity = resolve_or_create_identity(email='candidato-compartilhado@example.com')
        shared_candidate = CandidateProfile.objects.create(
            organization=other_org, identity=identity,
            first_name='Pessoa compartilhada', email='candidato-compartilhado@example.com',
            visibility_match=True,
        )
        shared_candidate.job_functions.add(other_function)
        entry_point = EntryPoint.objects.create(
            organization=other_org, kind=EntryPoint.KIND_STORE,
            scope_store=RecruitmentStore.objects.create(
                organization=other_org, company=other_company, name='Loja compartilhada',
            ), scope_network_id=self.org.slug, label='QR rede',
            canonical_destination_url='https://matchco.test/qr/network',
        )
        record_candidate_context(candidate=shared_candidate, entry_point=entry_point)

        self.assertEqual(eligible_candidate_count_for_position(position=self.position), 1)
        CandidateConsent.objects.create(
            identity=identity, organization=other_org,
            purpose=CandidateConsent.PURPOSE_CIRCULATION_SHOPPING,
            granted=True, policy_version='phase5-pool',
            source=f'entry_point:{entry_point.pk}',
        )
        CandidateConsent.objects.create(
            identity=identity, organization=other_org,
            purpose=CandidateConsent.PURPOSE_CIRCULATION_NETWORK,
            granted=True, policy_version='phase5-pool',
            source=f'entry_point:{entry_point.pk}',
        )
        self.assertEqual(eligible_candidate_count_for_position(position=self.position), 2)
