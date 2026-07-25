from django.contrib import admin

from .models import ContentQuestion, Publication, Tag


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'kind', 'status', 'published_at', 'author')
    list_filter = ('kind', 'status', 'audience_policy')
    search_fields = ('title', 'excerpt', 'body')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ContentQuestion)
class ContentQuestionAdmin(admin.ModelAdmin):
    list_display = ('content_object', 'user', 'status', 'answered_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('question', 'answer', 'user__username')
