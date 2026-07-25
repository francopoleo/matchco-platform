from types import SimpleNamespace

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse

from courses.models import Course
from library.models import ContentItem
from publishing.models import Publication
from documents.models import Document
from documents.services import can_view as can_view_document
from audience.selectors import eligible_items
from learning.models import ContentEvent
from learning.services import recommend_from_signal, track_event


def search(request):
    term = request.GET.get('query', '').strip()
    results = []
    if term:
        publications = eligible_items(
            Publication.objects.filter(status='published').filter(
                Q(title__icontains=term) | Q(excerpt__icontains=term) | Q(body__icontains=term)
            ), request.user
        )
        courses = eligible_items(
            Course.objects.filter(state='published').filter(
                Q(title__icontains=term) | Q(overview__icontains=term)
            ), request.user
        )
        items = eligible_items(
            ContentItem.objects.filter(published=True).filter(
                Q(title__icontains=term) | Q(description__icontains=term) | Q(body__icontains=term)
            ), request.user
        )
        documents = []
        if request.user.is_authenticated:
            candidates = Document.objects.filter(status=Document.PUBLISHED).select_related('current_version')
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
        results.extend(SimpleNamespace(title=item.title, description=item.overview, kind='Course', tags=[item.subject.title] if item.subject_id else [], url=reverse('course_detail', kwargs={'slug': item.slug})) for item in courses)
        results.extend(SimpleNamespace(title=item.title, description=item.description, kind='Content', tags=[], url=reverse('student_library_content_detail', kwargs={'pk': item.pk})) for item in items)
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
