from .menu import get_menu_items


DEFAULT_TERMINOLOGY = {
    'level_1_label': 'Empresa',
    'level_1_description': 'Organização empresarial ou grupo econômico.',
    'level_2_label': 'Unidade de negócio',
    'level_2_description': 'Divisão, operação, filial ou localidade.',
    'level_3_label': 'Unidade operacional',
    'level_3_description': 'Departamento, serviço ou equipe dentro da unidade.',
}


def navigation(request):
    area = "console" if request.path.startswith("/console/") else "frontend"
    terminology = DEFAULT_TERMINOLOGY.copy()
    if getattr(request.user, 'is_authenticated', False):
        membership = request.user.primary_membership
        configured = getattr(getattr(membership, 'organization', None), 'terminology', None)
        if configured:
            for key in terminology:
                terminology[key] = getattr(configured, key)
    return {
        "navigation_area": area,
        "navigation_items": get_menu_items(request, area),
        "organization_terminology": terminology,
    }
