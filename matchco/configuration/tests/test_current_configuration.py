from django.contrib.auth import get_user_model
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

from django.conf import settings
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from configuration.models import Company, Membership, Organization
from configuration.organization_context import available_organizations, set_selected_organization
from configuration.services import management_access


User = get_user_model()


class CurrentOrganizationModelTests(TestCase):
    def tearDown(self):
        from django.db import connection
        connection.set_schema_to_public()

    def test_organization_generates_schema_from_slug(self):
        organization = Organization.objects.create(
            name='Rede MatchCo', slug='rede-matchco',
        )
        self.assertEqual(organization.schema_name, 'rede-matchco')

    def test_user_can_select_between_active_memberships(self):
        user = User.objects.create_user(
            username='multi-org', email='multi-org@example.test', password='password',
        )
        first = Organization.objects.create(name='Empresa A', slug='empresa-a')
        second = Organization.objects.create(name='Empresa B', slug='empresa-b')
        Membership.objects.create(user=user, organization=first, active=True, is_primary=True)
        Membership.objects.create(user=user, organization=second, active=True)

        organizations = list(available_organizations(user))
        self.assertEqual({first.pk, second.pk}, {org.pk for org in organizations})

        class Session(dict):
            modified = False

        class Request:
            session = Session()

        request = Request()
        request.user = user
        self.assertTrue(set_selected_organization(request, second.pk))
        self.assertEqual(request.session['selected_organization_id'], second.pk)
        self.assertEqual(request.session['active_organization_id'], second.pk)

    def test_inactive_membership_is_not_available(self):
        user = User.objects.create_user(
            username='inactive-org', email='inactive-org@example.test', password='password',
        )
        organization = Organization.objects.create(name='Empresa Inativa', slug='empresa-inativa')
        Membership.objects.create(user=user, organization=organization, active=False)
        self.assertFalse(available_organizations(user).exists())

    def test_organization_admin_can_manage_users_without_delegated_assignment(self):
        admin = User.objects.create_user(username='org-admin', password='password')
        member = User.objects.create_user(username='org-member', password='password')
        organization = Organization.objects.create(name='ElectraTech', slug='electratech')
        company = Company.objects.create(organization=organization, name='ElectraTech')
        Membership.objects.create(
            user=admin, organization=organization, role='admin', active=True,
        )
        Membership.objects.create(
            user=member, organization=organization, company=company, role='member', active=True,
        )

        self.assertTrue(management_access.can_manage_user(admin, member))

    def test_superuser_can_switch_to_active_organization_without_membership(self):
        from matchco.views import SwitchOrganizationView

        admin = User.objects.create_superuser(
            username='global-admin', email='global-admin@example.test', password='password',
        )
        organization = Organization.objects.create(
            name='ElectraTech', slug='electratech-global-admin', active=True, is_public=False,
        )
        request = RequestFactory().post(reverse('switch-organization'), {
            'organization_id': organization.pk,
            'next': '/',
        })
        request.user = admin

        class Session(dict):
            modified = False

        request.session = Session()
        response = SwitchOrganizationView().post(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(request.session['selected_organization_id'], organization.pk)
        self.assertEqual(request.session['active_organization_id'], organization.pk)

class OrganizationSwitchSessionTests(SimpleTestCase):
    def tearDown(self):
        from django.db import connection
        connection.set_schema_to_public()

    def _request(self, session):
        request = RequestFactory().get('/')
        request.user = SimpleNamespace(is_authenticated=True, is_superuser=True)

        class Session(dict):
            modified = False

        request.session = Session(session)
        return request

    @patch('configuration.organization_context.available_organizations')
    def test_switch_synchronizes_active_tenant_and_clears_dependent_context(self, available):
        target = SimpleNamespace(pk=22, schema_name='tenant_22')
        available.return_value.filter.return_value.first.return_value = target
        request = self._request({
            'selected_organization_id': 11,
            'active_organization_id': 11,
            'active_company_id': 41,
            'active_membership_id': 42,
            'user_role': 'admin',
            'matchco_portal_organization_id': 11,
            'matchco_portal_recruitment_organization_id': 43,
            'matchco_portal_store_id': 44,
            'matchco_portal_entry_point_id': 'old-entry',
            'ep_store_id': 45,
            'ep_audience': 'old-audience',
            'ep_audience_role': 'old-role',
        })

        self.assertTrue(set_selected_organization(request, target.pk))
        self.assertEqual(request.session['selected_organization_id'], target.pk)
        self.assertEqual(request.session['active_organization_id'], target.pk)
        self.assertEqual(request.active_organization, target)
        self.assertEqual(request.active_organization_id, target.pk)
        self.assertEqual(request.tenant, target)
        self.assertEqual(request.active_role, 'owner')
        self.assertEqual(request.session['user_role'], 'owner')
        for key in (
            'active_company_id', 'active_membership_id',
            'matchco_portal_organization_id',
            'matchco_portal_recruitment_organization_id',
            'matchco_portal_store_id', 'matchco_portal_entry_point_id',
            'ep_store_id', 'ep_audience', 'ep_audience_role',
        ):
            self.assertNotIn(key, request.session)

    def test_switch_url_drops_stale_company_filter_for_new_organization(self):
        from matchco.views import SwitchOrganizationView

        request = self._request({
            'selected_organization_id': 11,
            'active_company_id': 41,
        })
        view = SwitchOrganizationView()

        destination = view._clear_stale_tenant_query(
            request,
            '/console/courses/?company_id=41&state=published',
            22,
        )

        self.assertEqual(destination, '/console/courses/?state=published')

    def test_switch_url_preserves_company_filter_inside_same_organization(self):
        from matchco.views import SwitchOrganizationView

        request = self._request({'selected_organization_id': 11})
        view = SwitchOrganizationView()

        destination = view._clear_stale_tenant_query(
            request,
            '/console/courses/?company_id=41&state=published',
            11,
        )

        self.assertEqual(destination, '/console/courses/?company_id=41&state=published')

    @patch('matchco.views.service_enabled', return_value=False)
    def test_switch_url_leaves_unavailable_service_route(self, _service_enabled):
        from matchco.views import SwitchOrganizationView

        request = self._request({'selected_organization_id': 11})
        view = SwitchOrganizationView()
        organization = SimpleNamespace(pk=22)

        destination = view._safe_destination_for_organization(
            '/console/certifications/', organization,
        )

        self.assertEqual(destination, '/console/organization/')

    @patch('configuration.organization_context.available_organizations')
    def test_selecting_same_organization_preserves_company_filter(self, available):
        organization = SimpleNamespace(pk=11, schema_name='tenant_11')
        available.return_value.filter.return_value.first.return_value = organization
        request = self._request({
            'selected_organization_id': 11,
            'active_organization_id': 11,
            'active_company_id': 41,
        })

        self.assertTrue(set_selected_organization(request, organization.pk))
        self.assertEqual(request.session['active_company_id'], 41)
        self.assertEqual(request.active_company_id, 41)

    def test_contextual_help_links_to_the_new_architecture_anchor(self):
        from console.contextual_docs import CONTEXTUAL_DOCS

        entry = CONTEXTUAL_DOCS['select-organization']
        html_path = Path(settings.BASE_DIR) / 'docs' / 'help' / 'html' / entry['arquivo']
        self.assertIn(f'id="{entry["ancora"]}"', html_path.read_text(encoding='utf-8'))

    def test_platform_wide_view_clears_tenant_and_portal_context(self):
        from configuration.organization_context import clear_organization_scope

        request = self._request({
            'selected_organization_id': 11,
            'active_organization_id': 11,
            'active_company_id': 41,
            'active_membership_id': 42,
            'user_role': 'admin',
            'matchco_portal_organization_id': 11,
            'matchco_portal_store_id': 44,
            'ep_audience': 'old-audience',
        })
        self.assertTrue(clear_organization_scope(request))
        self.assertEqual(request.session['selected_organization_id'], '__all__')
        self.assertIsNone(request.active_organization)
        for key in (
            'active_organization_id', 'active_company_id', 'active_membership_id',
            'user_role', 'matchco_portal_organization_id',
            'matchco_portal_store_id', 'ep_audience',
        ):
            self.assertNotIn(key, request.session)
