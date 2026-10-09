from django.contrib import admin

from .models import AnalyticsExportAudit, BadgeDefinition, ChallengeProgress, CourseCertificate, Certification, CertificationAward, CertificationRequirement, ContentEvent, ContentRecommendation, ContentTrail, LearningChallenge, NotificationDelivery, NotificationRule, PointLedger, PushSubscription, TrailAssignment, TrailProgress, TrailStep, UserBadge, UserNotification, UserNotificationPreference


@admin.register(ContentEvent)
class ContentEventAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'user', 'organization', 'content_type', 'object_id', 'active_seconds', 'occurred_at')
    list_filter = ('event_name', 'organization', 'occurred_at')
    search_fields = ('user__username', 'user__email', 'session_id')
    readonly_fields = ('occurred_at',)


@admin.register(PointLedger)
class PointLedgerAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'reason', 'organization', 'created_at')
    list_filter = ('reason', 'organization', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at',)


@admin.register(BadgeDefinition)
class BadgeDefinitionAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'points_threshold', 'active')
    list_filter = ('active',)


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'awarded_at')
    list_filter = ('badge', 'awarded_at')


@admin.register(LearningChallenge)
class LearningChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'challenge_type', 'target_points', 'starts_at', 'ends_at', 'active')
    list_filter = ('challenge_type', 'active')


@admin.register(ChallengeProgress)
class ChallengeProgressAdmin(admin.ModelAdmin):
    list_display = ('challenge', 'user', 'points', 'completed_at', 'updated_at')
    list_filter = ('completed_at', 'challenge')


@admin.register(AnalyticsExportAudit)
class AnalyticsExportAuditAdmin(admin.ModelAdmin):
    list_display = ('report_name', 'user', 'organization', 'row_count', 'created_at')
    list_filter = ('report_name', 'organization', 'created_at')
    readonly_fields = ('created_at',)


class TrailStepInline(admin.TabularInline):
    model = TrailStep
    extra = 0


@admin.register(ContentTrail)
class ContentTrailAdmin(admin.ModelAdmin):
    list_display = ('title', 'trail_type', 'status', 'version', 'organization', 'company', 'updated_at')
    list_filter = ('trail_type', 'status', 'organization', 'company')
    search_fields = ('title', 'slug')
    inlines = (TrailStepInline,)


@admin.register(TrailAssignment)
class TrailAssignmentAdmin(admin.ModelAdmin):
    list_display = ('trail', 'user', 'audience_policy', 'assigned_at', 'due_at', 'completed_at', 'revoked_at')
    list_filter = ('trail', 'assigned_at', 'completed_at', 'revoked_at')


@admin.register(TrailProgress)
class TrailProgressAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'step', 'started_at', 'completed_at', 'active_seconds', 'usefulness')
    list_filter = ('completed_at', 'usefulness')


@admin.register(ContentRecommendation)
class ContentRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_type', 'object_id', 'source', 'is_mandatory', 'shown_at', 'opened_at', 'dismissed_at')
    list_filter = ('source', 'is_mandatory', 'shown_at', 'opened_at', 'dismissed_at')
    search_fields = ('user__username', 'reason')


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'priority', 'read_at', 'created_at')
    list_filter = ('priority', 'read_at', 'created_at')


@admin.register(UserNotificationPreference)
class UserNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'minimum_priority', 'in_app', 'email', 'push', 'updated_at')
    list_filter = ('minimum_priority', 'in_app', 'email', 'push')


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'trigger_type', 'organization', 'enabled', 'updated_at')
    list_filter = ('trigger_type', 'enabled', 'organization')
    search_fields = ('name',)


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = ('notification', 'channel', 'status', 'attempted_at', 'delivered_at', 'opened_at')
    list_filter = ('channel', 'status')


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'active', 'created_at', 'last_seen_at')
    list_filter = ('active', 'organization')
    search_fields = ('user__username', 'endpoint')


@admin.register(CourseCertificate)
class CourseCertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_number', 'course', 'user', 'issued_at', 'verification_code')
    search_fields = ('certificate_number', 'user__username', 'course__title')
    readonly_fields = ('certificate_number', 'verification_code', 'issued_at')


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'status', 'version', 'validity_days', 'updated_at')
    list_filter = ('status', 'organization', 'requires_manual_approval')
    search_fields = ('title', 'slug')


@admin.register(CertificationRequirement)
class CertificationRequirementAdmin(admin.ModelAdmin):
    list_display = ('certification', 'position', 'course', 'quiz', 'required', 'minimum_score')
    list_filter = ('required', 'certification')


@admin.register(CertificationAward)
class CertificationAwardAdmin(admin.ModelAdmin):
    list_display = ('certificate_number', 'certification', 'user', 'version', 'issued_at', 'expires_at', 'revoked_at')
    list_filter = ('certification', 'revoked_at')
    search_fields = ('certificate_number', 'user__username', 'certification__title')
    readonly_fields = ('certificate_number', 'verification_code', 'issued_at')
    search_fields = ('title', 'message', 'user__username')
