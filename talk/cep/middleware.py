from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from configuration.models import Membership, Organization


class ActiveOrganizationMiddleware:
    """
    Manages active organization context for multi-tenant support.

    Like Slack: maintains active workspace for current user session.
    - Validates user has membership in selected organization
    - Prevents access if membership is revoked during session
    - Auto-selects if user has only one organization
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            redirect_response = self._set_active_org(request)
            if redirect_response:
                return redirect_response

        response = self.get_response(request)
        return response

    def _set_active_org(self, request):
        """Ensure active organization is set and valid for user"""

        # Skip for certain paths
        if self._should_skip_org_check(request):
            return None

        org_id = request.session.get('active_organization_id')

        # No active org selected - select one
        if not org_id:
            return self._select_default_organization(request)

        # Validate membership still exists and is active
        try:
            membership = request.user.memberships.get(
                organization_id=org_id,
                active=True
            )
            # Attach to request for use in views
            request.active_organization_id = org_id
            request.active_membership = membership
            request.active_role = membership.role
            request.active_company_id = membership.company_id

        except Membership.DoesNotExist:
            # Access revoked during session or org changed
            return self._handle_access_revoked(request, org_id)

        return None

    def _select_default_organization(self, request):
        """Select default organization for user (primary or first active)"""

        # Check for organization selector pages
        if 'select-organization' in request.path or 'logout' in request.path:
            return None

        # Get user's organizations
        memberships = request.user.memberships.filter(
            active=True
        ).select_related('organization')

        if not memberships.exists():
            # No organizations - redirect to no-access page
            if not any(x in request.path for x in ['logout', 'no-access']):
                return redirect('no-access')
            return None

        # Auto-select primary or first organization
        primary = memberships.filter(is_primary=True).first()
        membership = primary or memberships.order_by('created_at').first()

        request.session['active_organization_id'] = membership.organization_id
        request.session['active_membership_id'] = membership.id
        request.session['user_role'] = membership.role
        request.session['selected_organization_id'] = membership.organization_id  # Old key for backward compatibility

        # Attach to request
        request.active_organization_id = membership.organization_id
        request.active_membership = membership
        request.active_role = membership.role
        request.active_company_id = membership.company_id

        return None

    def _handle_access_revoked(self, request, org_id):
        """Handle case where user's access to organization was revoked"""

        # Clear from session
        if 'active_organization_id' in request.session:
            del request.session['active_organization_id']

        # Check if user has other organizations
        other_memberships = request.user.memberships.filter(
            active=True
        ).exclude(organization_id=org_id)

        if other_memberships.exists():
            # Switch to another organization
            membership = other_memberships.filter(is_primary=True).first() or other_memberships.first()
            request.session['active_organization_id'] = membership.organization_id
            request.session['active_membership_id'] = membership.id
            request.session['user_role'] = membership.role

            # Access was revoked, redirect to re-select
            if not self._should_skip_org_check(request):
                raise PermissionDenied(
                    'Your access to the previous organization was revoked. '
                    'Switched to another organization.'
                )
            return None
        else:
            # No other organizations - logout
            from django.contrib.auth import logout
            logout(request)
            return redirect('login')

    def _should_skip_org_check(self, request):
        """Determine if this request should skip org validation"""

        skip_paths = [
            '/logout',
            '/login',
            '/select-organization',
            '/no-access',
            '/api/',
            '/static/',
            '/media/',
        ]

        return any(request.path.startswith(path) for path in skip_paths)
