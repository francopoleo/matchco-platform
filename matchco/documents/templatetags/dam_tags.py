from django import template

register = template.Library()


@register.filter
def media_metric(asset, name):
    return getattr(asset, name, 0)
