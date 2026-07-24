from django import template

from ..models import ContentItemProgress

register = template.Library()


@register.simple_tag
def get_library_items(module):
    return module.library_items.filter(published=True)


@register.simple_tag
def library_item_is_done(item, user):
    return ContentItemProgress.objects.filter(item=item, user=user, completed=True).exists()
