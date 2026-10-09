from django.contrib import admin

from .models import (
    Answer,
    Content,
    Course,
    File,
    Image,
    Module,
    Question,
    Quiz,
    Subject,
    Tests,
    Text,
    Video,
    UserQuizAttempt,
    UserAnswer,
)


class ModuleInline(admin.StackedInline):
    model = Module
    extra = 0
    fields = ('title', 'description', 'order')


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2
    fields = ('text', 'correct')


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0
    fields = ('text', 'order')
    show_change_link = True


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug')
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'state', 'owner', 'organization', 'company', 'published_date')
    list_filter = ('type', 'state', 'subject', 'organization', 'company')
    search_fields = ('title', 'slug', 'overview')
    prepopulated_fields = {'slug': ('title',)}
    # TENANT_APPS: owner e author agora usam TenantUser (removido autocomplete)
    autocomplete_fields = ('audience_policy',)
    filter_horizontal = ('students',)
    inlines = (ModuleInline,)


@admin.register(Tests)
class TestsAdmin(CourseAdmin):
    list_display = ('title', 'state', 'owner', 'published_date')


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('module', 'content_type', 'object_id', 'order')
    list_filter = ('content_type',)
    search_fields = ('module__title',)


class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created', 'updated')
    list_filter = ('created', 'updated')
    search_fields = ('title',)
    autocomplete_fields = ('owner',)


@admin.register(Quiz)
class QuizAdmin(ItemAdmin):
    inlines = (QuestionInline,)
    fieldsets = (
        (None, {'fields': ('title', 'owner', 'overview', 'quiz_type')}),
        ('Requirements', {'fields': ('is_required', 'required_score_to_pass', 'points_per_approval')}),
        ('Attempts & Time', {
            'fields': ('allow_multiple_attempts', 'max_attempts', 'attempts_limit_period_days', 'time_limit_minutes')
        }),
        ('User Experience', {
            'fields': ('show_feedback_type', 'shuffle_questions', 'show_correct_answers')
        }),
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'order', 'created')
    list_filter = ('quiz',)
    search_fields = ('text', 'quiz__title')
    inlines = (AnswerInline,)


@admin.register(Text)
class TextAdmin(ItemAdmin):
    pass


@admin.register(Video)
class VideoAdmin(ItemAdmin):
    list_display = ('title', 'url', 'owner', 'created')


@admin.register(File)
class FileAdmin(ItemAdmin):
    pass


@admin.register(Image)
class ImageAdmin(ItemAdmin):
    pass


class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    fields = ('question', 'user_answer_text', 'selected_answer', 'is_correct', 'points_earned')
    readonly_fields = ('question', 'user_answer_text', 'selected_answer', 'is_correct', 'points_earned')
    can_delete = False


@admin.register(UserQuizAttempt)
class UserQuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'attempt_number', 'score', 'passed', 'started_at', 'completed_at')
    list_filter = ('passed', 'quiz', 'started_at')
    search_fields = ('user__email', 'user__first_name', 'quiz__title')
    readonly_fields = ('user', 'quiz', 'attempt_number', 'started_at', 'completed_at', 'score', 'passed', 'time_spent_minutes')
    inlines = (UserAnswerInline,)
    can_delete = False

    def has_add_permission(self, request):
        return False


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'user_answer_text', 'is_correct', 'points_earned')
    list_filter = ('is_correct', 'answered_at')
    search_fields = ('attempt__user__email', 'question__text')
    readonly_fields = ('attempt', 'question', 'user_answer_text', 'selected_answer', 'is_correct', 'points_earned', 'answered_at')
    can_delete = False

    def has_add_permission(self, request):
        return False
