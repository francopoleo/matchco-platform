import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from tenants_core.models import TenantUser, TenantOrganization, TenantCompany


class ContentEvent(models.Model):
    """Auditable, privacy-aware event stream for content and learning journeys."""

    SESSION_STARTED = 'session_started'
    CONTENT_OPENED = 'content_opened'
    CONTENT_ACTIVE = 'content_active'
    VIDEO_PROGRESS = 'video_progress'
    ATTACHMENT_OPENED = 'attachment_opened'
    CONTENT_ACKNOWLEDGED = 'content_acknowledged'
    FEEDBACK_SUBMITTED = 'feedback_submitted'
    QUESTION_SUBMITTED = 'question_submitted'
    CONTENT_RELATED_OPENED = 'content_related_opened'
    COURSE_ENROLLED = 'course_enrolled'
    MODULE_STARTED = 'module_started'
    QUIZ_STARTED = 'quiz_started'
    QUIZ_COMPLETED = 'quiz_completed'
    CONTENT_RESUMED = 'content_resumed'
    ACTION_COMPLETED = 'action_completed'
    CONTENT_COMPLETED = 'content_completed'
    COURSE_COMPLETED = 'course_completed'
    SEARCH_PERFORMED = 'search_performed'
    RECOMMENDATION_SHOWN = 'recommendation_shown'
    RECOMMENDATION_OPENED = 'recommendation_opened'
    RECOMMENDATION_DISMISSED = 'recommendation_dismissed'
    TRAIL_STARTED = 'trail_started'
    TRAIL_STEP_COMPLETED = 'trail_step_completed'
    TRAIL_COMPLETED = 'trail_completed'

    EVENT_CHOICES = tuple((value, value.replace('_', ' ').title()) for value in (
        SESSION_STARTED, CONTENT_OPENED, CONTENT_ACTIVE, VIDEO_PROGRESS,
        ATTACHMENT_OPENED, CONTENT_ACKNOWLEDGED, FEEDBACK_SUBMITTED,
        QUESTION_SUBMITTED, CONTENT_RELATED_OPENED, COURSE_ENROLLED,
        MODULE_STARTED, QUIZ_STARTED, QUIZ_COMPLETED, CONTENT_RESUMED, ACTION_COMPLETED,
        CONTENT_COMPLETED, COURSE_COMPLETED, SEARCH_PERFORMED,
        RECOMMENDATION_SHOWN, RECOMMENDATION_OPENED, RECOMMENDATION_DISMISSED,
        TRAIL_STARTED, TRAIL_STEP_COMPLETED, TRAIL_COMPLETED,
    ))

    user = models.ForeignKey(
        TenantUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='learning_events',
    )
    organization = models.ForeignKey(
        TenantOrganization,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='learning_events',
    )
    event_name = models.CharField(max_length=40, choices=EVENT_CHOICES)
    content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='learning_events',
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    session_id = models.CharField(max_length=80, blank=True)
    active_seconds = models.PositiveIntegerField(default=0)
    progress_percent = models.PositiveSmallIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-occurred_at',)
        indexes = [
            models.Index(fields=('event_name', 'occurred_at')),
            models.Index(fields=('content_type', 'object_id', 'event_name')),
            models.Index(fields=('user', 'occurred_at')),
            models.Index(fields=('organization', 'occurred_at')),
        ]


class PointLedger(models.Model):
    """Immutable points ledger derived from auditable learning events."""

    user = models.ForeignKey(TenantUser, on_delete=models.CASCADE, related_name='learning_points')
    organization = models.ForeignKey(TenantOrganization, null=True, blank=True, on_delete=models.SET_NULL, related_name='learning_points')
    source_event = models.OneToOneField(ContentEvent, null=True, blank=True, on_delete=models.SET_NULL, related_name='points_award')
    points = models.IntegerField()
    reason = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [models.Index(fields=('user', 'created_at')), models.Index(fields=('organization', 'created_at'))]


class BadgeDefinition(models.Model):
    code = models.SlugField(max_length=80, unique=True)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    points_threshold = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class UserBadge(models.Model):
    user = models.ForeignKey(TenantUser, on_delete=models.CASCADE, related_name='learning_badges')
    badge = models.ForeignKey(BadgeDefinition, on_delete=models.CASCADE, related_name='awards')
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('user', 'badge'), name='learning_user_badge_unique')]


class LearningChallenge(models.Model):
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    TYPE_CHOICES = ((WEEKLY, 'Semanal'), (MONTHLY, 'Mensal'))
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    challenge_type = models.CharField(max_length=16, choices=TYPE_CHOICES, default=WEEKLY)
    target_points = models.PositiveIntegerField(default=100)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ('-starts_at',)


class ChallengeProgress(models.Model):
    challenge = models.ForeignKey(LearningChallenge, on_delete=models.CASCADE, related_name='progress')
    user = models.ForeignKey(TenantUser, on_delete=models.CASCADE, related_name='learning_challenge_progress')
    points = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('challenge', 'user'), name='learning_challenge_user_unique')]


class AnalyticsExportAudit(models.Model):
    user = models.ForeignKey(TenantUser, null=True, on_delete=models.SET_NULL, related_name='analytics_exports')
    organization = models.ForeignKey(TenantOrganization, null=True, blank=True, on_delete=models.SET_NULL, related_name='analytics_exports')
    report_name = models.CharField(max_length=120)
    filters = models.JSONField(default=dict, blank=True)
    row_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [models.Index(fields=('organization', 'created_at'))]


class ContentTrail(models.Model):
    REQUIRED = 'required'
    RECOMMENDED = 'recommended'
    CONTEXTUAL = 'contextual'
    TYPE_CHOICES = (
        (REQUIRED, 'Obrigatória'),
        (RECOMMENDED, 'Recomendada'),
        (CONTEXTUAL, 'Contextual'),
    )
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    STATUS_CHOICES = ((DRAFT, 'Rascunho'), (PUBLISHED, 'Publicada'), (ARCHIVED, 'Arquivada'))

    organization = models.ForeignKey(
        TenantOrganization, null=True, blank=True,
        on_delete=models.CASCADE, related_name='content_trails',
    )
    company = models.ForeignKey(
        TenantCompany, null=True, blank=True,
        on_delete=models.CASCADE, related_name='content_trails',
    )
    audience_policy = models.ForeignKey(
        'audience.AudiencePolicy', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='content_trails',
    )
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True)
    objective = models.TextField(blank=True)
    trail_type = models.CharField(max_length=16, choices=TYPE_CHOICES, default=RECOMMENDED)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=DRAFT)
    version = models.PositiveIntegerField(default=1)
    valid_until = models.DateTimeField(null=True, blank=True)
    owner = models.ForeignKey(TenantUser, on_delete=models.PROTECT, related_name='content_trails_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return self.title

    @property
    def is_published(self):
        return self.status == self.PUBLISHED


class TrailStep(models.Model):
    trail = models.ForeignKey(ContentTrail, on_delete=models.CASCADE, related_name='steps')
    position = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=220, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    required = models.BooleanField(default=True)
    completion_event = models.CharField(max_length=40, default=ContentEvent.CONTENT_OPENED)
    prerequisite = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='dependents')

    class Meta:
        ordering = ('position', 'id')
        indexes = [models.Index(fields=('content_type', 'object_id'))]


class TrailAssignment(models.Model):
    COMPLIANCE_TYPE_CHOICES = (
        ('general', 'General'),
        ('internal', 'Internal Employee'),
        ('external', 'External Partner'),
        ('stakeholder', 'Stakeholder/Manager'),
    )

    trail = models.ForeignKey(ContentTrail, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(TenantUser, null=True, blank=True, on_delete=models.CASCADE, related_name='trail_assignments')
    audience_policy = models.ForeignKey('audience.AudiencePolicy', null=True, blank=True, on_delete=models.CASCADE, related_name='trail_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.CharField(max_length=220, blank=True)
    is_mandatory = models.BooleanField(default=False, help_text='If True, user MUST complete before accessing resources')
    compliance_type = models.CharField(max_length=20, choices=COMPLIANCE_TYPE_CHOICES, default='general')

    class Meta:
        indexes = [models.Index(fields=('trail', 'user')), models.Index(fields=('trail', 'audience_policy'))]


class TrailProgress(models.Model):
    assignment = models.ForeignKey(TrailAssignment, on_delete=models.CASCADE, related_name='progress')
    step = models.ForeignKey(TrailStep, on_delete=models.CASCADE, related_name='progress')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    active_seconds = models.PositiveIntegerField(default=0)
    usefulness = models.CharField(max_length=16, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('assignment', 'step'), name='learning_trail_progress_unique')]


class ContentRecommendation(models.Model):
    assignment = models.ForeignKey(TrailAssignment, null=True, blank=True, on_delete=models.CASCADE, related_name='recommendations')
    user = models.ForeignKey(TenantUser, on_delete=models.CASCADE, related_name='content_recommendations')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    reason = models.CharField(max_length=220)
    source = models.CharField(max_length=40, default='rule')
    is_mandatory = models.BooleanField(default=False)
    shown_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=('user', 'created_at')), models.Index(fields=('content_type', 'object_id'))]


class UserNotification(models.Model):
    ROUTINE = 'routine'
    IMPORTANT = 'important'
    CRITICAL = 'critical'
    PRIORITY_CHOICES = ((ROUTINE, 'Rotina'), (IMPORTANT, 'Importante'), (CRITICAL, 'Crítica'))

    user = models.ForeignKey(TenantUser, on_delete=models.CASCADE, related_name='notifications')
    organization = models.ForeignKey(TenantOrganization, null=True, blank=True, on_delete=models.CASCADE, related_name='user_notifications')
    title = models.CharField(max_length=220)
    message = models.TextField(blank=True)
    url = models.URLField(max_length=500)
    priority = models.CharField(max_length=12, choices=PRIORITY_CHOICES, default=ROUTINE)
    dedupe_key = models.CharField(max_length=180)
    read_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('read_at', '-created_at')
        constraints = [models.UniqueConstraint(fields=('user', 'dedupe_key'), name='learning_notification_user_key_unique')]


class UserNotificationPreference(models.Model):
    user = models.ForeignKey(TenantUser, on_delete=models.CASCADE, related_name='notification_preferences')
    organization = models.ForeignKey(TenantOrganization, null=True, blank=True, on_delete=models.CASCADE, related_name='notification_preferences')
    minimum_priority = models.CharField(max_length=12, choices=UserNotification.PRIORITY_CHOICES, default=UserNotification.ROUTINE)
    in_app = models.BooleanField(default=True)
    email = models.BooleanField(default=False)
    push = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('user', 'organization'), name='learning_user_notification_preference_unique')]


class NotificationRule(models.Model):
    """Declarative, auditable notification rule evaluated by domain events."""

    DOCUMENT_PUBLISHED = 'document_published'
    DOCUMENT_UPDATED = 'document_updated'
    DOCUMENT_ARCHIVED = 'document_archived'
    TRIGGER_CHOICES = (
        (DOCUMENT_PUBLISHED, 'Documento publicado'),
        (DOCUMENT_UPDATED, 'Documento atualizado'),
        (DOCUMENT_ARCHIVED, 'Documento arquivado'),
    )
    organization = models.ForeignKey(TenantOrganization, null=True, blank=True, on_delete=models.CASCADE, related_name='notification_rules')
    name = models.CharField(max_length=180)
    trigger_type = models.CharField(max_length=40, choices=TRIGGER_CHOICES)
    condition = models.JSONField(default=dict, blank=True)
    action = models.JSONField(default=dict, blank=True)
    enabled = models.BooleanField(default=True)
    created_by = models.ForeignKey(TenantUser, on_delete=models.PROTECT, related_name='notification_rules_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)
        constraints = [models.UniqueConstraint(fields=('organization', 'name'), name='learning_notification_rule_name_unique')]


class NotificationDelivery(models.Model):
    EMAIL = 'email'
    PUSH = 'push'
    CHANNEL_CHOICES = ((EMAIL, 'E-mail'), (PUSH, 'Push'))
    PENDING = 'pending'
    SENT = 'sent'
    FAILED = 'failed'
    STATUS_CHOICES = ((PENDING, 'Pendente'), (SENT, 'Enviada'), (FAILED, 'Falhou'))
    notification = models.ForeignKey(UserNotification, on_delete=models.CASCADE, related_name='deliveries')
    channel = models.CharField(max_length=12, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=PENDING)
    provider_message_id = models.CharField(max_length=180, blank=True)
    error_message = models.TextField(blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('notification', 'channel'), name='learning_notification_delivery_unique')]


class PushSubscription(models.Model):
    user = models.ForeignKey(TenantUser, on_delete=models.CASCADE, related_name='push_subscriptions')
    organization = models.ForeignKey(TenantOrganization, null=True, blank=True, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField(max_length=1000, unique=True)
    keys = models.JSONField(default=dict, blank=True)
    active = models.BooleanField(default=True)
    user_agent = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=('user', 'active'))]


class CourseCertificate(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='certificates')
    user = models.ForeignKey(TenantUser, on_delete=models.CASCADE, related_name='course_certificates')
    certificate_number = models.CharField(max_length=40, unique=True)
    verification_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    issued_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ('-issued_at',)
        constraints = [models.UniqueConstraint(fields=('course', 'user'), name='learning_course_certificate_unique')]
