import hashlib
import re

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from audience.models import AudiencePolicy
from tenants_core.models import TenantUser, TenantOrganization, TenantCompany


class Tag(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)

    def __str__(self):
        return self.name


class Publication(models.Model):
    WIKI = 'wiki'
    FEED = 'feed'
    KINDS = ((WIKI, 'Wiki'), (FEED, 'Feed'))
    DRAFT = 'draft'
    PUBLISHED = 'published'
    STATUS_CHOICES = ((DRAFT, 'Draft'), (PUBLISHED, 'Published'))
    ROUTINE = 'routine'
    IMPORTANT = 'important'
    CRITICAL = 'critical'
    IMPORTANCE_CHOICES = ((ROUTINE, 'Rotina'), (IMPORTANT, 'Importante'), (CRITICAL, 'Crítica'))
    CONTENT_CATEGORIES = (
        ('update', 'Atualização'),
        ('procedure_change', 'Mudança de procedimento'),
        ('document_update', 'Atualização de documento'),
        ('required_document', 'Documento obrigatório'),
        ('obsolete', 'Conteúdo obsoleto'),
        ('incident', 'Alerta operacional'),
        ('announcement', 'Comunicado'),
    )

    kind = models.CharField(max_length=8, choices=KINDS)
    organization = models.ForeignKey(TenantOrganization, null=True, blank=True, related_name='publications', on_delete=models.CASCADE)
    company = models.ForeignKey(TenantCompany, null=True, blank=True, related_name='publications', on_delete=models.CASCADE)
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True)
    excerpt = models.TextField(blank=True)
    body = models.TextField()
    image = models.ImageField(upload_to='publishing/images/', blank=True)
    video_url = models.URLField(blank=True)
    author = models.ForeignKey(TenantUser, related_name='publications', on_delete=models.PROTECT)
    audience_policy = models.ForeignKey(AudiencePolicy, null=True, blank=True, on_delete=models.SET_NULL)
    tags = models.ManyToManyField(Tag, blank=True, related_name='publications')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    points_per_view = models.PositiveIntegerField(default=0)
    importance = models.CharField(max_length=12, choices=IMPORTANCE_CHOICES, default=ROUTINE)
    content_category = models.CharField(max_length=24, choices=CONTENT_CATEGORIES, default='update')
    requires_acknowledgement = models.BooleanField(default=False)
    reminder_hours = models.PositiveIntegerField(default=24)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-published_at', '-created_at')

    def __str__(self):
        return self.title

    @property
    def is_published(self):
        return self.status == self.PUBLISHED and self.published_at is not None and not self.is_expired

    @property
    def is_expired(self):
        return bool(self.expires_at and self.expires_at <= timezone.now())

    @property
    def is_alert(self):
        return self.importance in {self.IMPORTANT, self.CRITICAL} or self.requires_acknowledgement


class ContentInteraction(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='talk_content_interactions')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(TenantUser, on_delete=models.CASCADE, related_name='content_interactions')
    first_viewed_at = models.DateTimeField(auto_now_add=True)
    last_viewed_at = models.DateTimeField(auto_now=True)
    view_count = models.PositiveIntegerField(default=1)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (('content_type', 'object_id', 'user'),)
        indexes = [models.Index(fields=('content_type', 'object_id'))]


class ContentFeedback(models.Model):
    HELPFUL = 'helpful'
    PARTIAL = 'partial'
    NOT_HELPFUL = 'not_helpful'
    RATING_CHOICES = ((HELPFUL, 'Ajudou'), (PARTIAL, 'Ajudou parcialmente'), (NOT_HELPFUL, 'Não ajudou'))
    REASON_CHOICES = (
        ('outdated', 'Estava desatualizada'),
        ('unclear', 'Não estava clara'),
        ('missing', 'Faltou informação'),
        ('hard_to_find', 'Foi difícil encontrar'),
        ('other', 'Outro motivo'),
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='talk_content_feedback')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(TenantUser, on_delete=models.CASCADE, related_name='content_feedback')
    rating = models.CharField(max_length=16, choices=RATING_CHOICES)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, blank=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('content_type', 'object_id', 'user'),)
        indexes = [models.Index(fields=('content_type', 'object_id', 'rating'))]


class ContentQuestion(models.Model):
    OPEN = 'open'
    ANSWERED = 'answered'
    CLOSED = 'closed'
    STATUS_CHOICES = ((OPEN, 'Aberta'), (ANSWERED, 'Respondida'), (CLOSED, 'Encerrada'))
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='talk_content_questions')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(TenantUser, on_delete=models.CASCADE, related_name='content_questions')
    question = models.TextField(max_length=2000)
    question_hash = models.CharField(max_length=64, db_index=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=OPEN)
    answer = models.TextField(blank=True)
    answered_by = models.ForeignKey(TenantUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='content_questions_answered')
    answered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [models.Index(fields=('content_type', 'object_id', 'status'))]

    def save(self, *args, **kwargs):
        normalized = re.sub(r'\s+', ' ', self.question.strip().lower())
        self.question_hash = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)
