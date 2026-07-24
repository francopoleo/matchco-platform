from django import template

from cep.utils import filter_entries

register = template.Library()


@register.simple_tag(name="filter_related_entries")
def filter_related_entries(entries, user):
    res = filter_entries(entries, user)
    return res