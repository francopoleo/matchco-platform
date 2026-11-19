"""Development data keeps Recruitment references aligned to the canonical org tree."""

from unittest.mock import patch

from django.test import TestCase

from configuration.models import (
    BusinessUnit as ConfigBusinessUnit,
    Company as ConfigCompany,
    Organization as ConfigOrganization,
)
from configuration.management.commands.reset_matchco_development import (
    Command as ResetDevelopmentCommand,
)
from recruitment.domain_models import (
    RecruitmentChannel, RecruitmentCompany, RecruitmentOrganization,
)
from recruitment.management.commands.seed_matchco_market_demos import Command


class SeedStructureAlignmentTests(TestCase):
    @patch.object(ConfigOrganization, 'create_schema', return_value=None)
    def test_recruitment_store_points_to_canonical_business_unit(self, _create_schema):
        config_org = ConfigOrganization.objects.create(
            name='Bourbon', slug='seed-bourbon', schema_name='seed_bourbon',
        )
        config_company = ConfigCompany.objects.create(
            organization=config_org, name='Bourbon Shopping',
        )
        canonical_unit = ConfigBusinessUnit.objects.create(
            company=config_company, name='Loja Bourbon', shopping_name='Bourbon Shopping',
        )
        recruitment_org = RecruitmentOrganization.objects.create(
            external_id='seed-bourbon', slug='seed-bourbon', name='Bourbon',
        )
        recruitment_company = RecruitmentCompany.objects.create(
            organization=recruitment_org, name='Bourbon Shopping',
        )
        channel = RecruitmentChannel.objects.create(company=recruitment_company, name='Moda')
        stores = Command().ensure_stores(
            recruitment_org, recruitment_company, [channel],
            {'slug': 'bourbon-shopping', 'units': [('Loja Bourbon', 'LOJA', 'moda')]},
            config_org=config_org,
        )
        self.assertEqual(len(stores), 1)
        self.assertEqual(stores[0].legacy_id, canonical_unit.pk)

    def test_full_reset_seeds_certifications_after_tenant_content(self):
        from unittest.mock import call, patch

        with (
            patch.object(ResetDevelopmentCommand, '_truncate_recruitment_shared_tables'),
            patch.object(ResetDevelopmentCommand, '_clear_shared_demo_catalog'),
            patch.object(ResetDevelopmentCommand, '_ensure_shared_entry_domain'),
            patch.object(ResetDevelopmentCommand, '_ensure_admin'),
            patch('configuration.management.commands.reset_matchco_development.call_command') as seed,
        ):
            ResetDevelopmentCommand().handle(
                yes=True,
                seed_recruitment=False,
                seed_content=True,
                tenant='bourbon-shopping',
                admin_password='admin',
            )

        self.assertIn(call('seed_certification_demo'), seed.call_args_list)
