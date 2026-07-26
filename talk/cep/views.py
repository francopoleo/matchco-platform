from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, View
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
            membership = request.user.memberships.get(
                organization_id=org_id,
                active=True
            )
        except Membership.DoesNotExist:
            return render(request, 'error.html', {
                'message': 'Access denied to this organization'
            }, status=403)

        # Set session (both new and old keys for compatibility)
        request.session['active_organization_id'] = membership.organization_id
        request.session['active_membership_id'] = membership.id
        request.session['user_role'] = membership.role
        request.session['selected_organization_id'] = membership.organization_id  # Old key for backward compatibility

        # Log this action (optional)
        # AuditLog.objects.create(
        #     user=request.user,
        #     action='org_selected',
        #     organization_id=org_id,
        #     ip_address=get_client_ip(request),
        # )

        # Redirect to company welcome page for context-aware landing
        from django.urls import reverse
        if membership.company_id:
            return redirect(reverse('company-welcome', kwargs={'company_id': membership.company_id}))
        return redirect(next_url)


class SwitchOrganizationView(LoginRequiredMixin, View):
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
                active=True
            )
        except Membership.DoesNotExist:
            raise PermissionDenied('Access denied to this organization')

        # Update session (both new and old keys for compatibility)
        request.session['active_organization_id'] = membership.organization_id
        request.session['active_membership_id'] = membership.id
        request.session['user_role'] = membership.role
        request.session['selected_organization_id'] = membership.organization_id  # Old key for backward compatibility

        # Invalidate any OBAC caches
        # cache.delete(f'user_{request.user.id}_org_scope')

        # Redirect to company welcome page for context-aware landing
        from django.urls import reverse
        if membership.company_id:
            return redirect(reverse('company-welcome', kwargs={'company_id': membership.company_id}))
        return redirect(next_url or 'home')


@login_required
def company_welcome_view(request, company_id):
    """Welcome page when switching to a new company - shows relevant content"""
    from configuration.models import Company
    from learning.models import ContentTrail
    from courses.models import Course
    from django.db.models import Q

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return redirect('home')

    # Check if user has access to this company
    if not request.user.memberships.filter(
        company_id=company_id, active=True
    ).exists():
        raise PermissionDenied()

    # Get user's active trails in this company
    user_trails = ContentTrail.objects.filter(
        company_id=company_id,
        status='published'
    ).order_by('-created_at')[:3]

    # Get recommended content (new or popular)
    recommended_trails = ContentTrail.objects.filter(
        company_id=company_id,
        status='published'
    ).exclude(id__in=user_trails.values_list('id', flat=True)
    ).order_by('-created_at')[:3]

    # Count active trails
    total_trails = ContentTrail.objects.filter(
        company_id=company_id,
        status='published'
    ).count()

    # Get team members in this company
    team_members = request.user.memberships.filter(
        company_id=company_id,
        active=True
    ).select_related('user', 'company').count()

    context = {
        'company': company,
        'user_trails': user_trails,
        'recommended_trails': recommended_trails,
        'total_trails': total_trails,
        'team_members': team_members,
    }

    return render(request, 'company_welcome.html', context)


@login_required
def no_access_view(request):
    """User has no memberships in any organization"""

    return render(request, 'no_access.html', {
        'message': 'You do not have access to any organization. Please contact your administrator.'
    })
