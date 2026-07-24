from django.db import models
from django.utils.translation import gettext_lazy as _
from user_management.models import User
from courses.models import Course, Module, Content, Quiz, Question, Answer


class CourseEnroll(models.Model):
    student_id = models.ForeignKey(User, related_name='student', on_delete=models.CASCADE)
    course_id = models.ForeignKey(Course, related_name='course', on_delete=models.CASCADE)
    enroll_date = models.DateTimeField(auto_now_add=True)

    def get_course_progress(self):
        from learning.services import enrollment_progress

        return enrollment_progress(self)


class ModuleEnroll(models.Model):
    course_enroll_id = models.ForeignKey(CourseEnroll, on_delete=models.CASCADE, related_name="modules_enroll")
    module_id = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="modules_enroll")


class ContentEnroll(models.Model):
    module_enroll_id = models.ForeignKey(ModuleEnroll, on_delete=models.CASCADE, related_name="contents_enroll")
    content_id = models.ForeignKey(Content, on_delete=models.CASCADE, related_name="contents_enroll")
    done = models.BooleanField(verbose_name=_('Done'), default=False)
    quiz_id = models.ForeignKey(Quiz, on_delete=models.CASCADE, blank=True, null=True)


class QuizResult(models.Model):
    content_enroll = models.ForeignKey(ContentEnroll, on_delete=models.CASCADE, related_name="quiz_result")
    score = models.FloatField()


class QuestionResult(models.Model):
    quiz_result_id = models.ForeignKey(QuizResult, on_delete=models.CASCADE, related_name="questions")
    question_id = models.ForeignKey(Question, on_delete=models.CASCADE)
    correct_answer_id = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='correct_answer')
    student_answer_id = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='student_answer')
