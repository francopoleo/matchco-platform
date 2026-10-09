from django.contrib import admin

from .models import (
    Document, DocumentEvent, DocumentLink, DocumentPermission, DocumentVersion, DocumentView,
    MediaAsset, MediaAssetVersion, MediaAssetAuditEvent, MediaAssetUsage, MediaAssetShareLink,
    MediaCollection, MediaTag
)


class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    readonly_fields = ('version_number', 'created_at', 'created_by', 'file_size', 'checksum')


class DocumentPermissionInline(admin.TabularInline):
    model = DocumentPermission
    extra = 0


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'category', 'status', 'organization', 'current_version', 'updated_at')
    list_filter = ('status', 'category', 'organization')
    search_fields = ('title', 'code', 'slug')
    list_select_related = ('organization', 'current_version')
    inlines = (DocumentVersionInline, DocumentPermissionInline)


@admin.register(DocumentPermission)
class DocumentPermissionAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'can_view', 'can_download', 'can_manage', 'expires_at', 'granted_by')
    list_filter = ('can_view', 'can_download', 'can_manage')
    list_select_related = ('document', 'user', 'granted_by')
    autocomplete_fields = ('document',)


@admin.register(DocumentView)
class DocumentViewAdmin(admin.ModelAdmin):
    list_display = ('document', 'version', 'user', 'active_seconds', 'download_count', 'last_seen_at')
    list_filter = ('document', 'version')
    list_select_related = ('document', 'version', 'user')


@admin.register(DocumentEvent)
class DocumentEventAdmin(admin.ModelAdmin):
    list_display = ('document', 'version', 'user', 'event_name', 'active_seconds', 'occurred_at')
    list_filter = ('event_name', 'document')
    list_select_related = ('document', 'version', 'user')


@admin.register(DocumentLink)
class DocumentLinkAdmin(admin.ModelAdmin):
    list_display = ('document', 'content_type', 'object_id', 'label', 'created_at')
    list_select_related = ('document',)


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ('title', 'kind', 'organization', 'workflow_status', 'active', 'access_count', 'updated_at')
    list_filter = ('kind', 'workflow_status', 'active', 'organization')
    search_fields = ('title', 'alt_text')
    list_select_related = ('organization', 'owner', 'collection')


@admin.register(MediaAssetVersion)
class MediaAssetVersionAdmin(admin.ModelAdmin):
    list_display = ('asset', 'version_number', 'file_size', 'checksum', 'created_at')
    list_select_related = ('asset', 'created_by')


@admin.register(MediaAssetAuditEvent)
class MediaAssetAuditEventAdmin(admin.ModelAdmin):
    list_display = ('asset', 'event_name', 'actor', 'organization', 'occurred_at')
    list_filter = ('event_name', 'organization')
    list_select_related = ('asset', 'actor', 'organization')


@admin.register(MediaAssetUsage)
class MediaAssetUsageAdmin(admin.ModelAdmin):
    list_display = ('asset', 'content_type', 'object_id', 'field_name', 'first_seen_at')
    list_select_related = ('asset', 'content_type', 'created_by')


@admin.register(MediaAssetShareLink)
class MediaAssetShareLinkAdmin(admin.ModelAdmin):
    list_display = ('asset', 'expires_at', 'active', 'access_count', 'created_at')
    list_filter = ('active',)
    list_select_related = ('asset', 'created_by')


@admin.register(MediaCollection)
class MediaCollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'active', 'created_at')
    list_filter = ('active', 'organization')
    list_select_related = ('organization', 'owner')


@admin.register(MediaTag)
class MediaTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'created_at')
    list_select_related = ('organization',)
