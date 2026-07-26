from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from configuration.models import Membership, Organization


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
            is_active=True
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
            membership = request.user.memberships.get(
                organization_id=org_id,
                is_active=True
            )
        except Membership.DoesNotExist:
            return render(request, 'error.html', {
                'message': 'Access denied to this organization'
            }, status=403)

        # Set session
        request.session['active_organization_id'] = membership.organization_id
        request.session['active_membership_id'] = membership.id
        request.session['user_role'] = membership.role

        # Log this action (optional)
        # AuditLog.objects.create(
        #     user=request.user,
        #     action='org_selected',
        #     organization_id=org_id,
        #     ip_address=get_client_ip(request),
        # )

        return redirect(next_url)


class SwitchOrganizationView(LoginRequiredMixin, TemplateView):
    """
    Switch active organization (like Slack workspace switch).

    POST request to change active organization in session.
    """

    login_url = 'login'

    def post(self, request, *args, **kwargs):
        """Handle organization switch"""

        org_id = request.POST.get('organization_id')
        next_url = request.POST.get('next', 'home')

        if not org_id:
            return redirect('home')

        try:
            # Validate user has access to this organization
            membership = request.user.memberships.get(
                organization_id=org_id,
                is_active=True
            )
        except Membership.DoesNotExist:
            raise PermissionDenied('Access denied to this organization')

        # Update session
        request.session['active_organization_id'] = membership.organization_id
        request.session['active_membership_id'] = membership.id
        request.session['user_role'] = membership.role

        # Invalidate any OBAC caches
        # cache.delete(f'user_{request.user.id}_org_scope')

        return redirect(next_url or 'home')


@login_required
def no_access_view(request):
    """User has no memberships in any organization"""

    return render(request, 'no_access.html', {
        'message': 'You do not have access to any organization. Please contact your administrator.'
    })
