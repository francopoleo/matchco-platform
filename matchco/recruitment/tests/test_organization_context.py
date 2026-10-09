"""Fase 2 — autoridade comercial e unidade física compartilhável."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from recruitment.domain_models import (
    RecruitmentCompany,
    RecruitmentOrganization,
    RecruitmentOrganizationRelation,
    RecruitmentPlatformBinding,
    RecruitmentPhysicalUnit,
    RecruitmentStore,
)
from recruitment.services import resolve_platform_context


class OrganizationContextTests(TestCase):
    def test_one_physical_unit_can_have_two_organization_representations(self):
        shopping = RecruitmentOrganization.objects.create(
            external_id='shopping-context', slug='shopping-context', name='Shopping',
        )
        network = RecruitmentOrganization.objects.create(
            external_id='network-context', slug='network-context', name='Rede',
        )
        physical = RecruitmentPhysicalUnit.objects.create(
            external_key='bourbon-loja-01', name='Loja 01', city='São Paulo', state='SP',
        )
        shopping_company = RecruitmentCompany.objects.create(organization=shopping, name='Lojas do shopping')
        network_company = RecruitmentCompany.objects.create(organization=network, name='Rede nacional')
        shopping_store = RecruitmentStore.objects.create(
            organization=shopping, company=shopping_company, physical_unit=physical, name='Loja 01',
        )
        network_store = RecruitmentStore.objects.create(
            organization=network, company=network_company, physical_unit=physical, name='Unidade 01',
        )

        self.assertEqual(physical.representations.count(), 2)
        self.assertNotEqual(shopping_store.organization_id, network_store.organization_id)

    def test_relation_cannot_point_to_itself(self):
        org = RecruitmentOrganization.objects.create(
            external_id='self-context', slug='self-context', name='Organização',
        )
        relation = RecruitmentOrganizationRelation(
            organization=org, related_organization=org,
            relation_type=RecruitmentOrganizationRelation.RELATION_PARTNER,
        )

        with self.assertRaises(ValidationError):
            relation.full_clean()

    def test_platform_context_is_a_projection_without_granting_access(self):
        org = RecruitmentOrganization.objects.create(
            external_id='platform-context', slug='platform-context', name='Shopping Talk',
        )
        RecruitmentPlatformBinding.objects.create(
            recruitment_organization=org,
            platform_organization_id=42,
            capabilities=['talk', 'courses'],
        )

        context = resolve_platform_context(organization=org)

        self.assertEqual(context['platform_organization_ids'], [42])
        self.assertEqual(context['capabilities'], ['courses', 'talk'])
