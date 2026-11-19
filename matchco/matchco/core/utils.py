"""Utility functions for multi-tenant operations."""
import hashlib
from django.db.models import QuerySet
from tenants_core.models import TenantUser, TenantOrganization, TenantCompany


def get_tenant_user(user):
    """Convert User to TenantUser if needed. Returns TenantUser or None."""
    if isinstance(user, TenantUser):
        return user
    if not user or not getattr(user, 'is_authenticated', False):
        return None
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


def get_tenant_organization(organization):
    """Convert Organization to TenantOrganization if needed. Returns TenantOrganization or None."""
    if not organization:
        return None
    if isinstance(organization, TenantOrganization):
        return organization
    # organization_id is the PK of TenantOrganization
    return TenantOrganization.objects.filter(organization_id=organization.id).first()


def get_tenant_company(company):
    """Convert Company to TenantCompany if needed. Returns TenantCompany or None."""
    if not company:
        return None
    if isinstance(company, TenantCompany):
        return company
    # company_id is the PK of TenantCompany
    return TenantCompany.objects.filter(company_id=company.id).first()


def compute_file_checksum(file):
    """Compute SHA256 checksum of a file, preserving seek position."""
    if not file:
        return ''
    digest = hashlib.sha256()
    try:
        current_position = file.tell()
    except (AttributeError, ValueError):
        current_position = 0
    try:
        try:
            file.seek(0)
        except (OSError, ValueError):
            opener = getattr(file, 'open', None)
            if not opener:
                return ''
            opener('rb')
            file.seek(0)
        for chunk in file.chunks():
            digest.update(chunk)
        return digest.hexdigest()
    finally:
        # Django's upload handlers/storage backends may close the underlying
        # stream after ``chunks()``. Restoring the cursor is best effort and
        # must not turn a successful checksum into a failed form submission.
        try:
            file.seek(current_position)
        except (AttributeError, OSError, ValueError):
            pass
