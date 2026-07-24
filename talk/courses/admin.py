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
    list_display = ('title', 'type', 'state', 'owner', 'published_date')
    list_filter = ('type', 'state', 'subject')
    search_fields = ('title', 'slug', 'overview')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ('owner', 'author', 'audience_policy')
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
        (None, {'fields': ('title', 'owner', 'overview')}),
        ('Evaluation', {'fields': ('required_score_to_pass', 'points_per_approval', 'number_of_questions', 'time')}),
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
