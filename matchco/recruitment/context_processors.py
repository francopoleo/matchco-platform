"""Contexto visual comum dos portais externos."""


def portal_context(request):
    """Expose organization/store scope to portal shells without trusting UI."""
    if not request.path.startswith('/portal/') or not request.user.is_authenticated:
        return {}

    from .portal_views import _lojista_org, _portal_store_scope

    actor, org = _lojista_org(request)
    stores, selected_store, filtered = _portal_store_scope(request, actor=actor, org=org)
    return {
        'portal_scope_organization': org,
        'portal_scope_actor': actor,
        'portal_scope_stores': stores,
        'portal_selected_store': selected_store,
        'portal_store_filter_active': filtered,
        'portal_can_choose_store': bool(
            request.user.is_superuser or (actor and actor.business_unit_id is None)
        ),
    }
