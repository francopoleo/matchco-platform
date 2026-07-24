from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag(name="get_posthog_key")
def get_posthog_key():
    return settings.POSTHOG_KEY


@register.simple_tag(name="get_posthog_url")
def get_posthog_url():
    return settings.POSTHOG_URL
