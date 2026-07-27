"""Utility functions for multi-tenant operations."""
from django.db.models import QuerySet
from tenants_core.models import TenantUser


def get_tenant_user(user):
    """Convert User to TenantUser if needed. Returns TenantUser or None."""
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    if isinstance(user, TenantUser):
        return user
    return TenantUser.objects.filter(user_id=user.id).first()


def ensure_tenant_user(user_or_users):
    """
    Convert User instance(s) to TenantUser.

    Args:
        user_or_users: A User instance, queryset, list of Users, or TenantUser

    Returns:
        TenantUser instance/queryset or None if not found/not authenticated
    """
    if isinstance(user_or_users, TenantUser):
        return user_or_users

    if hasattr(user_or_users, 'is_authenticated'):
        # Single User instance
        return get_tenant_user(user_or_users)

    if isinstance(user_or_users, QuerySet):
        # Queryset of User instances - convert to TenantUser queryset
        user_ids = user_or_users.values_list('id', flat=True)
        return TenantUser.objects.filter(user_id__in=user_ids)

    if isinstance(user_or_users, (list, tuple)):
        # List/tuple of User instances
        if not user_or_users:
            return []
        user_ids = [u.id for u in user_or_users if hasattr(u, 'id')]
        return TenantUser.objects.filter(user_id__in=user_ids)

    return None
