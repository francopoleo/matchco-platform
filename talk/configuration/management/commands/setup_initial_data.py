from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from configuration.models import Organization, Domain, Membership
from tenants_core.models import TenantUser
from django_tenants.utils import schema_context
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup initial data: superadmin user, organizations, and domains'

    def add_arguments(self, parser):
        parser.add_argument(
            '--config',
            type=str,
            help='JSON file with configuration (organizations, domains, admin credentials)'
        )
        parser.add_argument(
            '--interactive',
            action='store_true',
            default=True,
            help='Interactive setup (default)'
        )
        parser.add_argument(
            '--demo',
            action='store_true',
            help='Setup demo data (3 test organizations)'
        )

    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load config: {str(e)}")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Talk Platform - Initial Setup\n'))

        # Determine setup source
        if options['config']:
            config = self.load_config(options['config'])
            self.setup_from_config(config)
        elif options['demo']:
            self.setup_demo_data()
        else:
            self.setup_interactive()

        self.stdout.write(self.style.SUCCESS('\n✅ Setup complete!\n'))

    def setup_demo_data(self):
        """Setup demo organizations and superadmin"""
        self.stdout.write('📦 Setting up demo data...\n')

        # Create superadmin
        admin_user, admin_created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@talk.local',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if admin_created:
            admin_user.set_password('Admin@123!')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('✓ Superadmin created: admin'))
        else:
            self.stdout.write(self.style.WARNING('✓ Superadmin exists: admin'))

        # Create demo organizations
        demo_orgs = [
            {
                'name': 'Acme Corporation',
                'slug': 'acme',
                'schema_name': 'acme',
                'domain': 'acme.colabore.local',
                'description': 'Demo Organization 1'
            },
            {
                'name': 'Tech Startup',
                'slug': 'techstartup',
                'schema_name': 'techstartup',
                'domain': 'tech.colabore.local',
                'description': 'Demo Organization 2'
            },
            {
                'name': 'Education First',
                'slug': 'edufirst',
                'schema_name': 'edufirst',
                'domain': 'edu.colabore.local',
                'description': 'Demo Organization 3'
            }
        ]

        for org_data in demo_orgs:
            org, org_created = Organization.objects.get_or_create(
                schema_name=org_data['schema_name'],
                defaults={
                    'name': org_data['name'],
                    'slug': org_data['slug'],
                    'description': org_data['description'],
                    'active': True,
                }
            )

            status = '✓ Created' if org_created else '✓ Exists'
            self.stdout.write(f"{status}: {org.name} ({org.schema_name})")

            # Create domain
            domain, domain_created = Domain.objects.get_or_create(
                domain=org_data['domain'],
                defaults={'tenant': org, 'is_primary': True}
            )
            self.stdout.write(f"         → {domain.domain}")

            # Create membership for admin
            membership, mem_created = Membership.objects.get_or_create(
                user=admin_user,
                organization=org,
                defaults={'role': 'admin', 'is_primary': org_data['schema_name'] == 'acme'}
            )

            # Create TenantUser
            with schema_context(org.schema_name):
                TenantUser.objects.get_or_create(
                    user_id=admin_user.id,
                    defaults={
                        'username': admin_user.username,
                        'email': admin_user.email,
                    }
                )

        self.stdout.write('\n📝 Demo credentials:')
        self.stdout.write('   Username: admin')
        self.stdout.write('   Password: Admin@123!')
        self.stdout.write('\n🌐 Access at:')
        for org_data in demo_orgs:
            self.stdout.write(f"   http://{org_data['domain']}/login/")

    def setup_interactive(self):
        """Interactive setup"""
        self.stdout.write('📋 Interactive Setup\n')

        # Superadmin setup
        username = input("Superadmin username [admin]: ").strip() or 'admin'
        email = input("Superadmin email [admin@talk.local]: ").strip() or 'admin@talk.local'
        password = input("Superadmin password [Admin@123!]: ").strip() or 'Admin@123!'

        # Create superadmin
        admin_user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password(password)
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'\n✓ Superadmin created: {username}'))
        else:
            self.stdout.write(self.style.WARNING(f'\n✓ Superadmin exists: {username}'))

        # Organizations setup
        self.stdout.write('\n📦 Organizations Setup')
        self.stdout.write('(Enter blank name to skip)\n')

        org_count = 0
        while True:
            org_name = input(f"Organization {org_count + 1} name: ").strip()
            if not org_name:
                break

            org_domain = input(f"Domain (e.g., {org_name.lower()}.colabore.local): ").strip()
            org_description = input("Description: ").strip()

            if not org_domain:
                continue

            org_slug = org_name.lower().replace(' ', '-')
            org_schema = org_slug[:63]

            org, org_created = Organization.objects.get_or_create(
                schema_name=org_schema,
                defaults={
                    'name': org_name,
                    'slug': org_slug,
                    'description': org_description,
                    'active': True,
                }
            )

            # Create domain
            domain, _ = Domain.objects.get_or_create(
                domain=org_domain,
                defaults={'tenant': org, 'is_primary': org_count == 0}
            )

            # Create membership
            membership, _ = Membership.objects.get_or_create(
                user=admin_user,
                organization=org,
                defaults={'role': 'admin', 'is_primary': org_count == 0}
            )

            # Create TenantUser
            with schema_context(org_schema):
                TenantUser.objects.get_or_create(
                    user_id=admin_user.id,
                    defaults={'username': username, 'email': email}
                )

            self.stdout.write(self.style.SUCCESS(f'✓ Organization created: {org_name}'))
            org_count += 1
            self.stdout.write('')

    def setup_from_config(self, config):
        """Setup from JSON configuration"""
        self.stdout.write('📄 Loading from config file...\n')

        # Create superadmin
        admin_data = config.get('superadmin', {})
        username = admin_data.get('username', 'admin')
        email = admin_data.get('email', 'admin@talk.local')
        password = admin_data.get('password', 'Admin@123!')

        admin_user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password(password)
            admin_user.save()

        self.stdout.write(self.style.SUCCESS(f'✓ Superadmin: {username}'))

        # Create organizations
        for org_data in config.get('organizations', []):
            org, org_created = Organization.objects.get_or_create(
                schema_name=org_data['schema_name'],
                defaults={
                    'name': org_data['name'],
                    'slug': org_data['slug'],
                    'description': org_data.get('description', ''),
                    'active': True,
                }
            )

            # Create domain
            domain, _ = Domain.objects.get_or_create(
                domain=org_data['domain'],
                defaults={'tenant': org, 'is_primary': org_data.get('is_primary', False)}
            )

            # Create membership
            Membership.objects.get_or_create(
                user=admin_user,
                organization=org,
                defaults={'role': 'admin', 'is_primary': org_data.get('is_primary', False)}
            )

            # Create TenantUser
            with schema_context(org_data['schema_name']):
                TenantUser.objects.get_or_create(
                    user_id=admin_user.id,
                    defaults={'username': username, 'email': email}
                )

            self.stdout.write(self.style.SUCCESS(f'✓ {org_data["name"]} → {org_data["domain"]}'))
