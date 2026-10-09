from django.utils.translation import gettext_lazy as gettext_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import ListView, View

from configuration.models import Membership
from user_management.models import DemoVisit, RegistrationRequest
from accounts.emailing import send_registration_decision_email

from .views import ManagerRequiredMixin


class RegistrationRequestListView(ManagerRequiredMixin, ListView):
    template_name = 'console/registration_request_list.html'
    context_object_name = 'registration_requests'
    queryset = RegistrationRequest.objects.select_related(
        'user', 'invitation_code', 'invitation_code__organization',
        'invitation_code__company', 'invitation_code__business_unit',
        'invitation_code__operational_unit', 'invitation_code__person_type',
    )

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status', 'pending')
        if status in ('pending', 'approved', 'rejected'):
            queryset = queryset.filter(status=status)
        return queryset


class RegistrationRequestDecisionView(ManagerRequiredMixin, View):
    def post(self, request, pk, decision):
        registration = get_object_or_404(RegistrationRequest.objects.select_related('invitation_code'), pk=pk, status=RegistrationRequest.PENDING)
        if decision == 'approve':
            invitation = registration.invitation_code
            if not invitation or not invitation.available or not invitation.company:
                messages.error(request, gettext_lazy('O código não está disponível para aprovação.'))
                return redirect('console:registration-requests')
            user = registration.user
            user.is_active = True
            user.save(update_fields=['is_active'])
            Membership.objects.update_or_create(
                user=user,
                company=invitation.company,
                business_unit=invitation.business_unit,
                operational_unit=invitation.operational_unit,
                defaults={'organization': invitation.organization, 'person_type': invitation.person_type, 'active': True, 'is_primary': not user.memberships.filter(active=True).exists()},
            )
            invitation.uses_count += 1
            if invitation.uses_count >= invitation.max_uses:
                invitation.active = False
            invitation.save(update_fields=['uses_count', 'active'])
            registration.status = RegistrationRequest.APPROVED
            registration.reviewer_notes = request.POST.get('reviewer_notes', '').strip()
            registration.reviewed_by = request.user
            registration.reviewed_at = timezone.now()
            registration.save(update_fields=['status', 'reviewer_notes', 'reviewed_by', 'reviewed_at'])
            send_registration_decision_email(registration)
            messages.success(request, f'Acesso de {user.get_full_name() or user.username} aprovado.')
        elif decision == 'reject':
            registration.status = RegistrationRequest.REJECTED
            registration.reviewer_notes = request.POST.get('reviewer_notes', '').strip()
            registration.reviewed_by = request.user
            registration.reviewed_at = timezone.now()
            registration.user.is_active = False
            registration.user.save(update_fields=['is_active'])
            registration.save(update_fields=['status', 'reviewer_notes', 'reviewed_by', 'reviewed_at'])
            send_registration_decision_email(registration)
            messages.success(request, gettext_lazy('Solicitação rejeitada.'))
        return redirect('console:registration-requests')


class DemoVisitListView(ManagerRequiredMixin, ListView):
    template_name = 'console/demo_visit_list.html'
    context_object_name = 'demo_visits'
    queryset = DemoVisit.objects.select_related('demo_user')

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(visitor_name__icontains=query) | queryset.filter(visitor_email__icontains=query)
        return queryset
