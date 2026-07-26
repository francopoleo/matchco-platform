from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


def email_verification_required(view_func):
    """
    Decorator to ensure user has verified email before accessing view.
    Redirects unverified users to verification pending page.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            # Check if user has verified email
            if not request.user.is_active:
                messages.warning(
                    request,
                    'Por favor confirme seu email para acessar esta página.'
                )
                return redirect('public-signup-confirmation', category='candidates')

            # For public users, also check if they have an active membership
            from configuration.models import Membership
            try:
                active_org_id = request.session.get('active_organization_id')
                if active_org_id:
                    membership = Membership.objects.get(
                        user=request.user,
                        organization_id=active_org_id
                    )
                    if not membership.active:
                        messages.warning(
                            request,
                            'Sua membressia ainda está sendo processada. Confirme seu email para ativar.'
                        )
                        return redirect('public-signup-confirmation', category='candidates')
            except Membership.DoesNotExist:
                pass

        return view_func(request, *args, **kwargs)

    return wrapper
