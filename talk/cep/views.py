from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import TemplateView, View
from django.views import View as BaseView
from configuration.models import Membership, Organization
from configuration.organization_context import SESSION_KEY


class SmartHomeView(BaseView):
    """
    Página home inteligente que redireciona baseado na autenticação.

    - Usuário NÃO autenticado → Landing page ou /login
    - Usuário autenticado SEM organização → Seletor de organização
    - Usuário autenticado COM organização → Dashboard da app (/app/)
    - Admin → Console admin (/console/)
    """

    def get(self, request, *args, **kwargs):
        # Se não está autenticado
        if not request.user.is_authenticated:
            # Ir para landing page ou login
            return redirect('matchco_landing')  # ou 'login'

        # Se é admin, ir para console
        if request.user.is_staff or request.user.is_superuser:
            return redirect('console_dashboard')

        # Se está autenticado, verificar se tem organização
        selected_org = request.session.get('selected_organization')

        if selected_org:
            # Tem organização selecionada, ir para app/dashboard
            return redirect('app_dashboard')
        else:
            # Precisa selecionar organização
            return redirect('organization_selector')


class OrganizationSelectorView(LoginRequiredMixin, TemplateView):
    """
    Show organization selection page after login.

    Like Slack workspace selector - user picks which organization to work in.
    """

    template_name = 'organization_selector.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get user's active memberships
        memberships = user.memberships.filter(
            active=True
        ).select_related('organization').order_by('-is_primary', '-created_at')

        if not memberships.exists():
            # No access anywhere
            return redirect('no-access')

        context.update({
            'memberships': memberships,
            'membership_count': memberships.count(),
        })

        return context

    def post(self, request, *args, **kwargs):
        """Handle organization selection"""

        org_id = request.POST.get('organization_id')
        next_url = request.POST.get('next', 'home')

        if not org_id:
            return self.get(request, *args, **kwargs)

        try:
            # Validate user has access to this organization
            # If multiple memberships, get the primary one, or the most recent
            memberships = request.user.memberships.filter(
                organization_id=org_id,
                active=True
            ).order_by('-is_primary', '-created_at')

            if not memberships.exists():
                raise Membership.DoesNotExist

            membership = memberships.first()
        except Membership.DoesNotExist:
            return render(request, 'error.html', {
                'message': 'Access denied to this organization'
            }, status=403)

        # Set session (both new and old keys for compatibility)
        request.session['active_organization_id'] = membership.organization_id
        request.session['active_membership_id'] = membership.id
        request.session['active_company_id'] = membership.company_id
        request.session['user_role'] = membership.role
        request.session['selected_organization_id'] = membership.organization_id  # Old key for backward compatibility

        # Log this action (optional)
        # AuditLog.objects.create(
        #     user=request.user,
        #     action='org_selected',
        #     organization_id=org_id,
        #     ip_address=get_client_ip(request),
        # )

        # Redirect to home with new org/company context
        return redirect('home')


class SwitchOrganizationView(LoginRequiredMixin, View):
    """
    Switch active organization (like Slack workspace switch).

    POST request to change active organization in session.
    """

    login_url = 'login'

    def _safe_next_url(self, request, next_url):
        """Keep the user on the current page without allowing an open redirect."""
        if url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return next_url
        return None

    def _current_page_url(self, request, posted_next):
        """Prefer the browser's actual origin page over a stale hidden field."""
        referer = request.META.get('HTTP_REFERER')
        safe_referer = self._safe_next_url(request, referer) if referer else None
        return safe_referer or self._safe_next_url(request, posted_next)

    def post(self, request, *args, **kwargs):
        """Handle organization switch"""

        org_id = request.POST.get('organization_id')
        next_url = request.POST.get('next', 'home')
        safe_next_url = self._current_page_url(request, next_url)

        if not org_id:
            return redirect('home')

        # Superadmin can view all organizations with "__all__"
        if org_id == '__all__':
            if not request.user.is_superuser:
                raise PermissionDenied('Only superadmin can view all organizations')
            # Set marker to see all organizations
            request.session[SESSION_KEY] = '__all__'
            request.session.pop('active_organization_id', None)
            request.session.pop('active_membership_id', None)
            request.session.pop('active_company_id', None)
            request.session.pop('user_role', None)
            request.session.modified = True
            return redirect(safe_next_url or 'home')

        try:
            # Validate user has access to this organization
            # If multiple memberships, get the primary one, or the most recent
            memberships = request.user.memberships.filter(
                organization_id=org_id,
                active=True
            ).order_by('-is_primary', '-created_at')

            if not memberships.exists():
                raise Membership.DoesNotExist

            membership = memberships.first()
        except Membership.DoesNotExist:
            raise PermissionDenied('Access denied to this organization')

        # Update session (both new and old keys for compatibility)
        request.session[SESSION_KEY] = membership.organization_id
        request.session['active_organization_id'] = membership.organization_id
        request.session['active_membership_id'] = membership.id
        request.session['active_company_id'] = membership.company_id
        request.session['user_role'] = membership.role

        # Invalidate any OBAC caches
        # cache.delete(f'user_{request.user.id}_org_scope')

        # Preserve the current console/frontend page after changing organization.
        return redirect(safe_next_url or 'home')


@login_required
def no_access_view(request):
    """User has no memberships in any organization"""

    return render(request, 'no_access.html', {
        'message': 'You do not have access to any organization. Please contact your administrator.'
    })
