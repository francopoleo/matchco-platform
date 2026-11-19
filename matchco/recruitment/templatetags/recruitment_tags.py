from django import template

register = template.Library()

DAY_LABELS = {
    'mon': 'segunda',
    'tue': 'terça',
    'wed': 'quarta',
    'thu': 'quinta',
    'fri': 'sexta',
    'sat': 'sábado',
    'sun': 'domingo',
}


@register.filter
def get_dict_value(dictionary, key):
    """Get a value from a dictionary in templates."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''


@register.filter
def translate_days(days_list):
    """Translate day abbreviations (mon, tue, etc.) to Portuguese."""
    if not days_list:
        return ''
    if isinstance(days_list, list):
        return ', '.join(DAY_LABELS.get(day, day) for day in days_list)
    return str(days_list)
