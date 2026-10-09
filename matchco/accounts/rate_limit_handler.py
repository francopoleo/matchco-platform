from django.http import HttpResponse
from django.shortcuts import render


def get_rate_limit_response(request, exception=None):
    """Handle rate limit errors with user-friendly message"""
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
