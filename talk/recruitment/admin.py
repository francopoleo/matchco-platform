from django.contrib import admin

from .models import (
    CandidateProfile, Position, Offer, CandidateOnboardingTrail,
    CandidateProfileSurveyResponse, CandidateScore,
    CandidateCourseEnroll, CandidateCourseCompletion,
)


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'organization', 'city', 'status', 'created_at')
    list_filter = ('organization', 'status', 'city', 'state')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'cep')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'city', 'active', 'created_at')
    list_filter = ('organization', 'active', 'city', 'state')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'position', 'organization', 'status', 'sent_at')
    list_filter = ('organization', 'status')
    search_fields = ('candidate__first_name', 'candidate__last_name', 'candidate__email', 'position__title')
    readonly_fields = ('sent_at', 'responded_at')


@admin.register(CandidateOnboardingTrail)
class CandidateOnboardingTrailAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'status', 'survey_completed', 'created_at')
    list_filter = ('status', 'survey_completed', 'organization')
    search_fields = ('candidate__first_name', 'candidate__last_name', 'candidate__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CandidateProfileSurveyResponse)
class CandidateProfileSurveyResponseAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'organization', 'created_at')
    list_filter = ('organization', 'created_at')
    search_fields = ('candidate__first_name', 'candidate__last_name', 'candidate__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CandidateScore)
class CandidateScoreAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'overall_score', 'survey_score', 'courses_score', 'engagement_score')
    list_filter = ('organization', 'calculated_at')
    search_fields = ('candidate__first_name', 'candidate__last_name', 'candidate__email')
    readonly_fields = ('calculated_at',)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('overall_score', 'survey_score', 'courses_score', 'engagement_score')
        return self.readonly_fields


@admin.register(CandidateCourseEnroll)
class CandidateCourseEnrollAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'course_title', 'enrolled_at')
    list_filter = ('enrolled_at',)
    search_fields = ('candidate__first_name', 'candidate__last_name', 'candidate__email', 'course_title')
    readonly_fields = ('enrolled_at', 'updated_at')


@admin.register(CandidateCourseCompletion)
class CandidateCourseCompletionAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'course_title', 'progress_percentage', 'completed', 'completion_date')
    list_filter = ('completed', 'completion_date', 'updated_at')
    search_fields = ('candidate__first_name', 'candidate__last_name', 'candidate__email', 'course_title')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('candidate', 'course_id', 'course_title')
        }),
        ('Progress', {
            'fields': ('progress_percentage', 'completed', 'completion_date')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
