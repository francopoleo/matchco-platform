from .organization_context import selected_organization


class OrganizationContextMiddleware:
    """Expose the session-selected tenant to audience and application views."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.active_organization = selected_organization(request)
        if getattr(request.user, 'is_authenticated', False):
            request.user._active_organization_id = getattr(request.active_organization, 'pk', None)
        return self.get_response(request)
