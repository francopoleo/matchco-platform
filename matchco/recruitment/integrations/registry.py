"""Lazy adapter registry.

Adapters are configured with dotted paths in ``RECRUITMENT_INTEGRATIONS``.
Missing optional apps therefore do not cause import-time failures.
"""

from django.conf import settings
from django.utils.module_loading import import_string

from .defaults import (
    NullAssessmentAdapter,
    NullFileAdapter,
    NullAIMatchingAdapter,
    NullIdentityAdapter,
    NullNotificationAdapter,
)


_DEFAULTS = {
    'identity': NullIdentityAdapter,
    'assessment': NullAssessmentAdapter,
    'notification': NullNotificationAdapter,
    'file': NullFileAdapter,
    'ai': NullAIMatchingAdapter,
}


def _get(name):
    configured = getattr(settings, 'RECRUITMENT_INTEGRATIONS', {}).get(name)
    implementation = import_string(configured) if configured else _DEFAULTS[name]
    return implementation()


def get_identity_port():
    return _get('identity')


def get_assessment_port():
    return _get('assessment')


def get_notification_port():
    return _get('notification')


def get_file_port():
    return _get('file')


def get_ai_port():
    return _get('ai')
