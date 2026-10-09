from django.utils import timezone
from rest_framework.authentication import BaseAuthentication, SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed

from configuration.models import IntegrationCredential


class IntegrationAPIKeyAuthentication(BaseAuthentication):
    """Authenticate partner calls with ``X-MatchCo-API-Key`` or ``ApiKey``."""

    keyword = 'apikey'

    def authenticate_header(self, request):
        return self.keyword

    def authenticate(self, request):
        raw_key = request.headers.get('X-MatchCo-API-Key', '').strip()
        authorization = request.headers.get('Authorization', '')
        if not raw_key and authorization.lower().startswith('apikey '):
            raw_key = authorization[7:].strip()
        if not raw_key:
            return None
        credential = IntegrationCredential.objects.select_related('created_by', 'organization').filter(
            key_hash=IntegrationCredential.hash_key(raw_key), active=True,
        ).first()
        if not credential or (credential.expires_at and credential.expires_at <= timezone.now()):
            raise AuthenticationFailed('API key inválida, expirada ou revogada.')
        credential.last_used_at = timezone.now()
        credential.save(update_fields=('last_used_at',))
        request.integration_credential = credential
        return credential.created_by, credential


class IntegrationSessionAuthentication(SessionAuthentication):
    """Session auth remains available for the Console and local API testing."""
