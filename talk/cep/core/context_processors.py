from .menu import get_menu_items


def navigation(request):
    area = "console" if request.path.startswith("/console/") else "frontend"
    return {
        "navigation_area": area,
        "navigation_items": get_menu_items(request, area),
    }
