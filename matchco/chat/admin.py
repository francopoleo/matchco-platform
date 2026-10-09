from django.contrib import admin

# Register your models here.
from .models import TalkInteraction


@admin.register(TalkInteraction)
class TalkInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'platform_organization_id', 'room_key', 'message_length', 'created_at')
    list_filter = ('platform_organization_id', 'created_at')
    search_fields = ('user__email', 'room_key', 'topic_key')
    readonly_fields = ('user', 'platform_organization_id', 'room_key', 'topic_key', 'message_length', 'created_at')
