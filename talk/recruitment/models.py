from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import json

from configuration.models import Organization, JobFunction, BusinessUnit


class CandidateProfile(models.Model):
    """A person interested in job opportunities at an organization."""

    STATUS_NEW = 'new'
    STATUS_CONTACTED = 'contacted'
    STATUS_INTERVIEWED = 'interviewed'
    STATUS_HIRED = 'hired'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_NEW, _('New')),
        (STATUS_CONTACTED, _('Contacted')),
        (STATUS_INTERVIEWED, _('Interviewed')),
        (STATUS_HIRED, _('Hired')),
        (STATUS_REJECTED, _('Rejected')),
    ]

    organization = models.ForeignKey(
        Organization,
        related_name='candidates',
        on_delete=models.CASCADE,
    )

    first_name = models.CharField(_('First Name'), max_length=120)
    last_name = models.CharField(_('Last Name'), max_length=120, blank=True)
    email = models.EmailField(_('Email'))
    phone = models.CharField(_('Phone'), max_length=30, blank=True)

    cep = models.CharField(_('CEP'), max_length=9, blank=True, db_index=True)
    address = models.CharField(_('Address'), max_length=255, blank=True)
    city = models.CharField(_('City'), max_length=120, blank=True, db_index=True)
    state = models.CharField(_('State'), max_length=2, blank=True)

    bio = models.TextField(_('About'), blank=True)
    experience_years = models.PositiveIntegerField(_('Years of experience'), default=0)
    linkedin_url = models.URLField(_('LinkedIn URL'), blank=True)

    interested_in = models.CharField(
        _('Position of interest'),
        max_length=160,
        blank=True,
        help_text=_('Free-text: role the candidate is looking for'),
    )

    # Preferências de função e loja
    job_functions = models.ManyToManyField(
        JobFunction,
        related_name='interested_candidates',
        blank=True,
        help_text=_('Job functions the candidate is interested in'),
    )
    preferred_store = models.ForeignKey(
        BusinessUnit,
        null=True,
        blank=True,
        related_name='interested_candidates',
        on_delete=models.SET_NULL,
        help_text=_('Store where candidate applied (from QR code)'),
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW, db_index=True)
    onboarding_completed = models.BooleanField(default=False, help_text=_('Whether candidate completed onboarding trail'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Candidate')
        verbose_name_plural = _('Candidates')
        ordering = ['-created_at']
        unique_together = [('organization', 'email')]
        indexes = [
            models.Index(fields=['organization', 'status']),
        ]

    def __str__(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.email

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()


class Position(models.Model):
    """A job opening within an organization."""

    organization = models.ForeignKey(
        Organization,
        related_name='positions',
        on_delete=models.CASCADE,
    )

    title = models.CharField(_('Title'), max_length=160)
    description = models.TextField(_('Description'), blank=True)
    requirements = models.TextField(_('Requirements'), blank=True)

    cep = models.CharField(_('CEP'), max_length=9, blank=True)
    city = models.CharField(_('City'), max_length=120, blank=True)
    state = models.CharField(_('State'), max_length=2, blank=True)

    salary_min = models.DecimalField(
        _('Salary min'), max_digits=10, decimal_places=2, null=True, blank=True,
    )
    salary_max = models.DecimalField(
        _('Salary max'), max_digits=10, decimal_places=2, null=True, blank=True,
    )

    active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Position')
        verbose_name_plural = _('Positions')
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Offer(models.Model):
    """An outreach message from an organization to a candidate for a position."""

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_ACCEPTED, _('Accepted')),
        (STATUS_REJECTED, _('Rejected')),
    ]

    candidate = models.ForeignKey(
        CandidateProfile,
        related_name='offers',
        on_delete=models.CASCADE,
    )
    position = models.ForeignKey(
        Position,
        related_name='offers',
        on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(
        Organization,
        related_name='offers',
        on_delete=models.CASCADE,
    )
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sent_offers',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    message = models.TextField(_('Message'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)

    sent_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('Offer')
        verbose_name_plural = _('Offers')
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.candidate} → {self.position}'


class CandidateOnboardingTrail(models.Model):
    """Onboarding trail assignment for a candidate with courses and survey."""

    STATUS_NOT_STARTED = 'not_started'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = [
        (STATUS_NOT_STARTED, _('Not Started')),
        (STATUS_IN_PROGRESS, _('In Progress')),
        (STATUS_COMPLETED, _('Completed')),
    ]

    candidate = models.OneToOneField(
        CandidateProfile,
        related_name='onboarding_trail',
        on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(
        Organization,
        related_name='candidate_trails',
        on_delete=models.CASCADE,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NOT_STARTED,
        db_index=True,
    )

    # Cursos a completar (JSON array de IDs)
    courses = models.JSONField(
        default=list,
        blank=True,
        help_text=_('List of course IDs in onboarding trail'),
    )

    # Pesquisa de perfil respondida?
    survey_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Candidate Onboarding Trail')
        verbose_name_plural = _('Candidate Onboarding Trails')

    def __str__(self):
        return f'{self.candidate} - {self.get_status_display()}'

    def mark_completed(self):
        """Mark trail as completed"""
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        self.save()


class CandidateProfileSurveyResponse(models.Model):
    """Respostas da pesquisa de perfil do candidato."""

    candidate = models.OneToOneField(
        CandidateProfile,
        related_name='profile_survey',
        on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(
        Organization,
        related_name='survey_responses',
        on_delete=models.CASCADE,
    )

    # Respostas estruturadas como JSON
    responses = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Survey responses as JSON'),
    )

    completed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Candidate Profile Survey Response')
        verbose_name_plural = _('Candidate Profile Survey Responses')

    def __str__(self):
        return f'{self.candidate} - Survey Responses'


class CandidateScore(models.Model):
    """Score calculado do candidato baseado em respostas e conclusão de cursos."""

    candidate = models.OneToOneField(
        CandidateProfile,
        related_name='score',
        on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(
        Organization,
        related_name='candidate_scores',
        on_delete=models.CASCADE,
    )

    # Score geral (0-100)
    overall_score = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text=_('Overall score 0-100'),
    )

    # Componentes do score
    survey_score = models.PositiveIntegerField(default=0, help_text=_('Score based on survey responses 0-40'))
    courses_score = models.PositiveIntegerField(default=0, help_text=_('Score based on courses completed 0-40'))
    engagement_score = models.PositiveIntegerField(default=0, help_text=_('Engagement bonus 0-20'))

    # Metadata
    calculation_method = models.CharField(
        max_length=50,
        default='weighted',
        help_text=_('Method used to calculate score'),
    )

    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Candidate Score')
        verbose_name_plural = _('Candidate Scores')

    def __str__(self):
        return f'{self.candidate} - Score: {self.overall_score}'

    def recalculate(self):
        """Recalcular score baseado em respostas e cursos completados."""
        # Calcular survey score (0-40)
        try:
            survey = self.candidate.profile_survey
            responses = survey.responses or {}
            # Pontos por cada resposta completa
            self.survey_score = min(len(responses) * 8, 40)
        except CandidateProfileSurveyResponse.DoesNotExist:
            self.survey_score = 0

        # Calcular courses score (0-40) - baseado em cursos completados
        completed_courses = CandidateCourseCompletion.objects.filter(
            candidate=self.candidate,
            completed=True
        ).count()
        # 8 pontos por curso completo (máximo 40 pontos = 5 cursos)
        self.courses_score = min(completed_courses * 8, 40)

        # Calcular engagement (0-20) - tempo desde cadastro
        days_since_signup = (timezone.now() - self.candidate.created_at).days
        self.engagement_score = min(days_since_signup, 20)

        # Score total
        self.overall_score = self.survey_score + self.courses_score + self.engagement_score
        self.save()

        return self.overall_score


class CandidateCourseEnroll(models.Model):
    """Track course enrollment for candidates."""

    candidate = models.ForeignKey(
        CandidateProfile,
        related_name='course_enrollments',
        on_delete=models.CASCADE,
    )
    course_id = models.PositiveIntegerField(
        _('Course ID'),
        help_text=_('ID of course from tenant schema'),
    )
    course_title = models.CharField(
        _('Course Title'),
        max_length=255,
        blank=True,
        help_text=_('Denormalized course title for display'),
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Candidate Course Enrollment')
        verbose_name_plural = _('Candidate Course Enrollments')
        unique_together = ('candidate', 'course_id')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f'{self.candidate} - {self.course_title}'


class CandidateCourseCompletion(models.Model):
    """Track course completion for candidates."""

    candidate = models.ForeignKey(
        CandidateProfile,
        related_name='course_completions',
        on_delete=models.CASCADE,
    )
    course_id = models.PositiveIntegerField(
        _('Course ID'),
        help_text=_('ID of course from tenant schema'),
    )
    course_title = models.CharField(
        _('Course Title'),
        max_length=255,
        blank=True,
        help_text=_('Denormalized course title for display'),
    )
    completed = models.BooleanField(
        _('Completed'),
        default=False,
        db_index=True,
    )
    completion_date = models.DateTimeField(
        _('Completion Date'),
        null=True,
        blank=True,
    )
    progress_percentage = models.PositiveIntegerField(
        _('Progress'),
        default=0,
        help_text=_('0-100%'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Candidate Course Completion')
        verbose_name_plural = _('Candidate Course Completions')
        unique_together = ('candidate', 'course_id')
        ordering = ['-completion_date', '-updated_at']
        indexes = [
            models.Index(fields=['candidate', 'completed']),
            models.Index(fields=['completed', '-completion_date']),
        ]

    def __str__(self):
        status = _('Completed') if self.completed else f'{self.progress_percentage}%'
        return f'{self.candidate} - {self.course_title} ({status})'
