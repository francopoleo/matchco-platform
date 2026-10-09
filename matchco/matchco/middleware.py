from django.conf import settings
from django.middleware.locale import LocaleMiddleware
from django.utils.translation import get_supported_language_variant
from django.shortcuts import redirect
from configuration.models import Membership, Organization


class DefaultPortugueseLocaleMiddleware(LocaleMiddleware):
    """Use Brazilian Portuguese until a person explicitly chooses a language.

    Django's default locale negotiation follows the browser's Accept-Language
    header. MatchCo intentionally starts in pt-BR and changes language only
    after a supported session/cookie preference has been saved.
    """

    def process_request(self, request):
        language_cookie = settings.LANGUAGE_COOKIE_NAME
        selected_language = request.COOKIES.get(language_cookie)
        try:
            if selected_language:
                get_supported_language_variant(selected_language)
        except LookupError:
            selected_language = None

        if not selected_language:
            request.COOKIES[language_cookie] = settings.LANGUAGE_CODE

        return super().process_request(request)


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

        # OrganizationContextMiddleware uses this marker for the explicit
        # superadmin "all organizations" view.  Do not auto-select the
        # primary membership in that mode, otherwise the next middleware
        # silently reintroduces a tenant filter.
        if request.session.get('selected_organization_id') == '__all__':
            request.active_organization_id = None
            request.active_membership = None
            request.active_role = None
            request.active_company_id = None
            request.user._active_organization_id = None
            return None

        # Skip for certain paths
        if self._should_skip_org_check(request):
            return None

        org_id = request.session.get('active_organization_id')

        # No active org selected - select one
        if not org_id:
            return self._select_default_organization(request)

        # Superusers can work across all active private organizations without
        # one Membership row per tenant. The switch view deliberately stores
        # the selected organization for them, so do not treat the absence of
        # a membership as revoked access on the following request.
        if request.user.is_superuser:
            organization = Organization.objects.filter(
                pk=org_id, active=True, is_public=False,
            ).first()
            if organization:
                request.active_organization_id = organization.pk
                request.active_membership = None
                request.active_role = 'owner'
                request.active_company_id = None
                request.user._active_organization_id = organization.pk
                return None

        # Validate membership still exists and is active
        memberships = request.user.memberships.filter(
            organization_id=org_id,
            active=True
        ).order_by('-is_primary', '-created_at')

        if not memberships.exists():
            # Access revoked during session or org changed
            return self._handle_access_revoked(request, org_id)

        # Get the primary membership or most recent
        membership = memberships.first()

        # Attach to request for use in views
        request.active_organization_id = org_id
        request.active_membership = membership
        request.active_role = membership.role
        request.active_company_id = membership.company_id

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
            request.session['selected_organization_id'] = membership.organization_id
            request.session['active_company_id'] = membership.company_id
            request.session['user_role'] = membership.role

            # Access was revoked: continue safely in the organization that is
            # still available instead of returning a confusing 403 after the
            # fallback has already been selected.
            return redirect('home')
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


class HTMXMiddleware:
    """Detects HTMX requests and marks them for content-only rendering."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.is_htmx = request.headers.get('HX-Request') == 'true' or request.GET.get('_htmx') == '1'
        response = self.get_response(request)
        return response
