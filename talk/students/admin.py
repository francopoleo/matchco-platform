from django.contrib import admin

from .models import ContentEnroll, CourseEnroll, ModuleEnroll, QuestionResult, QuizResult


@admin.register(CourseEnroll)
class CourseEnrollAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'course_id', 'enroll_date')
    list_filter = ('enroll_date',)
    search_fields = ('student_id__username', 'course_id__title')
    autocomplete_fields = ('course_id',)


@admin.register(ModuleEnroll)
class ModuleEnrollAdmin(admin.ModelAdmin):
    list_display = ('course_enroll_id', 'module_id')
    search_fields = ('course_enroll_id__student_id__username', 'module_id__title')


@admin.register(ContentEnroll)
class ContentEnrollAdmin(admin.ModelAdmin):
    list_display = ('module_enroll_id', 'content_id', 'done')
    list_filter = ('done',)
    search_fields = ('module_enroll_id__course_enroll_id__student_id__username',)


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ('content_enroll', 'score')


@admin.register(QuestionResult)
class QuestionResultAdmin(admin.ModelAdmin):
    list_display = ('quiz_result_id', 'question_id', 'student_answer_id')
