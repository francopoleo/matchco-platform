from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import DetailView, ListView

from audience.services import eligibility

from .models import Publication, Tag


class PublicationListView(LoginRequiredMixin, ListView):
    model = Publication
    template_name = 'publishing/list.html'
    context_object_name = 'publications'
    paginate_by = 12

    def get_queryset(self):
        kind = self.kwargs['kind']
        candidates = Publication.objects.filter(kind=kind, status=Publication.PUBLISHED).select_related('author')
        tag = self.request.GET.get('tag', '').strip()
        if tag:
            candidates = candidates.filter(tags__slug=tag)
        return [item for item in candidates if item.published_at and eligibility.can_view(self.request.user, item).allowed]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visible = self.get_queryset()
        context['publication_total'] = len(visible)
        context['publication_media_total'] = sum(bool(item.image or item.video_url) for item in visible)
        context['publication_author_total'] = len({item.author_id for item in visible})
        context['publication_tags'] = Tag.objects.filter(publications__kind=self.kwargs['kind'], publications__status=Publication.PUBLISHED).distinct().order_by('name')
        context['selected_tag'] = self.request.GET.get('tag', '').strip()
        return context


class PublicationDetailView(LoginRequiredMixin, DetailView):
    model = Publication
    template_name = 'publishing/detail.html'

    def get_queryset(self):
        return Publication.objects.filter(
            kind=self.kwargs['kind'],
            status=Publication.PUBLISHED,
        ).select_related('author')

    def get_object(self, queryset=None):
        item = super().get_object(queryset)
        if not item.published_at or not eligibility.can_view(self.request.user, item).allowed:
            raise Http404
        return item

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = context['object']
        related = Publication.objects.filter(
            kind=item.kind,
            status=Publication.PUBLISHED,
            tags__in=item.tags.all(),
        ).exclude(pk=item.pk).select_related('author').distinct()[:4]
        context['related_publications'] = [
            publication for publication in related
            if publication.published_at and eligibility.can_view(self.request.user, publication).allowed
        ]
        context['publication_tags'] = item.tags.all()
        return context
