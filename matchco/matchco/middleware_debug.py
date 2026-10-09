import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class DebugMiddleware(MiddlewareMixin):
    def process_request(self, request):
        logger.warning(f"REQUEST DEBUG:")
        logger.warning(f"  HTTP_HOST: {request.META.get('HTTP_HOST')}")
        logger.warning(f"  SERVER_NAME: {request.META.get('SERVER_NAME')}")
        logger.warning(f"  SERVER_PORT: {request.META.get('SERVER_PORT')}")
        logger.warning(f"  PATH: {request.path}")
        return None
