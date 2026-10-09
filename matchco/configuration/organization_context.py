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
    request.session[SESSION_KEY] = organization.pk
    request.session.modified = True
    return True
