from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.http import Http404
from django.views.generic import TemplateView

from configuration.models import Partner, PartnerMembership
from courses.models import Course
from documents.models import Document
from documents.services import can_view
from audience.services import eligibility
from .models import ContentEvent, PointLedger


class PartnerPortalView(LoginRequiredMixin, TemplateView):
    template_name = 'learning/partner_portal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        memberships = list(PartnerMembership.objects.filter(
            user=self.request.user, active=True, partner__status=Partner.ACTIVE,
        ).select_related('partner', 'partner__organization', 'partner__company'))
        if not memberships:
            raise Http404
        portals = []
        for membership in memberships:
            partner = membership.partner
            documents = [item for item in Document.objects.filter(status=Document.PUBLISHED, organization=partner.organization).select_related('current_version') if can_view(self.request.user, item)]
            courses = [item for item in Course.objects.filter(state='published', organization=partner.organization, students=self.request.user) if eligibility.can_view(self.request.user, item).allowed]
            events = ContentEvent.objects.filter(user=self.request.user, organization=partner.organization)
            portals.append({
                'partner': partner,
                'membership': membership,
                'documents': documents[:6],
                'documents_count': len(documents),
                'courses': courses[:6],
                'courses_count': len(courses),
                'completed_courses': events.filter(event_name=ContentEvent.COURSE_COMPLETED).values('object_id').distinct().count(),
                'last_activity': events.order_by('-occurred_at').values_list('occurred_at', flat=True).first(),
                'points': PointLedger.objects.filter(user=self.request.user, organization=partner.organization).aggregate(total=Sum('points'))['total'] or 0,
            })
        context['portals'] = portals
        return context
