from django.shortcuts import render
from django.http import HttpResponse
from django_ratelimit.exceptions import Ratelimited


class RateLimitMiddleware:
    """Handle RateLimited exceptions and return proper 429 response"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Ratelimited:
            if request.method == 'POST':
                return render(
                    request,
                    'rate_limit_error.html',
                    {
                        'error': 'Muitas tentativas. Por favor tente novamente em 1 hora.',
                        'message': 'Por segurança, limitamos o número de tentativas de login e signup.'
                    },
                    status=429
                )
            return HttpResponse('Rate limit exceeded', status=429)
        return response
