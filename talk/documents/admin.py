from django.contrib import admin

from .models import Document, DocumentEvent, DocumentLink, DocumentPermission, DocumentVersion, DocumentView


class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    readonly_fields = ('version_number', 'created_at', 'created_by', 'file_size', 'checksum')


class DocumentPermissionInline(admin.TabularInline):
    model = DocumentPermission
    extra = 0
    autocomplete_fields = ('user', 'granted_by')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'category', 'status', 'organization', 'current_version', 'updated_at')
    list_filter = ('status', 'category', 'organization')
    search_fields = ('title', 'code', 'slug')
    inlines = (DocumentVersionInline, DocumentPermissionInline)


@admin.register(DocumentPermission)
class DocumentPermissionAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'can_view', 'can_download', 'can_manage', 'expires_at', 'granted_by')
    list_filter = ('can_view', 'can_download', 'can_manage')
    autocomplete_fields = ('document', 'user', 'granted_by')


@admin.register(DocumentView)
class DocumentViewAdmin(admin.ModelAdmin):
    list_display = ('document', 'version', 'user', 'active_seconds', 'download_count', 'last_seen_at')
    list_filter = ('document', 'version')


@admin.register(DocumentEvent)
class DocumentEventAdmin(admin.ModelAdmin):
    list_display = ('document', 'version', 'user', 'event_name', 'active_seconds', 'occurred_at')
    list_filter = ('event_name', 'document')


@admin.register(DocumentLink)
class DocumentLinkAdmin(admin.ModelAdmin):
    list_display = ('document', 'content_type', 'object_id', 'label', 'created_at')
