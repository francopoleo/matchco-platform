from django import template

register = template.Library()


@register.filter
def level_label(terminology, level):
    """Get terminology label for hierarchy level (1, 2, or 3)."""
    if not terminology:
        defaults = {1: 'Empresa', 2: 'Unidade de negócio', 3: 'Unidade operacional'}
        return defaults.get(level, '')

    level_map = {
        1: terminology.level_1_label,
        2: terminology.level_2_label,
        3: terminology.level_3_label,
    }
    return level_map.get(level, '')


@register.filter
def level_description(terminology, level):
    """Get terminology description for hierarchy level (1, 2, or 3)."""
    if not terminology:
        return ''

    level_map = {
        1: terminology.level_1_description,
        2: terminology.level_2_description,
        3: terminology.level_3_description,
    }
    return level_map.get(level, '')
