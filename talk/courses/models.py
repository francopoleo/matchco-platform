import random
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.template.loader import render_to_string
from configuration.models import Organization
from user_management.models import User
from gamification.models import GamificationSettings
from audience.models import AudiencePolicy

from .fields import OrderField


def ap_for_action_course_enrollment():
    settings = GamificationSettings.objects.filter(pk=1).first()

    return settings.dp_course_enrollment if settings else 1


def ap_for_action_course_completation():
    settings = GamificationSettings.objects.filter(pk=1).first()

    return settings.dp_course_completation if settings else 1


def ap_for_action_passed_tests():
    settings = GamificationSettings.objects.filter(pk=1).first()

    return settings.dp_passed_tests if settings else 1


class Subject(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class Course(models.Model):
    STATE_CHOICES = [('published', 'Published'), ('unpublished', 'Not Published')]
    TYPE_CHOICES = [('test', 'Test'), ('course', 'Course')]

    type = models.CharField(max_length=256, choices=TYPE_CHOICES, default="course", verbose_name=_('Type'))

    state = models.CharField(max_length=256, choices=STATE_CHOICES, blank=False, null=False, default="unpublished",
                             verbose_name=_('State'))

    published_date = models.DateTimeField(blank=True, null=True)

    banner = models.ImageField(upload_to='courses/banners/', null=True, blank=True)

    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='courses_author', on_delete=models.CASCADE,
                               blank=True, null=True, default=1,)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              related_name='courses_created',
                              on_delete=models.CASCADE, default=1)

    organization = models.ForeignKey(Organization, related_name='courses', null=True, blank=True, on_delete=models.CASCADE)

    audience_policy = models.ForeignKey(
        AudiencePolicy,
        related_name='courses',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    subject = models.ForeignKey(Subject,
                                related_name='courses',
                                on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
 #   overview = models.TextField()
    overview = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    students = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                      related_name='courses_joined',
                                      blank=True)

    points_per_enrollment = models.IntegerField(null=True, blank=True, verbose_name=_('Points for enrollment this course'),
                                          default=ap_for_action_course_enrollment)

    points_per_completation = models.IntegerField(null=True, blank=True, verbose_name=_('Points for completing this course'),
                                          default=ap_for_action_course_completation)

    # points_per_passed_tests = models.IntegerField(null=True, blank=True, verbose_name=_('Points for pass in tests'),
    #                                       default=ap_for_action_passed_tests)

    go_live_at = models.DateTimeField(
        verbose_name=_("go live date/time"),
        blank=True,
        null=True
    )
    expire_at = models.DateTimeField(
        verbose_name=_("expiry date/time"),
        blank=True,
        null=True
    )
    expired = models.BooleanField(verbose_name=_('expired'), default=False, editable=False)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        import re
        self.overview = re.sub(r'</?p>', '', self.overview).strip()
        super().save(*args, **kwargs)

    def register_course_points(self, event):
        gpv = GamificationPostView.objects.filter(user=user,  feed_post=feed_post)


class Module(models.Model):
    course = models.ForeignKey(Course,
                               related_name='modules',
                               on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = OrderField(blank=True, for_fields=['course'])

    def __str__(self):
        return f'{self.order}. {self.title}'

    class Meta:
        ordering = ['order']

    def get_content(self):
        contents = Content.objects.filter(module=self)
        return contents


class Content(models.Model):
    module = models.ForeignKey(Module,
                               related_name='contents',
                               on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType,
                                     on_delete=models.CASCADE,
                                     limit_choices_to={'model__in': (
                                         'text',
                                         'video',
                                         'image',
                                         'quiz',
                                         'file')})
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(blank=True, for_fields=['module'])

    class Meta:
        ordering = ['order']


class ItemBase(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              related_name='%(class)s_related',
                              on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    content_type = models.ForeignKey(Content, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.title

    def render(self):
        return render_to_string(f'courses/content/{self._meta.model_name}.html',
                                {'item': self})


class Text(ItemBase):
    content = models.TextField()


class File(ItemBase):
    file = models.FileField(upload_to='courses/files/', null=True, blank=True)


class Image(ItemBase):
    file = models.ImageField(upload_to='courses/images/', null=True, blank=True)


class Video(ItemBase):
    url = models.URLField()
    content = models.TextField(null=True, blank=True)


class Quiz(ItemBase):
    overview = models.TextField(null=True, blank=True)
    number_of_questions = models.PositiveIntegerField(blank=True, null=True)
    time = models.PositiveIntegerField(help_text="Duration of the quiz in minutes", blank=True, null=True)
    required_score_to_pass = models.PositiveIntegerField(help_text=_("Requried score in %"))
    points_per_approval = models.IntegerField(null=True, blank=True, default=ap_for_action_passed_tests,
        verbose_name=_("Points per approval"), help_text=_("Award points to passed in quiz"))

    def __str__(self):
        return f"{self.title}"

    def get_questions(self):
        questions = list(self.question.all())
        random.shuffle(questions)
        return questions


class Question(models.Model):
    text = models.CharField(max_length=250)
    order = models.PositiveIntegerField(blank=True, null=True)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="question")
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.text)

    def get_answers(self):
        answers = list(self.answers.all())
        random.shuffle(answers)
        return answers


class Answer(models.Model):
    text = models.CharField(max_length=250)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    correct = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"question: {self.question.text}, answer: {self.text}, correct: {self.correct}"


class Result(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.FloatField()

    def __str__(self):
        return str(self.pk)


class Tests(Course):
    class Meta:
        proxy = True
        verbose_name = _('Test')
        verbose_name_plural = _('Tests')
