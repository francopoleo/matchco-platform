from django.contrib import admin

from .models import ContentItem, ContentItemProgress


@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'kind', 'module', 'published', 'updated_at')
    list_filter = ('kind', 'published')
    search_fields = ('title', 'description', 'body')


@admin.register(ContentItemProgress)
class ContentItemProgressAdmin(admin.ModelAdmin):
    list_display = ('item', 'user', 'completed', 'completed_at')
    list_filter = ('completed',)
    search_fields = ('item__title', 'user__username')
