"""
Signals para sincronizar dados de SHARED_APPS para TENANT_APPS

Quando um usuário, organização ou company é criado/modificado em schema público,
estes signals garantem que os dados sejam espelhados em todos os schemas tenant.
"""

from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django_tenants.utils import get_tenant_model, tenant_context

from .models import Organization, Company, Membership, MembershipAudit

User = get_user_model()


def _membership_snapshot(instance):
    return {
        'organization_id': instance.organization_id,
        'company_id': instance.company_id,
        'business_unit_id': instance.business_unit_id,
        'operational_unit_id': instance.operational_unit_id,
        'role': instance.role,
        'is_primary': instance.is_primary,
        'active': instance.active,
        'person_type_id': instance.person_type_id,
    }


@receiver(pre_save, sender=Membership)
def capture_membership_before_save(sender, instance, **kwargs):
    if not instance.pk:
        instance._membership_audit_old = {}
        return
    previous = sender.objects.filter(pk=instance.pk).first()
    instance._membership_audit_old = _membership_snapshot(previous) if previous else {}


@receiver(post_save, sender=Membership)
def audit_membership_save(sender, instance, created, **kwargs):
    old_values = getattr(instance, '_membership_audit_old', {})
    new_values = _membership_snapshot(instance)
    if not created and old_values == new_values:
        return
    changed_scope = any(old_values.get(field) != new_values.get(field) for field in (
        'organization_id', 'company_id', 'business_unit_id', 'operational_unit_id',
    ))
    changed_role = old_values.get('role') != new_values.get('role')
    if created:
        action = 'created'
    elif old_values.get('active') != new_values.get('active'):
        action = 'activated' if instance.active else 'deactivated'
    elif changed_role:
        action = 'role_changed'
    elif changed_scope:
        action = 'scope_changed'
    else:
        action = 'updated'
    MembershipAudit.objects.create(
        membership=instance,
        user=instance.user,
        action=action,
        old_values=old_values,
        new_values=new_values,
        reason='automatic_membership_audit',
    )


@receiver(pre_delete, sender=Membership)
def audit_membership_delete(sender, instance, **kwargs):
    MembershipAudit.objects.create(
        membership=instance,
        user=instance.user,
        action='deleted',
        old_values=_membership_snapshot(instance),
        reason='automatic_membership_audit',
    )


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
                with tenant_context(tenant):
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
                with tenant_context(tenant):
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

        tenant = Tenant.objects.filter(schema_name=instance.schema_name).first()
        if tenant:
            try:
                with tenant_context(tenant):
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

        tenant = Tenant.objects.filter(schema_name=instance.schema_name).first()
        if tenant:
            try:
                with tenant_context(tenant):
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

        tenant = Tenant.objects.filter(pk=instance.organization_id).first()
        if tenant:
            try:
                with tenant_context(tenant):
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

        tenant = Tenant.objects.filter(pk=instance.organization_id).first()
        if tenant:
            try:
                with tenant_context(tenant):
                    TenantCompany.objects.filter(company_id=instance.id).delete()
            except Exception as e:
                print(f"Erro ao deletar company {instance.id} de tenant {tenant.slug}: {e}")
    except Exception as e:
        print(f"Erro geral em delete_company_from_tenants: {e}")
