"""
Comprehensive seed data script for Talk platform.

Creates realistic organizations with:
- Multiple organizations (Hospital, Seguradora, School, Manufacturing, Retail, Fintech)
- Users with different roles and hierarchies
- Group hierarchies (Parents, Alumni, Departments)
- Compliance policies
- Example content
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from django.db import transaction
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
import io
from configuration.models import (
    Organization, Membership, Company, BusinessUnit, OperationalUnit,
    BusinessChannel, JobFunction, OrganizationTerminology,
    GroupHierarchyType, GroupNode, UserGroupMembership,
)
from courses.models import Course, Subject, Content
from publishing.models import Publication
from documents.models import Document
from learning.models import ContentTrail, TrailStep, TrailAssignment

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed complete system with realistic organizations and hierarchies'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data first')

    @transaction.atomic
    def handle(self, *args, **options):
        if options['clear']:
            self.clear_existing_data()

        self.stdout.write(self.style.SUCCESS('🚀 Starting seed...'))

        # Create organizations
        orgs = self.create_organizations()
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(orgs)} organizations'))

        # Create users for each organization
        users_by_org = self.create_users(orgs)
        self.stdout.write(self.style.SUCCESS('✅ Created users'))

        # Ensure admin has access to all organizations
        self.create_admin_access(orgs, users_by_org)
        self.stdout.write(self.style.SUCCESS('✅ Admin access configured'))

        # Create hierarchies
        self.create_hierarchies(orgs, users_by_org)
        self.stdout.write(self.style.SUCCESS('✅ Created hierarchies'))

        # Create subjects for courses
        subjects = self.create_subjects()
        self.stdout.write(self.style.SUCCESS('✅ Created subjects'))

        # Create content
        self.create_content(orgs, users_by_org, subjects)
        self.stdout.write(self.style.SUCCESS('✅ Created content'))

        # Create course banners
        self.create_course_banners(orgs, users_by_org)
        self.stdout.write(self.style.SUCCESS('✅ Created course banners'))

        # Create publications (feeds/wikis)
        self.create_publications(orgs, users_by_org)
        self.stdout.write(self.style.SUCCESS('✅ Created publications'))

        # Create documents
        self.create_documents(orgs, users_by_org)
        self.stdout.write(self.style.SUCCESS('✅ Created documents'))

        self.stdout.write(self.style.SUCCESS('\n✨ Seed complete!'))

    def clear_existing_data(self):
        """Clear existing seed data"""
        self.stdout.write('Clearing existing data...')
        # Delete content first (it has FK to users)
        ContentTrail.objects.filter(slug__contains='-trail-').delete()
        Course.objects.filter(slug__contains='-course-').delete()
        Publication.objects.all().delete()
        Document.objects.all().delete()
        # Then delete users and orgs
        User.objects.filter(email__endswith='@example.com').delete()
        Organization.objects.filter(is_public=False).delete()
        self.stdout.write('✅ Cleared')

    def create_organizations(self):
        """Create realistic organizations"""
        orgs_config = [
            {
                'name': 'Hospital Generative',
                'slug': 'hospital-generative',
                'description': 'Healthcare organization focused on patient education and compliance training',
                'terminology': {
                    'level_1_label': 'Departamento',
                    'level_2_label': 'Setor',
                    'level_3_label': 'Equipe',
                }
            },
            {
                'name': 'Seguradora Generative',
                'slug': 'seguradora-generative',
                'description': 'Insurance company with compliance and regulatory requirements',
                'terminology': {
                    'level_1_label': 'Regional',
                    'level_2_label': 'Agência',
                    'level_3_label': 'Filial',
                }
            },
            {
                'name': 'Escola Generative',
                'slug': 'escola-generative',
                'description': 'Educational institution managing student-parent relationships',
                'terminology': {
                    'level_1_label': 'Série',
                    'level_2_label': 'Turma',
                    'level_3_label': 'Disciplina',
                }
            },
            {
                'name': 'Manufatura XYZ',
                'slug': 'manufatura-xyz',
                'description': 'Manufacturing company: New lines in 5 days, proven safety, <1% error',
                'terminology': {
                    'level_1_label': 'Fábrica',
                    'level_2_label': 'Linha de Produção',
                    'level_3_label': 'Estação',
                }
            },
            {
                'name': 'Retail 800',
                'slug': 'retail-800',
                'description': 'Retail network: 800 stores, one standard, consistent service',
                'terminology': {
                    'level_1_label': 'Região',
                    'level_2_label': 'Loja',
                    'level_3_label': 'Departamento',
                }
            },
            {
                'name': 'FinTech Rapido',
                'slug': 'fintech-rapido',
                'description': 'Fintech: Product certified in 5 days, automated compliance',
                'terminology': {
                    'level_1_label': 'Produto',
                    'level_2_label': 'Equipe',
                    'level_3_label': 'Squad',
                }
            },
            {
                'name': 'Farmalab Biotech',
                'slug': 'farmalab-biotech',
                'description': 'Pharmaceutical company: Medical representatives, doctor visits, products, bulletins',
                'terminology': {
                    'level_1_label': 'Região Comercial',
                    'level_2_label': 'Área de Vendas',
                    'level_3_label': 'Representante',
                }
            },
        ]

        orgs = {}
        for config in orgs_config:
            org, created = Organization.objects.get_or_create(
                slug=config['slug'],
                defaults={
                    'name': config['name'],
                    'description': config['description'],
                    'active': True,
                    'is_public': False,
                }
            )

            # Create terminology
            terminology_data = config.get('terminology', {})
            if terminology_data:
                from configuration.models import OrganizationTerminology
                OrganizationTerminology.objects.update_or_create(
                    organization=org,
                    defaults=terminology_data
                )

            orgs[config['slug']] = org
            status = '📝 Created' if created else '✓ Exists'
            self.stdout.write(f'  {status}: {org.name}')

        return orgs

    def create_users(self, orgs):
        """Create users for each organization"""
        users_by_org = {}

        for org_slug, org in orgs.items():
            users_by_org[org_slug] = {}

            # Admin user
            admin_user, _ = User.objects.get_or_create(
                email=f'admin-{org_slug}@example.com',
                defaults={
                    'username': f'admin_{org_slug}',
                    'first_name': 'Admin',
                    'last_name': org.name.split()[0],
                    'is_staff': True,
                    'is_active': True,
                }
            )
            Membership.objects.get_or_create(
                user=admin_user,
                organization=org,
                defaults={'role': 'admin', 'active': True, 'is_primary': True}
            )
            users_by_org[org_slug]['admin'] = admin_user

            # Manager users (2 per org)
            for i in range(2):
                manager_user, _ = User.objects.get_or_create(
                    email=f'manager{i+1}-{org_slug}@example.com',
                    defaults={
                        'username': f'manager{i+1}_{org_slug}',
                        'first_name': f'Manager {i+1}',
                        'last_name': org.name.split()[0],
                        'is_active': True,
                    }
                )
                Membership.objects.get_or_create(
                    user=manager_user,
                    organization=org,
                    defaults={'role': 'manager', 'active': True, 'is_primary': True}
                )
                if 'managers' not in users_by_org[org_slug]:
                    users_by_org[org_slug]['managers'] = []
                users_by_org[org_slug]['managers'].append(manager_user)

            # Regular users (5 per org)
            users_by_org[org_slug]['members'] = []
            for i in range(5):
                member_user, _ = User.objects.get_or_create(
                    email=f'user{i+1}-{org_slug}@example.com',
                    defaults={
                        'username': f'user{i+1}_{org_slug}',
                        'first_name': f'User {i+1}',
                        'last_name': org.name.split()[0],
                        'is_active': True,
                    }
                )
                Membership.objects.get_or_create(
                    user=member_user,
                    organization=org,
                    defaults={'role': 'member', 'active': True, 'is_primary': True}
                )
                users_by_org[org_slug]['members'].append(member_user)

            self.stdout.write(f'  Created users for {org.name}')

        return users_by_org

    def create_admin_access(self, orgs, users_by_org):
        """Create admin/superuser with access to all organizations"""
        admin_password = 'Admin@Talk123!'

        # Create or get superadmin user
        superadmin, created = User.objects.get_or_create(
            email='superadmin@example.com',
            defaults={
                'username': 'superadmin',
                'first_name': 'Super',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        superadmin.set_password(admin_password)
        superadmin.save()

        # Give superadmin membership in all organizations with is_primary
        for org_slug, org in orgs.items():
            membership, _ = Membership.objects.get_or_create(
                user=superadmin,
                organization=org,
                defaults={
                    'role': 'admin',
                    'active': True,
                    'is_primary': (org_slug == list(orgs.keys())[0]),  # First org is primary
                }
            )

        # Set password for all org admins
        for org_slug, org in orgs.items():
            admin_user = users_by_org[org_slug].get('admin')
            if admin_user:
                admin_user.set_password(admin_password)
                admin_user.save()

    def create_subjects(self):
        """Create subject categories for courses"""
        subjects_config = ['Compliance', 'Safety', 'Operations', 'Customer Service', 'Product Training']
        subjects = {}

        for subject_name in subjects_config:
            subject, _ = Subject.objects.get_or_create(
                title=subject_name,
                defaults={'slug': subject_name.lower().replace(' ', '-')}
            )
            subjects[subject_name] = subject

        return subjects

    def create_hierarchies(self, orgs, users_by_org):
        """Create group hierarchies for each organization"""

        for org_slug, org in orgs.items():
            org_users = users_by_org[org_slug]

            # Hierarchy 1: Department/Team structure (3 levels)
            hierarchy_dept, _ = GroupHierarchyType.objects.get_or_create(
                organization=org,
                code='departments',
                defaults={
                    'name': 'Department Structure',
                    'description': 'Organizational hierarchy by department and teams',
                    'max_levels': 3,
                    'allow_links': False,
                    'active': True,
                }
            )

            # Create level 1 nodes (departments)
            l1_node, _ = GroupNode.objects.get_or_create(
                hierarchy_type=hierarchy_dept,
                code='dept_main',
                defaults={
                    'name': 'Main Department',
                    'level': 1,
                    'active': True,
                }
            )

            # Create level 2 nodes (teams)
            l2_node, _ = GroupNode.objects.get_or_create(
                hierarchy_type=hierarchy_dept,
                code='team_operations',
                parent_node=l1_node,
                defaults={
                    'name': 'Operations Team',
                    'level': 2,
                    'active': True,
                }
            )

            # Create level 3 nodes (sub-teams)
            l3_node, _ = GroupNode.objects.get_or_create(
                hierarchy_type=hierarchy_dept,
                code='squad_a',
                parent_node=l2_node,
                defaults={
                    'name': 'Squad A',
                    'level': 3,
                    'active': True,
                }
            )

            # Add members to nodes
            if 'managers' in org_users and org_users['managers']:
                manager = org_users['managers'][0]
                UserGroupMembership.objects.get_or_create(
                    user=manager,
                    group_node=l1_node,
                    defaults={'role': 'admin', 'status': 'active'}
                )

            for idx, member in enumerate(org_users.get('members', [])[:3]):
                node = [l2_node, l3_node, l3_node][idx % 3]
                UserGroupMembership.objects.get_or_create(
                    user=member,
                    group_node=node,
                    defaults={'role': 'member', 'status': 'active'}
                )

            # Hierarchy 2: Parents/Relationships (1 level, with linking)
            hierarchy_parents, _ = GroupHierarchyType.objects.get_or_create(
                organization=org,
                code='parents',
                defaults={
                    'name': 'Parent-Student Relationships',
                    'description': 'Links between parents and students for monitoring',
                    'max_levels': 1,
                    'allow_links': True,
                    'active': True,
                }
            )

            parent_node, _ = GroupNode.objects.get_or_create(
                hierarchy_type=hierarchy_parents,
                code='parents_group',
                defaults={
                    'name': 'Parents',
                    'level': 1,
                    'active': True,
                }
            )

            # Add parent-student links if enough users
            if len(org_users.get('members', [])) >= 2:
                parent = org_users['members'][0]
                student = org_users['members'][1]
                UserGroupMembership.objects.get_or_create(
                    user=parent,
                    group_node=parent_node,
                    linked_user=student,
                    defaults={'role': 'admin', 'status': 'active'}
                )

            self.stdout.write(f'  Hierarchies created for {org.name}')

            # Special hierarchy for pharma company
            if org_slug == 'farmalab-biotech' and org_slug in org_users:
                self.create_pharma_hierarchy(org, org_users[org_slug])

    def create_content(self, orgs, users_by_org, subjects):
        """Create example content for each organization"""

        content_templates = {
            'hospital-generative': {
                'courses': [
                    {'title': 'Patient Safety 101', 'description': 'Essential safety protocols', 'subject': 'Safety'},
                    {'title': 'HIPAA Compliance', 'description': 'Patient data protection', 'subject': 'Compliance'},
                ],
                'trails': [
                    {'title': 'New Employee Onboarding', 'description': 'Complete orientation program'},
                ]
            },
            'seguradora-generative': {
                'courses': [
                    {'title': 'Insurance Regulations', 'description': 'Compliance and regulatory requirements', 'subject': 'Compliance'},
                    {'title': 'Customer Service Excellence', 'description': 'Service standards', 'subject': 'Customer Service'},
                ],
                'trails': [
                    {'title': 'Compliance Training', 'description': 'Annual compliance certification'},
                ]
            },
            'escola-generative': {
                'courses': [
                    {'title': 'School Policies', 'description': 'Rules and regulations', 'subject': 'Compliance'},
                    {'title': 'Curriculum Overview', 'description': 'Course offerings', 'subject': 'Product Training'},
                ],
                'trails': [
                    {'title': 'Parent Orientation', 'description': 'Introduction to school'},
                ]
            },
            'manufatura-xyz': {
                'courses': [
                    {'title': 'Safety First', 'description': 'Proven safety protocols', 'subject': 'Safety'},
                    {'title': 'Quality Standards', 'description': '<1% error quality training', 'subject': 'Operations'},
                ],
                'trails': [
                    {'title': 'Production Line Certification', 'description': '5-day certification program'},
                ]
            },
            'retail-800': {
                'courses': [
                    {'title': 'Brand Standards', 'description': 'One standard, 800 stores', 'subject': 'Compliance'},
                    {'title': 'Customer Service', 'description': 'Consistent service excellence', 'subject': 'Customer Service'},
                ],
                'trails': [
                    {'title': 'Store Management', 'description': 'Complete store operations'},
                ]
            },
            'fintech-rapido': {
                'courses': [
                    {'title': 'Regulatory Compliance', 'description': 'Automated compliance training', 'subject': 'Compliance'},
                    {'title': 'Product Certification', 'description': '5-day certification', 'subject': 'Product Training'},
                ],
                'trails': [
                    {'title': 'Compliance Automation', 'description': 'Quick integration program'},
                ]
            },
            'farmalab-biotech': {
                'courses': [
                    {'title': 'Medical Representative Training', 'description': 'Complete training for sales representatives', 'subject': 'Product Training'},
                    {'title': 'Regulatory & Compliance for Pharma', 'description': 'Pharmaceutical regulatory compliance', 'subject': 'Compliance'},
                    {'title': 'Product Portfolio 2024', 'description': 'Complete drug portfolio and specifications', 'subject': 'Product Training'},
                ],
                'trails': [
                    {'title': 'Onboarding for Medical Reps', 'description': 'Complete medical representative certification'},
                    {'title': 'Doctor Visit Protocol', 'description': 'Best practices for medical visits'},
                ]
            },
        }

        for org_slug, org in orgs.items():
            templates = content_templates.get(org_slug, {'courses': [], 'trails': []})

            # Get admin user for this org
            org_admin = users_by_org[org_slug].get('admin')
            if not org_admin:
                continue

            # Create courses
            for idx, course_config in enumerate(templates.get('courses', [])):
                subject = subjects.get(course_config.get('subject', 'Product Training'), list(subjects.values())[0])
                title = course_config['title']
                slug = f"{org_slug}-course-{idx+1}"

                course, created = Course.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'organization': org,
                        'title': title,
                        'type': 'course',
                        'overview': course_config['description'],
                        'state': 'unpublished',
                        'owner': org_admin,
                        'author': org_admin,
                        'subject': subject,
                    }
                )

            # Create trails
            for idx, trail_config in enumerate(templates.get('trails', [])):
                slug = f"{org_slug}-trail-{idx+1}"
                trail, _ = ContentTrail.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'organization': org,
                        'title': trail_config['title'],
                        'objective': trail_config.get('description', ''),
                        'trail_type': ContentTrail.RECOMMENDED,
                        'status': ContentTrail.DRAFT,
                        'owner': org_admin,
                    }
                )

            self.stdout.write(f'  Content created for {org.name}')

    def create_pharma_hierarchy(self, org, org_users):
        """Create pharmaceutical-specific hierarchy: Regional > Área > Representante"""

        # Create main hierarchy
        hierarchy_pharma, _ = GroupHierarchyType.objects.get_or_create(
            organization=org,
            code='sales_structure',
            defaults={
                'name': 'Sales Structure',
                'description': 'Commercial hierarchy: Regional > Area > Representatives',
                'max_levels': 3,
                'allow_links': True,  # Allow linking doctors to representatives
                'active': True,
            }
        )

        org_admin = org_users.get('admin')
        if not org_admin:
            return

        # Level 1: Regional offices
        regions = ['Southeast Region', 'Northeast Region', 'South Region']
        region_nodes = {}

        for region_name in regions:
            region_node, _ = GroupNode.objects.get_or_create(
                hierarchy_type=hierarchy_pharma,
                code=region_name.lower().replace(' ', '_'),
                defaults={
                    'name': region_name,
                    'level': 1,
                    'active': True,
                    'metadata': {'type': 'regional_office', 'region': region_name}
                }
            )
            region_nodes[region_name] = region_node

            # Add regional manager
            if 'managers' in org_users and org_users['managers']:
                manager = org_users['managers'][0 if region_name == 'Southeast Region' else 1]
                UserGroupMembership.objects.get_or_create(
                    user=manager,
                    group_node=region_node,
                    defaults={'role': 'admin', 'status': 'active'}
                )

        # Level 2: Sales Areas
        areas_map = {
            'Southeast Region': ['São Paulo Area', 'Rio de Janeiro Area'],
            'Northeast Region': ['Bahia Area', 'Pernambuco Area'],
            'South Region': ['Rio Grande do Sul Area', 'Santa Catarina Area'],
        }

        area_nodes = {}
        for region_name, areas in areas_map.items():
            region_node = region_nodes[region_name]

            for area_name in areas:
                area_code = area_name.lower().replace(' ', '_')
                area_node, _ = GroupNode.objects.get_or_create(
                    hierarchy_type=hierarchy_pharma,
                    code=area_code,
                    parent_node=region_node,
                    defaults={
                        'name': area_name,
                        'level': 2,
                        'active': True,
                        'metadata': {'type': 'sales_area', 'region': region_name}
                    }
                )
                area_nodes[area_name] = area_node

        # Level 3: Medical Representatives
        reps = [
            {'name': 'João Silva', 'area': 'São Paulo Area', 'specialty': 'Cardiology'},
            {'name': 'Maria Santos', 'area': 'São Paulo Area', 'specialty': 'Oncology'},
            {'name': 'Pedro Costa', 'area': 'Rio de Janeiro Area', 'specialty': 'Neurology'},
            {'name': 'Ana Oliveira', 'area': 'Bahia Area', 'specialty': 'General Practice'},
        ]

        for idx, rep_info in enumerate(reps):
            area_node = area_nodes.get(rep_info['area'])
            if not area_node:
                continue

            rep_code = f"rep_{idx+1}_{rep_info['name'].lower().replace(' ', '_')}"
            rep_node, _ = GroupNode.objects.get_or_create(
                hierarchy_type=hierarchy_pharma,
                code=rep_code,
                parent_node=area_node,
                defaults={
                    'name': rep_info['name'],
                    'level': 3,
                    'active': True,
                    'metadata': {
                        'type': 'medical_representative',
                        'specialty': rep_info['specialty'],
                        'doctors_visited': 0,
                    }
                }
            )

            # Add member as representative
            if idx < len(org_users.get('members', [])):
                member = org_users['members'][idx]
                UserGroupMembership.objects.get_or_create(
                    user=member,
                    group_node=rep_node,
                    defaults={
                        'role': 'member',
                        'status': 'active',
                        'metadata': {'function': 'Medical Representative', 'specialty': rep_info['specialty']}
                    }
                )

    def create_publications(self, orgs, users_by_org):
        """Create publications (Feed and Wiki) for each organization"""

        publications_config = {
            'hospital-generative': [
                {
                    'title': 'New Hospital Protocol Update',
                    'body': 'We are pleased to announce the new patient safety protocols effective immediately. All staff must review and acknowledge.',
                    'kind': Publication.FEED,
                    'status': Publication.PUBLISHED,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'HIPAA Compliance Guidelines',
                    'body': 'Complete guide to HIPAA compliance for all healthcare professionals. Includes best practices and common mistakes to avoid.',
                    'kind': Publication.WIKI,
                    'status': Publication.PUBLISHED,
                    'importance': Publication.CRITICAL,
                },
                {
                    'title': 'Emergency Response Procedures',
                    'body': 'Step-by-step emergency response procedures for various medical situations.',
                    'kind': Publication.WIKI,
                    'status': Publication.PUBLISHED,
                    'importance': Publication.CRITICAL,
                },
            ],
            'seguradora-generative': [
                {
                    'title': 'New Insurance Product Launch',
                    'body': 'Introducing our new comprehensive insurance product for small businesses.',
                    'kind': Publication.FEED,
                    'status': Publication.PUBLISHED,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Claims Processing Guide',
                    'body': 'Complete guide to processing insurance claims efficiently.',
                    'kind': Publication.WIKI,
                    'status': Publication.PUBLISHED,
                    'importance': Publication.ROUTINE,
                },
                {
                    'title': 'Regulatory Updates Q4 2024',
                    'body': 'Important regulatory changes affecting insurance operations.',
                    'kind': Publication.FEED,
                    'status': Publication.PUBLISHED,
                    'importance': Publication.IMPORTANT,
                },
            ],
            'escola-generative': [
                {
                    'title': 'Academic Calendar 2024',
                    'body': 'Important dates and deadlines for the 2024 academic year.',
                    'kind': Publication.FEED,
                    'status': Publication.PUBLISHED,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Student Conduct Policy',
                    'body': 'School policies and expectations for student behavior.',
                    'kind': Publication.WIKI,
                    'status': Publication.PUBLISHED,
                    'importance': Publication.ROUTINE,
                },
            ],
            'manufatura-xyz': [
                {
                    'title': 'Safety Alert: New Equipment',
                    'body': 'Critical safety information about newly installed manufacturing equipment.',
                    'kind': Publication.FEED,
                    'status': Publication.PUBLISHED,
                    'importance': Publication.CRITICAL,
                },
                {
                    'title': 'Quality Control Procedures',
                    'body': 'Detailed procedures for quality control achieving <1% error rate.',
                    'kind': Publication.WIKI,
                    'status': Publication.PUBLISHED,
                    'importance': Publication.IMPORTANT,
                },
            ],
            'retail-800': [
                {
                    'title': 'Brand Standards Update',
                    'body': 'Updated brand guidelines for all 800 stores ensuring one consistent standard.',
                    'kind': Publication.FEED,
                    'status': Publication.PUBLISHED,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Customer Service Best Practices',
                    'body': 'Comprehensive guide to providing excellent customer service across all locations.',
                    'kind': Publication.WIKI,
                    'status': Publication.PUBLISHED,
                    'importance': Publication.ROUTINE,
                },
            ],
            'fintech-rapido': [
                {
                    'title': 'Regulatory Compliance Update',
                    'body': 'Latest regulatory requirements and compliance checklist.',
                    'kind': Publication.FEED,
                    'status': Publication.PUBLISHED,
                    'importance': Publication.CRITICAL,
                },
                {
                    'title': 'Product Security Guidelines',
                    'body': 'Security protocols and best practices for fintech products.',
                    'kind': Publication.WIKI,
                    'status': Publication.PUBLISHED,
                    'importance': Publication.CRITICAL,
                },
            ],
            'farmalab-biotech': [
                {
                    'title': 'Medical Representative Territory Updates',
                    'body': 'Territory assignments and market updates for all representatives.',
                    'kind': Publication.FEED,
                    'status': Publication.PUBLISHED,
                    'importance': Publication.IMPORTANT,
                },
                {
                    'title': 'Product Information Database',
                    'body': 'Complete product information, dosages, and clinical data for all medications.',
                    'kind': Publication.WIKI,
                    'status': Publication.PUBLISHED,
                    'importance': Publication.CRITICAL,
                },
                {
                    'title': 'Doctor Visit Report Form',
                    'body': 'Template and guide for completing doctor visit reports.',
                    'kind': Publication.WIKI,
                    'status': Publication.PUBLISHED,
                    'importance': Publication.ROUTINE,
                },
            ],
        }

        for org_slug, org in orgs.items():
            pubs = publications_config.get(org_slug, [])
            org_admin = users_by_org[org_slug].get('admin')
            if not org_admin:
                continue

            for idx, pub_config in enumerate(pubs):
                slug = slugify(f"{pub_config['title']}-{org_slug}-{idx}")
                publication, _ = Publication.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'organization': org,
                        'title': pub_config['title'],
                        'kind': pub_config['kind'],
                        'status': pub_config['status'],
                        'importance': pub_config.get('importance', Publication.ROUTINE),
                        'body': pub_config['body'],
                        'excerpt': pub_config['body'][:150],
                        'author': org_admin,
                        'published_at': timezone.now(),
                    }
                )

            self.stdout.write(f'  Publications created for {org.name}')

    def create_documents(self, orgs, users_by_org):
        """Create documents for each organization"""

        documents_config = {
            'hospital-generative': [
                {'title': 'Patient Safety Manual', 'description': 'Complete patient safety procedures'},
                {'title': 'HIPAA Compliance Document', 'description': 'Legal compliance documentation'},
                {'title': 'Emergency Protocols', 'description': 'Emergency response procedures'},
            ],
            'seguradora-generative': [
                {'title': 'Insurance Policy Templates', 'description': 'Standard policy documents'},
                {'title': 'Claims Processing Manual', 'description': 'Claims handling procedures'},
                {'title': 'Regulatory Compliance Guide', 'description': 'Regulatory requirements'},
            ],
            'escola-generative': [
                {'title': 'Academic Handbook', 'description': 'Student and faculty handbook'},
                {'title': 'Curriculum Documentation', 'description': 'Course descriptions and requirements'},
            ],
            'manufatura-xyz': [
                {'title': 'Safety Manual', 'description': 'Comprehensive safety guide'},
                {'title': 'Quality Standards Document', 'description': 'Quality control procedures'},
                {'title': 'Equipment Operation Guide', 'description': 'Machinery operation manual'},
            ],
            'retail-800': [
                {'title': 'Brand Guidelines Manual', 'description': 'Brand identity and standards'},
                {'title': 'Store Operations Manual', 'description': 'Standard operating procedures'},
                {'title': 'Customer Service Guide', 'description': 'Service standards and protocols'},
            ],
            'fintech-rapido': [
                {'title': 'Security Compliance Document', 'description': 'Security protocols and procedures'},
                {'title': 'API Documentation', 'description': 'Technical API specifications'},
                {'title': 'Regulatory Framework', 'description': 'Compliance requirements'},
            ],
            'farmalab-biotech': [
                {'title': 'Product Catalog', 'description': 'Complete product information and specifications'},
                {'title': 'Medical Representative Handbook', 'description': 'Guidelines for medical representatives'},
                {'title': 'Clinical Trial Data', 'description': 'Clinical research and trial results'},
                {'title': 'Regulatory Documentation', 'description': 'FDA and regulatory approvals'},
            ],
        }

        for org_slug, org in orgs.items():
            docs = documents_config.get(org_slug, [])
            org_admin = users_by_org[org_slug].get('admin')
            if not org_admin:
                continue

            for idx, doc_config in enumerate(docs):
                slug = slugify(f"{doc_config['title']}-{org_slug}-{idx}")
                document, _ = Document.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'organization': org,
                        'title': doc_config['title'],
                        'description': doc_config['description'],
                        'status': Document.PUBLISHED,
                        'owner': org_admin,
                    }
                )

            self.stdout.write(f'  Documents created for {org.name}')

    def create_course_banners(self, orgs, users_by_org):
        """Create placeholder banner images for all courses"""
        org_colors = {
            'hospital-generative': '#2E7D32',  # Green
            'seguradora-generative': '#1565C0',  # Blue
            'escola-generative': '#F57C00',  # Orange
            'manufatura-xyz': '#C62828',  # Red
            'retail-800': '#6A1B9A',  # Purple
            'fintech-rapido': '#00796B',  # Teal
            'farmalab-biotech': '#0277BD',  # Light Blue
        }

        for org_slug, org in orgs.items():
            color = org_colors.get(org_slug, '#1976D2')
            courses = Course.objects.filter(organization=org)

            for idx, course in enumerate(courses):
                if course.banner:
                    continue

                img = Image.new('RGB', (1200, 400), color=color)
                draw = ImageDraw.Draw(img)

                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
                    small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
                except:
                    font = ImageFont.load_default()
                    small_font = ImageFont.load_default()

                text = course.title[:40]
                org_text = org.name

                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                text_x = (1200 - text_width) // 2
                text_y = (400 - text_height) // 2 - 40

                draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)

                org_bbox = draw.textbbox((0, 0), org_text, font=small_font)
                org_width = org_bbox[2] - org_bbox[0]
                org_x = (1200 - org_width) // 2
                org_y = text_y + text_height + 20

                draw.text((org_x, org_y), org_text, fill=(255, 255, 255), font=small_font)

                img_io = io.BytesIO()
                img.save(img_io, format='PNG')
                img_io.seek(0)

                course.banner.save(
                    f'{slugify(course.title)}-banner.png',
                    ContentFile(img_io.getvalue()),
                    save=True
                )

            self.stdout.write(f'  Banners created for {org.name} courses')

    def delete_existing_test_data(self):
        """Delete existing test/example data"""
        User.objects.filter(email__endswith='@example.com').delete()
        Organization.objects.filter(slug__in=[
            'hospital-generative',
            'seguradora-generative',
            'escola-generative',
            'manufatura-xyz',
            'retail-800',
            'fintech-rapido',
            'farmalab-biotech',
        ]).delete()
