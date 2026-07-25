from django.http import HttpResponseForbidden

from user_management.demo_tracking import track_demo_request


class DemoReadOnlyMiddleware:
    """Prevents demo accounts from changing application state."""

    ALLOWED_POST_PATHS = ('/logout/', '/organization/select/', '/i18n/setlang/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if getattr(user, 'is_authenticated', False) and getattr(user, 'is_demo', False):
            if request.method not in ('GET', 'HEAD', 'OPTIONS') and not request.path.startswith(self.ALLOWED_POST_PATHS):
                return HttpResponseForbidden('A conta de demonstração é somente para navegação.')
            track_demo_request(request)
        return self.get_response(request)
