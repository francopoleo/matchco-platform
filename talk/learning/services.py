from django.db import transaction
from django.db.models import Sum
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
import json
from django.contrib.contenttypes.models import ContentType
import uuid

from django.utils import timezone

from courses.models import Content
from students.models import CourseEnroll, ContentEnroll, ModuleEnroll
from .models import ContentEvent
from .models import BadgeDefinition, ChallengeProgress, ContentRecommendation, ContentTrail, CourseCertificate, LearningChallenge, NotificationDelivery, NotificationRule, PointLedger, PushSubscription, TrailAssignment, TrailProgress, TrailStep, UserBadge, UserNotification, UserNotificationPreference
from audience.services import eligibility
from cep.core.utils import get_tenant_user as _get_tenant_user


def _object_organization(obj):
    organization = getattr(obj, 'organization', None)
    if organization is not None:
        return organization
    module = getattr(obj, 'module', None)
    course = getattr(module, 'course', None)
    return getattr(course, 'organization', None)


def track_event(user, event_name, obj=None, *, organization=None, session_id='',
                active_seconds=0, progress_percent=None, metadata=None):
    """Record a non-blocking product/learning event with minimal context."""
    tenant_user = _get_tenant_user(user)
    content_type = None
    object_id = None
    if obj is not None:
        content_type = ContentType.objects.get_for_model(obj)
        object_id = obj.pk
        organization = organization or _object_organization(obj)
    event = ContentEvent.objects.create(
        user=tenant_user,
        organization=organization,
        event_name=event_name,
        content_type=content_type,
        object_id=object_id,
        session_id=session_id or '',
        active_seconds=max(0, int(active_seconds or 0)),
        progress_percent=progress_percent,
        metadata=metadata or {},
    )
    award_points_for_event(event)
    if event.organization:
        from .integrations import enqueue_webhook_event
        enqueue_webhook_event(
            organization=event.organization,
            event_type=event.event_name,
            payload={'event_id': event.pk, 'user_id': event.user_id, 'object_id': event.object_id, 'metadata': event.metadata},
        )
    return event


def award_points_for_event(event):
    """Translate selected events into an immutable, explainable points ledger."""
    if not event.user_id:
        return None
    points_by_event = {
        ContentEvent.CONTENT_OPENED: 10,
        ContentEvent.CONTENT_ACKNOWLEDGED: 10,
        ContentEvent.COURSE_ENROLLED: 5,
        ContentEvent.COURSE_COMPLETED: 100,
        ContentEvent.CONTENT_COMPLETED: 25,
        ContentEvent.QUIZ_COMPLETED: 25,
        ContentEvent.TRAIL_COMPLETED: 100,
        ContentEvent.ACTION_COMPLETED: 20,
    }
    points = points_by_event.get(event.event_name, 0)
    if event.event_name == ContentEvent.QUIZ_COMPLETED and event.metadata.get('score') == event.metadata.get('required_score'):
        points += 50
    if not points:
        return None
    ledger, created = PointLedger.objects.get_or_create(
        source_event=event,
        defaults={'user_id': event.user_id, 'organization': event.organization, 'points': points, 'reason': event.event_name},
    )
    if not created:
        return ledger
    total = PointLedger.objects.filter(user_id=event.user_id).aggregate(total=Sum('points')).get('total') or 0
    for badge in BadgeDefinition.objects.filter(active=True, points_threshold__lte=total):
        UserBadge.objects.get_or_create(user_id=event.user_id, badge=badge)
    now = timezone.now()
    for challenge in LearningChallenge.objects.filter(active=True, starts_at__lte=now, ends_at__gte=now):
        progress, _ = ChallengeProgress.objects.get_or_create(challenge=challenge, user_id=event.user_id)
        progress.points = min(challenge.target_points, progress.points + points)
        if progress.points >= challenge.target_points and progress.completed_at is None:
            progress.completed_at = now
        progress.save(update_fields=('points', 'completed_at', 'updated_at'))
    return ledger


def start_trail(user, trail):
    """Start an eligible trail without silently bypassing audience rules."""
    decision = eligibility.can_view(user, trail)
    if not decision.allowed:
        return None
    assignment, created = TrailAssignment.objects.get_or_create(trail=trail, user=user)
    if assignment.revoked_at:
        return None
    if assignment.started_at is None:
        assignment.started_at = timezone.now()
        assignment.save(update_fields=('started_at',))
    if created:
        track_event(user, ContentEvent.TRAIL_STARTED, trail)
    return assignment


def ensure_user_trail_assignments(user):
    """Materialize eligible audience assignments lazily for the current user."""
    if not getattr(user, 'is_authenticated', False):
        return []
    tenant_user = _get_tenant_user(user)
    if not tenant_user:
        return []
    assignments = []
    for trail in ContentTrail.objects.filter(status=ContentTrail.PUBLISHED).select_related('audience_policy'):
        if not eligibility.can_view(user, trail).allowed:
            continue
        assignment, _ = TrailAssignment.objects.get_or_create(trail=trail, user=tenant_user)
        if not assignment.revoked_at:
            assignments.append(assignment)
    return assignments


@transaction.atomic
def reconcile_policy_assignments(policy, *, user_queryset=None):
    """Re-evaluate materialized trail assignments after audience changes.

    Assignments are never deleted: users who lost eligibility are marked as
    revoked, preserving the operational audit trail. If eligibility returns,
    the assignment is restored and can continue from its previous progress.
    """
    if not policy:
        return {'created': 0, 'restored': 0, 'revoked': 0, 'checked': 0}
    trails = list(ContentTrail.objects.filter(
        audience_policy=policy, status=ContentTrail.PUBLISHED,
    ))
    if user_queryset is None:
        from configuration.models import Membership
        user_queryset = get_user_model().objects.filter(
            memberships__organization_id=policy.organization_id,
            memberships__active=True,
        ).distinct()
    users = list(user_queryset)
    eligible_users = {
        user.pk for user in users
        if all(eligibility.can_view(user, trail).allowed for trail in trails)
    }
    stats = {'created': 0, 'restored': 0, 'revoked': 0, 'checked': 0}
    for trail in trails:
        existing = {
            assignment.user_id: assignment
            for assignment in TrailAssignment.objects.filter(trail=trail, audience_policy=policy, user__isnull=False)
        }
        for user in users:
            assignment = existing.get(user.pk)
            if user.pk in eligible_users:
                if assignment is None:
                    TrailAssignment.objects.create(trail=trail, user=user, audience_policy=policy)
                    stats['created'] += 1
                elif assignment.revoked_at:
                    assignment.revoked_at = None
                    assignment.revocation_reason = ''
                    assignment.save(update_fields=('revoked_at', 'revocation_reason'))
                    stats['restored'] += 1
            elif assignment and not assignment.revoked_at:
                assignment.revoked_at = timezone.now()
                assignment.revocation_reason = 'Usuário deixou de atender à política de audiência.'
                assignment.save(update_fields=('revoked_at', 'revocation_reason'))
                stats['revoked'] += 1
            stats['checked'] += 1
    return stats


def next_trail_step(user, trail):
    assignment = start_trail(user, trail)
    if assignment is None:
        return None
    completed_ids = set(
        TrailProgress.objects.filter(assignment=assignment, completed_at__isnull=False)
        .values_list('step_id', flat=True)
    )
    for step in trail.steps.select_related('content_type').order_by('position', 'id'):
        if step.pk in completed_ids:
            continue
        if step.prerequisite_id and step.prerequisite_id not in completed_ids:
            continue
        target = step.content_object
        if target is None or not eligibility.can_view(user, target).allowed:
            continue
        return assignment, step
    return assignment, None


def eligible_next_trail_step(user, trail):
    """Return the next eligible step without creating an assignment."""
    if not eligibility.can_view(user, trail).allowed:
        return None
    tenant_user = _get_tenant_user(user)
    if not tenant_user:
        return None
    assignment = TrailAssignment.objects.filter(trail=trail, user=tenant_user).first()
    completed_ids = set()
    if assignment:
        completed_ids = set(
            TrailProgress.objects.filter(assignment=assignment, completed_at__isnull=False)
            .values_list('step_id', flat=True)
        )
    for step in trail.steps.select_related('content_type').order_by('position', 'id'):
        if step.pk in completed_ids:
            continue
        if step.prerequisite_id and step.prerequisite_id not in completed_ids:
            continue
        if step.content_object is not None and eligibility.can_view(user, step.content_object).allowed:
            return step
    return None


@transaction.atomic
def complete_trail_step(user, assignment, step, *, active_seconds=0, usefulness=''):
    if assignment.user_id != user.pk or step.trail_id != assignment.trail_id:
        return None
    progress, _ = TrailProgress.objects.get_or_create(assignment=assignment, step=step)
    if progress.completed_at is None:
        progress.started_at = progress.started_at or timezone.now()
        progress.completed_at = timezone.now()
        progress.active_seconds = max(progress.active_seconds, int(active_seconds or 0))
        progress.usefulness = usefulness
        progress.save(update_fields=('started_at', 'completed_at', 'active_seconds', 'usefulness'))
        track_event(user, ContentEvent.TRAIL_STEP_COMPLETED, step.content_object, metadata={'trail_id': assignment.trail_id, 'step_id': step.pk})
    remaining = TrailProgress.objects.filter(assignment=assignment, completed_at__isnull=True).exists()
    if not remaining:
        assignment.completed_at = timezone.now()
        assignment.save(update_fields=('completed_at',))
        track_event(user, ContentEvent.TRAIL_COMPLETED, assignment.trail)
    return progress


def create_rule_recommendation(user, target, reason, *, assignment=None, source='rule', is_mandatory=False):
    """Create an explainable recommendation only after eligibility is evaluated."""
    if not eligibility.can_view(user, target).allowed:
        return None
    return ContentRecommendation.objects.create(
        assignment=assignment,
        user=user,
        content_type=ContentType.objects.get_for_model(target),
        object_id=target.pk,
        reason=reason,
        source=source,
        is_mandatory=is_mandatory,
    )


def get_or_create_recommendation(user, target, reason, *, source='rule', is_mandatory=False):
    """Return one open recommendation and register its impression."""
    content_type = ContentType.objects.get_for_model(target)
    recommendation = ContentRecommendation.objects.filter(
        user=user, content_type=content_type, object_id=target.pk,
        opened_at__isnull=True, dismissed_at__isnull=True,
    ).order_by('-created_at').first()
    if recommendation is None:
        recommendation = create_rule_recommendation(
            user, target, reason, source=source, is_mandatory=is_mandatory,
        )
    if recommendation and recommendation.shown_at is None:
        recommendation.shown_at = timezone.now()
        recommendation.save(update_fields=('shown_at',))
        track_event(user, ContentEvent.RECOMMENDATION_SHOWN, target, metadata={'recommendation_id': recommendation.pk, 'source': source})
    return recommendation


def dismiss_recommendation(user, recommendation):
    """Dismiss optional guidance while preserving an auditable event."""
    if recommendation.user_id != user.pk or recommendation.is_mandatory or recommendation.opened_at:
        return False
    recommendation.dismissed_at = timezone.now()
    recommendation.save(update_fields=('dismissed_at',))
    target = recommendation.content_object
    if target:
        track_event(
            user, ContentEvent.RECOMMENDATION_DISMISSED, target,
            metadata={'recommendation_id': recommendation.pk, 'source': recommendation.source},
        )
    return True


def recommend_from_signal(user, *, signal, term='', target=None, limit=3):
    """Create explainable recommendations from a search or usefulness signal."""
    from publishing.models import Publication
    candidates = Publication.objects.filter(
        status=Publication.PUBLISHED,
        published_at__isnull=False,
    ).prefetch_related('tags').order_by('-importance', '-published_at')
    if target is not None and hasattr(target, 'tags'):
        candidates = candidates.filter(tags__in=target.tags.all()).exclude(pk=target.pk).distinct()
    elif term:
        # A failed search is answered with a small, high-confidence operational
        # shortlist rather than pretending that an exact match exists.
        candidates = candidates.filter(importance__in=(Publication.CRITICAL, Publication.IMPORTANT))
    results = []
    for candidate in candidates[:20]:
        if not eligibility.can_view(user, candidate).allowed:
            continue
        recommendation = get_or_create_recommendation(
            user,
            candidate,
            'Sugestão gerada a partir de ' + ('uma busca sem resultados.' if signal == 'search_no_result' else 'um feedback que indicou necessidade de melhoria.'),
            source=signal,
        )
        if recommendation:
            results.append(recommendation)
        if len(results) >= limit:
            break
    return results


def mark_recommendation_opened(user, recommendation):
    if recommendation.user_id != user.pk or recommendation.opened_at:
        return False
    recommendation.opened_at = timezone.now()
    recommendation.save(update_fields=('opened_at',))
    target = recommendation.content_object
    if target:
        track_event(user, ContentEvent.RECOMMENDATION_OPENED, target, metadata={'recommendation_id': recommendation.pk, 'source': recommendation.source})
    return True


def create_notification(user, *, title, message='', url='/', priority=UserNotification.ROUTINE,
                        dedupe_key='', organization=None, expires_at=None):
    """Create one controlled in-app notification per user and business event."""
    tenant_user = _get_tenant_user(user)
    if not tenant_user:
        return None
    preference = UserNotificationPreference.objects.filter(user=tenant_user, organization=organization).first()
    if preference:
        priority_rank = {UserNotification.ROUTINE: 0, UserNotification.IMPORTANT: 1, UserNotification.CRITICAL: 2}
        if priority != UserNotification.CRITICAL and (not preference.in_app or priority_rank[priority] < priority_rank[preference.minimum_priority]):
            return None
    notification, created = UserNotification.objects.get_or_create(
        user=tenant_user,
        dedupe_key=dedupe_key or f'{priority}:{url}:{title}',
        defaults={
            'organization': organization,
            'title': title,
            'message': message,
            'url': url,
            'priority': priority,
            'expires_at': expires_at,
        },
    )
    if created and preference and preference.email and getattr(user, 'email', ''):
        deliver_notification(notification, channel=NotificationDelivery.EMAIL)
    if created and preference and preference.push:
        deliver_notification(notification, channel=NotificationDelivery.PUSH)
    return notification


def evaluate_notification_rules(trigger_type, target, *, actor=None):
    """Apply enabled rules to an object while preserving audience eligibility."""
    organization = getattr(target, 'organization', None)
    rules = NotificationRule.objects.filter(enabled=True, trigger_type=trigger_type)
    if organization:
        rules = rules.filter(organization__isnull=True) | rules.filter(organization=organization)
    users = get_user_model().objects.filter(is_active=True)
    if organization:
        users = users.filter(memberships__organization=organization, memberships__active=True).distinct()
    created = 0
    for rule in rules:
        condition = rule.condition or {}
        if condition.get('category') and getattr(target, 'category', '') != condition['category']:
            continue
        if condition.get('importance') and getattr(target, 'importance', '') != condition['importance']:
            continue
        if condition.get('status') and getattr(target, 'status', '') != condition['status']:
            continue
        policy = getattr(target, 'audience_policy', None)
        for user in users:
            if policy and not eligibility.can_view(user, target).allowed:
                continue
            action = rule.action or {}
            notification = create_notification(
                user,
                title=action.get('title') or rule.name,
                message=action.get('message') or getattr(target, 'description', ''),
                url=action.get('url') or '/',
                priority=action.get('priority', UserNotification.IMPORTANT),
                dedupe_key=f'rule:{rule.pk}:{trigger_type}:{target.pk}',
                organization=organization,
            )
            created += bool(notification)
    return created


def deliver_notification(notification, *, channel):
    """Attempt configured delivery and preserve a provider-neutral audit record."""
    delivery, _ = NotificationDelivery.objects.get_or_create(notification=notification, channel=channel)
    if channel == NotificationDelivery.PUSH:
        try:
            from pywebpush import webpush
            vapid_private_key = getattr(settings, 'TALK_VAPID_PRIVATE_KEY', '')
            vapid_subject = getattr(settings, 'TALK_VAPID_SUBJECT', '')
            subscriptions = PushSubscription.objects.filter(user=notification.user, active=True)
            if not vapid_private_key or not subscriptions.exists():
                raise RuntimeError('Push não configurado ou usuário sem inscrição ativa.')
            for subscription in subscriptions:
                webpush(
                    subscription_info={
                        'endpoint': subscription.endpoint,
                        'keys': subscription.keys,
                    },
                    data=json.dumps({'title': notification.title, 'message': notification.message, 'url': notification.url}),
                    vapid_private_key=vapid_private_key,
                    vapid_claims={'sub': vapid_subject},
                )
            delivery.status = NotificationDelivery.SENT
            delivery.delivered_at = timezone.now()
            delivery.error_message = ''
        except Exception as exc:
            delivery.status = NotificationDelivery.FAILED
            delivery.error_message = str(exc)[:2000]
        delivery.save(update_fields=('status', 'delivered_at', 'error_message'))
        return delivery
    if channel != NotificationDelivery.EMAIL:
        return delivery
    try:
        context = {'notification': notification, 'user': notification.user}
        text_body = render_to_string('learning/emails/notification.txt', context)
        html_body = render_to_string('learning/emails/notification.html', context)
        email = EmailMultiAlternatives(
            subject=f'[Talk] {notification.title}',
            body=text_body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            to=[notification.user.email],
        )
        email.attach_alternative(html_body, 'text/html')
        email.send(fail_silently=False)
        delivery.status = NotificationDelivery.SENT
        delivery.delivered_at = timezone.now()
        delivery.error_message = ''
    except Exception as exc:  # delivery failures must not block content access
        delivery.status = NotificationDelivery.FAILED
        delivery.error_message = str(exc)[:2000]
    delivery.save(update_fields=('status', 'delivered_at', 'error_message'))
    return delivery


def mark_notifications_read_for_url(user, url):
    """Mark content alerts as read when the user opens their destination."""
    if not getattr(user, 'is_authenticated', False) or not url:
        return 0
    notifications = UserNotification.objects.filter(
        user=user,
        url=url,
        read_at__isnull=True,
    )
    notification_ids = list(notifications.values_list('pk', flat=True))
    count = notifications.update(read_at=timezone.now())
    NotificationDelivery.objects.filter(notification_id__in=notification_ids, opened_at__isnull=True).update(opened_at=timezone.now())
    return count


def get_enrollment(user, course):
    return CourseEnroll.objects.filter(student_id=user, course_id=course).first()


@transaction.atomic
def enroll_user(user, course):
    enrollment, created = CourseEnroll.objects.get_or_create(
        student_id=user,
        course_id=course,
    )
    course.students.add(user)
    if created:
        track_event(user, ContentEvent.COURSE_ENROLLED, course)
    return enrollment, created


def issue_course_certificate(user, course, *, completed_at=None):
    completed_at = completed_at or timezone.now()
    certificate, created = CourseCertificate.objects.get_or_create(
        course=course,
        user=user,
        defaults={
            'certificate_number': f'TALK-{course.pk}-{user.pk}-{uuid.uuid4().hex[:10].upper()}',
            'completed_at': completed_at,
            'metadata': {'course_title': course.title},
        },
    )
    return certificate, created


def calculate_progress(total_items, completed_items):
    if total_items <= 0:
        return 0
    completed_items = min(completed_items, total_items)
    return (completed_items / total_items) * 100


def enrollment_progress(enrollment):
    total_items = Content.objects.filter(module__course=enrollment.course_id).count()
    completed_items = ContentEnroll.objects.filter(
        module_enroll_id__course_enroll_id=enrollment,
        done=True,
    ).count()
    return calculate_progress(total_items, completed_items)


@transaction.atomic
def mark_content_completed(user, content):
    enrollment = get_enrollment(user, content.module.course)
    if enrollment is None:
        return None

    module_enrollment, _ = ModuleEnroll.objects.get_or_create(
        course_enroll_id=enrollment,
        module_id=content.module,
    )
    content_enrollment, created = ContentEnroll.objects.get_or_create(
        module_enroll_id=module_enrollment,
        content_id=content,
    )
    was_done = content_enrollment.done
    content_enrollment.done = True
    if content.content_type.model == 'quiz':
        content_enrollment.quiz_id = content.item
    content_enrollment.save(update_fields=['done', 'quiz_id'])
    if created or not was_done:
        track_event(user, ContentEvent.CONTENT_COMPLETED, content)
        content_type = ContentType.objects.get_for_model(content)
        assigned_steps = TrailStep.objects.filter(
            content_type=content_type,
            object_id=content.pk,
            trail__status=ContentTrail.PUBLISHED,
            trail__assignments__user=user,
        ).select_related('trail')
        for step in assigned_steps:
            assignment = TrailAssignment.objects.filter(trail=step.trail, user=user).first()
            if assignment:
                complete_trail_step(user, assignment, step)
        total_items = Content.objects.filter(module__course=enrollment.course_id).count()
        completed_items = ContentEnroll.objects.filter(
            module_enroll_id__course_enroll_id=enrollment, done=True,
        ).count()
        if total_items and completed_items >= total_items:
            certificate, certificate_created = issue_course_certificate(user, enrollment.course)
            if certificate_created:
                track_event(user, ContentEvent.COURSE_COMPLETED, enrollment.course, metadata={'certificate_id': certificate.pk})
    return content_enrollment
