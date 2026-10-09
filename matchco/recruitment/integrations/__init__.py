"""Integration boundary for the recruitment bounded context.

Recruitment owns its workflow. Integrations with the rest of MatchCo are
implemented behind ports and are loaded lazily, so an optional product can be
absent without preventing recruitment from starting.
"""

from .registry import get_ai_port, get_assessment_port, get_file_port, get_identity_port, get_notification_port

__all__ = [
    'get_assessment_port',
    'get_file_port',
    'get_identity_port',
    'get_notification_port',
    'get_ai_port',
]
