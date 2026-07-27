"""Utility functions for multi-tenant operations."""
from tenants_core.models import TenantUser


def get_tenant_user(user):
    """Convert User to TenantUser if needed. Returns TenantUser or None."""
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    if isinstance(user, TenantUser):
        return user
    return TenantUser.objects.filter(user_id=user.id).first()
