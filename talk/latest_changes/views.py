from types import SimpleNamespace

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import Paginator
from django.views.generic import TemplateView
from django.urls import reverse

from courses.models import Course
from library.models import ContentItem
from publishing.models import Publication


class LatestChangesView(UserPassesTestMixin, TemplateView):
    template_name = 'reports/latest_changes.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        changes = []
        filter_type = self.request.GET.get('type', 'all')

        # Get publications
        if filter_type in ('all', 'Publication'):
            for item in Publication.objects.order_by('-updated_at')[:100]:
                route = 'publication_detail' if item.kind == Publication.WIKI else 'publication_feed_detail'
                changes.append(SimpleNamespace(
                    title=item.title,
                    kind='Publication',
                    subkind=item.get_kind_display(),
                    updated_at=item.updated_at,
                    organization=item.organization.name if item.organization else '—',
                    url=reverse(route, kwargs={'slug': item.slug}),
                ))

        # Get courses
        if filter_type in ('all', 'Course'):
            for item in Course.objects.order_by('-created')[:100]:
                changes.append(SimpleNamespace(
                    title=item.title,
                    kind='Course',
                    subkind=item.subject.title if item.subject else 'Sem categoria',
                    updated_at=item.created,
                    organization=item.organization.name if item.organization else '—',
                    url=reverse('course_detail', kwargs={'slug': item.slug}),
                ))

        # Get content items
        if filter_type in ('all', 'Content'):
            for item in ContentItem.objects.order_by('-updated_at')[:100]:
                changes.append(SimpleNamespace(
                    title=item.title,
                    kind='Content',
                    subkind=item.get_type_display() if hasattr(item, 'get_type_display') else 'Item',
                    updated_at=item.updated_at,
                    organization=item.library.organization.name if hasattr(item, 'library') and item.library and item.library.organization else '—',
                    url=reverse('student_library_content_detail', kwargs={'pk': item.pk}),
                ))

        changes.sort(key=lambda item: item.updated_at, reverse=True)
        context['changes'] = Paginator(changes, 25).get_page(self.request.GET.get('page', 1))
        context['filter_type'] = filter_type
        return context
