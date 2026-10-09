from django.contrib import admin

from .models import AudiencePolicy, AudienceRule


class AudienceRuleInline(admin.TabularInline):
    model = AudienceRule
    extra = 1


@admin.register(AudiencePolicy)
class AudiencePolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'match_mode', 'active', 'updated_at')
    list_filter = ('active', 'match_mode')
    search_fields = ('name', 'description')
    inlines = (AudienceRuleInline,)


@admin.register(AudienceRule)
class AudienceRuleAdmin(admin.ModelAdmin):
    list_display = ('policy', 'dimension', 'operator', 'negate', 'position')
    list_filter = ('dimension', 'operator', 'negate')
