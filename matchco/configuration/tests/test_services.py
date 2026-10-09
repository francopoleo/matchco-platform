from datetime import timedelta
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import resolve
from django.utils import timezone
from django.utils import translation
from django.utils.translation import gettext

from configuration.models import Company, Organization, OrganizationServiceSubscription
from configuration.services import service_enabled
from configuration.service_middleware import ServiceAccessMiddleware, required_service_for_request
from console.contextual_docs import CONTEXTUAL_DOCS


class ServiceLabelLocalizationTests(SimpleTestCase):
    def test_service_names_use_brazilian_portuguese_labels(self):
        expected = {
            'content': 'Conteúdo',
            'talk': 'Talk',
            'training': 'Treinamento',
            'certification': 'Certificação',
            'recruitment': 'Recrutamento Match',
            'campaigns': 'Campanhas e pesquisas',
            'operations': 'Operação',
            'partners': 'Parceiros',
            'analytics': 'Indicadores',
        }

        with translation.override('pt-br'):
            labels = {
                code: str(label)
                for code, label in OrganizationServiceSubscription.SERVICE_CHOICES
            }

        self.assertEqual({code: labels[code] for code in expected}, expected)

    def test_organization_services_screen_has_english_and_spanish_catalog_entries(self):
        expected = {
            'en': ('Organization services', 'Active services', 'Content', 'Training'),
            'es': ('Servicios de la organización', 'Servicios activos', 'Contenido', 'Formación'),
        }

        for language, messages in expected.items():
            with self.subTest(language=language), translation.override(language):
                translated = (
                    gettext('Serviços da organização'),
                    gettext('Serviços ativos'),
                    gettext('Content'),
                    gettext('Training'),
                    str(CONTEXTUAL_DOCS['console:organization_services']['descricao']),
                )
                expected_description = {
                    'en': "Set the organization's default services and, when needed, create a company-specific override. A company inherits the default until it has its own settings. The server also blocks direct routes for suspended services; this screen remains available to activate the first service.",
                    'es': 'Define los servicios predeterminados de la organización y, cuando sea necesario, crea una excepción para una empresa. La empresa hereda la configuración predeterminada hasta tener una propia. El servidor también bloquea las rutas directas de los servicios suspendidos; esta pantalla sigue disponible para activar el primer servicio.',
                }
                self.assertEqual(translated[-1], expected_description[language])
                self.assertEqual(translated[:4], messages)


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


class ServiceRouteEnforcementTests(TestCase):
    @patch.object(Organization, 'create_schema', return_value=None)
    def setUp(self, _create_schema):
        self.organization = Organization.objects.create(
            name='Organização de teste', slug='org-servicos-rotas', schema_name='org_servicos_rotas',
        )
        self.company = Company.objects.create(organization=self.organization, name='Empresa A')
        self.other_company = Company.objects.create(organization=self.organization, name='Empresa B')
        self.factory = RequestFactory()
        self.middleware = ServiceAccessMiddleware(lambda request: None)

    def _check_route(self, path, *, organization=None, company_id=None):
        request = self.factory.get(path)
        request.resolver_match = resolve(path)
        request.user = AnonymousUser()
        request.session = {}
        request.active_organization = organization
        request.active_company_id = company_id
        request.active_membership = None
        return self.middleware.process_view(request, None, (), {})

    def test_operational_route_families_resolve_to_their_service(self):
        expected = {
            '/console/publications/': 'content',
            '/app/courses/': 'training',
            '/api/courses/': 'training',
            '/portal/necessidades/': 'recruitment',
            '/certificacoes/verificar/00000000-0000-0000-0000-000000000000/': 'certification',
        }
        for path, service in expected.items():
            with self.subTest(path=path):
                request = self.factory.get(path)
                request.resolver_match = resolve(path)
                self.assertEqual(required_service_for_request(request), service)

    def test_direct_console_url_requires_active_service(self):
        denied = self._check_route('/console/publications/', organization=self.organization)
        self.assertEqual(denied.status_code, 404)

        OrganizationServiceSubscription.objects.create(
            organization=self.organization,
            service_code=OrganizationServiceSubscription.SERVICE_CONTENT,
        )
        self.assertIsNone(self._check_route('/console/publications/', organization=self.organization))

    def test_company_override_is_applied_to_direct_routes(self):
        OrganizationServiceSubscription.objects.create(
            organization=self.organization,
            service_code=OrganizationServiceSubscription.SERVICE_CONTENT,
        )
        OrganizationServiceSubscription.objects.create(
            organization=self.organization,
            company=self.company,
            service_code=OrganizationServiceSubscription.SERVICE_CONTENT,
            status=OrganizationServiceSubscription.STATUS_SUSPENDED,
        )

        self.assertEqual(
            self._check_route(
                '/console/publications/', organization=self.organization,
                company_id=self.company.pk,
            ).status_code,
            404,
        )
        self.assertIsNone(self._check_route(
            '/console/publications/', organization=self.organization,
            company_id=self.other_company.pk,
        ))

    def test_tenant_data_route_fails_closed_without_organization(self):
        self.assertEqual(self._check_route('/console/publications/').status_code, 404)

    def test_invalid_selected_company_does_not_fall_back_to_organization_service(self):
        OrganizationServiceSubscription.objects.create(
            organization=self.organization,
            service_code=OrganizationServiceSubscription.SERVICE_CONTENT,
        )
        self.assertEqual(
            self._check_route(
                '/console/publications/', organization=self.organization,
                company_id=999999,
            ).status_code,
            404,
        )

    def test_onboarding_service_configuration_remains_accessible(self):
        # The service setup route must remain available so an organization can
        # activate its first product; it is not itself a product screen.
        self.assertIsNone(self._check_route('/console/organization/services/'))
