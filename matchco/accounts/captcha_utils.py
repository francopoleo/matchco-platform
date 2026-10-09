import requests
from django.conf import settings


def verify_recaptcha_v3(token, action='signup'):
    """
    Verify reCAPTCHA v3 token with Google.
    Returns (is_valid, score) tuple.
    """
    if not settings.RECAPTCHA_PRIVATE_KEY:
        # In development without CAPTCHA keys, always pass
        return True, 1.0

    try:
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': settings.RECAPTCHA_PRIVATE_KEY,
                'response': token,
            },
            timeout=5
        )
        data = response.json()

        if data.get('success'):
            score = data.get('score', 0)
            action_match = data.get('action') == action

            if action_match and score >= getattr(settings, 'RECAPTCHA_REQUIRED_SCORE', 0.85):
                return True, score

        return False, data.get('score', 0)
    except Exception as e:
        # Log error but don't block on network issues
        import logging
        logging.error(f"CAPTCHA verification failed: {e}")
        # Fail open in development, fail closed in production
        return getattr(settings, 'DEBUG', False), 0
