from datetime import datetime, timedelta
from types import SimpleNamespace

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.views.generic import TemplateView
from django.urls import reverse
from django.contrib.auth import get_user_model

from courses.models import Course
from library.models import ContentItem
from publishing.models import Publication, ContentFeedback

User = get_user_model()


class LatestChangesView(UserPassesTestMixin, TemplateView):
    template_name = 'reports/latest_changes.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        changes = []

        active_organization_id = getattr(self.request.user, '_active_organization_id', None)

        # Parse filters
        filter_type = self.request.GET.get('type', 'all')
        filter_user = self.request.GET.get('user', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')

        # Parse dates
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else None
        except ValueError:
            date_from_obj = None

        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else None
        except ValueError:
            date_to_obj = None

        # Get publications
        if filter_type in ('all', 'Publication'):
            publications = Publication.objects.select_related('author', 'organization').order_by('-updated_at')
            if active_organization_id:
                publications = publications.filter(organization_id=active_organization_id)
            if filter_user:
                publications = publications.filter(author_id=filter_user)
            if date_from_obj:
                publications = publications.filter(updated_at__date__gte=date_from_obj)
            if date_to_obj:
                publications = publications.filter(updated_at__date__lte=date_to_obj)

            for item in publications[:200]:
                feedbacks = ContentFeedback.objects.filter(
                    content_type__model='publication',
                    object_id=item.pk
                ).count()
                route = 'publication_detail' if item.kind == Publication.WIKI else 'publication_feed_detail'
                view_url = reverse(route, kwargs={'slug': item.slug})
                edit_url = reverse('console:publication-edit', kwargs={'pk': item.pk}) if item.author and item.author == self.request.user else None
                changes.append(SimpleNamespace(
                    title=item.title,
                    kind='Publication',
                    subkind=item.get_kind_display(),
                    created_by=item.author.get_full_name() or item.author.username if item.author else '—',
                    created_by_id=item.author_id if item.author else None,
                    created_at=item.created_at if hasattr(item, 'created_at') else item.updated_at,
                    updated_at=item.updated_at,
                    organization=item.organization.name if item.organization else '—',
                    feedbacks=feedbacks,
                    url=view_url,
                    edit_url=edit_url,
                    pk=item.pk,
                ))

        # Get courses
        if filter_type in ('all', 'Course'):
            courses = Course.objects.select_related('owner', 'organization').order_by('-created')
            if active_organization_id:
                courses = courses.filter(organization_id=active_organization_id)
            if filter_user:
                courses = courses.filter(owner_id=filter_user)
            if date_from_obj:
                courses = courses.filter(created__date__gte=date_from_obj)
            if date_to_obj:
                courses = courses.filter(created__date__lte=date_to_obj)

            for item in courses[:200]:
                feedbacks = ContentFeedback.objects.filter(
                    content_type__model='course',
                    object_id=item.pk
                ).count()
                view_url = reverse('course_detail', kwargs={'slug': item.slug})
                edit_url = reverse('console:course-edit', kwargs={'pk': item.pk}) if item.owner and item.owner == self.request.user else None
                changes.append(SimpleNamespace(
                    title=item.title,
                    kind='Course',
                    subkind=item.subject.title if item.subject else 'Sem categoria',
                    created_by=item.owner.get_full_name() or item.owner.username if item.owner else '—',
                    created_by_id=item.owner_id if item.owner else None,
                    created_at=item.created,
                    updated_at=item.updated_at if hasattr(item, 'updated_at') else item.created,
                    organization=item.organization.name if item.organization else '—',
                    feedbacks=feedbacks,
                    url=view_url,
                    edit_url=edit_url,
                    pk=item.pk,
                ))

        # Get content items
        if filter_type in ('all', 'Content'):
            content_items = ContentItem.objects.select_related('module__course__owner', 'module__course__organization').order_by('-updated_at')
            if active_organization_id:
                content_items = content_items.filter(module__course__organization_id=active_organization_id)
            if filter_user:
                content_items = content_items.filter(module__course__owner_id=filter_user)
            if date_from_obj:
                content_items = content_items.filter(updated_at__date__gte=date_from_obj)
            if date_to_obj:
                content_items = content_items.filter(updated_at__date__lte=date_to_obj)

            for item in content_items[:200]:
                feedbacks = ContentFeedback.objects.filter(
                    content_type__model='contentitem',
                    object_id=item.pk
                ).count()
                view_url = reverse('student_library_content_detail', kwargs={'pk': item.pk})
                changes.append(SimpleNamespace(
                    title=item.title,
                    kind='Content',
                    subkind=item.get_type_display() if hasattr(item, 'get_type_display') else 'Item',
                    created_by=item.module.course.owner.get_full_name() or item.module.course.owner.username if item.module and item.module.course and item.module.course.owner else '—',
                    created_by_id=item.module.course.owner_id if item.module and item.module.course else None,
                    created_at=item.created_at if hasattr(item, 'created_at') else item.updated_at,
                    updated_at=item.updated_at,
                    organization=item.module.course.organization.name if item.module and item.module.course and item.module.course.organization else '—',
                    feedbacks=feedbacks,
                    url=view_url,
                    edit_url=None,
                    pk=item.pk,
                ))

        changes.sort(key=lambda item: item.updated_at, reverse=True)

        # Get available users for filter
        if active_organization_id:
            users = User.objects.filter(
                Q(publications__organization_id=active_organization_id) |
                Q(courses_author__organization_id=active_organization_id)
            ).distinct().order_by('first_name', 'last_name', 'username')
        else:
            users = User.objects.filter(
                Q(publications__isnull=False) |
                Q(courses_author__isnull=False)
            ).distinct().order_by('first_name', 'last_name', 'username')

        context['changes'] = Paginator(changes, 25).get_page(self.request.GET.get('page', 1))
        context['filter_type'] = filter_type
        context['filter_user'] = filter_user
        context['date_from'] = date_from
        context['date_to'] = date_to
        context['available_users'] = users
        return context
