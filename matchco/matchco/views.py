from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from django.views.generic import TemplateView, View
from django.views import View as BaseView
from configuration.models import Membership, Organization
from configuration.services import service_enabled
from configuration.organization_context import SESSION_KEY, set_selected_organization


class SmartHomeView(BaseView):
    """
    Página home inteligente que redireciona baseado na autenticação.

    - Usuário NÃO autenticado → Landing page ou /login
    - Usuário autenticado SEM organização → Seletor de organização
    - Qualquer usuário autenticado → Dashboard do app (/app/)
    - O Console é acessado pelo link administrativo próprio.
    """

    def get(self, request, *args, **kwargs):
        # Se não está autenticado
        if not request.user.is_authenticated:
            # Renderiza a entrada institucional na própria raiz. Assim o
            # visitante não é deslocado para uma rota específica de produto.
            return render(request, 'recruitment/matchco_site/platform.html')

        # A raiz é a experiência principal do usuário: cursos, trilhas,
        # Feed, Wiki e notificações. O contexto de organização já aplicado
        # pelo middleware também vale para administradores.
        return redirect('app:dashboard')


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

        # Use the same canonical context switch as the Console navbar. This
        # also clears the previous company's service scope when the tenant
        # changes, including for the legacy selector route.
        if not set_selected_organization(request, org_id):
            return render(request, 'error.html', {
                'message': 'Access denied to this organization'
            }, status=403)
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

    def _clear_stale_tenant_query(self, request, url, target_organization_id):
        """Remove subordinate filters that belong to the previous tenant.

        The navbar deliberately preserves the current page when switching
        organizations.  A URL such as ``/console/courses/?company_id=41``
        cannot be reused after changing to an organization that does not own
        company 41: service access correctly rejects that cross-tenant ID.
        Clearing the company filter here lets the destination render its
        normal empty state instead of surfacing a tenant-mismatch 404.
        """
        current_organization_id = request.session.get(SESSION_KEY)
        if str(current_organization_id) == str(target_organization_id):
            return url

        parts = urlsplit(url or '')
        query = [
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if key != 'company_id'
        ]
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

    def _safe_destination_for_organization(self, url, organization):
        """Avoid landing on a service route unavailable in the new tenant."""
        if not url or organization is None:
            return url
        path = urlsplit(url).path
        service_prefixes = (
            ('/console/certifications/', 'certification'),
            ('/console/courses/', 'training'),
            ('/console/course-modules/', 'training'),
            ('/console/quizzes/', 'training'),
            ('/console/trails/', 'training'),
            ('/console/publications/', 'content'),
            ('/console/documents/', 'content'),
            ('/console/media/', 'content'),
            ('/app/courses/', 'training'),
            ('/app/trails/', 'training'),
            ('/app/feed/', 'content'),
            ('/app/wiki/', 'content'),
        )
        service_code = next((code for prefix, code in service_prefixes if path.startswith(prefix)), None)
        if service_code and not service_enabled(organization, service_code):
            return reverse('console:organization-home') if path.startswith('/console/') else reverse('home')
        return url

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
            from configuration.organization_context import clear_organization_scope
            destination = self._clear_stale_tenant_query(request, safe_next_url, '__all__')
            clear_organization_scope(request)
            response = redirect(destination or 'home')
            response['HX-Trigger-Retry'] = 'orgSwitched'
            return response

        # A superuser can enter any active private organization, even when no
        # explicit Membership row exists for that user.
        if request.user.is_superuser:
            organization = Organization.objects.filter(
                pk=org_id, active=True, is_public=False,
            ).first()
            if organization is None:
                raise PermissionDenied('Access denied to this organization')
            destination = self._clear_stale_tenant_query(request, safe_next_url, organization.pk)
            destination = self._safe_destination_for_organization(destination, organization)
            set_selected_organization(request, organization.pk)
            response = redirect(destination or 'home')
            response['HX-Trigger-Retry'] = 'orgSwitched'
            return response

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

        destination = self._clear_stale_tenant_query(request, safe_next_url, membership.organization_id)
        destination = self._safe_destination_for_organization(destination, membership.organization)
        set_selected_organization(request, membership.organization_id)

        # Invalidate any OBAC caches
        # cache.delete(f'user_{request.user.id}_org_scope')

        # Preserve the current console/frontend page after changing organization.
        response = redirect(destination or 'home')
        response['HX-Trigger-Retry'] = 'orgSwitched'
        return response


@login_required
def no_access_view(request):
    """User has no memberships in any organization"""

    return render(request, 'no_access.html', {
        'message': 'You do not have access to any organization. Please contact your administrator.'
    })
