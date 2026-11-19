from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.conf import settings
from django.test import override_settings

from recruitment.domain_models import (
    RecruitmentCompany,
    RecruitmentJobFunction,
    RecruitmentOrganization,
    RecruitmentStore,
)
from recruitment.models import (
    AuthorityScope,
    CandidateIdentity,
    CandidateProfile,
    EmployerActor,
    Position,
    Relation,
)
from recruitment.services import deliver_opportunity_notice


User = get_user_model()


@override_settings(
    MIDDLEWARE=[
        middleware for middleware in settings.MIDDLEWARE
        if middleware not in {
            'django_tenants.middleware.main.TenantMainMiddleware',
            'configuration.middleware.OrganizationContextMiddleware',
            'matchco.middleware.ActiveOrganizationMiddleware',
        }
    ]
)
class TenantBoundaryTests(TestCase):
    def setUp(self):
        self.org_a = RecruitmentOrganization.objects.create(
            external_id='boundary-a', slug='boundary-a', name='Empresa A',
        )
        self.org_b = RecruitmentOrganization.objects.create(
            external_id='boundary-b', slug='boundary-b', name='Empresa B',
        )
        self.company_a = RecruitmentCompany.objects.create(
            organization=self.org_a, name='Empresa A',
        )
        self.company_b = RecruitmentCompany.objects.create(
            organization=self.org_b, name='Empresa B',
        )
        self.store_a = RecruitmentStore.objects.create(
            organization=self.org_a, company=self.company_a, name='Unidade A',
        )
        self.store_b = RecruitmentStore.objects.create(
            organization=self.org_b, company=self.company_b, name='Unidade B',
        )
        self.function_a = RecruitmentJobFunction.objects.create(
            organization=self.org_a, company=self.company_a, name='Vendas A',
        )
        identity = CandidateIdentity.objects.create(
            email_normalized='candidate@boundary.test',
        )
        self.profile_a = CandidateProfile.objects.create(
            organization=self.org_a, identity=identity,
            first_name='Pessoa', last_name='A',
            email='candidate@boundary.test', phone='11999990000',
        )
        self.profile_b = CandidateProfile.objects.create(
            organization=self.org_b, identity=identity,
            first_name='Pessoa', last_name='B',
            email='candidate@boundary.test', phone='11999990000',
        )

    def test_candidate_can_switch_only_between_own_organization_profiles(self):
        client = Client()
        session = client.session
        session['matchco_profile_id'] = self.profile_a.pk
        session.save()

        response = client.post('/candidato/contexto/', {
            'profile_id': self.profile_b.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(client.session['matchco_profile_id'], self.profile_b.pk)

        outsider = CandidateProfile.objects.create(
            organization=self.org_a, first_name='Outra', email='other@test',
            phone='11999991111',
        )
        response = client.post('/candidato/contexto/', {'profile_id': outsider.pk})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(client.session['matchco_profile_id'], self.profile_b.pk)

    def test_portal_relation_is_not_visible_to_actor_from_other_organization(self):
        function_b = RecruitmentJobFunction.objects.create(
            organization=self.org_b, company=self.company_b, name='Vendas B',
        )
        opportunity = Position.objects.create(
            organization=self.org_a, business_unit=self.store_a,
            job_function=self.function_a, title='Oportunidade A',
            state=Position.STATE_ACTIVATED, pre_interest_set_complete=True,
        )
        relation = Relation.objects.create(
            candidate=self.profile_a, opportunity=opportunity,
            opportunity_version=opportunity.version,
        )
        user = User.objects.create_user(
            username='actor-b', password='password', email='actor-b@test',
        )
        EmployerActor.objects.create(
            user=user, organization=self.org_b, business_unit=self.store_b,
            authority_scopes=[AuthorityScope.AA6_VIEW_EMPLOYER_INTEREST_VIEW],
        )
        client = Client()
        self.assertTrue(client.login(username='actor-b', password='password'))
        session = client.session
        session['matchco_portal_recruitment_organization_id'] = self.org_b.pk
        session.save()

        response = client.get(f'/portal/relation/{relation.pk}/')
        # Foreign-tenant objects are intentionally indistinguishable from
        # nonexistent ones, preventing identifier enumeration.
        self.assertEqual(response.status_code, 404)

    def test_staff_flag_without_recruitment_scope_cannot_view_candidate_interest(self):
        opportunity = Position.objects.create(
            organization=self.org_a, business_unit=self.store_a,
            job_function=self.function_a, title='Oportunidade A',
            state=Position.STATE_ACTIVATED, pre_interest_set_complete=True,
        )
        user = User.objects.create_user(
            username='staff-without-scope', password='password',
            email='staff-without-scope@test', is_staff=True,
        )
        client = Client()
        self.assertTrue(client.login(username='staff-without-scope', password='password'))
        session = client.session
        session['active_organization_id'] = self.org_a.legacy_id
        session['selected_organization_id'] = self.org_a.legacy_id
        session.save()

        response = client.get(
            f'/console/recruitment/empregador/oportunidades/{opportunity.pk}/interesse/'
        )
        self.assertIn(response.status_code, (403, 404))

    def test_portal_function_lookup_hides_unit_from_another_organization(self):
        user = User.objects.create_user(
            username='actor-b-functions', password='password', email='actor-b-functions@test',
        )
        EmployerActor.objects.create(
            user=user, organization=self.org_b, business_unit=self.store_b,
            authority_scopes=[AuthorityScope.AA6_VIEW_EMPLOYER_INTEREST_VIEW],
        )
        client = Client()
        self.assertTrue(client.login(username='actor-b-functions', password='password'))
        session = client.session
        session['matchco_portal_recruitment_organization_id'] = self.org_b.pk
        session.save()

        response = client.get(
            f'/portal/necessidades/unidade/{self.store_a.pk}/funcoes/'
        )
        self.assertEqual(response.status_code, 404)

    def test_portal_pool_estimate_hides_unit_from_another_organization(self):
        user = User.objects.create_user(
            username='actor-b-estimate', password='password', email='actor-b-estimate@test',
        )
        EmployerActor.objects.create(
            user=user, organization=self.org_b, business_unit=self.store_b,
            authority_scopes=[AuthorityScope.AA6_VIEW_EMPLOYER_INTEREST_VIEW],
        )
        client = Client()
        self.assertTrue(client.login(username='actor-b-estimate', password='password'))
        session = client.session
        session['matchco_portal_recruitment_organization_id'] = self.org_b.pk
        session.save()

        response = client.get('/portal/necessidades/simular/', {'store_id': self.store_a.pk})
        self.assertEqual(response.status_code, 404)

    def test_relation_rejects_profile_from_another_organization(self):
        opportunity = Position.objects.create(
            organization=self.org_a, business_unit=self.store_a,
            job_function=self.function_a, title='Oportunidade A',
            state=Position.STATE_ACTIVATED, pre_interest_set_complete=True,
        )
        relation = Relation(
            candidate=self.profile_b, opportunity=opportunity,
            opportunity_version=opportunity.version,
        )
        with self.assertRaises(ValidationError) as caught:
            relation.full_clean()
        self.assertIn('candidate', caught.exception.message_dict)

    def test_notice_delivery_rejects_cross_organization_profile(self):
        opportunity = Position.objects.create(
            organization=self.org_a, business_unit=self.store_a,
            job_function=self.function_a, title='Oportunidade A',
            state=Position.STATE_ACTIVATED, pre_interest_set_complete=True,
        )
        with self.assertRaises(ValidationError):
            deliver_opportunity_notice(candidate=self.profile_b, opportunity=opportunity)
