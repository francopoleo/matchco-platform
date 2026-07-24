from types import SimpleNamespace

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse

from courses.models import Course
from library.models import ContentItem
from publishing.models import Publication
from audience.selectors import eligible_items


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

    page = Paginator(results, 10).get_page(request.GET.get('page', 1))
    return render(request, 'search/search.html', {'search_query': term, 'search_results': page})
