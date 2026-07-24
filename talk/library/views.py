from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import DetailView

from audience.services import eligibility

from .models import ContentItem
from .services import mark_item_completed


class ContentItemDetailView(LoginRequiredMixin, DetailView):
    model = ContentItem
    template_name = 'library/content_detail.html'

    def get_queryset(self):
        return ContentItem.objects.filter(published=True).select_related('module', 'module__course')

    def get_object(self, queryset=None):
        item = super().get_object(queryset)
        decision = eligibility.can_view(self.request.user, item)
        if not decision.allowed:
            raise Http404
        mark_item_completed(self.request.user, item)
        return item
