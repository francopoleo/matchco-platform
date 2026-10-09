from .organization_context import selected_organization
from django.db import connection


class OrganizationContextMiddleware:
    """Expose the session-selected tenant to audience and application views."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.active_organization = selected_organization(request)
        if getattr(request.user, 'is_authenticated', False):
            request.user._active_organization_id = getattr(request.active_organization, 'pk', None)
        # The tenant schema is normally selected from the request host by
        # TenantMainMiddleware, which runs before this middleware.  The
        # organization switcher is an explicit workspace switch, so selected
        # organizations must also switch the schema used by tenant models
        # (courses, publications, learning data, etc.).
        if request.active_organization is not None:
            request.tenant = request.active_organization
            connection.set_tenant(request.active_organization)
        return self.get_response(request)
