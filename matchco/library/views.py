from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import render
from django.views.generic import DetailView

from audience.services import eligibility

from .models import ContentItem
from .services import mark_item_completed


class ContentItemDetailView(LoginRequiredMixin, DetailView):
    model = ContentItem
    template_name = 'library/content_detail.html'

    def get_queryset(self):
        return ContentItem.objects.filter(published=True).select_related('module', 'module__course')

    def get(self, request, *args, **kwargs):
        """Keep audience isolation, but replace a technical 404 with guidance.

        A stale link can point to a content item in another active organization.
        The content must remain hidden, while the user should understand that
        changing the organization in the navbar may solve the problem.
        """
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            candidate = self.get_queryset().filter(pk=kwargs.get('pk')).first()
            if candidate is None:
                raise
            decision = eligibility.can_view(request.user, candidate)
            return render(
                request,
                'library/content_item_unavailable.html',
                {
                    'access_code': decision.code,
                    'active_organization': getattr(request, 'active_organization', None),
                },
                status=403,
            )

    def get_object(self, queryset=None):
        item = super().get_object(queryset)
        decision = eligibility.can_view(self.request.user, item)
        if not decision.allowed:
            raise Http404
        mark_item_completed(self.request.user, item)
        return item
