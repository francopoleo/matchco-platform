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

    # Localização do candidato (para match com vagas)
    latitude = models.DecimalField(
        _('Latitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text=_('Candidate location for job matching')
    )
    longitude = models.DecimalField(
        _('Longitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    # Expectativa salarial
    salary_expectation = models.DecimalField(
        _('Salary Expectation'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Expected salary in local currency')
    )

    # Disponibilidade de relocation
    permite_relocation = models.BooleanField(
        _('Allows Relocation'),
        default=False,
        help_text=_('Candidate is open to relocating for a job')
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
    """A job opening within an organization - linked to a business unit and job function."""

    organization = models.ForeignKey(
        Organization,
        related_name='positions',
        on_delete=models.CASCADE,
    )

    business_unit = models.ForeignKey(
        'configuration.BusinessUnit',
        related_name='positions',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text=_('Which store/unit has this opening')
    )

    job_function = models.ForeignKey(
        'configuration.JobFunction',
        related_name='positions',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_('Job function for this position')
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

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.business_unit and self.job_function:
            if self.business_unit.channel and self.job_function.channels.exists():
                if not self.job_function.channels.filter(pk=self.business_unit.channel.pk).exists():
                    raise ValidationError(
                        f'Job function "{self.job_function.name}" is not valid for channel "{self.business_unit.channel.name}"'
                    )


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


class CandidatePosition(models.Model):
    """Match between candidate and position with score components."""

    candidate = models.ForeignKey(
        CandidateProfile,
        related_name='position_matches',
        on_delete=models.CASCADE,
    )
    position = models.ForeignKey(
        Position,
        related_name='candidate_matches',
        on_delete=models.CASCADE,
    )

    # Overall match score (0-100)
    match_score = models.PositiveIntegerField(
        _('Match Score'),
        default=0,
        db_index=True,
        help_text=_('Overall match score 0-100')
    )

    # Score components
    skills_match = models.PositiveIntegerField(_('Skills Match'), default=0, help_text=_('0-100'))
    location_match = models.PositiveIntegerField(_('Location Match'), default=0, help_text=_('0-100'))
    salary_match = models.PositiveIntegerField(_('Salary Match'), default=0, help_text=_('0-100'))
    experience_match = models.PositiveIntegerField(_('Experience Match'), default=0, help_text=_('0-100'))

    # Distance in km (if applicable)
    distance_km = models.DecimalField(
        _('Distance'),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Distance in kilometers between candidate and position')
    )

    # Calculated timestamp
    calculated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Candidate Position Match')
        verbose_name_plural = _('Candidate Position Matches')
        unique_together = ('candidate', 'position')
        ordering = ['-match_score', '-calculated_at']
        indexes = [
            models.Index(fields=['candidate', '-match_score']),
            models.Index(fields=['position', '-match_score']),
            models.Index(fields=['-match_score', '-calculated_at']),
        ]

    def __str__(self):
        return f'{self.candidate} ↔ {self.position.title} ({self.match_score}%)'

    def calculate_match(self):
        """Recalculate all match scores."""
        from math import radians, sin, cos, sqrt, atan2

        # 1. Skills match (job_functions)
        candidate_functions = set(self.candidate.job_functions.values_list('id', flat=True))
        position_functions = set(self.position.job_functions.values_list('id', flat=True) if hasattr(self.position, 'job_functions') else [])

        if position_functions:
            matching = len(candidate_functions & position_functions)
            self.skills_match = int((matching / len(position_functions)) * 100)
        else:
            self.skills_match = 50  # Neutral score if no functions specified

        # 2. Location match (distance)
        if (self.candidate.latitude and self.candidate.longitude and
                self.position.business_unit.latitude and self.position.business_unit.longitude):
            # Calculate distance
            lat1 = radians(float(self.candidate.latitude))
            lon1 = radians(float(self.candidate.longitude))
            lat2 = radians(float(self.position.business_unit.latitude))
            lon2 = radians(float(self.position.business_unit.longitude))

            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = 6371 * c  # Earth radius in km

            self.distance_km = distance

            # Score based on distance
            if distance < 2:
                self.location_match = 100
            elif distance < 5:
                self.location_match = 90
            elif distance < 10:
                self.location_match = 75
            elif distance < 20:
                self.location_match = 50
            elif distance < 50:
                self.location_match = 25
            elif self.candidate.permite_relocation:
                self.location_match = 30  # Candidate willing to relocate
            else:
                self.location_match = 0
        else:
            self.location_match = 50  # Neutral if coordinates missing

        # 3. Salary match
        if self.candidate.salary_expectation:
            if (self.position.salary_min <= self.candidate.salary_expectation <= self.position.salary_max):
                self.salary_match = 100
            elif self.candidate.salary_expectation < self.position.salary_min:
                self.salary_match = 70  # Candidate willing to accept less
            else:
                self.salary_match = 30  # Expects more than offered
        else:
            self.salary_match = 50  # Neutral if salary not provided

        # 4. Experience match
        position_exp_years = getattr(self.position, 'required_experience_years', 0)
        if position_exp_years == 0:
            self.experience_match = 100
        elif self.candidate.experience_years >= position_exp_years:
            self.experience_match = 100
        elif self.candidate.experience_years >= (position_exp_years * 0.8):
            self.experience_match = 80
        elif self.candidate.experience_years >= (position_exp_years * 0.5):
            self.experience_match = 60
        else:
            self.experience_match = 30

        # Calculate final score (weighted)
        self.match_score = int(
            self.skills_match * 0.35 +
            self.location_match * 0.35 +
            self.salary_match * 0.20 +
            self.experience_match * 0.10
        )

        self.save()
        return self.match_score
