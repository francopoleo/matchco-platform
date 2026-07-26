"""Shared navigation model for the frontend and management console."""

from django.urls import reverse, NoReverseMatch
from django.utils.translation import gettext_lazy as _


MENU_ITEMS = (
    {"label": _("Home"), "url": "home", "icon": "home", "areas": ("frontend",), "group": "start"},
    {"label": _("Courses"), "url": "course_list", "icon": "course", "areas": ("frontend",), "group": "content"},
    {"label": _("Minhas trilhas"), "url": "student_trail_list", "icon": "course", "areas": ("frontend",), "auth": True, "group": "content"},
    {"label": _("Notificações"), "url": "notifications", "icon": "feed", "areas": ("frontend",), "auth": True, "group": "start"},
    {"label": _("Feed"), "url": "publication_feed_list", "icon": "feed", "areas": ("frontend",), "group": "content"},
    {"label": _("Wiki"), "url": "publication_list", "icon": "wiki", "areas": ("frontend",), "group": "content"},
    {"label": _("Documentos"), "url": "document-list", "icon": "wiki", "areas": ("frontend",), "auth": True, "group": "content"},
    {"label": _("Search"), "url": "search", "icon": "search", "areas": ("frontend",), "group": "content"},
    {"label": _("Profile"), "url": "user_management_profile:user_profile_detail", "icon": "profile", "areas": ("frontend",), "auth": True, "group": "account"},
    {"label": _("Gamification"), "url": "user_management_profile:user_gamification_points", "icon": "game", "areas": ("frontend",), "auth": True, "group": "account"},
    {"label": _("Visão geral"), "url": "console:dashboard", "icon": "console", "areas": ("console",), "staff": True, "group": "start"},
    {"label": _("Courses"), "url": "console:course-list", "icon": "course", "areas": ("console",), "staff": True, "group": "content"},
    {"label": _("Publications"), "url": "console:publication-list", "icon": "wiki", "areas": ("console",), "staff": True, "group": "content"},
    {"label": _("Documentos"), "url": "console:document-list", "icon": "wiki", "areas": ("console",), "staff": True, "group": "content"},
    {"label": _("Métricas de conteúdo"), "url": "console:content-metrics", "icon": "feed", "areas": ("console",), "staff": True, "group": "intelligence"},
    {"label": _("Funil de engajamento"), "url": "console:engagement-funnel", "icon": "feed", "areas": ("console",), "staff": True, "group": "intelligence"},
    {"label": _("Métricas de aprendizagem"), "url": "console:learning-metrics", "icon": "course", "areas": ("console",), "staff": True, "group": "intelligence"},
    {"label": _("Dúvidas e feedback"), "url": "console:content-questions", "icon": "feed", "areas": ("console",), "staff": True, "group": "intelligence"},
    {"label": _("Auditoria de conteúdos"), "url": "console:latest-changes", "icon": "feed", "areas": ("console",), "staff": True, "group": "intelligence"},
    {"label": _("Trilhas e recomendações"), "url": "console:trail-list", "icon": "course", "areas": ("console",), "staff": True, "group": "content"},
    {"label": _("Simulador de audiência"), "url": "console:audience-simulation", "icon": "search", "areas": ("console",), "staff": True, "group": "audience"},
    {"label": _("Atribuir usuários"), "url": "console:assignment", "icon": "profile", "areas": ("console",), "staff": True, "group": "people"},
    {"label": _("Usuários"), "url": "console:user-list", "icon": "profile", "areas": ("console",), "staff": True, "group": "people"},
    {"label": _("Solicitações de cadastro"), "url": "console:registration-requests", "icon": "profile", "areas": ("console",), "staff": True, "group": "people"},
    {"label": _("Visitas de demonstração"), "url": "console:demo-visits", "icon": "feed", "areas": ("console",), "staff": True, "group": "organization"},
    {"label": _("Terminologia da organização"), "url": "console:organization-settings", "icon": "policy", "areas": ("console",), "staff": True, "group": "organization"},
    {"label": _("Papéis de gestão"), "url": "console:management-assignments", "icon": "policy", "areas": ("console",), "staff": True, "group": "organization"},
    {"label": _("Relatórios subordinados"), "url": "console:management-reports", "icon": "feed", "areas": ("console",), "staff": True, "group": "organization"},
    {"label": _("Management console"), "url": "console:dashboard", "icon": "console", "areas": ("frontend",), "staff": True, "group": "management"},
)


def get_menu_items(request, area):
    """Return only resolvable, authorized links for the requested shell."""
    items = []
    can_manage_console = (
        request.user.is_authenticated and (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.groups.filter(name__in=("content_manager", "audience_manager")).exists()
        )
    )
    for item in MENU_ITEMS:
        if area not in item["areas"]:
            continue
        if item.get("auth") and not request.user.is_authenticated:
            continue
        if item.get("staff") and not can_manage_console:
            continue
        try:
            kwargs = {"pk": request.user.pk} if item["url"].endswith(("user_profile_detail", "user_gamification_points")) else {}
            item = {**item, "href": reverse(item["url"], kwargs=kwargs)}
            item["active"] = request.path == item["href"].split("?", 1)[0]
        except NoReverseMatch:
            continue
        items.append(item)
    return items


GROUPS = {
    "start": _("Início"),
    "content": _("Conteúdo"),
    "intelligence": _("Inteligência"),
    "audience": _("Audiência"),
    "people": _("Pessoas"),
    "organization": _("Organização"),
    "account": _("Conta"),
    "management": _("Gestão"),
}


def get_menu_groups(request, area):
    return group_menu_items(get_menu_items(request, area))


def group_menu_items(items):
    groups = []
    by_key = {}
    for item in items:
        key = item.get("group", "content")
        if key not in by_key:
            by_key[key] = {"key": key, "label": GROUPS.get(key, key), "items": []}
            groups.append(by_key[key])
        by_key[key]["items"].append(item)
        by_key[key]["active"] = by_key[key].get("active", False) or item.get("active", False)
    return groups
