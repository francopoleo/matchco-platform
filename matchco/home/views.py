from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from courses.models import Course
from publishing.models import ContentFeedback, ContentInteraction, Publication
from audience.services import eligibility
from learning.models import ContentTrail
from learning.models import UserNotification
from learning.services import create_notification, eligible_next_trail_step, ensure_user_trail_assignments
from tenants_core.models import TenantUser


def _rank_publications(user, publications):
    content_type = ContentType.objects.get_for_model(Publication)
    ids = [publication.pk for publication in publications]
    # Convert User to TenantUser if needed
    tenant_user = TenantUser.objects.filter(user_id=user.id).first() if user.is_authenticated else None
    interactions = {
        row['object_id']: row
        for row in ContentInteraction.objects.filter(content_type=content_type, object_id__in=ids, user=tenant_user).values('object_id', 'view_count', 'acknowledged_at') if tenant_user
    } if tenant_user else {}
    feedback = {}
    for row in ContentFeedback.objects.filter(content_type=content_type, object_id__in=ids).values('object_id', 'rating'):
        feedback.setdefault(row['object_id'], []).append(row['rating'])
    now = timezone.now()
    importance_score = {Publication.CRITICAL: 100, Publication.IMPORTANT: 55, Publication.ROUTINE: 10}
    for publication in publications:
        interaction = interactions.get(publication.pk)
        ratings = feedback.get(publication.pk, [])
        age_hours = max((now - publication.published_at).total_seconds() / 3600, 0) if publication.published_at else 999
        publication.home_view_count = interaction['view_count'] if interaction else 0
        publication.home_feedback_count = len(ratings)
        publication.home_helpful_count = ratings.count(ContentFeedback.HELPFUL)
        publication.home_unread = not interaction
        publication.home_alert_open = publication.is_alert and not (interaction and interaction['acknowledged_at'])
        publication.home_priority_score = importance_score.get(publication.importance, 10) + (35 if publication.home_alert_open else 0) + max(0, 30 - int(age_hours))
    return sorted(publications, key=lambda item: (-item.home_priority_score, -item.published_at.timestamp() if item.published_at else 0))


def home(request):
    active_organization_id = getattr(request.user, '_active_organization_id', None) or getattr(request, 'active_organization_id', None)
    active_company_id = getattr(request, 'active_company_id', None)

    courses = Course.objects.filter(state='published')
    publications = Publication.objects.filter(status=Publication.PUBLISHED, published_at__isnull=False)

    if active_organization_id:
        courses = courses.filter(Q(organization_id=active_organization_id) | Q(organization__isnull=True))
        publications = publications.filter(Q(organization_id=active_organization_id) | Q(organization__isnull=True))

    # Filter by company if active
    if active_company_id:
        courses = courses.filter(Q(company_id=active_company_id) | Q(company__isnull=True))
        publications = publications.filter(Q(company_id=active_company_id) | Q(company__isnull=True))

    visible_courses = [course for course in courses.select_related('subject') if eligibility.can_view(request.user, course).allowed]
    visible_publications = [publication for publication in publications.select_related('author').prefetch_related('tags') if not publication.is_expired and eligibility.can_view(request.user, publication).allowed]
    ranked_publications = _rank_publications(request.user, visible_publications)

    trails = ContentTrail.objects.filter(status=ContentTrail.PUBLISHED)
    if active_organization_id:
        trails = trails.filter(Q(organization_id=active_organization_id) | Q(organization__isnull=True))

    # Filter trails by company if active
    if active_company_id:
        trails = trails.filter(Q(company_id=active_company_id) | Q(company__isnull=True))
    trail_recommendations = []
    for trail in trails.prefetch_related('steps'):
        step = eligible_next_trail_step(request.user, trail)
        if step:
            target = step.content_object
            if isinstance(target, Publication):
                target_url = reverse('app:student_trail_start', kwargs={'pk': trail.pk})
                target_kind = target.get_kind_display()
            elif hasattr(target, 'module'):
                target_url = reverse('app:student_trail_start', kwargs={'pk': trail.pk})
                target_kind = 'Curso'
            elif isinstance(target, Course):
                target_url = reverse('app:student_trail_start', kwargs={'pk': trail.pk})
                target_kind = 'Curso'
            else:
                continue
            trail_recommendations.append({'trail': trail, 'step': step, 'target': target, 'target_url': target_url, 'target_kind': target_kind})
        if len(trail_recommendations) >= 3:
            break
    trail_assignments = ensure_user_trail_assignments(request.user)
    trail_completed = sum(assignment.completed_at is not None for assignment in trail_assignments)
    trail_started = sum(
        assignment.started_at is not None and assignment.completed_at is None
        for assignment in trail_assignments
    )
    alert_publications = [publication for publication in ranked_publications if publication.home_alert_open][:5]
    for publication in alert_publications:
        create_notification(
            request.user,
            title=publication.title,
            message='Esta comunicação pode afetar sua operação e ainda não foi lida.',
            url=reverse('publication_feed_detail' if publication.kind == Publication.FEED else 'publication_detail', kwargs={'slug': publication.slug}),
            priority=UserNotification.CRITICAL if publication.importance == Publication.CRITICAL else UserNotification.IMPORTANT,
            dedupe_key=f'publication-alert:{publication.pk}:{publication.updated_at.isoformat()}',
            organization=publication.organization,
        )
    priority_publications = ranked_publications[:6]
    visible_apps = [
        {
            'label': _('Courses'),
            'description': _('Continue your learning journey.'),
            'url': reverse('app:courses'),
            'icon': 'course',
            'tone': 'cyan',
        },
        {
            'label': _('Feed'),
            'description': _('See the latest updates.'),
            'url': reverse('app:feed'),
            'icon': 'feed',
            'tone': 'emerald',
        },
        {
            'label': _('Wiki'),
            'description': _('Explore the knowledge base.'),
            'url': reverse('app:wiki'),
            'icon': 'wiki',
            'tone': 'amber',
        },
        {
            'label': _('Gamification'),
            'description': _('Track your points and achievements.'),
            'url': reverse('app:profile') if request.user.is_authenticated else reverse('login'),
            'icon': 'game',
            'tone': 'fuchsia',
        },
    ]
    return render(request, 'home/home.html', {
        'visible_apps': visible_apps,
        'course_count': len(visible_courses),
        'publication_count': len(visible_publications),
        'published_publication_count': len(visible_publications),
        'priority_publications': priority_publications,
        'alert_publications': alert_publications,
        'recent_courses': visible_courses[:4],
        'important_count': sum(item.importance == Publication.IMPORTANT for item in visible_publications),
        'critical_count': sum(item.importance == Publication.CRITICAL for item in visible_publications),
        'pending_count': sum(item.home_unread for item in visible_publications),
        'pending_critical_count': sum(item.home_unread and item.importance == Publication.CRITICAL for item in visible_publications),
        'trail_recommendations': trail_recommendations,
        'trail_total': len(trail_assignments),
        'trail_completed': trail_completed,
        'trail_started': trail_started,
    })
