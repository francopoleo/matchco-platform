from .menu import get_menu_items, group_menu_items
from configuration.organization_context import available_organizations, selected_organization
from django.conf import settings


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
    navigation_items = get_menu_items(request, area)
    terminology = DEFAULT_TERMINOLOGY.copy()
    organizations = available_organizations(request.user)
    active_organization = selected_organization(request)
    if active_organization:
        configured = getattr(active_organization, 'terminology', None)
    elif getattr(request.user, 'is_authenticated', False):
        membership = request.user.primary_membership
        configured = getattr(getattr(membership, 'organization', None), 'terminology', None)
    else:
        configured = None
        if configured:
            for key in terminology:
                terminology[key] = getattr(configured, key)
    return {
        "navigation_area": area,
        "navigation_items": navigation_items,
        "navigation_groups": group_menu_items(navigation_items),
        "organization_terminology": terminology,
        "available_organizations": organizations,
        "selected_organization": active_organization,
        "TALK_VAPID_PUBLIC_KEY": getattr(settings, 'TALK_VAPID_PUBLIC_KEY', ''),
    }
