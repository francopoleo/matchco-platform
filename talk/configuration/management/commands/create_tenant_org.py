from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from configuration.models import Organization, Domain
from tenants_core.models import TenantOrganization
from django_tenants.utils import schema_context
import re


class Command(BaseCommand):
    help = 'Create a new tenant (company/organization) with schema isolation'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='Company name (e.g., "Empresa Nova")')
        parser.add_argument('domain', type=str, help='Primary domain (e.g., "empresa-nova.colabore.com")')
        parser.add_argument(
            '--description',
            type=str,
            default='',
            help='Optional description'
        )
        parser.add_argument(
            '--active',
            action='store_true',
            default=True,
            help='Set tenant as active'
        )

    def validate_domain(self, domain):
        """Validate domain format"""
        domain_regex = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(domain_regex, domain):
            raise CommandError(f"❌ Invalid domain format: {domain}")

        # Check if domain already exists
        if Domain.objects.filter(domain=domain).exists():
            raise CommandError(f"❌ Domain '{domain}' already registered!")

    def validate_schema_name(self, schema_name):
        """Validate schema name"""
        # Schema names must be lowercase, max 63 chars, no spaces
        if not re.match(r'^[a-z0-9_-]{1,63}$', schema_name):
            raise CommandError(f"❌ Invalid schema name: {schema_name}")

        # Check if schema already exists
        if Organization.objects.filter(schema_name=schema_name).exists():
            raise CommandError(f"❌ Schema '{schema_name}' already exists!")

        # Check in PostgreSQL
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                [schema_name]
            )
            if cursor.fetchone():
                raise CommandError(f"❌ Schema '{schema_name}' already exists in database!")

    def handle(self, *args, **options):
        name = options['name'].strip()
        domain = options['domain'].strip().lower()
        description = options['description'].strip()
        active = options['active']

        self.stdout.write(self.style.SUCCESS('🔄 Creating new tenant...'))
        self.stdout.write('')

        # Validate inputs
        if not name:
            raise CommandError("❌ Company name cannot be empty")

        if not domain:
            raise CommandError("❌ Domain cannot be empty")

        # Create slug from name
        slug = name.lower().replace(' ', '-').replace('_', '-')
        slug = re.sub(r'[^a-z0-9-]', '', slug)

        # Create schema name from slug (max 63 chars)
        schema_name = slug[:63]

        self.stdout.write(f"  Name:         {name}")
        self.stdout.write(f"  Slug:         {slug}")
        self.stdout.write(f"  Schema:       {schema_name}")
        self.stdout.write(f"  Domain:       {domain}")
        self.stdout.write(f"  Description:  {description or '(none)'}")
        self.stdout.write(f"  Active:       {'✓' if active else '✗'}")
        self.stdout.write('')

        # Validate
        self.stdout.write('📋 Validating...')
        self.validate_domain(domain)
        self.validate_schema_name(schema_name)
        self.stdout.write(self.style.SUCCESS('  ✓ Validation passed'))
        self.stdout.write('')

        # Create Organization
        self.stdout.write('🏢 Creating Organization...')
        try:
            org = Organization.objects.create(
                name=name,
                slug=slug,
                schema_name=schema_name,
                description=description,
                active=active
            )
            self.stdout.write(self.style.SUCCESS(f'  ✓ Organization created: {org.id}'))
        except Exception as e:
            raise CommandError(f'❌ Failed to create organization: {str(e)}')

        self.stdout.write('')

        # Register Domain
        self.stdout.write('🌐 Registering Domain...')
        try:
            domain_obj = Domain.objects.create(
                domain=domain,
                tenant=org,
                is_primary=True
            )
            self.stdout.write(self.style.SUCCESS(f'  ✓ Domain registered'))
        except Exception as e:
            org.delete()
            raise CommandError(f'❌ Failed to register domain: {str(e)}')

        self.stdout.write('')

        # Initialize tenant schema with mirror organization
        self.stdout.write('🔗 Initializing tenant schema with mirror model...')
        try:
            with schema_context(schema_name):
                tenant_org, created = TenantOrganization.objects.get_or_create(
                    organization_id=org.id,
                    defaults={
                        'name': org.name,
                        'slug': org.slug
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ TenantOrganization mirror created'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ TenantOrganization mirror exists'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠ Could not initialize mirror model: {str(e)}'))

        self.stdout.write('')
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.SUCCESS('✅ TENANT CREATED SUCCESSFULLY'))
        self.stdout.write('=' * 70)
        self.stdout.write('')
        self.stdout.write('📌 Next Steps:')
        self.stdout.write(f'   1. Access: http://{domain}/')
        self.stdout.write(f'   2. The system will route to schema: {schema_name}')
        self.stdout.write(f'   3. Users can signup at: http://{domain}/accounts/signup/')
        self.stdout.write(f'   4. Admin access: http://{domain}/admin/')
        self.stdout.write('')
        self.stdout.write('💾 Database Info:')
        self.stdout.write(f'   Organization ID: {org.id}')
        self.stdout.write(f'   Schema Name:     {schema_name}')
        self.stdout.write(f'   Domain:          {domain}')
        self.stdout.write('')
