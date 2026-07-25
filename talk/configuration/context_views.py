from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .organization_context import set_selected_organization


@login_required
def select_organization(request):
    if request.method == 'POST':
        set_selected_organization(request, request.POST.get('organization'))
    return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER') or '/')
