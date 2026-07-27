import random
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.template.loader import render_to_string
from ckeditor.fields import RichTextField
from gamification.models import GamificationSettings

from .fields import OrderField

# TENANT_APPS: Importar modelos espelho de SHARED_APPS
from tenants_core.models import TenantUser, TenantOrganization, TenantCompany
from audience.models import AudiencePolicy


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
    IMPORTANCE_CHOICES = [('routine', 'Rotina'), ('important', 'Importante'), ('critical', 'Crítica')]
    CONTENT_CATEGORY_CHOICES = [
        ('learning', 'Aprendizagem'), ('procedure_change', 'Mudança de procedimento'),
        ('required_document', 'Conteúdo obrigatório'), ('incident', 'Alerta operacional'),
    ]

    type = models.CharField(max_length=256, choices=TYPE_CHOICES, default="course", verbose_name=_('Type'))

    state = models.CharField(max_length=256, choices=STATE_CHOICES, blank=False, null=False, default="unpublished",
                             verbose_name=_('State'))

    published_date = models.DateTimeField(blank=True, null=True)

    banner = models.ImageField(upload_to='courses/banners/', null=True, blank=True)
    importance = models.CharField(max_length=12, choices=IMPORTANCE_CHOICES, default='routine')
    content_category = models.CharField(max_length=24, choices=CONTENT_CATEGORY_CHOICES, default='learning')
    requires_acknowledgement = models.BooleanField(default=False)

    # TENANT_APPS: FK para TenantUser (espelho de auth.User)
    author = models.ForeignKey(TenantUser, related_name='courses_author', on_delete=models.CASCADE,
                               blank=True, null=True)

    owner = models.ForeignKey(TenantUser,
                              related_name='courses_created',
                              on_delete=models.CASCADE)

    # TENANT_APPS: FK para TenantOrganization (espelho de configuration.Organization)
    organization = models.ForeignKey(TenantOrganization, related_name='courses', null=True, blank=True, on_delete=models.CASCADE)

    # TENANT_APPS: FK para TenantCompany (espelho de configuration.Company)
    company = models.ForeignKey(TenantCompany, related_name='courses', null=True, blank=True, on_delete=models.CASCADE)

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
    overview = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    # TENANT_APPS: M2M para TenantUser (espelho de auth.User)
    students = models.ManyToManyField(TenantUser,
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

    # TENANT_APPS: Helpers para acessar dados do schema público
    def get_real_author(self):
        """Retorna o usuário real em schema público"""
        if not self.author_id:
            return None
        from user_management.models import User
        try:
            return User.objects.get(id=self.author_id)
        except User.DoesNotExist:
            return None

    def get_real_owner(self):
        """Retorna o owner real em schema público"""
        from user_management.models import User
        try:
            return User.objects.get(id=self.owner_id)
        except User.DoesNotExist:
            return None

    def get_real_organization(self):
        """Retorna a organização real em schema público"""
        if not self.organization_id:
            return None
        from configuration.models import Organization
        try:
            return Organization.objects.get(id=self.organization_id)
        except Organization.DoesNotExist:
            return None

    def get_real_company(self):
        """Retorna a company real em schema público"""
        if not self.company_id:
            return None
        from configuration.models import Company
        try:
            return Company.objects.get(id=self.company_id)
        except Company.DoesNotExist:
            return None

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
    content = RichTextField(config_name='default')


class File(ItemBase):
    file = models.FileField(upload_to='courses/files/', null=True, blank=True)


class Image(ItemBase):
    file = models.ImageField(upload_to='courses/images/', null=True, blank=True)


class Video(ItemBase):
    url = models.URLField()
    content = models.TextField(null=True, blank=True)


class Quiz(ItemBase):
    TYPE_CHOICES = [
        ('formative', _('Formativo')),
        ('exam', _('Prova')),
        ('certification', _('Certificação')),
    ]
    FEEDBACK_CHOICES = [
        ('immediate', _('Imediato por questão')),
        ('final_only', _('Apenas score final')),
        ('delayed', _('Adiado')),
    ]
    QUESTION_ORDER_CHOICES = [
        ('original', _('Original')),
        ('random', _('Aleatório')),
    ]

    # TENANT_APPS: FK para TenantOrganization (espelho de configuration.Organization)
    organization = models.ForeignKey(TenantOrganization, related_name='quizzes', null=True, blank=True, on_delete=models.CASCADE)
    overview = models.TextField(null=True, blank=True)
    quiz_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='formative', verbose_name=_('Type'))
    is_required = models.BooleanField(default=True, verbose_name=_('Required'))
    required_score_to_pass = models.PositiveIntegerField(help_text=_("Required score in %"))
    allow_multiple_attempts = models.BooleanField(default=True, verbose_name=_('Allow multiple attempts'))
    max_attempts = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Maximum attempts'))
    attempts_limit_period_days = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Attempts limit period (days)'))
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Time limit (minutes)'))
    show_feedback_type = models.CharField(max_length=20, choices=FEEDBACK_CHOICES, default='final_only', verbose_name=_('Feedback type'))
    shuffle_questions = models.CharField(max_length=20, choices=QUESTION_ORDER_CHOICES, default='original', verbose_name=_('Question order'))
    show_correct_answers = models.BooleanField(default=True, verbose_name=_('Show correct answers'))
    points_per_approval = models.IntegerField(null=True, blank=True, default=ap_for_action_passed_tests,
        verbose_name=_("Points per approval"), help_text=_("Award points to passed in quiz"))

    class Meta:
        verbose_name = _('Quiz')
        verbose_name_plural = _('Quizzes')

    def __str__(self):
        return f"{self.title} ({self.get_quiz_type_display()})"

    def get_questions(self):
        questions = list(self.questions.all())
        if self.shuffle_questions == 'random':
            random.shuffle(questions)
        return questions

    def get_question_count(self):
        return self.questions.count()


class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', _('Múltipla Escolha - Uma Resposta')),
        ('multiple_correct', _('Múltipla Escolha - Várias Respostas')),
        ('true_false', _('Verdadeiro/Falso')),
        ('short_answer', _('Resposta Curta')),
        ('essay', _('Dissertativa')),
        ('matching', _('Associação')),
        ('ordering', _('Ordenação')),
        ('dropdown', _('Seleção em Lista')),
        ('drag_drop', _('Arrastar e Soltar')),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='multiple_choice',
        verbose_name=_('Tipo de Pergunta')
    )
    text = RichTextField(config_name='default', verbose_name=_('Texto da Pergunta'))
    explanation = RichTextField(
        null=True,
        blank=True,
        config_name='minimal',
        verbose_name=_('Explicação/Feedback')
    )

    # For matching and drag_drop questions
    matching_pairs = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        verbose_name=_('Pares de Associação'),
        help_text=_('JSON com pares: {"item1": "match1", "item2": "match2"}')
    )

    order = OrderField(blank=True, for_fields=['quiz'])
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = _('Pergunta')
        verbose_name_plural = _('Perguntas')

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"

    def get_answers(self):
        answers = list(self.answers.all())
        random.shuffle(answers)
        return answers

    def get_correct_answer(self):
        return self.answers.filter(correct=True).first()

    def get_correct_answers(self):
        """Get all correct answers (for multiple_correct type)"""
        return self.answers.filter(correct=True)

    def has_correct_answer(self):
        """Check if question has at least one correct answer"""
        return self.answers.filter(correct=True).exists()


class Answer(models.Model):
    text = models.CharField(max_length=250)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    correct = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"question: {self.question.text}, answer: {self.text}, correct: {self.correct}"


class UserQuizAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    attempt_number = models.PositiveIntegerField(default=1, verbose_name=_('Attempt number'))
    started_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Started at'))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Completed at'))
    score = models.FloatField(null=True, blank=True, verbose_name=_('Score'))
    passed = models.BooleanField(null=True, blank=True, verbose_name=_('Passed'))
    time_spent_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Time spent (minutes)'))

    class Meta:
        ordering = ['-started_at']
        verbose_name = _('Quiz Attempt')
        verbose_name_plural = _('Quiz Attempts')
        unique_together = [['user', 'quiz', 'attempt_number']]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.quiz.title} (Attempt {self.attempt_number})"

    def calculate_score(self):
        """Calculate score based on correct answers"""
        total_questions = self.quiz.questions.count()
        if total_questions == 0:
            return 0

        correct_count = self.answers.filter(is_correct=True).count()
        score = (correct_count / total_questions) * 100
        self.score = score
        self.passed = score >= self.quiz.required_score_to_pass
        return score

    def get_correct_answers_count(self):
        return self.answers.filter(is_correct=True).count()

    def get_wrong_answers_count(self):
        return self.answers.filter(is_correct=False).count()


class UserAnswer(models.Model):
    attempt = models.ForeignKey(UserQuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='user_answers')
    user_answer_text = models.TextField(null=True, blank=True, verbose_name=_('User answer'))
    selected_answer = models.ForeignKey('Answer', on_delete=models.SET_NULL, null=True, blank=True, related_name='user_selections')
    is_correct = models.BooleanField(default=False, verbose_name=_('Is correct'))
    points_earned = models.FloatField(default=0, verbose_name=_('Points earned'))
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['question__order']
        verbose_name = _('User Answer')
        verbose_name_plural = _('User Answers')
        unique_together = [['attempt', 'question']]

    def __str__(self):
        return f"{self.attempt.user.get_full_name()} - Q{self.question.order}"


class Result(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    # TENANT_APPS: FK para TenantUser (espelho de auth.User)
    user = models.ForeignKey(TenantUser, on_delete=models.CASCADE)
    score = models.FloatField()

    def __str__(self):
        return str(self.pk)


class Tests(Course):
    class Meta:
        proxy = True
        verbose_name = _('Test')
        verbose_name_plural = _('Tests')
