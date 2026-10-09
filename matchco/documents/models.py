import mimetypes
import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from audience.models import AudiencePolicy
from tenants_core.models import TenantUser, TenantOrganization
from tenants_core.models import TenantCompany
from matchco.core.utils import compute_file_checksum


class AutoSlugMixin(models.Model):
    """Mixin to auto-generate slug from name field."""
    slug = models.SlugField(blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:getattr(self, '_slug_max_length', 90)]
        super().save(*args, **kwargs)


class BaseShareLink(models.Model):
    """Abstract base for time-limited share links (documents and media)."""
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_by = models.ForeignKey(TenantUser, null=True, blank=True, on_delete=models.SET_NULL)
    expires_at = models.DateTimeField()
    active = models.BooleanField(default=True)
    access_count = models.PositiveIntegerField(default=0)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ('-created_at',)

    @property
    def is_valid(self):
        return self.active and self.expires_at > timezone.now() and self._linked_object_is_available()

    def _linked_object_is_available(self):
        """Override in concrete class to check parent object availability."""
        raise NotImplementedError


class Document(models.Model):
    DRAFT = 'draft'
    IN_REVIEW = 'in_review'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    STATUS_CHOICES = ((DRAFT, 'Rascunho'), (IN_REVIEW, 'Em revisão'), (PUBLISHED, 'Publicado'), (ARCHIVED, 'Arquivado'))
    CATEGORY_CHOICES = (
        ('policy', 'Política'), ('procedure', 'Procedimento'), ('manual', 'Manual'),
        ('form', 'Formulário'), ('evidence', 'Evidência'), ('other', 'Outro'),
    )
    organization = models.ForeignKey(TenantOrganization, null=True, blank=True, on_delete=models.CASCADE, related_name='documents')
    company = models.ForeignKey(TenantCompany, null=True, blank=True, on_delete=models.SET_NULL, related_name='documents')
    audience_policy = models.ForeignKey('audience.AudiencePolicy', null=True, blank=True, on_delete=models.SET_NULL, related_name='documents')
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True)
    code = models.CharField(max_length=80, blank=True, db_index=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True)
    announce_changes = models.BooleanField(default=True, help_text='Gera uma comunicação no Feed quando houver nova versão ou arquivamento.')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=DRAFT)
    requires_approval = models.BooleanField(default=False, help_text='Exige aprovação antes de publicar alterações.')
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(TenantUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='documents_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
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


class DocumentShareLink(BaseShareLink):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='share_links')
    created_by = models.ForeignKey(TenantUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='document_share_links_created')

    def _linked_object_is_available(self):
        return self.document.is_available


class MediaCollection(AutoSlugMixin):
    organization = models.ForeignKey(TenantOrganization, null=True, blank=True, on_delete=models.CASCADE, related_name='media_collections')
    owner = models.ForeignKey(TenantUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='owned_media_collections')
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, blank=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    _slug_max_length = 140

    class Meta:
        ordering = ('name',)
        constraints = [models.UniqueConstraint(fields=('organization', 'name'), name='unique_media_collection_org_name')]

    def __str__(self):
        return self.name


class MediaTag(AutoSlugMixin):
    organization = models.ForeignKey(TenantOrganization, null=True, blank=True, on_delete=models.CASCADE, related_name='media_tags')
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=90, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    _slug_max_length = 90

    class Meta:
        ordering = ('name',)
        constraints = [models.UniqueConstraint(fields=('organization', 'name'), name='unique_media_tag_org_name')]

    def __str__(self):
        return self.name


class MediaAsset(models.Model):
    IMAGE = 'image'
    VIDEO = 'video'
    FILE = 'file'
    KIND_CHOICES = ((IMAGE, 'Imagem'), (VIDEO, 'Vídeo'), (FILE, 'Arquivo'))

    DRAFT = 'draft'
    REVIEW = 'review'
    APPROVED = 'approved'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    WORKFLOW_CHOICES = (
        (DRAFT, 'Rascunho'),
        (REVIEW, 'Em revisão'),
        (APPROVED, 'Aprovado'),
        (PUBLISHED, 'Publicado'),
        (ARCHIVED, 'Arquivado'),
    )

    organization = models.ForeignKey(TenantOrganization, null=True, blank=True, on_delete=models.CASCADE, related_name='media_assets')
    company = models.ForeignKey(TenantCompany, null=True, blank=True, on_delete=models.SET_NULL, related_name='media_assets')
    audience_policy = models.ForeignKey(AudiencePolicy, null=True, blank=True, on_delete=models.SET_NULL, related_name='media_assets')
    owner = models.ForeignKey(TenantUser, on_delete=models.PROTECT, related_name='owned_media_assets')
    collection = models.ForeignKey(MediaCollection, null=True, blank=True, on_delete=models.SET_NULL, related_name='assets')
    tags = models.ManyToManyField(MediaTag, blank=True, related_name='assets')
    title = models.CharField(max_length=220)
    kind = models.CharField(max_length=12, choices=KIND_CHOICES, default=IMAGE)
    file = models.FileField(upload_to='media-library/', blank=True)
    preview_file = models.FileField(upload_to='media-library/previews/', blank=True)
    webp_file = models.FileField(upload_to='media-library/derivatives/', blank=True)
    avif_file = models.FileField(upload_to='media-library/derivatives/', blank=True)
    external_url = models.URLField(blank=True)
    alt_text = models.CharField(max_length=220, blank=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    public_access = models.BooleanField(default=False, help_text='Permite abertura sem login. Desativado por padrão.')
    requires_approval = models.BooleanField(default=False, help_text='Exige aprovação de um gestor antes do uso.')
    workflow_status = models.CharField(max_length=12, choices=WORKFLOW_CHOICES, default='published')
    rejection_reason = models.TextField(blank=True)
    approved_by = models.ForeignKey(TenantUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_media_assets')
    approved_at = models.DateTimeField(null=True, blank=True)
    license_name = models.CharField(max_length=160, blank=True)
    source_label = models.CharField(max_length=220, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    retention_until = models.DateTimeField(null=True, blank=True)
    mime_type = models.CharField(max_length=120, blank=True)
    file_size = models.PositiveBigIntegerField(default=0)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    checksum = models.CharField(max_length=64, blank=True, db_index=True)
    access_count = models.PositiveBigIntegerField(default=0)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-updated_at', '-created_at')

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        return bool(self.valid_until and self.valid_until <= timezone.now())

    @property
    def is_published(self):
        return self.active and self.workflow_status in (self.APPROVED, self.PUBLISHED) and not self.is_expired

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size or 0
            self.mime_type = mimetypes.guess_type(self.file.name)[0] or 'application/octet-stream'
            self.checksum = compute_file_checksum(self.file)
        super().save(*args, **kwargs)

    @property
    def url(self):
        if self.file:
            return f'/documents/media/{self.pk}/'
        return self.external_url if self.public_access else ''

    @property
    def preview_url(self):
        if self.preview_file:
            return f'/documents/media/{self.pk}/preview/'
        return self.url

    def delete(self, *args, **kwargs):
        stored_file = self.file
        derivative_files = [self.preview_file, self.webp_file, self.avif_file]
        version_files = [version.file for version in self.versions.all() if version.file]
        super().delete(*args, **kwargs)
        if stored_file:
            stored_file.delete(save=False)
        for version_file in version_files:
            version_file.delete(save=False)
        for derivative_file in derivative_files:
            if derivative_file:
                derivative_file.delete(save=False)


class MediaAssetVersion(models.Model):
    asset = models.ForeignKey(MediaAsset, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    file = models.FileField(upload_to='media-library/versions/', blank=True)
    external_url = models.URLField(blank=True)
    mime_type = models.CharField(max_length=120, blank=True)
    file_size = models.PositiveBigIntegerField(default=0)
    checksum = models.CharField(max_length=64, blank=True)
    change_summary = models.TextField(blank=True)
    created_by = models.ForeignKey(TenantUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='media_versions_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-version_number',)
        constraints = [models.UniqueConstraint(fields=('asset', 'version_number'), name='unique_media_asset_version')]

    def __str__(self):
        return f'{self.asset.title} v{self.version_number}'


class MediaAssetAuditEvent(models.Model):
    UPLOADED = 'uploaded'
    UPDATED = 'updated'
    REPLACED = 'replaced'
    MOVED = 'moved'
    TAGGED = 'tagged'
    PUBLICATED = 'publicated'
    SHARED = 'shared'
    DELETED = 'deleted'
    EVENT_CHOICES = tuple((value, label) for value, label in (
        (UPLOADED, 'Enviado'), (UPDATED, 'Editado'), (REPLACED, 'Substituído'),
        (MOVED, 'Movido'), (TAGGED, 'Tags alteradas'), (PUBLICATED, 'Acesso público alterado'),
        (SHARED, 'Link temporário criado'),
        (DELETED, 'Excluído'),
    ))
    asset = models.ForeignKey(MediaAsset, null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_events')
    organization = models.ForeignKey(TenantOrganization, null=True, blank=True, on_delete=models.SET_NULL)
    actor = models.ForeignKey(TenantUser, null=True, blank=True, on_delete=models.SET_NULL)
    event_name = models.CharField(max_length=20, choices=EVENT_CHOICES)
    metadata = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-occurred_at',)


class MediaAssetUsage(models.Model):
    asset = models.ForeignKey(MediaAsset, on_delete=models.CASCADE, related_name='usages')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    field_name = models.CharField(max_length=80, default='content')
    created_by = models.ForeignKey(TenantUser, null=True, blank=True, on_delete=models.SET_NULL)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('asset', 'content_type', 'object_id', 'field_name'), name='unique_media_asset_usage')]
        indexes = [models.Index(fields=('content_type', 'object_id'))]


class MediaAssetUserState(models.Model):
    asset = models.ForeignKey(MediaAsset, on_delete=models.CASCADE, related_name='user_states')
    user = models.ForeignKey(TenantUser, on_delete=models.CASCADE, related_name='media_asset_states')
    favorite = models.BooleanField(default=False)
    open_count = models.PositiveIntegerField(default=0)
    last_opened_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('asset', 'user'), name='unique_media_asset_user_state')]
        indexes = [models.Index(fields=('user', 'favorite')), models.Index(fields=('user', 'last_opened_at'))]


class MediaAssetShareLink(BaseShareLink):
    asset = models.ForeignKey(MediaAsset, on_delete=models.CASCADE, related_name='share_links')
    created_by = models.ForeignKey(TenantUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='media_share_links_created')

    def _linked_object_is_available(self):
        return self.asset.active


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
    SOURCE_UPLOAD = 'upload'
    SOURCE_RICH_TEXT = 'rich_text'
    SOURCE_GENERATED = 'generated'
    SOURCE_EXTERNAL = 'external'
    SOURCE_CHOICES = (
        (SOURCE_UPLOAD, 'Arquivo anexado'),
        (SOURCE_RICH_TEXT, 'Conteúdo criado no sistema'),
        (SOURCE_GENERATED, 'PDF gerado pelo sistema'),
        (SOURCE_EXTERNAL, 'Link externo'),
    )
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    source_type = models.CharField(max_length=12, choices=SOURCE_CHOICES, default=SOURCE_UPLOAD)
    file = models.FileField(upload_to='documents/versions/', blank=True)
    body = models.TextField(blank=True)
    external_url = models.URLField(blank=True)
    generated_pdf = models.FileField(upload_to='documents/generated/', blank=True)
    thumbnail_file = models.ImageField(upload_to='documents/previews/', blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    generated_by = models.ForeignKey(TenantUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='generated_document_pdfs')
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

    @property
    def display_file(self):
        return self.generated_pdf or self.file

    @property
    def display_mime_type(self):
        if self.generated_pdf:
            return 'application/pdf'
        if self.mime_type:
            return self.mime_type
        if self.body:
            return 'text/html'
        if self.file and self.file.name.lower().endswith(('.html', '.htm')):
            return 'text/html'
        return ''

    @property
    def has_visual_content(self):
        return bool(self.body or self.display_file or self.external_url)

    @property
    def has_html_source(self):
        return bool(
            self.body
            or (self.file and self.file.name.lower().endswith(('.html', '.htm')))
            or (self.mime_type or '').lower() in ('text/html', 'application/xhtml+xml')
        )

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size or 0
            if not self.mime_type:
                self.mime_type = getattr(self.file.file, 'content_type', '') or ''
            if not self.checksum:
                self.checksum = compute_file_checksum(self.file)
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
    MANAGED = 'managed'
    EVENT_CHOICES = ((OPENED, 'Aberto'), (ACTIVE, 'Leitura ativa'), (DOWNLOADED, 'Baixado'), (MANAGED, 'Administrado'))
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='events')
    version = models.ForeignKey(DocumentVersion, null=True, blank=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(TenantUser, null=True, on_delete=models.SET_NULL)
    event_name = models.CharField(max_length=16, choices=EVENT_CHOICES)
    active_seconds = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-occurred_at',)
