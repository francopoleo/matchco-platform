from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView

from audience.services import eligibility
from console.views import active_organization_queryset
from learning.models import ContentEvent
from learning.services import dismiss_recommendation, get_or_create_recommendation, mark_notifications_read_for_url, mark_recommendation_opened, recommend_from_signal, track_event
from documents.models import DocumentLink
from documents.services import can_view as can_view_document
from courses.models import Content
from students.models import CourseEnroll

from .models import ContentFeedback, ContentInteraction, ContentQuestion, Publication, Tag


class PublicationListView(LoginRequiredMixin, ListView):
    model = Publication
    template_name = 'publishing/list.html'
    context_object_name = 'publications'
    paginate_by = 12

    def get_queryset(self):
        kind = self.kwargs['kind']
        candidates = Publication.objects.filter(kind=kind, status=Publication.PUBLISHED).select_related('author')
        candidates = active_organization_queryset(self.request, candidates)

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

        # Get tags for current organization
        tags_query = Tag.objects.filter(publications__kind=self.kwargs['kind'], publications__status=Publication.PUBLISHED)
        tags_query = active_organization_queryset(self.request, tags_query, field='publications__organization_id')
        context['publication_tags'] = tags_query.distinct().order_by('name')
        context['selected_tag'] = self.request.GET.get('tag', '').strip()
        return context


class PublicationDetailView(LoginRequiredMixin, DetailView):
    model = Publication
    template_name = 'publishing/detail.html'

    def get_queryset(self):
        queryset = Publication.objects.filter(
            kind=self.kwargs['kind'],
            status=Publication.PUBLISHED,
        ).select_related('author')
        return active_organization_queryset(self.request, queryset)

    def get(self, request, *args, **kwargs):
        """Keep audience isolation, but replace a technical 404 with guidance.

        A stale link can point to a publication in another active organization.
        The content must remain hidden, while the user should understand that
        changing the organization in the navbar may solve the problem.
        """
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            candidate = self.get_queryset().filter(slug=kwargs.get('slug')).first()
            if candidate is None:
                raise
            decision = eligibility.can_view(request.user, candidate)
            return render(
                request,
                'publishing/unavailable.html',
                {
                    'access_code': decision.code,
                    'active_organization': getattr(request, 'active_organization', None),
                },
                status=403,
            )

    def get_object(self, queryset=None):
        item = super().get_object(queryset)
        if not item.published_at or not eligibility.can_view(self.request.user, item).allowed:
            raise Http404
        content_type = ContentType.objects.get_for_model(Publication)
        interaction, created = ContentInteraction.objects.get_or_create(
            content_type=content_type, object_id=item.pk, user=self.request.user,
        )
        if not created:
            ContentInteraction.objects.filter(pk=interaction.pk).update(
                view_count=interaction.view_count + 1,
                last_viewed_at=timezone.now(),
            )
        track_event(self.request.user, ContentEvent.CONTENT_OPENED, item)
        mark_notifications_read_for_url(self.request.user, self.request.path)
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
        linked_documents = DocumentLink.objects.filter(
            content_type=ContentType.objects.get_for_model(Publication), object_id=item.pk,
        ).select_related('document', 'document__current_version')
        context['linked_documents'] = [link for link in linked_documents if can_view_document(self.request.user, link.document)]
        context['publication_recommendations'] = []
        for related in context['related_publications']:
            recommendation = get_or_create_recommendation(
                self.request.user, related,
                f'Conteúdo relacionado ao tema de “{item.title}”.',
                source='publication_tags',
            )
            if recommendation:
                context['publication_recommendations'].append({'recommendation': recommendation, 'target': related})
            if len(context['publication_recommendations']) >= 3:
                break
        context['content_feedback'] = ContentFeedback.objects.filter(
            content_type=ContentType.objects.get_for_model(Publication),
            object_id=item.pk,
            user=self.request.user,
        ).first()
        return context


class RecommendationOpenView(LoginRequiredMixin, View):
    def get(self, request, pk):
        from learning.models import ContentRecommendation
        recommendation = get_object_or_404(ContentRecommendation, pk=pk, user=request.user)
        mark_recommendation_opened(request.user, recommendation)
        target = recommendation.content_object
        if isinstance(target, Publication):
            return redirect('publication_feed_detail' if target.kind == Publication.FEED else 'publication_detail', slug=target.slug)
        return redirect('home')


class RecommendationDismissView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from learning.models import ContentRecommendation
        recommendation = get_object_or_404(ContentRecommendation, pk=pk, user=request.user)
        dismiss_recommendation(request.user, recommendation)
        return JsonResponse({'ok': True})


class PublicationEventView(LoginRequiredMixin, View):
    """Receive lightweight active-time heartbeats for a publication."""

    def post(self, request, kind, slug):
        if request.content_type != 'application/json':
            return JsonResponse({'ok': False, 'error': 'JSON obrigatório.'}, status=400)
        try:
            import json
            payload = json.loads(request.body or '{}')
            active_seconds = min(300, max(0, int(payload.get('active_seconds', 0) or 0)))
        except (TypeError, ValueError, json.JSONDecodeError):
            return JsonResponse({'ok': False, 'error': 'Dados inválidos.'}, status=400)

        publication = get_object_or_404(
            Publication,
            kind=kind,
            slug=slug,
            status=Publication.PUBLISHED,
        )
        if not publication.published_at or not eligibility.can_view(request.user, publication).allowed:
            raise Http404
        track_event(
            request.user,
            ContentEvent.CONTENT_ACTIVE,
            publication,
            session_id=str(payload.get('session_id', ''))[:80],
            active_seconds=active_seconds,
        )
        return JsonResponse({'ok': True})


class ContentFeedbackView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        publication = None
        if request.POST.get('publication_id'):
            target = get_object_or_404(Publication, pk=request.POST.get('publication_id'), status=Publication.PUBLISHED)
            publication = target
        else:
            target = get_object_or_404(Content.objects.select_related('module__course'), pk=request.POST.get('content_id'))
            if target.module.course.state != 'published' or not CourseEnroll.objects.filter(course_id=target.module.course, student_id=request.user).exists():
                raise Http404
        if not eligibility.can_view(request.user, target).allowed:
            raise Http404
        rating = request.POST.get('rating', '')
        valid_ratings = {choice[0] for choice in ContentFeedback.RATING_CHOICES}
        if rating not in valid_ratings:
            return JsonResponse({'ok': False, 'error': 'Resposta inválida.'}, status=400)
        content_type = ContentType.objects.get_for_model(target)
        feedback, _ = ContentFeedback.objects.update_or_create(
            content_type=content_type,
            object_id=target.pk,
            user=request.user,
            defaults={
                'rating': rating,
                'reason': request.POST.get('reason', '') if rating != ContentFeedback.HELPFUL else '',
                'comment': request.POST.get('comment', '').strip() if rating != ContentFeedback.HELPFUL else '',
            },
        )
        if publication and publication.requires_acknowledgement:
            ContentInteraction.objects.filter(content_type=content_type, object_id=target.pk, user=request.user).update(acknowledged_at=timezone.now())
            track_event(request.user, ContentEvent.CONTENT_ACKNOWLEDGED, target)
        track_event(
            request.user,
            ContentEvent.FEEDBACK_SUBMITTED,
            target,
            metadata={'rating': rating, 'reason': feedback.reason},
        )
        if publication and rating in {ContentFeedback.PARTIAL, ContentFeedback.NOT_HELPFUL}:
            recommend_from_signal(
                request.user,
                signal='negative_feedback',
                target=publication,
            )
        return JsonResponse({'ok': True, 'rating': feedback.rating})


class ContentQuestionView(LoginRequiredMixin, View):
    def post(self, request):
        target = get_object_or_404(Publication, pk=request.POST.get('publication_id'), status=Publication.PUBLISHED)
        if not target.is_published or not eligibility.can_view(request.user, target).allowed:
            raise Http404
        question = request.POST.get('question', '').strip()
        if not question:
            return JsonResponse({'ok': False, 'error': 'Escreva uma dúvida.'}, status=400)
        content_type = ContentType.objects.get_for_model(target)
        item = ContentQuestion.objects.create(
            content_type=content_type, object_id=target.pk,
            user=request.user, question=question[:2000],
        )
        track_event(request.user, ContentEvent.QUESTION_SUBMITTED, target, metadata={'question_id': item.pk})
        recommend_from_signal(request.user, signal='question_submitted', target=target)
        return JsonResponse({'ok': True, 'question_id': item.pk})
