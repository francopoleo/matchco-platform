"""Reset reproduzível dos dados de desenvolvimento do MatchCo."""

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from configuration.models import (
    BusinessChannel, BusinessUnit, Company, IntegrationConnection,
    IntegrationCredential, JobFunction, ManagementAssignment, Membership,
    MembershipAudit, OperationalUnit, Organization, OrganizationTerminology,
    Partner, PartnerMembership, PersonType, SectorTemplate, Domain,
)


class Command(BaseCommand):
    help = 'Limpa dados demo e deixa o banco pronto para seeds separados de recrutamento e conteúdo.'

    def add_arguments(self, parser):
        parser.add_argument('--yes', action='store_true', help='Confirma a operação destrutiva.')
        parser.add_argument('--seed-recruitment', action='store_true', help='Executa o seed de recrutamento após limpar.')
        parser.add_argument('--seed-content', action='store_true', help='Executa o seed de conteúdo após limpar.')
        parser.add_argument('--tenant', default='bourbon-shopping', help='Tenant usado pelo seed de conteúdo.')
        parser.add_argument('--admin-password', default='admin', help='Senha do usuário admin de desenvolvimento.')

    @transaction.atomic
    def handle(self, *args, **options):
        if not options['yes']:
            raise CommandError('Operação destrutiva. Execute com --yes.')

        # O comando existente limpa cada schema de tenant e usuários, mas
        # preserva a configuração de roteamento para que o ambiente continue
        # acessível. Em seguida limpamos explicitamente os apps compartilhados.
        call_command('reset_demo_system', yes=True, reset_only=True)
        self._truncate_recruitment_shared_tables()
        self._clear_shared_demo_catalog()
        Organization.objects.filter(slug__in=['bourbon-shopping', 'drogasil-rede']).update(active=True)
        self._ensure_shared_entry_domain()
        self._ensure_admin(options['admin_password'])

        self.stdout.write(self.style.SUCCESS('Dados de desenvolvimento limpos.'))
        self.stdout.write('Próximos seeds independentes: seed_matchco_recruitment e seed_matchco_content.')

        if options['seed_recruitment']:
            call_command('seed_matchco_recruitment', reset=False)
        if options['seed_content']:
            call_command('seed_matchco_content', tenant=options['tenant'])
            if Organization.objects.filter(schema_name='drogasil-rede').exists():
                call_command('seed_market_tenant_content', tenant='drogasil-rede', market='pharma')
            if Organization.objects.filter(schema_name='electratech-demo').exists():
                call_command('seed_market_tenant_content', tenant='electratech-demo', market='manufacturer')

    def _truncate_recruitment_shared_tables(self):
        tables = [model._meta.db_table for model in apps.get_app_config('recruitment').get_models()]
        quoted = ', '.join(connection.ops.quote_name(table) for table in tables)
        if quoted:
            with connection.cursor() as cursor:
                cursor.execute(f'TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE')
        # Mantém esta limpeza explícita porque o domínio de recrutamento tem
        # módulos históricos importados fora do models.py principal.
        from recruitment.domain_models import RecruitmentOrganization
        RecruitmentOrganization.objects.all().delete()

    def _clear_shared_demo_catalog(self):
        # Preserve Organization and Domain: they are the routing registry.
        # Everything below is recreated by the canonical recruitment seed or
        # by the organization's real onboarding flow.
        for model in (
            IntegrationConnection, IntegrationCredential,
            PartnerMembership, Partner, ManagementAssignment,
            MembershipAudit, Membership,
            JobFunction, BusinessChannel, OperationalUnit, BusinessUnit,
            Company, PersonType, OrganizationTerminology, SectorTemplate,
        ):
            model.objects.all().delete()

        Organization.objects.exclude(is_public=True).update(active=False)

    def _ensure_admin(self, password):
        User = get_user_model()
        admin, _ = User.objects.update_or_create(
            username='admin',
            defaults={
                'email': 'admin@matchco.local',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            },
        )
        admin.set_password(password)
        admin.save(update_fields=['password', 'email', 'is_staff', 'is_superuser', 'is_active'])
        for index, organization in enumerate(Organization.objects.filter(slug__in=[
            'bourbon-shopping', 'drogasil-rede', 'electratech-demo',
        ]).order_by('slug')):
            Membership.objects.update_or_create(
                user=admin,
                organization=organization,
                defaults={'role': 'admin', 'active': True, 'is_primary': index == 0},
            )

    def _ensure_shared_entry_domain(self):
        """Keep the common QR/console hostname routable in development.

        The hostname is only the initial tenant required by django-tenants.
        Organization selection remains explicit in the authenticated console,
        and recruitment QR records carry their own organization context.
        """
        bourbon = Organization.objects.filter(slug='bourbon-shopping', active=True).first()
        if bourbon:
            Domain.objects.update_or_create(
                domain='direct.ddns.net',
                defaults={'tenant': bourbon, 'is_primary': False},
            )
