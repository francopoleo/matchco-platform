"""Shared navigation model for the frontend and management console."""

from django.urls import reverse, NoReverseMatch
from django.utils.translation import gettext_lazy as _


MENU_ITEMS = (
    {"label": _("Home"), "url": "home", "icon": "home", "areas": ("frontend",)},
    {"label": _("Courses"), "url": "course_list", "icon": "course", "areas": ("frontend", "console")},
    {"label": _("Feed"), "url": "publication_feed_list", "icon": "feed", "areas": ("frontend",)},
    {"label": _("Wiki"), "url": "publication_list", "icon": "wiki", "areas": ("frontend",)},
    {"label": _("Search"), "url": "search", "icon": "search", "areas": ("frontend",)},
    {"label": _("Profile"), "url": "user_management_profile:user_profile_detail", "icon": "profile", "areas": ("frontend",), "auth": True},
    {"label": _("Gamification"), "url": "user_management_profile:user_gamification_points", "icon": "game", "areas": ("frontend",), "auth": True},
    {"label": _("Publications"), "url": "console:publication-list", "icon": "wiki", "areas": ("console",), "staff": True},
    {"label": _("Audience policies"), "url": "console:policy-list", "icon": "policy", "areas": ("console",), "staff": True},
    {"label": _("Audience simulator"), "url": "console:audience-simulation", "icon": "search", "areas": ("console",), "staff": True},
    {"label": _("Assign users"), "url": "console:assignment", "icon": "profile", "areas": ("console",), "staff": True},
    {"label": _("Management roles"), "url": "console:management-assignments", "icon": "policy", "areas": ("console",), "staff": True},
    {"label": _("Subordinate reports"), "url": "console:management-reports", "icon": "feed", "areas": ("console",), "staff": True},
    {"label": _("Management console"), "url": "console:dashboard", "icon": "console", "areas": ("frontend",), "staff": True},
)


def get_menu_items(request, area):
    """Return only resolvable, authorized links for the requested shell."""
    items = []
    for item in MENU_ITEMS:
        if area not in item["areas"]:
            continue
        if item.get("auth") and not request.user.is_authenticated:
            continue
        if item.get("staff") and not (request.user.is_staff or request.user.is_superuser):
            continue
        try:
            kwargs = {"pk": request.user.pk} if item["url"].endswith(("user_profile_detail", "user_gamification_points")) else {}
            item = {**item, "href": reverse(item["url"], kwargs=kwargs)}
        except NoReverseMatch:
            continue
        items.append(item)
    return items
