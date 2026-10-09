from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from configuration.models import Company, Organization, OrganizationServiceSubscription
from configuration.services import service_enabled


class ServiceScopeTests(TestCase):
    @patch.object(Organization, 'create_schema', return_value=None)
    def setUp(self, _create_schema):
        self.organization = Organization.objects.create(
            name='Organização de teste', slug='org-servicos', schema_name='org_servicos',
        )
        self.other_organization = Organization.objects.create(
            name='Outra organização', slug='org-outro', schema_name='org_outro',
        )
        self.company = Company.objects.create(organization=self.organization, name='Empresa A')
        self.other_company = Company.objects.create(organization=self.organization, name='Empresa B')

    def test_company_inherits_organization_default(self):
        OrganizationServiceSubscription.objects.create(
            organization=self.organization,
            service_code=OrganizationServiceSubscription.SERVICE_TALK,
        )

        self.assertTrue(service_enabled(self.organization, 'talk', self.company))
        self.assertTrue(service_enabled(self.organization, 'talk', self.other_company))

    def test_company_override_can_suspend_only_one_company(self):
        OrganizationServiceSubscription.objects.create(
            organization=self.organization,
            service_code=OrganizationServiceSubscription.SERVICE_RECRUITMENT,
        )
        OrganizationServiceSubscription.objects.create(
            organization=self.organization,
            company=self.company,
            service_code=OrganizationServiceSubscription.SERVICE_RECRUITMENT,
            status=OrganizationServiceSubscription.STATUS_SUSPENDED,
        )

        self.assertFalse(service_enabled(self.organization, 'recruitment', self.company))
        self.assertTrue(service_enabled(self.organization, 'recruitment', self.other_company))

    def test_company_scope_never_falls_back_across_organizations(self):
        other_company = Company.objects.create(
            organization=self.other_organization, name='Empresa isolada',
        )
        OrganizationServiceSubscription.objects.create(
            organization=self.organization,
            company=self.company,
            service_code=OrganizationServiceSubscription.SERVICE_CONTENT,
        )

        self.assertFalse(service_enabled(self.organization, 'content', other_company))

    def test_expired_and_future_services_are_inactive(self):
        OrganizationServiceSubscription.objects.create(
            organization=self.organization,
            service_code=OrganizationServiceSubscription.SERVICE_CONTENT,
            ends_at=timezone.now() - timedelta(minutes=1),
        )
        self.assertFalse(service_enabled(self.organization, 'content'))
