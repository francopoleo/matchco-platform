from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib.auth import get_user_model, authenticate, login
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.db import connection
from django.utils.decorators import method_decorator
from configuration.models import Organization, Domain, Membership
from tenants_core.models import TenantUser
from django_tenants.utils import schema_context, get_public_schema_name
import json

User = get_user_model()


@method_decorator(ensure_csrf_cookie, name='get')
@method_decorator(csrf_protect, name='post')
class SetupView(TemplateView):
    template_name = 'configuration/setup.html'

    def dispatch(self, request, *args, **kwargs):
        with schema_context(get_public_schema_name()):
            return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check if setup is needed
        has_admin = User.objects.filter(is_superuser=True).exists()
        has_orgs = Organization.objects.exists()

        context['needs_setup'] = not has_admin or not has_orgs
        context['has_admin'] = has_admin
        context['has_orgs'] = has_orgs
        context['organizations'] = Organization.objects.all()

        return context

    def post(self, request):
        data = json.loads(request.body)
        action = data.get('action')

        if action == 'create_admin':
            return self.create_admin(data)
        elif action == 'create_organization':
            return self.create_organization(data)
        elif action == 'test_domain':
            return self.test_domain(data)
        elif action == 'get_status':
            return self.get_status()

        return JsonResponse({'error': 'Invalid action'}, status=400)

    def create_admin(self, data):
        """Create superadmin user"""
        try:
            username = data.get('username', 'admin')
            email = data.get('email', 'admin@talk.local')
            password = data.get('password', '')

            if not username or not email or not password:
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            admin, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': True,
                    'is_superuser': True,
                }
            )

            if created:
                admin.set_password(password)
                admin.save()
                return JsonResponse({
                    'success': True,
                    'message': f'Superadmin "{username}" created',
                    'username': username
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': f'Superadmin "{username}" already exists',
                    'username': username
                })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def create_organization(self, data):
        """Create organization with domain and membership"""
        try:
            name = data.get('name', '')
            domain = data.get('domain', '')
            description = data.get('description', '')
            admin_username = data.get('admin_username', 'admin')

            if not name or not domain:
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            # Get admin user
            admin = User.objects.get(username=admin_username)

            # Create slug and schema
            slug = name.lower().replace(' ', '-')
            schema_name = slug[:63]

            # Create organization
            org, org_created = Organization.objects.get_or_create(
                schema_name=schema_name,
                defaults={
                    'name': name,
                    'slug': slug,
                    'description': description,
                    'active': True,
                }
            )

            # Create domain
            domain_obj, domain_created = Domain.objects.get_or_create(
                domain=domain,
                defaults={
                    'tenant': org,
                    'is_primary': not Organization.objects.exists()
                }
            )

            # Create membership
            membership, mem_created = Membership.objects.get_or_create(
                user=admin,
                organization=org,
                defaults={
                    'role': 'admin',
                    'is_primary': not Membership.objects.filter(user=admin).exists()
                }
            )

            # Create TenantUser
            with schema_context(schema_name):
                tenant_user, _ = TenantUser.objects.get_or_create(
                    user_id=admin.id,
                    defaults={
                        'username': admin.username,
                        'email': admin.email,
                    }
                )

            return JsonResponse({
                'success': True,
                'message': f'Organization "{name}" created',
                'organization': {
                    'id': org.id,
                    'name': org.name,
                    'domain': domain,
                    'schema_name': schema_name,
                    'url': f'http://{domain}/login/'
                }
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def test_domain(self, data):
        """Test if domain is accessible"""
        domain = data.get('domain', '')
        if not domain:
            return JsonResponse({'error': 'Domain required'}, status=400)

        # Check if domain is already registered
        exists = Domain.objects.filter(domain=domain).exists()

        return JsonResponse({
            'available': not exists,
            'message': 'Domain already registered' if exists else 'Domain available'
        })

    def get_status(self):
        """Get setup status"""
        has_admin = User.objects.filter(is_superuser=True).exists()
        has_orgs = Organization.objects.exists()
        orgs_count = Organization.objects.count()

        return JsonResponse({
            'has_admin': has_admin,
            'has_organizations': has_orgs,
            'organizations_count': orgs_count,
            'organizations': list(
                Organization.objects.values('id', 'name', 'schema_name')
            )
        })
