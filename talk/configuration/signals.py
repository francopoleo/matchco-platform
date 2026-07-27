"""
Signals para sincronizar dados de SHARED_APPS para TENANT_APPS

Quando um usuário, organização ou company é criado/modificado em schema público,
estes signals garantem que os dados sejam espelhados em todos os schemas tenant.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django_tenants.utils import get_tenant_model

from .models import Organization, Company

User = get_user_model()


@receiver(post_save, sender=User)
def sync_user_to_tenants(sender, instance, created, **kwargs):
    """
    Sincroniza usuário para todos os schemas tenant quando criado/modificado
    """
    try:
        from tenants_core.models import TenantUser

        Tenant = get_tenant_model()

        # Sincronizar em cada schema tenant
        for tenant in Tenant.objects.exclude(schema_name='public'):
            try:
                tenant.activate()
                TenantUser.objects.update_or_create(
                    user_id=instance.id,
                    defaults={
                        'username': instance.username,
                        'email': instance.email,
                        'first_name': instance.first_name,
                        'last_name': instance.last_name,
                        'is_active': instance.is_active,
                    }
                )
            except Exception as e:
                print(f"Erro ao sincronizar user {instance.id} para tenant {tenant.slug}: {e}")
    except Exception as e:
        print(f"Erro geral em sync_user_to_tenants: {e}")


@receiver(post_delete, sender=User)
def delete_user_from_tenants(sender, instance, **kwargs):
    """
    Remove usuário de todos os schemas tenant quando deletado
    """
    try:
        from tenants_core.models import TenantUser

        Tenant = get_tenant_model()

        for tenant in Tenant.objects.exclude(schema_name='public'):
            try:
                tenant.activate()
                TenantUser.objects.filter(user_id=instance.id).delete()
            except Exception as e:
                print(f"Erro ao deletar user {instance.id} de tenant {tenant.slug}: {e}")
    except Exception as e:
        print(f"Erro geral em delete_user_from_tenants: {e}")


@receiver(post_save, sender=Organization)
def sync_organization_to_tenants(sender, instance, created, **kwargs):
    """
    Sincroniza organização para todos os schemas tenant
    """
    try:
        from tenants_core.models import TenantOrganization

        Tenant = get_tenant_model()

        # Não sincronizar a organização pública para ela mesma
        if instance.schema_name == 'public':
            return

        for tenant in Tenant.objects.exclude(schema_name='public'):
            try:
                tenant.activate()
                TenantOrganization.objects.update_or_create(
                    organization_id=instance.id,
                    defaults={
                        'name': instance.name,
                        'slug': instance.slug,
                    }
                )
            except Exception as e:
                print(f"Erro ao sincronizar org {instance.id} para tenant {tenant.slug}: {e}")
    except Exception as e:
        print(f"Erro geral em sync_organization_to_tenants: {e}")


@receiver(post_delete, sender=Organization)
def delete_organization_from_tenants(sender, instance, **kwargs):
    """
    Remove organização de todos os schemas tenant
    """
    try:
        from tenants_core.models import TenantOrganization

        Tenant = get_tenant_model()

        for tenant in Tenant.objects.exclude(schema_name='public'):
            try:
                tenant.activate()
                TenantOrganization.objects.filter(organization_id=instance.id).delete()
            except Exception as e:
                print(f"Erro ao deletar org {instance.id} de tenant {tenant.slug}: {e}")
    except Exception as e:
        print(f"Erro geral em delete_organization_from_tenants: {e}")


@receiver(post_save, sender=Company)
def sync_company_to_tenants(sender, instance, created, **kwargs):
    """
    Sincroniza company para todos os schemas tenant
    """
    try:
        from tenants_core.models import TenantCompany

        Tenant = get_tenant_model()

        for tenant in Tenant.objects.exclude(schema_name='public'):
            try:
                tenant.activate()
                TenantCompany.objects.update_or_create(
                    company_id=instance.id,
                    defaults={
                        'name': instance.name,
                    }
                )
            except Exception as e:
                print(f"Erro ao sincronizar company {instance.id} para tenant {tenant.slug}: {e}")
    except Exception as e:
        print(f"Erro geral em sync_company_to_tenants: {e}")


@receiver(post_delete, sender=Company)
def delete_company_from_tenants(sender, instance, **kwargs):
    """
    Remove company de todos os schemas tenant
    """
    try:
        from tenants_core.models import TenantCompany

        Tenant = get_tenant_model()

        for tenant in Tenant.objects.exclude(schema_name='public'):
            try:
                tenant.activate()
                TenantCompany.objects.filter(company_id=instance.id).delete()
            except Exception as e:
                print(f"Erro ao deletar company {instance.id} de tenant {tenant.slug}: {e}")
    except Exception as e:
        print(f"Erro geral em delete_company_from_tenants: {e}")
