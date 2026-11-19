from django.shortcuts import redirect

from .models import Organization


SESSION_KEY = 'selected_organization_id'


def available_organizations(user):
    if not getattr(user, 'is_authenticated', False):
        return Organization.objects.none()
    if getattr(user, 'is_superuser', False):
        return Organization.objects.filter(active=True, is_public=False).order_by('name')
    ids = user.memberships.filter(active=True).values_list('organization_id', flat=True).distinct()
    return Organization.objects.filter(active=True, is_public=False, pk__in=ids).order_by('name')


def selected_organization(request):
    organizations = available_organizations(request.user)
    if not organizations.exists():
        return None

    # Check session for explicitly selected org
    selected_id = request.session.get(SESSION_KEY)

    # "__all__" means superadmin viewing all organizations
    if selected_id == '__all__':
        return None

    if selected_id:
        organization = organizations.filter(pk=selected_id).first()
        if organization:
            return organization

    # Fall back to primary membership
    primary = getattr(request.user, 'primary_membership', None)
    if primary:
        organization = organizations.filter(pk=primary.organization_id).first()
        if organization:
            return organization

    # Fall back to first available organization
    return organizations.first()


def set_selected_organization(request, organization_id):
    organization = available_organizations(request.user).filter(pk=organization_id).first()
    if organization is None:
        return False
    is_superuser = getattr(request.user, 'is_superuser', False)
    membership = None if is_superuser else request.user.memberships.filter(
        organization=organization, active=True,
    ).order_by('-is_primary', '-created_at').first()
    if not is_superuser and membership is None:
        return False

    previous_id = request.session.get(SESSION_KEY)
    previous_company_id = request.session.get('active_company_id')
    previous_membership_id = request.session.get('active_membership_id')
    if previous_id != organization.pk:
        # Company/unit/audience choices are subordinate to the active tenant.
        # Keeping one across a workspace switch can make the UI show one
        # organization while data queries still use the previous scope.
        for key in (
            'active_company_id', 'active_membership_id', 'user_role',
            'matchco_portal_organization_id',
            'matchco_portal_recruitment_organization_id',
            'matchco_portal_store_id', 'matchco_portal_entry_point_id',
            'ep_store_id', 'ep_audience', 'ep_audience_role',
        ):
            request.session.pop(key, None)

    request.session[SESSION_KEY] = organization.pk
    request.session['active_organization_id'] = organization.pk
    request.session.modified = True

    # Keep the current request in sync too. Some administrative views select
    # an organization during dispatch and render immediately instead of
    # redirecting through another request/middleware cycle.
    request.active_organization = organization
    request.active_organization_id = organization.pk
    request.tenant = organization
    if is_superuser:
        request.session.pop('active_membership_id', None)
        request.session['user_role'] = 'owner'
        request.active_membership = None
        request.active_role = 'owner'
        request.active_company_id = request.session.get('active_company_id')
    else:
        request.session['active_membership_id'] = membership.pk
        request.session['active_company_id'] = membership.company_id
        request.session['user_role'] = membership.role
        request.active_membership = membership
        request.active_role = membership.role
        request.active_company_id = membership.company_id
    request.user._active_organization_id = organization.pk
    if previous_id != organization.pk and getattr(request.user, 'is_authenticated', False):
        from .models import Company, Membership, TenantContextEvent
        from configuration.security import client_ip
        previous_org = Organization.objects.filter(pk=previous_id).first() if previous_id and previous_id != '__all__' else None
        TenantContextEvent.objects.create(
            user=request.user,
            actor=request.user,
            from_organization=previous_org,
            to_organization=organization,
            from_company=Company.objects.filter(pk=previous_company_id).first() if previous_company_id else None,
            to_company=Company.objects.filter(pk=request.session.get('active_company_id')).first() if request.session.get('active_company_id') else None,
            from_membership=Membership.objects.filter(pk=previous_membership_id).first() if previous_membership_id else None,
            to_membership=membership,
            ip_address=client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:1000],
        )
    from django.db import connection
    connection.set_tenant(organization)
    return True


def clear_organization_scope(request):
    """Enter the platform-wide view without retaining tenant-specific state."""
    if not getattr(request.user, 'is_superuser', False):
        return False
    for key in (
        SESSION_KEY, 'active_organization_id', 'active_company_id',
        'active_membership_id', 'user_role', 'matchco_portal_organization_id',
        'matchco_portal_recruitment_organization_id', 'matchco_portal_store_id',
        'matchco_portal_entry_point_id', 'ep_store_id', 'ep_audience',
        'ep_audience_role',
    ):
        request.session.pop(key, None)
    request.session[SESSION_KEY] = '__all__'
    request.session.modified = True
    request.active_organization = None
    request.active_organization_id = None
    request.active_company_id = None
    request.active_membership = None
    request.active_role = None
    request.tenant = None
    from django.db import connection
    connection.set_schema_to_public()
    return True
