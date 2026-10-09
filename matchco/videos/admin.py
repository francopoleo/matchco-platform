from django.contrib import admin

from videos.models import VideoContent


@admin.register(VideoContent)
class VideoContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'url')
    list_filter = ('tags',)
    search_fields = ('title',)
