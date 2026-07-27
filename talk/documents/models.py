import hashlib

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from tenants_core.models import TenantUser, TenantOrganization


class Document(models.Model):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    STATUS_CHOICES = ((DRAFT, 'Rascunho'), (PUBLISHED, 'Publicado'), (ARCHIVED, 'Arquivado'))
    CATEGORY_CHOICES = (
        ('policy', 'Política'), ('procedure', 'Procedimento'), ('manual', 'Manual'),
        ('form', 'Formulário'), ('evidence', 'Evidência'), ('other', 'Outro'),
    )
    organization = models.ForeignKey(TenantOrganization, null=True, blank=True, on_delete=models.CASCADE, related_name='documents')
    audience_policy = models.ForeignKey('audience.AudiencePolicy', null=True, blank=True, on_delete=models.SET_NULL, related_name='documents')
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True)
    code = models.CharField(max_length=80, blank=True, db_index=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True)
    announce_changes = models.BooleanField(default=True, help_text='Gera uma comunicação no Feed quando houver nova versão ou arquivamento.')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=DRAFT)
    current_version = models.ForeignKey('DocumentVersion', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    owner = models.ForeignKey(TenantUser, on_delete=models.PROTECT, related_name='owned_documents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-updated_at',)

    def __str__(self):
        return f'{self.code} · {self.title}' if self.code else self.title

    @property
    def is_available(self):
        if self.status != self.PUBLISHED or self.current_version_id is None:
            return False
        version = self.current_version
        now = timezone.now()
        return (
            version.effective_at is None or version.effective_at <= now
        ) and (
            version.expires_at is None or version.expires_at > now
        )

    @property
    def is_expired(self):
        return bool(
            self.current_version_id and self.current_version.expires_at
            and self.current_version.expires_at <= timezone.now()
        )


class DocumentPermission(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='explicit_permissions')
    user = models.ForeignKey(TenantUser, on_delete=models.CASCADE, related_name='document_permissions')
    can_view = models.BooleanField(default=True)
    can_download = models.BooleanField(default=False)
    can_manage = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    granted_by = models.ForeignKey(TenantUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='document_permissions_granted')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('document', 'user'), name='unique_document_permission')]


class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    file = models.FileField(upload_to='documents/versions/', blank=True)
    body = models.TextField(blank=True)
    mime_type = models.CharField(max_length=120, blank=True)
    file_size = models.PositiveBigIntegerField(default=0)
    checksum = models.CharField(max_length=64, blank=True)
    change_summary = models.TextField(blank=True)
    created_by = models.ForeignKey(TenantUser, on_delete=models.PROTECT, related_name='document_versions_created')
    created_at = models.DateTimeField(auto_now_add=True)
    effective_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    superseded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-version_number',)
        constraints = [models.UniqueConstraint(fields=('document', 'version_number'), name='unique_document_version')]

    def __str__(self):
        return f'{self.document.title} v{self.version_number}'

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size or 0
            if not self.mime_type:
                self.mime_type = getattr(self.file.file, 'content_type', '') or ''
            if not self.checksum:
                digest = hashlib.sha256()
                current_position = self.file.tell()
                self.file.seek(0)
                for chunk in self.file.chunks():
                    digest.update(chunk)
                self.file.seek(current_position)
                self.checksum = digest.hexdigest()
        super().save(*args, **kwargs)


class DocumentView(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='views')
    version = models.ForeignKey(DocumentVersion, null=True, blank=True, on_delete=models.SET_NULL, related_name='views')
    user = models.ForeignKey(TenantUser, on_delete=models.CASCADE, related_name='document_views')
    session_id = models.CharField(max_length=80, blank=True)
    first_opened_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    active_seconds = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('document', 'version', 'user', 'session_id'), name='unique_document_view_session')]


class DocumentLink(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='links')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    label = models.CharField(max_length=120, blank=True)
    created_by = models.ForeignKey(TenantUser, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('document', 'content_type', 'object_id'), name='unique_document_link')]


class DocumentEvent(models.Model):
    OPENED = 'opened'
    ACTIVE = 'active'
    DOWNLOADED = 'downloaded'
    EVENT_CHOICES = ((OPENED, 'Aberto'), (ACTIVE, 'Leitura ativa'), (DOWNLOADED, 'Baixado'))
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='events')
    version = models.ForeignKey(DocumentVersion, null=True, blank=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(TenantUser, null=True, on_delete=models.SET_NULL)
    event_name = models.CharField(max_length=16, choices=EVENT_CHOICES)
    active_seconds = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-occurred_at',)
