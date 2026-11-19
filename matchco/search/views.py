from types import SimpleNamespace

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse

from courses.models import Course, File, Image, Quiz, Text, Video
from library.models import ContentItem
from publishing.models import Publication
from documents.models import Document
from documents.services import can_view as can_view_document
from audience.selectors import eligible_items
from configuration.organization_context import selected_organization
from learning.models import ContentEvent
from learning.services import recommend_from_signal, track_event


def search(request):
    term = request.GET.get('query', '').strip()
    results = []
    organization = selected_organization(request)
    if organization:
        request.user._active_organization_id = organization.pk
    elif request.user.is_authenticated:
        request.user._active_organization_id = None
    active_company_id = request.session.get('active_company_id')

    def company_scope(queryset, field='company_id'):
        if not active_company_id:
            return queryset
        return queryset.filter(Q(**{f'{field}__isnull': True}) | Q(**{field: active_company_id}))

    if term:
        publications = eligible_items(
            company_scope(Publication.objects.filter(status='published')).filter(
                Q(title__icontains=term) | Q(excerpt__icontains=term) | Q(body__icontains=term)
            ), request.user
        )
        courses = eligible_items(
            company_scope(Course.objects.filter(state='published')).filter(
                Q(title__icontains=term) | Q(overview__icontains=term)
            ), request.user
        )
        items = eligible_items(
            company_scope(ContentItem.objects.filter(published=True), 'module__course__company_id').filter(
                Q(title__icontains=term) | Q(description__icontains=term) | Q(body__icontains=term)
            ), request.user
        )
        course_content = []
        searchable_course_items = (
            (Text, Q(title__icontains=term) | Q(content__icontains=term)),
            (Video, Q(title__icontains=term) | Q(content__icontains=term)),
            (Image, Q(title__icontains=term)),
            (File, Q(title__icontains=term)),
            (Quiz, Q(title__icontains=term) | Q(overview__icontains=term)),
        )
        for model, query in searchable_course_items:
            course_content.extend(eligible_items(
                company_scope(model.objects.filter(
                    content_type__module__course__state=Course.STATE_CHOICES[0][0],
                ), 'content_type__module__course__company_id').filter(query).select_related('content_type__module__course'),
                request.user,
            ))
        documents = []
        if request.user.is_authenticated:
            candidates = company_scope(Document.objects.filter(status=Document.PUBLISHED)).select_related('current_version')
            documents = [
                item for item in candidates
                if can_view_document(request.user, item)
                and (
                    term.lower() in item.title.lower()
                    or term.lower() in item.code.lower()
                    or term.lower() in item.description.lower()
                    or (item.current_version and term.lower() in item.current_version.body.lower())
                )
            ]
        results.extend(
            SimpleNamespace(
                title=item.title,
                description=item.excerpt,
                kind='Feed' if item.kind == Publication.FEED else 'Wiki',
                tags=list(item.tags.all()),
                url=reverse(
                    'publication_feed_detail' if item.kind == Publication.FEED else 'publication_detail',
                    kwargs={'slug': item.slug},
                ),
            )
            for item in publications
        )
        results.extend(SimpleNamespace(title=item.title, description=item.overview, kind='Course', tags=[item.subject.title] if item.subject_id else [], url=reverse('app:course_detail', kwargs={'course_id': item.slug})) for item in courses)
        results.extend(SimpleNamespace(title=item.title, description=item.description, kind='Content', tags=[], url=reverse('app:student_library_content_detail', kwargs={'pk': item.pk})) for item in items)
        results.extend(
            SimpleNamespace(
                title=item.title,
                description=getattr(item, 'overview', '') or getattr(item, 'content', '') or item._meta.verbose_name.title(),
                kind='Quiz' if isinstance(item, Quiz) else 'Conteúdo do curso',
                tags=[item.content_type.module.course.title],
                url=reverse(
                    'app:student_course_detail_module_content',
                    kwargs={
                        'pk': item.content_type.module.course.slug,
                        'module_id': item.content_type.module_id,
                        'content_id': item.pk,
                        'model_name': item._meta.model_name,
                    },
                ),
            )
            for item in course_content
        )
        results.extend(SimpleNamespace(
            title=item.title,
            description=item.description,
            kind='Documento',
            tags=[item.get_category_display()],
            url=reverse('document-detail', kwargs={'slug': item.slug}),
        ) for item in documents)

    page = Paginator(results, 10).get_page(request.GET.get('page', 1))
    signal_recommendations = []
    if term and getattr(request.user, 'is_authenticated', False):
        started_at = request.GET.get('search_started_at', '')
        try:
            elapsed_ms = max(0, min(300000, int(__import__('time').time() * 1000) - int(started_at))) if started_at else None
        except (TypeError, ValueError):
            elapsed_ms = None
        track_event(
            request.user,
            ContentEvent.SEARCH_PERFORMED,
            metadata={'query': term[:120], 'result_count': len(results), 'page': page.number, 'time_to_results_ms': elapsed_ms},
        )
        if not results:
            signal_recommendations = recommend_from_signal(
                request.user, signal='search_no_result', term=term,
            )
    return render(request, 'search/search.html', {'search_query': term, 'search_results': page, 'signal_recommendations': signal_recommendations})
