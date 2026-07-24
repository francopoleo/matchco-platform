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
        for item in Publication.objects.order_by('-updated_at')[:100]:
            route = 'publication_detail' if item.kind == Publication.WIKI else 'publication_feed_detail'
            changes.append(SimpleNamespace(
                title=item.title,
                kind='Publication',
                updated_at=item.updated_at,
                url=reverse(route, kwargs={'slug': item.slug}),
            ))
        changes.extend(SimpleNamespace(title=item.title, kind='Course', updated_at=item.created, url=reverse('course_detail', kwargs={'slug': item.slug})) for item in Course.objects.order_by('-created')[:100])
        changes.extend(SimpleNamespace(title=item.title, kind='Content', updated_at=item.updated_at, url=reverse('student_library_content_detail', kwargs={'pk': item.pk})) for item in ContentItem.objects.order_by('-updated_at')[:100])
        changes.sort(key=lambda item: item.updated_at, reverse=True)
        context['changes'] = Paginator(changes, 25).get_page(self.request.GET.get('page', 1))
        return context
