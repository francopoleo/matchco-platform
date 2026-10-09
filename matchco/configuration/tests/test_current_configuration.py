from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from configuration.models import Company, Membership, Organization
from configuration.organization_context import available_organizations, set_selected_organization
from configuration.services import management_access


User = get_user_model()


class CurrentOrganizationModelTests(TestCase):
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
