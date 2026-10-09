from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
import json
import uuid

from .domain_models import (
    RecruitmentChannel,
    RecruitmentCompany,
    RecruitmentJobFunction,
    RecruitmentOrganization,
    RecruitmentStore,
)
from .questionnaire_compliance import MAX_QUESTIONS, validate_question_definition

# Local aliases keep the existing domain code readable while all persistence
# now belongs to recruitment.
Organization = RecruitmentOrganization
JobFunction = RecruitmentJobFunction
BusinessUnit = RecruitmentStore


class RecruitmentPolicy(models.Model):
    """Configurable SLA and visibility defaults for an organization."""

    organization = models.OneToOneField(
        Organization,
        related_name='recruitment_policy',
        on_delete=models.CASCADE,
    )
    first_alert_hours = models.PositiveIntegerField(default=24)
    priority_window_hours = models.PositiveIntegerField(default=48)
    shopping_pool_after_hours = models.PositiveIntegerField(default=48)
    external_pool_after_hours = models.PositiveIntegerField(default=168)
    candidate_response_hours = models.PositiveIntegerField(default=72)
    employer_decision_hours = models.PositiveIntegerField(default=120)
    invite_batch_size = models.PositiveIntegerField(default=12)
    round_wait_hours = models.PositiveIntegerField(default=24)
    policy_version = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Recruitment policy')
        verbose_name_plural = _('Recruitment policies')

    def __str__(self):
        return f'{self.organization} · v{self.policy_version}'


class CandidateIdentity(models.Model):
    """Global person record shared by all recruitment organizations."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # E-mail is optional in the phone-first OTP flow. NULL (not '') allows
    # more than one identity to exist without an e-mail while preserving
    # uniqueness whenever an e-mail is actually supplied.
    email_normalized = models.EmailField(unique=True, null=True, blank=True, db_index=True)
    phone_normalized = models.CharField(max_length=30, blank=True, db_index=True)
    cpf_hash = models.CharField(max_length=128, blank=True, unique=True, null=True, db_index=True)
    cpf_last4 = models.CharField(max_length=4, blank=True)
    pool_opt_in = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Candidate identity')
        verbose_name_plural = _('Candidate identities')

    def __str__(self):
        return self.email_normalized or self.phone_normalized or str(self.pk)


class CandidateConsent(models.Model):
    """Consentimento granular por finalidade (SISTEMA_MATCHCO_CANONICO §3.10).

    Base legal explícita por finalidade. Revogação cria evento no Ledger.
    """

    # --- Escopo territorial de circulação (Porta Match) ---
    PURPOSE_CIRCULATION_STORE = 'circulation_store'
    PURPOSE_CIRCULATION_NETWORK = 'circulation_network'
    PURPOSE_CIRCULATION_SHOPPING = 'circulation_shopping'
    PURPOSE_CIRCULATION_RADIUS = 'circulation_radius'

    # --- Visibilidade por porta ---
    PURPOSE_VISIBILITY_MATCH = 'visibility_match'

    # --- Integrações (Fase 10) ---
    PURPOSE_INTEGRATION_COURSES = 'integration_courses'
    PURPOSE_INTEGRATION_WIKI = 'integration_wiki'
    PURPOSE_INTEGRATION_TESTS = 'integration_tests'
    PURPOSE_INTEGRATION_CERTIFICATIONS = 'integration_certifications'
    PURPOSE_INTEGRATION_TALK = 'integration_talk'

    # --- Comunicação ---
    PURPOSE_TRANSACTIONAL_MESSAGING = 'transactional_messaging'

    PURPOSE_CHOICES = [
        (PURPOSE_CIRCULATION_STORE, _('Circular para a loja escaneada')),
        (PURPOSE_CIRCULATION_NETWORK, _('Circular para a rede')),
        (PURPOSE_CIRCULATION_SHOPPING, _('Circular para o shopping')),
        (PURPOSE_CIRCULATION_RADIUS, _('Circular por raio geográfico')),
        (PURPOSE_VISIBILITY_MATCH, _('Aparecer na Porta Match')),
        (PURPOSE_INTEGRATION_COURSES, _('Sinais de Cursos no Perfil')),
        (PURPOSE_INTEGRATION_WIKI, _('Consumo de Wiki registrado')),
        (PURPOSE_INTEGRATION_TESTS, _('Testes propostos por lojista')),
        (PURPOSE_INTEGRATION_CERTIFICATIONS, _('Certificações no Perfil')),
        (PURPOSE_INTEGRATION_TALK, _('Sinais de Talk no Perfil')),
        (PURPOSE_TRANSACTIONAL_MESSAGING, _('Mensagens transacionais')),
    ]

    # --- Bases legais (LGPD art. 7º) ---
    BASIS_CONSENT = 'consent'
    BASIS_CONTRACT_EXECUTION = 'contract_execution'
    BASIS_LEGITIMATE_INTEREST = 'legitimate_interest'
    BASIS_LEGAL_OBLIGATION = 'legal_obligation'
    BASIS_CHOICES = [
        (BASIS_CONSENT, _('Consentimento')),
        (BASIS_CONTRACT_EXECUTION, _('Execução de contrato')),
        (BASIS_LEGITIMATE_INTEREST, _('Legítimo interesse')),
        (BASIS_LEGAL_OBLIGATION, _('Obrigação legal')),
    ]

    identity = models.ForeignKey(CandidateIdentity, related_name='consents', on_delete=models.CASCADE)
    organization = models.ForeignKey(
        Organization, null=True, blank=True,
        related_name='candidate_consents', on_delete=models.CASCADE,
    )
    purpose = models.CharField(max_length=40, choices=PURPOSE_CHOICES)
    legal_basis = models.CharField(
        max_length=32, choices=BASIS_CHOICES, default=BASIS_CONSENT,
    )
    granted = models.BooleanField(default=False)
    policy_version = models.CharField(max_length=40)
    source = models.CharField(max_length=80, default='public_signup')
    granted_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-granted_at']
        indexes = [models.Index(fields=['identity', 'purpose', 'granted'])]


class CandidateAssessment(models.Model):
    """Provider-neutral assessment snapshot; no FK to courses or learning."""

    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_COMPLETED, _('Completed')),
        (STATUS_FAILED, _('Failed')),
    ]

    candidate = models.ForeignKey('CandidateProfile', related_name='assessments', on_delete=models.CASCADE)
    provider = models.CharField(max_length=80)
    external_id = models.CharField(max_length=160)
    title_snapshot = models.CharField(max_length=255, blank=True)
    version = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('candidate', 'provider', 'external_id')]
        indexes = [models.Index(fields=['candidate', 'status'])]


class EmploymentRecord(models.Model):
    """Employment history linked to the same global candidate identity."""

    STATUS_ACTIVE = 'active'
    STATUS_ENDED = 'ended'
    STATUS_CHOICES = [(STATUS_ACTIVE, _('Active')), (STATUS_ENDED, _('Ended'))]

    identity = models.ForeignKey(CandidateIdentity, related_name='employment_records', on_delete=models.PROTECT)
    candidate = models.ForeignKey('CandidateProfile', null=True, blank=True, related_name='employment_records', on_delete=models.SET_NULL)
    organization = models.ForeignKey(Organization, related_name='employment_records', on_delete=models.PROTECT)
    store = models.ForeignKey(BusinessUnit, null=True, blank=True, related_name='employment_records', on_delete=models.SET_NULL)
    position_title = models.CharField(max_length=160)
    employment_type = models.CharField(max_length=60, default='employee')
    corporate_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True)
    started_at = models.DateField()
    ended_at = models.DateField(null=True, blank=True)
    external_employee_id = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-started_at']
        indexes = [models.Index(fields=['identity', 'status']), models.Index(fields=['organization', 'status'])]


class EmploymentEvent(models.Model):
    employment = models.ForeignKey(EmploymentRecord, related_name='events', on_delete=models.CASCADE)
    event_type = models.CharField(max_length=40)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RecruitmentAuditEvent(models.Model):
    """Audit access to personal data and sensitive recruitment actions."""

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    identity = models.ForeignKey(CandidateIdentity, null=True, blank=True, on_delete=models.SET_NULL)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=60)
    object_type = models.CharField(max_length=80, blank=True)
    object_id = models.CharField(max_length=80, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['identity', 'action', 'created_at']), models.Index(fields=['organization', 'created_at'])]


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
    identity = models.ForeignKey(
        CandidateIdentity,
        null=True,
        blank=True,
        related_name='profiles',
        on_delete=models.SET_NULL,
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

    # Fase 9 — visibilidade por porta (SISTEMA_MATCHCO_CANONICO §3.2, §8.4).
    # Cada porta é opt-in independente; consent LGPD granular por porta.
    visibility_match = models.BooleanField(
        default=True,
        help_text=_('Aparece no feed territorial (Porta Match)'),
    )
    availability_days = models.JSONField(default=list, blank=True)
    availability_period = models.CharField(max_length=16, blank=True)
    preferred_work_format = models.CharField(max_length=15, blank=True)
    available_from = models.DateField(null=True, blank=True, db_index=True)
    availability_start = models.TimeField(null=True, blank=True)
    availability_end = models.TimeField(null=True, blank=True)
    interest_categories = models.JSONField(default=list, blank=True)
    linkedin_url = models.URLField(_('LinkedIn URL'), blank=True)

    interested_in = models.CharField(
        _('Position of interest'),
        max_length=160,
        blank=True,
        help_text=_('Free-text: role the candidate is looking for'),
    )

    # Fase 8 — estado de circulação (SISTEMA_MATCHCO_CANONICO §8).
    # ALLOWED/PAUSED é dimensão independente de freshness dos sinais.
    # Só o próprio candidato alterna; empregador/shopping nunca reativa.
    CIRCULATION_ALLOWED = 'allowed'
    CIRCULATION_PAUSED = 'paused'
    CIRCULATION_CHOICES = [
        (CIRCULATION_ALLOWED, _('Circulação ativa')),
        (CIRCULATION_PAUSED, _('Circulação pausada pelo candidato')),
    ]
    circulation_state = models.CharField(
        max_length=10, choices=CIRCULATION_CHOICES,
        default=CIRCULATION_ALLOWED, db_index=True,
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

    # Origem do cadastro (especialmente útil para QR Codes impressos).
    qr_id = models.CharField(_('QR identifier'), max_length=120, blank=True, db_index=True)
    utm_source = models.CharField(_('Campaign source'), max_length=120, blank=True)
    utm_medium = models.CharField(_('Campaign medium'), max_length=120, blank=True)
    utm_campaign = models.CharField(_('Campaign'), max_length=160, blank=True)

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
    """Opportunity — necessidade estruturada de contratação.

    Nome legado ``Position`` mantido para compat de FKs; use ``Opportunity``
    (alias no fim do módulo) em novo código. Ver SISTEMA_MATCHCO_CANONICO §3.3.
    """

    # Porta a que a Opportunity pertence (Fase 9 do roadmap).
    MODE_MATCH = 'match'
    MODE_CHOICES = [(MODE_MATCH, _('Porta Match'))]

    # Tag da necessidade (SISTEMA_MATCHCO_CANONICO §2.2).
    TAG_PRECISA = 'PRECISA'
    TAG_SERIA_BOM = 'SERIA_BOM'
    TAG_PODE_APRENDER = 'PODE_APRENDER'
    TAG_CHOICES = [
        (TAG_PRECISA, _('Precisa — vai contratar')),
        (TAG_SERIA_BOM, _('Seria bom — abriria se aparecer alguém')),
        (TAG_PODE_APRENDER, _('Pode aprender aqui — aceita primeiro emprego')),
    ]

    # Formato da relação de trabalho.
    FORMAT_FIXO = 'fixo'
    FORMAT_TEMPORARIO = 'temporario'
    FORMAT_AMBOS = 'ambos'
    FORMAT_CHOICES = [
        (FORMAT_FIXO, _('Fixo')),
        (FORMAT_TEMPORARIO, _('Temporário')),
        (FORMAT_AMBOS, _('Fixo ou temporário')),
    ]

    SALARY_PERIOD_CHOICES = [
        ('hour', _('por hora')),
        ('day', _('por diária')),
        ('month', _('por mês')),
        ('total', _('valor total do contrato')),
        ('negotiable', _('a combinar')),
    ]
    EMPLOYMENT_TYPE_CHOICES = [
        ('clt', _('CLT')),
        ('pj', _('Pessoa jurídica')),
        ('temporary', _('Temporário')),
        ('intermittent', _('Intermitente')),
        ('freelance', _('Freelance/diária')),
        ('internship', _('Estágio/aprendiz')),
        ('commission', _('Comissionado')),
        ('mixed', _('Misto')),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('monthly', _('Mensal')),
        ('hourly', _('Por hora')),
        ('daily', _('Por diária')),
        ('commission', _('Comissão')),
        ('mixed', _('Fixo + comissão')),
        ('negotiable', _('A combinar')),
    ]

    PERIOD_ANY = 'any'
    PERIOD_CHOICES = [
        ('morning', _('Manhã')),
        ('afternoon', _('Tarde')),
        ('evening', _('Noite')),
        (PERIOD_ANY, _('Qualquer período')),
    ]

    EXPERIENCE_ANY = 'any'
    EXPERIENCE_SIMILAR = 'similar'
    EXPERIENCE_AREA = 'area'
    EXPERIENCE_CHOICES = [
        (EXPERIENCE_ANY, _('Não exige experiência')),
        (EXPERIENCE_SIMILAR, _('Experiência parecida desejável')),
        (EXPERIENCE_AREA, _('Experiência na área obrigatória')),
    ]

    # Estado no ciclo de vida (lado empregador).
    STATE_STRUCTURED = 'structured'
    STATE_ACTIVATED = 'activated'
    STATE_CIRCULATED = 'circulated'
    STATE_CLOSED = 'closed'
    STATE_CHOICES = [
        (STATE_STRUCTURED, _('Estruturada — Pre-Interest Set em aberto')),
        (STATE_ACTIVATED, _('Ativada — pronta para circular')),
        (STATE_CIRCULATED, _('Em circulação')),
        (STATE_CLOSED, _('Encerrada')),
    ]

    organization = models.ForeignKey(
        Organization,
        related_name='positions',
        on_delete=models.CASCADE,
    )

    business_unit = models.ForeignKey(
        BusinessUnit,
        related_name='positions',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text=_('Loja/unidade responsável pela Opportunity'),
    )

    job_function = models.ForeignKey(
        JobFunction,
        related_name='positions',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    title = models.CharField(_('Título'), max_length=160)
    description = models.TextField(_('Descrição'), blank=True)
    requirements = models.TextField(_('Requisitos'), blank=True)
    benefits = models.JSONField(default=list, blank=True)
    required_experience_years = models.PositiveIntegerField(default=0)

    # Território e local de trabalho canônicos.
    workplace = models.CharField(
        _('Local de trabalho'),
        max_length=200,
        blank=True,
        help_text=_('Descrição do local onde o trabalho acontece'),
    )
    cep = models.CharField(max_length=9, blank=True)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=2, blank=True)

    # Horário e formato — parte do Pre-Interest Decision Set.
    schedule = models.CharField(
        _('Horário'),
        max_length=200,
        blank=True,
        help_text=_('Turno / dias / carga horária'),
    )
    required_days = models.JSONField(default=list, blank=True)
    required_period = models.CharField(max_length=16, choices=PERIOD_CHOICES, blank=True)
    required_experience = models.CharField(max_length=16, choices=EXPERIENCE_CHOICES, default=EXPERIENCE_ANY)
    required_experience_contexts = models.JSONField(default=list, blank=True)
    requested_slots = models.PositiveIntegerField(default=1)
    invite_batch_size = models.PositiveIntegerField(default=12)
    candidate_response_hours = models.PositiveIntegerField(default=72)
    employer_decision_hours = models.PositiveIntegerField(default=120)
    negotiable_fields = models.JSONField(default=list, blank=True)
    work_format = models.CharField(
        max_length=15, choices=FORMAT_CHOICES, blank=True,
    )
    starts_at = models.DateField(null=True, blank=True)
    active_until = models.DateField(null=True, blank=True)

    # Remuneração (Pre-Interest Set).
    salary_min = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
    )
    salary_max = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
    )
    salary_period = models.CharField(max_length=16, blank=True, default='')
    employment_type = models.CharField(max_length=24, blank=True, default='')
    payment_method = models.CharField(max_length=24, blank=True, default='')

    # Cânone MatchCo — versionamento e taxonomia.
    mode = models.CharField(
        max_length=10, choices=MODE_CHOICES, default=MODE_MATCH, db_index=True,
    )
    tag = models.CharField(
        max_length=15, choices=TAG_CHOICES, default=TAG_PRECISA, db_index=True,
        help_text=_('Intensidade da necessidade — PRECISA/SERIA_BOM/PODE_APRENDER'),
    )
    version = models.PositiveIntegerField(
        default=1,
        help_text=_('Incrementada a cada mudança material'),
    )
    pre_interest_set_complete = models.BooleanField(
        default=False,
        help_text=_('True quando todos os campos do Pre-Interest Decision Set estão preenchidos'),
    )
    state = models.CharField(
        max_length=15, choices=STATE_CHOICES, default=STATE_STRUCTURED, db_index=True,
    )
    activated_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    # Flag legado (Porta Vaga clássica): activo para listagem tradicional.
    active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Opportunity')
        verbose_name_plural = _('Opportunities')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'state']),
            models.Index(fields=['mode', 'state']),
            models.Index(fields=['tag', 'state']),
        ]

    def __str__(self):
        return f'{self.title} · v{self.version}'

    # ------------------------------------------------------------------
    # Pre-Interest Decision Set (SISTEMA_MATCHCO_CANONICO §2.3)
    # ------------------------------------------------------------------
    #
    # Campos que DEVEM estar presentes antes de PERSON_INTERESTED. Sem eles,
    # o candidato não tem informação suficiente para decidir e a Opportunity
    # não pode transitar de STRUCTURED → ACTIVATED.
    PRE_INTEREST_REQUIRED_FIELDS = (
        'organization',        # empregador
        'business_unit',       # loja específica
        'job_function',        # função
        'workplace',
        'schedule',
        'work_format',
        'starts_at',
    )

    # Campos cuja mudança dispara version+=1 e reconfirmação do candidato
    # (SISTEMA_MATCHCO_CANONICO §2.3).
    MATERIAL_FIELDS = (
        'organization_id',
        'business_unit_id',
        'job_function_id',
        'workplace',
        'schedule',
        'work_format',
        'salary_min',
        'salary_max',
        'starts_at',
        'active_until',
        'tag',
    )

    def compute_pre_interest_complete(self):
        for f in self.PRE_INTEREST_REQUIRED_FIELDS:
            value = getattr(self, f, None)
            if value in (None, '', 0):
                return False
        # Ao menos um critério REQUIRED declarado.
        if self.pk and not self.criteria.filter(
            weight=OpportunityCriterion.WEIGHT_REQUIRED
        ).exists():
            return False
        # A loja só pode publicar depois que sua função operacional foi
        # convertida para pelo menos uma função canônica do candidato.
        if self.business_unit_id and self.job_function_id:
            has_mapping = CanonicalFunctionMapping.objects.filter(
                organization=self.organization,
                job_function=self.job_function,
                active=True,
            ).filter(Q(business_unit=self.business_unit) | Q(business_unit__isnull=True)).exists()
            if not has_mapping:
                return False
        return True

    def can_activate(self):
        return self.state == self.STATE_STRUCTURED and self.pre_interest_set_complete

    def clean(self):
        from django.core.exceptions import ValidationError
        errors = {}
        if self.business_unit_id and self.organization_id:
            if self.business_unit.organization_id != self.organization_id:
                errors['business_unit'] = _(
                    'A unidade deve pertencer à organização da necessidade.'
                )
        if self.job_function_id and self.organization_id:
            if self.job_function.organization_id != self.organization_id:
                errors['job_function'] = _(
                    'A função deve pertencer à organização da necessidade.'
                )
        if self.business_unit and self.job_function:
            if self.business_unit.channel and self.job_function.channels.exists():
                if not self.job_function.channels.filter(pk=self.business_unit.channel.pk).exists():
                    errors['job_function'] = _(
                        f'Função "{self.job_function.name}" não é válida para o canal '
                        f'"{self.business_unit.channel.name}"'
                    )
        if errors:
            raise ValidationError(errors)


# Alias canônico — use este nome em código novo.
Opportunity = Position


class OpportunityCriterion(models.Model):
    """Critério de uma Opportunity — REQUIRED / DESIRABLE / CAN_LEARN.

    Ver SISTEMA_MATCHCO_CANONICO §3.3.
    """

    WEIGHT_REQUIRED = 'REQUIRED'
    WEIGHT_DESIRABLE = 'DESIRABLE'
    WEIGHT_CAN_LEARN = 'CAN_LEARN'
    WEIGHT_CHOICES = [
        (WEIGHT_REQUIRED, _('Obrigatório')),
        (WEIGHT_DESIRABLE, _('Desejável')),
        (WEIGHT_CAN_LEARN, _('Pode aprender aqui')),
    ]

    opportunity = models.ForeignKey(
        Position, related_name='criteria', on_delete=models.CASCADE,
    )
    label = models.CharField(_('Descrição'), max_length=200)
    weight = models.CharField(
        max_length=15, choices=WEIGHT_CHOICES, default=WEIGHT_REQUIRED,
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Critério de Opportunity')
        verbose_name_plural = _('Critérios de Opportunity')
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['opportunity', 'weight']),
        ]

    def __str__(self):
        return f'[{self.get_weight_display()}] {self.label}'


class OpportunityVersionHistory(models.Model):
    """Registro imutável de cada bump de versão de Opportunity.

    Alimenta o Ledger (Fase 4) e serve para reconfirmação do candidato.
    """

    opportunity = models.ForeignKey(
        Position, related_name='version_history', on_delete=models.CASCADE,
    )
    from_version = models.PositiveIntegerField()
    to_version = models.PositiveIntegerField()
    changed_fields = models.JSONField(default=list)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Histórico de versão de Opportunity')
        verbose_name_plural = _('Históricos de versão de Opportunity')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['opportunity', '-created_at']),
        ]

    def __str__(self):
        return f'{self.opportunity_id}: v{self.from_version}→v{self.to_version}'


class CandidateOnboardingTrail(models.Model):
    """Legacy profile-wide trail kept for historical compatibility.

    New assignments must use ``PreboardingAssignment`` and carry context.
    """

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


class PreboardingAssignment(models.Model):
    """Contextual pre-onboarding assignment; it is not a candidate score."""

    TAG_PRECISA = 'PRECISA'
    TAG_SERIA_BOM = 'SERIA_BOM'
    TAG_PODE_APRENDER = 'PODE_APRENDER'
    TAG_CHOICES = [
        (TAG_PRECISA, _('Precisa')),
        (TAG_SERIA_BOM, _('Seria bom')),
        (TAG_PODE_APRENDER, _('Pode aprender')),
    ]
    STATE_AVAILABLE = 'available'
    STATE_IN_PROGRESS = 'in_progress'
    STATE_COMPLETED = 'completed'
    STATE_BLOCKED = 'blocked'
    STATE_EXPIRED = 'expired'
    STATE_REVOKED = 'revoked'
    STATE_CHOICES = [
        (STATE_AVAILABLE, _('Disponível')),
        (STATE_IN_PROGRESS, _('Em andamento')),
        (STATE_COMPLETED, _('Concluído')),
        (STATE_BLOCKED, _('Bloqueado')),
        (STATE_EXPIRED, _('Expirado')),
        (STATE_REVOKED, _('Revogado')),
    ]

    candidate = models.ForeignKey(CandidateProfile, related_name='preboarding_assignments', on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, related_name='preboarding_assignments', on_delete=models.CASCADE)
    segment_term = models.ForeignKey(
        'CanonicalTerm', null=True, blank=True, related_name='preboarding_assignments', on_delete=models.SET_NULL,
    )
    company = models.ForeignKey(
        RecruitmentCompany, null=True, blank=True, related_name='preboarding_assignments', on_delete=models.SET_NULL,
    )
    business_unit = models.ForeignKey(
        BusinessUnit, null=True, blank=True, related_name='preboarding_assignments', on_delete=models.SET_NULL,
    )
    program = models.ForeignKey(
        'Program', null=True, blank=True, related_name='preboarding_assignments', on_delete=models.SET_NULL,
    )
    position = models.ForeignKey(
        Position, null=True, blank=True, related_name='preboarding_assignments', on_delete=models.SET_NULL,
    )
    relation = models.ForeignKey(
        'Relation', null=True, blank=True, related_name='preboarding_assignments', on_delete=models.SET_NULL,
    )
    tag = models.CharField(max_length=20, choices=TAG_CHOICES, default=TAG_PRECISA)
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default=STATE_AVAILABLE, db_index=True)
    course_ids = models.JSONField(default=list, blank=True)
    required_evidence = models.JSONField(default=list, blank=True)
    requires_approved_access = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='+', on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['candidate', 'state']),
            models.Index(fields=['organization', 'state']),
            models.Index(fields=['position', 'tag']),
        ]

    def clean(self):
        if self.candidate_id and self.organization_id and self.candidate.organization_id != self.organization_id:
            raise ValidationError({'organization': _('A atribuição deve pertencer à organização do Perfil.')})
        for obj, field in ((self.company, 'company'), (self.business_unit, 'business_unit'), (self.program, 'program'), (self.position, 'position')):
            if obj is not None and getattr(obj, 'organization_id', None) != self.organization_id:
                raise ValidationError({field: _('O contexto deve pertencer à organização da atribuição.')})
        if self.segment_term_id and self.segment_term.term_type != CanonicalTerm.TYPE_SEGMENT:
            raise ValidationError({'segment_term': _('O pré-onboarding deve apontar para um termo de segmento.')})

    def __str__(self):
        return f'{self.candidate} · {self.get_tag_display()} · {self.get_state_display()}'


class PreboardingEvidence(models.Model):
    """Completion evidence with provenance and validity, without a score."""

    TYPE_MANUAL = 'manual'
    TYPE_COURSE = 'course'
    TYPE_QUIZ = 'quiz'
    TYPE_CERTIFICATION = 'certification'
    TYPE_TALK = 'talk'
    TYPE_CHOICES = [(value, value.replace('_', ' ').title()) for value in (
        TYPE_MANUAL, TYPE_COURSE, TYPE_QUIZ, TYPE_CERTIFICATION, TYPE_TALK,
    )]

    assignment = models.ForeignKey(PreboardingAssignment, related_name='evidence', on_delete=models.CASCADE)
    evidence_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    evidence_key = models.CharField(max_length=160)
    provider = models.CharField(max_length=80, blank=True)
    completed_at = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='+', on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['assignment', 'evidence_type', 'evidence_key'], name='unique_preboarding_evidence'),
        ]
        indexes = [models.Index(fields=['assignment', 'completed_at'])]

    def __str__(self):
        return f'{self.assignment_id} · {self.evidence_type} · {self.evidence_key}'


class QuestionnaireTemplate(models.Model):
    """Versioned, contextual questionnaire used during candidate onboarding.

    A template is deliberately separate from a candidate response: the same
    organization can publish variants by entry point, unit, channel or job
    function while preserving the exact version used for each response.
    """

    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_ARCHIVED = 'archived'
    STATUS_CHOICES = [
        (STATUS_DRAFT, _('Rascunho')),
        (STATUS_PUBLISHED, _('Publicado')),
        (STATUS_ARCHIVED, _('Arquivado')),
    ]

    PURPOSE_RECRUITMENT = 'recruitment'
    PURPOSE_CHOICES = [(PURPOSE_RECRUITMENT, _('Recrutamento'))]

    organization = models.ForeignKey(
        Organization,
        related_name='questionnaire_templates',
        on_delete=models.CASCADE,
    )
    code = models.SlugField(max_length=100)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    purpose = models.CharField(max_length=24, choices=PURPOSE_CHOICES, default=PURPOSE_RECRUITMENT)

    # Optional context. Blank fields make this a reusable organization-level template.
    audience_role = models.CharField(max_length=80, blank=True)
    market = models.CharField(max_length=80, blank=True)
    scope_store = models.ForeignKey(
        RecruitmentStore, null=True, blank=True,
        related_name='questionnaire_templates', on_delete=models.CASCADE,
    )
    scope_channel = models.ForeignKey(
        RecruitmentChannel, null=True, blank=True,
        related_name='questionnaire_templates', on_delete=models.CASCADE,
    )
    scope_job_function = models.ForeignKey(
        RecruitmentJobFunction, null=True, blank=True,
        related_name='questionnaire_templates', on_delete=models.CASCADE,
    )
    entry_point = models.ForeignKey(
        'EntryPoint', null=True, blank=True,
        related_name='questionnaire_templates', on_delete=models.CASCADE,
    )
    is_default = models.BooleanField(default=False)
    source = models.CharField(
        max_length=24,
        default='manual',
        help_text=_('manual, seed ou ai_draft; usado para auditoria da configuração.'),
    )
    generation_context = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Brief estruturado que originou um rascunho assistido.'),
    )
    max_questions = models.PositiveIntegerField(default=MAX_QUESTIONS)
    is_approved_by_ops = models.BooleanField(default=False)
    approval_date = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-version', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'code', 'version'],
                name='recruitment_questionnaire_org_code_version',
            ),
            models.CheckConstraint(
                check=models.Q(max_questions__lte=MAX_QUESTIONS),
                name='questionnaire_max_questions_limit',
            ),
        ]

        indexes = [
            models.Index(fields=['organization', 'status', 'purpose']),
            models.Index(fields=['entry_point', 'status']),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()
        if self.max_questions > MAX_QUESTIONS:
            raise ValidationError({'max_questions': f'O limite é {MAX_QUESTIONS} perguntas.'})
        if self.status == self.STATUS_PUBLISHED and self.pk:
            if self.questions.filter(active=True).count() > self.max_questions:
                raise ValidationError({'status': 'O template excede o limite de perguntas.'})
            if not self.is_approved_by_ops:
                raise ValidationError({'status': 'A operação precisa revisar as perguntas antes da publicação.'})

    def __str__(self):
        return f'{self.name} · v{self.version}'


class QuestionnaireQuestion(models.Model):
    """One editable question in a published questionnaire version."""

    TYPE_TEXT = 'text'
    TYPE_TEXTAREA = 'textarea'
    TYPE_SINGLE = 'single_choice'
    TYPE_MULTIPLE = 'multiple_choice'
    TYPE_BOOLEAN = 'boolean'
    TYPE_NUMBER = 'number'
    TYPE_DATE = 'date'
    TYPE_FILE = 'file'
    TYPE_SCALE = 'scale'
    TYPE_CHOICES = [
        (TYPE_TEXT, _('Texto curto')),
        (TYPE_TEXTAREA, _('Texto longo')),
        (TYPE_SINGLE, _('Uma opção')),
        (TYPE_MULTIPLE, _('Várias opções')),
        (TYPE_BOOLEAN, _('Sim ou não')),
        (TYPE_NUMBER, _('Número')),
        (TYPE_DATE, _('Data')),
        (TYPE_FILE, _('Arquivo')),
        (TYPE_SCALE, _('Escala')),
    ]

    template = models.ForeignKey(
        QuestionnaireTemplate, related_name='questions', on_delete=models.CASCADE,
    )
    key = models.SlugField(max_length=100)
    label = models.CharField(max_length=240)
    help_text = models.CharField(max_length=300, blank=True)
    field_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_TEXT)
    options = models.JSONField(default=list, blank=True)
    conditions = models.JSONField(
        default=dict, blank=True,
        help_text=_('Condição simples, por exemplo {"key": "experiencia", "equals": "sim"}.'),
    )
    scoring = models.JSONField(default=dict, blank=True)
    required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']
        constraints = [
            models.UniqueConstraint(fields=['template', 'key'], name='recruitment_questionnaire_template_key'),
        ]

    def __str__(self):
        return f'{self.template} · {self.label}'

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()
        validate_question_definition(label=self.label, field_type=self.field_type)
        if self.template_id and self.active:
            current = self.template.questions.exclude(pk=self.pk).filter(active=True).count()
            if current >= self.template.max_questions:
                raise ValidationError('O template já atingiu o limite de perguntas.')


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
    questionnaire_template = models.ForeignKey(
        QuestionnaireTemplate,
        null=True,
        blank=True,
        related_name='responses',
        on_delete=models.SET_NULL,
        help_text=_('Versão exata do questionário apresentada ao candidato.'),
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


class CandidateSignupAnswer(models.Model):
    """One contextual questionnaire submission for a candidate.

    The global profile remains reusable. Each opportunity/context gets its own
    immutable answer record so a new experience never copies old answers.
    """

    candidate = models.ForeignKey(
        CandidateProfile, related_name='signup_answers', on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(
        Organization, related_name='candidate_signup_answers', on_delete=models.CASCADE,
    )
    business_unit = models.ForeignKey(
        BusinessUnit, null=True, blank=True, related_name='candidate_signup_answers',
        on_delete=models.SET_NULL,
    )
    entry_point = models.ForeignKey(
        'EntryPoint', null=True, blank=True, related_name='candidate_signup_answers',
        on_delete=models.SET_NULL,
    )
    questionnaire_template = models.ForeignKey(
        QuestionnaireTemplate, null=True, blank=True, related_name='signup_answers',
        on_delete=models.SET_NULL,
    )
    relation = models.ForeignKey(
        'Relation', null=True, blank=True, related_name='signup_answers',
        on_delete=models.SET_NULL,
    )
    relation_state_at_response = models.CharField(
        max_length=30, default='not_interested',
        help_text=_('Estado da relação no momento da resposta.'),
    )
    created_via_questionnaire_version = models.PositiveIntegerField(default=1)
    responses = models.JSONField(default=dict, blank=True)
    gdpr_deletion_requested = models.DateTimeField(null=True, blank=True)
    gdpr_deletion_completed = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['business_unit', 'relation_state_at_response']),
            models.Index(fields=['candidate', 'created_at']),
        ]

    def __str__(self):
        return f'{self.candidate} · resposta {self.created_at:%Y-%m-%d}'


class StoreSignupConfiguration(models.Model):
    """Store-specific signup questionnaire configuration for QR-driven entry.

    Enables one universal QR code to route candidates to store-customized
    signup forms. Each store defines which questionnaire template to use
    for profile creation and which template (if any) for job applications.
    """

    ACTION_PROFILE = 'profile'
    ACTION_JOB = 'job'
    ACTION_CHOICES = [
        (ACTION_PROFILE, _('Criar Perfil')),
        (ACTION_JOB, _('Candidatar para Vaga')),
    ]

    store = models.OneToOneField(
        RecruitmentStore,
        related_name='signup_configuration',
        on_delete=models.CASCADE,
        help_text=_('Loja que essa configuração governa.'),
    )
    organization = models.ForeignKey(
        Organization,
        related_name='store_signup_configs',
        on_delete=models.CASCADE,
    )

    # Default templates for each action type
    profile_questionnaire = models.ForeignKey(
        QuestionnaireTemplate,
        null=True,
        blank=True,
        related_name='as_profile_config',
        on_delete=models.SET_NULL,
        help_text=_('Template padrão para criar perfil.'),
    )
    job_questionnaire = models.ForeignKey(
        QuestionnaireTemplate,
        null=True,
        blank=True,
        related_name='as_job_config',
        on_delete=models.SET_NULL,
        help_text=_('Template adicional para candidaturar a vaga (opcional).'),
    )

    # Configuration tracking
    is_active = models.BooleanField(
        default=True,
        help_text=_('Se False, essa loja não aceita novas assinaturas via QR.'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Store Signup Configuration')
        verbose_name_plural = _('Store Signup Configurations')
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['store', 'is_active']),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()
        if not self.profile_questionnaire and not self.job_questionnaire:
            raise ValidationError(
                _('Ao menos um template (perfil ou vaga) deve ser definido.')
            )
        if self.profile_questionnaire and self.profile_questionnaire.organization_id != self.organization_id:
            raise ValidationError(
                _('Template de perfil deve pertencer à mesma organização.')
            )
        if self.job_questionnaire and self.job_questionnaire.organization_id != self.organization_id:
            raise ValidationError(
                _('Template de vaga deve pertencer à mesma organização.')
            )

    def __str__(self):
        return f'{self.store.name} · Signup Config'


class CanonicalCatalog(models.Model):
    """Versioned vocabulary shared by organizations without free-text keys."""

    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_ARCHIVED = 'archived'
    STATUS_CHOICES = [
        (STATUS_DRAFT, _('Rascunho')),
        (STATUS_PUBLISHED, _('Publicado')),
        (STATUS_ARCHIVED, _('Arquivado')),
    ]

    code = models.SlugField(max_length=80)
    name = models.CharField(max_length=180)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    source = models.CharField(max_length=40, default='manual')
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code', '-version']
        constraints = [
            models.UniqueConstraint(fields=['code', 'version'], name='unique_canonical_catalog_version'),
        ]

    def __str__(self):
        return f'{self.name} · v{self.version}'


class CanonicalTerm(models.Model):
    """Canonical category/function/segment/skill in one catalog version."""

    TYPE_FUNCTION = 'function'
    TYPE_CATEGORY = 'category'
    TYPE_SEGMENT = 'segment'
    TYPE_SKILL = 'skill'
    TYPE_CHOICES = [
        (TYPE_FUNCTION, _('Função')),
        (TYPE_CATEGORY, _('Categoria')),
        (TYPE_SEGMENT, _('Segmento')),
        (TYPE_SKILL, _('Habilidade')),
    ]

    catalog = models.ForeignKey(CanonicalCatalog, related_name='terms', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.SET_NULL)
    term_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    code = models.SlugField(max_length=100)
    label = models.CharField(max_length=180)
    normalized_label = models.CharField(max_length=180, db_index=True)
    active = models.BooleanField(default=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['term_type', 'label']
        constraints = [
            models.UniqueConstraint(fields=['catalog', 'code'], name='unique_canonical_term_code'),
        ]
        indexes = [models.Index(fields=['catalog', 'term_type', 'active'])]

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        import unicodedata
        normalized = unicodedata.normalize('NFKD', self.label or '')
        normalized = ''.join(char for char in normalized if not unicodedata.combining(char))
        self.normalized_label = ' '.join(''.join(char if char.isalnum() else ' ' for char in normalized.lower()).split())
        super().save(*args, **kwargs)


class CanonicalTermAlias(models.Model):
    """Deterministic synonym; aliases never create a new function."""

    term = models.ForeignKey(CanonicalTerm, related_name='aliases', on_delete=models.CASCADE)
    alias = models.CharField(max_length=180)
    normalized_alias = models.CharField(max_length=180, db_index=True)
    source = models.CharField(max_length=40, default='manual')
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['term', 'normalized_alias'], name='unique_canonical_term_alias'),
        ]

    def __str__(self):
        return f'{self.alias} → {self.term.label}'

    def save(self, *args, **kwargs):
        import unicodedata
        normalized = unicodedata.normalize('NFKD', self.alias or '')
        normalized = ''.join(char for char in normalized if not unicodedata.combining(char))
        self.normalized_alias = ' '.join(''.join(char if char.isalnum() else ' ' for char in normalized.lower()).split())
        super().save(*args, **kwargs)


class CanonicalFunctionMapping(models.Model):
    """Maps a store/company function to the candidate's canonical function.

    ``business_unit`` makes the de-para local to a store. A null value is the
    organization's fallback mapping; a store-specific mapping always wins.
    """

    term = models.ForeignKey(CanonicalTerm, related_name='function_mappings', on_delete=models.CASCADE)
    job_function = models.ForeignKey(JobFunction, related_name='canonical_mappings', on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, related_name='canonical_function_mappings', on_delete=models.CASCADE)
    business_unit = models.ForeignKey(
        BusinessUnit, null=True, blank=True, related_name='canonical_function_mappings',
        on_delete=models.CASCADE,
    )
    local_label = models.CharField(max_length=180, blank=True)
    # Perfil operacional do cargo local. Requisitos e benefícios são listas
    # flexíveis para permitir evolução por segmento sem alterar o schema.
    job_description = models.TextField(blank=True)
    requirements = models.JSONField(default=list, blank=True)
    benefits = models.JSONField(default=list, blank=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_period = models.CharField(max_length=16, blank=True, default='')
    employment_type = models.CharField(max_length=24, blank=True, default='')
    payment_method = models.CharField(max_length=24, blank=True, default='')
    profile_metadata = models.JSONField(default=dict, blank=True)
    source = models.CharField(max_length=40, default='manual')
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['term', 'job_function', 'business_unit'], name='unique_canonical_function_mapping'),
        ]
        indexes = [models.Index(fields=['organization', 'active'])]

    def clean(self):
        if self.job_function_id and self.organization_id and self.job_function.organization_id != self.organization_id:
            raise ValidationError({'organization': _('A função deve pertencer à organização do mapeamento.')})
        if self.business_unit_id and self.business_unit.organization_id != self.organization_id:
            raise ValidationError({'business_unit': _('A loja deve pertencer à organização do mapeamento.')})
        if self.term_id and self.term.term_type != CanonicalTerm.TYPE_FUNCTION:
            raise ValidationError({'term': _('O mapeamento precisa apontar para um termo de função.')})


class CandidateCanonicalResponse(models.Model):
    """Versioned answer tied to a canonical term and an explicit scope."""

    SCOPE_GLOBAL = 'global'
    SCOPE_SEGMENT = 'segment'
    SCOPE_ORGANIZATION = 'organization'
    SCOPE_UNIT = 'unit'
    SCOPE_OPPORTUNITY = 'opportunity'
    SCOPE_CHOICES = [
        (SCOPE_GLOBAL, _('Global')),
        (SCOPE_SEGMENT, _('Segmento')),
        (SCOPE_ORGANIZATION, _('Organização')),
        (SCOPE_UNIT, _('Unidade')),
        (SCOPE_OPPORTUNITY, _('Oportunidade')),
    ]
    PURPOSE_PROFILE = 'profile'
    PURPOSE_DISTRIBUTION = 'distribution'
    PURPOSE_ENRICHMENT = 'enrichment'
    PURPOSE_PREBOARDING = 'preboarding'
    PURPOSE_CHOICES = [
        (PURPOSE_PROFILE, _('Perfil')),
        (PURPOSE_DISTRIBUTION, _('Distribuição')),
        (PURPOSE_ENRICHMENT, _('Enriquecimento')),
        (PURPOSE_PREBOARDING, _('Pré-onboarding')),
    ]
    ORIGIN_CANDIDATE = 'candidate'
    ORIGIN_QR = 'qr'
    ORIGIN_CAMPAIGN = 'campaign'
    ORIGIN_MANAGER = 'manager'
    ORIGIN_IMPORT = 'import'
    ORIGIN_CHOICES = [(value, value.replace('_', ' ').title()) for value in (
        ORIGIN_CANDIDATE, ORIGIN_QR, ORIGIN_CAMPAIGN, ORIGIN_MANAGER, ORIGIN_IMPORT,
    )]

    candidate = models.ForeignKey(CandidateProfile, related_name='canonical_responses', on_delete=models.CASCADE)
    term = models.ForeignKey(CanonicalTerm, related_name='candidate_responses', on_delete=models.PROTECT)
    segment_term = models.ForeignKey(
        CanonicalTerm, null=True, blank=True, related_name='segment_responses', on_delete=models.PROTECT,
    )
    organization = models.ForeignKey(Organization, related_name='canonical_responses', on_delete=models.CASCADE)
    business_unit = models.ForeignKey(BusinessUnit, null=True, blank=True, related_name='canonical_responses', on_delete=models.SET_NULL)
    position = models.ForeignKey(Position, null=True, blank=True, related_name='canonical_responses', on_delete=models.SET_NULL)
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES)
    catalog_version = models.PositiveIntegerField()
    value = models.JSONField(default=dict, blank=True)
    consented_at = models.DateTimeField(null=True, blank=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    source_reference = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['candidate', 'term', 'scope']),
            models.Index(fields=['organization', 'purpose', 'valid_until']),
        ]

    def clean(self):
        if self.term_id and self.catalog_version != self.term.catalog.version:
            raise ValidationError({'catalog_version': _('A resposta deve preservar a versão do catálogo usado.')})
        if self.candidate_id and self.organization_id and self.candidate.organization_id != self.organization_id:
            raise ValidationError({'organization': _('A resposta deve pertencer à organização do Perfil.')})
        if self.scope == self.SCOPE_UNIT and not self.business_unit_id:
            raise ValidationError({'business_unit': _('Resposta de unidade precisa de unidade.')})
        if self.scope == self.SCOPE_SEGMENT and not self.segment_term_id:
            raise ValidationError({'segment_term': _('Resposta de segmento precisa de segmento.')})
        if self.scope == self.SCOPE_OPPORTUNITY and not self.position_id:
            raise ValidationError({'position': _('Resposta de oportunidade precisa de oportunidade.')})


class OpportunityCanonicalRequirement(models.Model):
    """Structured requirement used for deterministic eligibility, never ranking."""

    REQUIRED = 'required'
    PREFERRED = 'preferred'
    LEARNABLE = 'learnable'
    REQUIREMENT_CHOICES = [
        (REQUIRED, _('Obrigatório')),
        (PREFERRED, _('Preferencial')),
        (LEARNABLE, _('Pode aprender')),
    ]

    position = models.ForeignKey(Position, related_name='canonical_requirements', on_delete=models.CASCADE)
    term = models.ForeignKey(CanonicalTerm, related_name='opportunity_requirements', on_delete=models.PROTECT)
    requirement = models.CharField(max_length=12, choices=REQUIREMENT_CHOICES, default=REQUIRED)
    source = models.CharField(max_length=40, default='manual')
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['position', 'term'], name='unique_opportunity_canonical_requirement'),
        ]

    def clean(self):
        if self.term_id and self.term.term_type not in (CanonicalTerm.TYPE_FUNCTION, CanonicalTerm.TYPE_SKILL, CanonicalTerm.TYPE_SEGMENT):
            raise ValidationError({'term': _('Categoria não pode ser requisito direto; escolha função, segmento ou habilidade.')})


class CoverageGap(models.Model):
    """Observable shortage of eligible or interested people for an opportunity."""

    STATE_OPEN = 'open'
    STATE_MONITORING = 'monitoring'
    STATE_RESOLVED = 'resolved'
    STATE_PAUSED = 'paused'
    STATE_CHOICES = [
        (STATE_OPEN, _('Aberto')),
        (STATE_MONITORING, _('Em acompanhamento')),
        (STATE_RESOLVED, _('Resolvido')),
        (STATE_PAUSED, _('Pausado')),
    ]

    position = models.OneToOneField(Position, related_name='coverage_gap', on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, related_name='coverage_gaps', on_delete=models.CASCADE)
    minimum_eligible = models.PositiveIntegerField(default=5)
    minimum_interested = models.PositiveIntegerField(default=2)
    eligible_count = models.PositiveIntegerField(default=0)
    interested_count = models.PositiveIntegerField(default=0)
    state = models.CharField(max_length=16, choices=STATE_CHOICES, default=STATE_OPEN, db_index=True)
    reason = models.CharField(max_length=80, default='insufficient_coverage')
    last_evaluated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['organization', 'state'])]

    def __str__(self):
        return f'{self.position.title} · {self.state}'


class EnrichmentCampaign(models.Model):
    """Optional, versioned questions used to widen deterministic coverage."""

    STATUS_DRAFT = 'draft'
    STATUS_ACTIVE = 'active'
    STATUS_PAUSED = 'paused'
    STATUS_CLOSED = 'closed'
    STATUS_REVOKED = 'revoked'
    STATUS_CHOICES = [
        (STATUS_DRAFT, _('Rascunho')),
        (STATUS_ACTIVE, _('Ativa')),
        (STATUS_PAUSED, _('Pausada')),
        (STATUS_CLOSED, _('Encerrada')),
        (STATUS_REVOKED, _('Revogada')),
    ]

    organization = models.ForeignKey(Organization, related_name='enrichment_campaigns', on_delete=models.CASCADE)
    coverage_gap = models.ForeignKey(CoverageGap, null=True, blank=True, related_name='campaigns', on_delete=models.SET_NULL)
    position = models.ForeignKey(Position, null=True, blank=True, related_name='enrichment_campaigns', on_delete=models.SET_NULL)
    questionnaire_template = models.ForeignKey(
        QuestionnaireTemplate, null=True, blank=True, related_name='enrichment_campaigns', on_delete=models.SET_NULL,
    )
    name = models.CharField(max_length=180)
    purpose = models.CharField(max_length=40, default='profile_enrichment')
    consent_text = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='+', on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['organization', 'status'])]

    def __str__(self):
        return self.name

    def clean(self):
        if self.position_id and self.position.organization_id != self.organization_id:
            raise ValidationError({'position': _('A oportunidade deve pertencer à organização da campanha.')})
        if self.coverage_gap_id and self.coverage_gap.organization_id != self.organization_id:
            raise ValidationError({'coverage_gap': _('A cobertura deve pertencer à organização da campanha.')})
        if self.questionnaire_template_id:
            if self.questionnaire_template.organization_id != self.organization_id:
                raise ValidationError({'questionnaire_template': _('O questionário deve pertencer à organização da campanha.')})
            if self.questionnaire_template.status != QuestionnaireTemplate.STATUS_PUBLISHED:
                raise ValidationError({'questionnaire_template': _('A campanha só pode usar questionário publicado.')})


class EnrichmentInvite(models.Model):
    """One opaque invitation to one candidate; it does not expose a candidate list."""

    STATE_INVITED = 'invited'
    STATE_STARTED = 'started'
    STATE_COMPLETED = 'completed'
    STATE_DECLINED = 'declined'
    STATE_REVOKED = 'revoked'
    STATE_EXPIRED = 'expired'
    STATE_CHOICES = [(value, value.replace('_', ' ').title()) for value in (
        STATE_INVITED, STATE_STARTED, STATE_COMPLETED, STATE_DECLINED, STATE_REVOKED, STATE_EXPIRED,
    )]

    campaign = models.ForeignKey(EnrichmentCampaign, related_name='invites', on_delete=models.CASCADE)
    candidate = models.ForeignKey(CandidateProfile, related_name='enrichment_invites', on_delete=models.CASCADE)
    token = models.CharField(max_length=96, unique=True)
    state = models.CharField(max_length=16, choices=STATE_CHOICES, default=STATE_INVITED, db_index=True)
    expires_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    declined_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['campaign', 'candidate'], name='unique_enrichment_campaign_candidate')]
        indexes = [models.Index(fields=['campaign', 'state'])]


class EnrichmentResponse(models.Model):
    """Immutable versioned response; never overwrites the global Profile."""

    invite = models.OneToOneField(EnrichmentInvite, related_name='response', on_delete=models.CASCADE)
    candidate = models.ForeignKey(CandidateProfile, related_name='enrichment_responses', on_delete=models.CASCADE)
    campaign = models.ForeignKey(EnrichmentCampaign, related_name='responses', on_delete=models.CASCADE)
    questionnaire_template = models.ForeignKey(QuestionnaireTemplate, null=True, blank=True, on_delete=models.SET_NULL)
    questionnaire_version = models.PositiveIntegerField(default=1)
    responses = models.JSONField(default=dict, blank=True)
    consented_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class CandidateContextEntry(models.Model):
    """Histórico de cada porta, loja ou campanha que reutilizou o perfil.

    A identidade e o perfil são globais/reutilizáveis; este registro preserva
    a origem da entrada sem transformar a pessoa em propriedade da unidade.
    Não guarda respostas sensíveis: respostas de questionários ficam em
    ``CandidateSignupAnswer`` e são sempre vinculadas ao contexto correto.
    """

    candidate = models.ForeignKey(
        CandidateProfile, related_name='context_entries', on_delete=models.CASCADE,
    )
    identity = models.ForeignKey(
        CandidateIdentity, related_name='context_entries', on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(
        Organization, related_name='candidate_context_entries', on_delete=models.CASCADE,
    )
    business_unit = models.ForeignKey(
        BusinessUnit, null=True, blank=True,
        related_name='candidate_context_entries', on_delete=models.SET_NULL,
    )
    entry_point = models.ForeignKey(
        'EntryPoint', null=True, blank=True,
        related_name='candidate_context_entries', on_delete=models.SET_NULL,
    )
    source_kind = models.CharField(max_length=40, blank=True)
    campaign_name = models.CharField(max_length=160, blank=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    visit_count = models.PositiveIntegerField(default=1)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-last_seen_at']
        constraints = [
            models.UniqueConstraint(
                fields=['candidate', 'entry_point'],
                condition=models.Q(entry_point__isnull=False),
                name='uniq_candidate_context_entrypoint',
            ),
        ]
        indexes = [
            models.Index(fields=['identity', 'last_seen_at']),
            models.Index(fields=['organization', 'last_seen_at']),
        ]

    def __str__(self):
        return f'{self.candidate} · {self.entry_point or self.organization}'



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

    # Rule-based scoring fields
    scoring_breakdown = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Breakdown of score by criteria: {criteria_name: {points, max_points, weight, type}}'),
    )
    scoring_rule_version = models.PositiveIntegerField(
        default=1,
        help_text=_('Version of scoring rules used to calculate this score'),
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
    """Historical candidate-position calculation, not active Match distribution.

    The current flow uses ``Relation`` and deterministic eligibility. These
    fields remain for backwards-compatible audit reads only.
    """

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
    algorithm_version = models.CharField(max_length=40, default='rules-v1')
    explanation = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _('Candidate Position Match')
        verbose_name_plural = _('Candidate Position Matches')
        unique_together = ('candidate', 'position')
        # Never make a quality score the implicit order of a queryset.
        ordering = ['-calculated_at']
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
        position_functions = {self.position.job_function_id} if self.position.job_function_id else set()

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
        self.explanation = {
            'algorithm_version': self.algorithm_version,
            'factors': {
                'skills': self.skills_match,
                'location': self.location_match,
                'salary': self.salary_match,
                'experience': self.experience_match,
            },
            'weights': {'skills': 0.35, 'location': 0.35, 'salary': 0.20, 'experience': 0.10},
        }

        self.save()
        return self.match_score


# ============ FLEXIBLE SCORING SYSTEM ============


class ScoringRuleSet(models.Model):
    """Organization-specific scoring configuration."""

    organization = models.OneToOneField(
        Organization,
        related_name='scoring_rule_set',
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        _('Name'),
        max_length=160,
        default=_('Default Scoring'),
    )
    description = models.TextField(
        _('Description'),
        blank=True,
    )

    # Version tracking for rule changes
    version = models.PositiveIntegerField(
        _('Version'),
        default=1,
    )
    is_active = models.BooleanField(
        _('Active'),
        default=True,
    )

    # Total max points possible
    max_score = models.PositiveIntegerField(
        _('Maximum Score'),
        default=100,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Scoring Rule Set')
        verbose_name_plural = _('Scoring Rule Sets')

    def __str__(self):
        return f'{self.organization} - v{self.version}'


class ScoringCriteria(models.Model):
    """Individual scoring criteria (questions, engagement, courses, etc)."""

    TYPE_QUESTION = 'question'
    TYPE_ENGAGEMENT = 'engagement'
    TYPE_COURSE = 'course'
    TYPE_CUSTOM = 'custom'
    TYPE_CHOICES = [
        (TYPE_QUESTION, _('Survey Question')),
        (TYPE_ENGAGEMENT, _('Engagement Metric')),
        (TYPE_COURSE, _('Course Completion')),
        (TYPE_CUSTOM, _('Custom Calculation')),
    ]

    rule_set = models.ForeignKey(
        ScoringRuleSet,
        related_name='criteria',
        on_delete=models.CASCADE,
    )

    name = models.CharField(
        _('Name'),
        max_length=160,
    )
    description = models.TextField(
        _('Description'),
        blank=True,
    )
    criteria_type = models.CharField(
        _('Type'),
        max_length=20,
        choices=TYPE_CHOICES,
    )

    # Weight/importance in overall score (0-100%)
    weight = models.PositiveIntegerField(
        _('Weight (%)'),
        default=10,
        help_text=_('Weight of this criteria in overall score (sum of all weights should equal 100)'),
    )

    # Max points this criteria can contribute
    max_points = models.PositiveIntegerField(
        _('Maximum Points'),
        default=10,
    )

    # Flexible rule definition as JSON
    rule_config = models.JSONField(
        _('Rule Configuration'),
        default=dict,
        help_text=_('Criteria-specific scoring logic (see documentation)'),
    )

    # Track which criteria was active when scoring
    rule_set_version = models.PositiveIntegerField(
        _('Rule Set Version'),
    )

    is_active = models.BooleanField(
        _('Active'),
        default=True,
    )
    order = models.PositiveIntegerField(
        _('Order'),
        default=0,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Scoring Criteria')
        verbose_name_plural = _('Scoring Criteria')
        ordering = ['order', 'created_at']
        unique_together = [('rule_set', 'name')]
        indexes = [
            models.Index(fields=['rule_set', 'is_active']),
        ]

    def __str__(self):
        return f'{self.name} ({self.get_criteria_type_display()})'


class WeightedQuestion(models.Model):
    """Maps survey questions to scoring with weighted answers."""

    criteria = models.OneToOneField(
        ScoringCriteria,
        related_name='question_mapping',
        on_delete=models.CASCADE,
        limit_choices_to={'criteria_type': ScoringCriteria.TYPE_QUESTION},
    )

    question_text = models.CharField(
        _('Question Text'),
        max_length=500,
    )

    # Possible answer choices with their point values
    # Format: [
    #   {"choice": "Senior", "points": 10, "weight": 1.0},
    #   {"choice": "Mid-level", "points": 5, "weight": 0.5},
    #   {"choice": "Junior", "points": 2, "weight": 0.2}
    # ]
    answer_scores = models.JSONField(
        _('Answer Scores'),
        default=list,
        help_text=_('Array of {choice, points, weight}'),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Weighted Question')
        verbose_name_plural = _('Weighted Questions')

    def __str__(self):
        return f'{self.criteria.name}: {self.question_text[:50]}'


class ScoringLog(models.Model):
    """Audit trail of scoring rule changes."""

    ACTION_CHOICES = [
        ('rule_created', _('Rule Set Created')),
        ('rule_updated', _('Rule Set Updated')),
        ('criteria_added', _('Criteria Added')),
        ('criteria_updated', _('Criteria Updated')),
        ('criteria_removed', _('Criteria Removed')),
        ('score_calculated', _('Score Calculated')),
    ]

    organization = models.ForeignKey(
        Organization,
        related_name='scoring_logs',
        on_delete=models.CASCADE,
    )

    rule_set = models.ForeignKey(
        ScoringRuleSet,
        null=True,
        blank=True,
        related_name='change_logs',
        on_delete=models.SET_NULL,
    )

    action = models.CharField(
        _('Action'),
        max_length=50,
        choices=ACTION_CHOICES,
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    # Store previous/new values for audit
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)

    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Scoring Log')
        verbose_name_plural = _('Scoring Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'created_at']),
        ]

    def __str__(self):
        return f'{self.organization} - {self.get_action_display()}'


# ---------------------------------------------------------------------------
# Porta Match — cânone MatchCo
# ---------------------------------------------------------------------------
#
# EntryPoint é o "ponto físico ou digital" que um QR resolve. Base da Porta
# Match e do futuro roteamento QR canônico. Ver SISTEMA_MATCHCO_CANONICO §3.8
# e ROADMAP_CONFORMIDADE Fase 1.
#
# Aditivo: não substitui o `qr_id` textual atual do CandidateProfile — os dois
# convivem até a Fase 9 (cutover).


class Program(models.Model):
    """Programa MatchCo que organiza uma campanha, curso ou certificação."""

    KIND_TRAINING = 'training'
    KIND_CERTIFICATION = 'certification'
    KIND_CAMPAIGN = 'campaign'
    KIND_COMMUNICATION = 'communication'
    KIND_RECRUITMENT = 'recruitment'
    KIND_CHOICES = [
        (KIND_TRAINING, _('Curso e capacitação')),
        (KIND_CERTIFICATION, _('Certificação')),
        (KIND_CAMPAIGN, _('Campanha ou ativação')),
        (KIND_COMMUNICATION, _('Comunicação / conteúdo')),
        (KIND_RECRUITMENT, _('Contratação')),
    ]

    STATUS_DRAFT = 'draft'
    STATUS_ACTIVE = 'active'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_DRAFT, _('Rascunho')),
        (STATUS_ACTIVE, _('Ativo')),
        (STATUS_CLOSED, _('Encerrado')),
    ]
    ACCESS_PUBLIC = 'public'
    ACCESS_AUTHENTICATED = 'authenticated'
    ACCESS_MEMBERS = 'members'
    ACCESS_CHOICES = [
        (ACCESS_PUBLIC, _('Público')),
        (ACCESS_AUTHENTICATED, _('Usuários autenticados')),
        (ACCESS_MEMBERS, _('Somente membros do programa')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, related_name='matchco_programs', on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=160)
    kind = models.CharField(max_length=24, choices=KIND_CHOICES, default=KIND_TRAINING)
    description = models.TextField(blank=True)
    sponsor_name = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    access_level = models.CharField(max_length=16, choices=ACCESS_CHOICES, default=ACCESS_PUBLIC)
    participant_free = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name='created_matchco_programs', on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['organization', 'status'])]

    def __str__(self):
        return self.name


class ProgramUnitScope(models.Model):
    """Participação de uma unidade em um programa sem duplicar a unidade.

    A unidade física continua pertencendo à sua organização de recrutamento;
    este vínculo registra em quais programas ela participa e por qual período.
    """

    program = models.ForeignKey(
        Program, related_name='unit_scopes', on_delete=models.CASCADE,
    )
    business_unit = models.ForeignKey(
        BusinessUnit, related_name='program_scopes', on_delete=models.CASCADE,
    )
    contract_label = models.CharField(max_length=160, blank=True)
    active = models.BooleanField(default=True, db_index=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['business_unit__name', 'program__name']
        constraints = [
            models.UniqueConstraint(
                fields=['program', 'business_unit'],
                name='uniq_program_business_unit_scope',
            ),
        ]
        indexes = [
            models.Index(fields=['business_unit', 'active']),
            models.Index(fields=['program', 'active']),
        ]

    def clean(self):
        if self.program_id and self.business_unit_id:
            if self.program.organization_id != self.business_unit.organization_id:
                raise ValidationError({
                    'business_unit': _('A unidade e o programa devem pertencer à mesma organização.'),
                })

    def __str__(self):
        return f'{self.business_unit} · {self.program}'


class ProgramMembership(models.Model):
    """Vínculo de uma pessoa com um Programa, independente de sua loja atual."""

    ROLE_PARTICIPANT = 'participant'
    ROLE_MANAGER = 'manager'
    ROLE_PARTNER = 'partner'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_PARTICIPANT, _('Participante')),
        (ROLE_MANAGER, _('Gestor do programa')),
        (ROLE_PARTNER, _('Parceiro')),
        (ROLE_ADMIN, _('Administrador')),
    ]

    STATE_PENDING_APPROVAL = 'pending_approval'
    STATE_APPROVED = 'approved'
    STATE_ACTIVE = 'active'
    STATE_SUSPENDED = 'suspended'
    STATE_REVOKED = 'revoked'
    STATE_EXPIRED = 'expired'
    STATE_CHOICES = [
        (STATE_PENDING_APPROVAL, _('Aguardando aprovação')),
        (STATE_APPROVED, _('Aprovado')),
        (STATE_ACTIVE, _('Ativo')),
        (STATE_SUSPENDED, _('Suspenso')),
        (STATE_REVOKED, _('Revogado')),
        (STATE_EXPIRED, _('Expirado')),
    ]

    user_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    identity = models.ForeignKey(
        'CandidateIdentity', null=True, blank=True,
        related_name='program_memberships', on_delete=models.CASCADE,
    )
    program = models.ForeignKey(Program, related_name='memberships', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_PARTICIPANT)
    active = models.BooleanField(default=True)
    state = models.CharField(max_length=24, choices=STATE_CHOICES, default=STATE_ACTIVE, db_index=True)
    consented_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=80, default='program_invite')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user_id', 'program'], name='unique_program_user_membership',
                condition=models.Q(user_id__isnull=False),
            ),
            models.UniqueConstraint(
                fields=['identity', 'program'], name='unique_program_identity_membership',
                condition=models.Q(identity__isnull=False),
            ),
        ]
        indexes = [
            models.Index(fields=['user_id', 'active']),
            models.Index(fields=['program', 'active']),
            models.Index(fields=['program', 'state']),
        ]

    def __str__(self):
        subject = self.user_id or self.identity_id
        return f'{subject} · {self.program.name}'


class ProgramInvite(models.Model):
    """Convite individual para entrar em um Programa privado."""

    STATE_PENDING = 'pending'
    STATE_REQUESTED = 'requested'
    STATE_PENDING_APPROVAL = 'pending_approval'
    STATE_ACCEPTED = 'accepted'
    STATE_EXPIRED = 'expired'
    STATE_REVOKED = 'revoked'
    STATE_CHOICES = [
        (STATE_PENDING, _('Pendente')),
        (STATE_REQUESTED, _('Solicitação criada')),
        (STATE_PENDING_APPROVAL, _('Aguardando aprovação')),
        (STATE_ACCEPTED, _('Aceito')),
        (STATE_EXPIRED, _('Expirado')),
        (STATE_REVOKED, _('Revogado')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program = models.ForeignKey(Program, related_name='invites', on_delete=models.CASCADE)
    email = models.EmailField(db_index=True)
    role = models.CharField(max_length=20, choices=ProgramMembership.ROLE_CHOICES, default=ProgramMembership.ROLE_PARTICIPANT)
    token = models.CharField(max_length=96, unique=True)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    state = models.CharField(max_length=24, choices=STATE_CHOICES, default=STATE_PENDING, db_index=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def is_valid(self, now=None):
        now = now or timezone.now()
        return self.state == self.STATE_PENDING and now < self.expires_at and self.program.status == Program.STATUS_ACTIVE


class ControlledAccessRequest(models.Model):
    """Solicitação de entrada em um escopo controlado do MatchCo.

    QR e convite iniciam este registro. Eles nunca concedem acesso sozinhos;
    a ativação é feita por um aprovador compatível com o escopo solicitado.
    """

    TYPE_PROGRAM = 'program'
    TYPE_EMPLOYER = 'employer'
    TYPE_CHOICES = [
        (TYPE_PROGRAM, _('Participação em programa')),
        (TYPE_EMPLOYER, _('Acesso operacional de empresa/unidade')),
    ]
    LEVEL_ORGANIZATION = 'organization'
    LEVEL_COMPANY = 'company'
    LEVEL_UNIT = 'unit'
    LEVEL_PROGRAM = 'program'
    LEVEL_CHOICES = [
        (LEVEL_ORGANIZATION, _('Organização')),
        (LEVEL_COMPANY, _('Empresa/rede')),
        (LEVEL_UNIT, _('Unidade')),
        (LEVEL_PROGRAM, _('Programa')),
    ]
    STATE_INVITED = 'invited'
    STATE_REQUESTED = 'requested'
    STATE_PENDING_APPROVAL = 'pending_approval'
    STATE_APPROVED = 'approved'
    STATE_ACTIVE = 'active'
    STATE_SUSPENDED = 'suspended'
    STATE_REVOKED = 'revoked'
    STATE_EXPIRED = 'expired'
    STATE_CHOICES = [
        (STATE_INVITED, _('Convidado')),
        (STATE_REQUESTED, _('Solicitado')),
        (STATE_PENDING_APPROVAL, _('Aguardando aprovação')),
        (STATE_APPROVED, _('Aprovado')),
        (STATE_ACTIVE, _('Ativo')),
        (STATE_SUSPENDED, _('Suspenso')),
        (STATE_REVOKED, _('Revogado')),
        (STATE_EXPIRED, _('Expirado')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    organization = models.ForeignKey(Organization, related_name='controlled_access_requests', on_delete=models.CASCADE)
    company = models.ForeignKey(
        RecruitmentCompany, null=True, blank=True, related_name='controlled_access_requests', on_delete=models.CASCADE,
    )
    business_unit = models.ForeignKey(
        BusinessUnit, null=True, blank=True, related_name='controlled_access_requests', on_delete=models.CASCADE,
    )
    program = models.ForeignKey(
        Program, null=True, blank=True, related_name='access_requests', on_delete=models.CASCADE,
    )
    entry_point = models.ForeignKey(
        'EntryPoint', null=True, blank=True, related_name='access_requests', on_delete=models.SET_NULL,
    )
    invite = models.ForeignKey(
        'ProgramInvite', null=True, blank=True, related_name='access_requests', on_delete=models.SET_NULL,
    )
    identity = models.ForeignKey(
        CandidateIdentity, null=True, blank=True, related_name='controlled_access_requests', on_delete=models.SET_NULL,
    )
    user_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='+', on_delete=models.SET_NULL)
    request_role = models.CharField(max_length=32, default=ProgramMembership.ROLE_PARTICIPANT)
    requested_scopes = models.JSONField(default=list, blank=True)
    required_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default=LEVEL_ORGANIZATION)
    state = models.CharField(max_length=24, choices=STATE_CHOICES, default=STATE_PENDING_APPROVAL, db_index=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='+', on_delete=models.SET_NULL)
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_reason = models.TextField(blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='+', on_delete=models.SET_NULL)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'state']),
            models.Index(fields=['user_id', 'state']),
            models.Index(fields=['program', 'state']),
        ]

    def clean(self):
        errors = {}
        if self.business_unit_id and self.business_unit.company.organization.legacy_id != self.organization.legacy_id:
            errors['business_unit'] = _('A unidade precisa pertencer à organização solicitada.')
        if self.company_id and self.company.organization_id != self.organization_id:
            errors['company'] = _('A empresa precisa pertencer à organização solicitada.')
        if self.entry_point_id and self.entry_point.organization_id != self.organization_id:
            errors['entry_point'] = _('O ponto de entrada precisa pertencer à organização solicitada.')
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.organization} · {self.request_type} · {self.state}'


class AccessApprovalEvent(models.Model):
    """Auditoria das decisões sobre uma entrada controlada."""

    ACTION_REQUESTED = 'requested'
    ACTION_APPROVED = 'approved'
    ACTION_REJECTED = 'rejected'
    ACTION_SUSPENDED = 'suspended'
    ACTION_REVOKED = 'revoked'
    ACTION_CHOICES = [(value, value.replace('_', ' ').title()) for value in (
        ACTION_REQUESTED, ACTION_APPROVED, ACTION_REJECTED, ACTION_SUSPENDED, ACTION_REVOKED,
    )]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(ControlledAccessRequest, related_name='approval_events', on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    level = models.CharField(max_length=20, choices=ControlledAccessRequest.LEVEL_CHOICES)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='+', on_delete=models.SET_NULL)
    reason = models.TextField(blank=True)
    scope_snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [models.Index(fields=['request', 'created_at'])]

    def __str__(self):
        return f'{self.request_id} · {self.action} · {self.level}'


class ProgramResource(models.Model):
    """Recurso existente ligado a um Programa, sem duplicar seu módulo de origem."""

    COURSE = 'course'
    FEED = 'feed'
    WIKI = 'wiki'
    ASSESSMENT = 'assessment'
    CERTIFICATION = 'certification'
    RESOURCE_CHOICES = [
        (COURSE, _('Curso')),
        (FEED, _('Feed')),
        (WIKI, _('Wiki')),
        (ASSESSMENT, _('Avaliação')),
        (CERTIFICATION, _('Certificação')),
    ]

    program = models.ForeignKey(Program, related_name='resources', on_delete=models.CASCADE)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_CHOICES)
    title = models.CharField(max_length=220)
    url = models.URLField(max_length=500)
    external_id = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f'{self.program} · {self.title}'


class EntryPoint(models.Model):
    """QR / ponto de entrada MatchCo com integridade e escopo territorial."""

    EXPERIENCE_GENERIC = 'generic'
    EXPERIENCE_SHOPPING = 'shopping'
    EXPERIENCE_MANUFACTURER = 'manufacturer'
    EXPERIENCE_DISTRIBUTOR = 'distributor'
    EXPERIENCE_RETAIL = 'retail'
    EXPERIENCE_HOSPITAL = 'hospital'
    EXPERIENCE_CORPORATE = 'corporate'
    EXPERIENCE_CHOICES = [
        (EXPERIENCE_GENERIC, _('MatchCo genérico')),
        (EXPERIENCE_SHOPPING, _('Shopping / território')),
        (EXPERIENCE_MANUFACTURER, _('Fabricante / marca')),
        (EXPERIENCE_DISTRIBUTOR, _('Distribuidor / canal')),
        (EXPERIENCE_RETAIL, _('Rede varejista')),
        (EXPERIENCE_HOSPITAL, _('Hospital / saúde')),
        (EXPERIENCE_CORPORATE, _('Empresa / página corporativa')),
    ]

    PURPOSE_RECRUITMENT = 'recruitment'
    PURPOSE_TRAINING = 'training'
    PURPOSE_CERTIFICATION = 'certification'
    PURPOSE_COMMUNICATION = 'communication'
    PURPOSE_CAMPAIGN = 'campaign'
    PURPOSE_PARTNER_ACCESS = 'partner_access'
    PURPOSE_CHOICES = [
        (PURPOSE_RECRUITMENT, _('Contratação')),
        (PURPOSE_TRAINING, _('Curso e capacitação')),
        (PURPOSE_CERTIFICATION, _('Certificação')),
        (PURPOSE_COMMUNICATION, _('Comunicação / conteúdo')),
        (PURPOSE_CAMPAIGN, _('Campanha ou ativação')),
        (PURPOSE_PARTNER_ACCESS, _('Acesso de parceiro')),
    ]

    AUDIENCE_ALL = 'all'
    AUDIENCE_MANAGER = 'manager'
    AUDIENCE_SELLER = 'seller'
    AUDIENCE_TECHNICIAN = 'technician'
    AUDIENCE_CANDIDATE = 'candidate'
    AUDIENCE_PARTNER = 'partner'
    AUDIENCE_CHOICES = [
        (AUDIENCE_ALL, _('Todos os participantes')),
        (AUDIENCE_MANAGER, _('Gerentes e responsáveis')),
        (AUDIENCE_SELLER, _('Vendedores e atendentes')),
        (AUDIENCE_TECHNICIAN, _('Técnicos e especialistas')),
        (AUDIENCE_CANDIDATE, _('Pessoas procurando oportunidade')),
        (AUDIENCE_PARTNER, _('Parceiros e distribuidores')),
    ]

    AUDIENCE_ROLE_MANUFACTURER = 'manufacturer'
    AUDIENCE_ROLE_DISTRIBUTOR = 'distributor'
    AUDIENCE_ROLE_RESELLER = 'reseller'
    AUDIENCE_ROLE_RETAIL_NETWORK = 'retail_network'
    AUDIENCE_ROLE_STORE_MANAGER = 'store_manager'
    AUDIENCE_ROLE_IT_MANAGER = 'it_manager'
    AUDIENCE_ROLE_SALESPERSON = 'salesperson'
    AUDIENCE_ROLE_TECHNICIAN = 'technician'
    AUDIENCE_ROLE_CANDIDATE = 'candidate'
    AUDIENCE_ROLE_CHOICES = [
        (AUDIENCE_ROLE_MANUFACTURER, _('Fabricante / marca')),
        (AUDIENCE_ROLE_DISTRIBUTOR, _('Distribuidor')),
        (AUDIENCE_ROLE_RESELLER, _('Revendedor autorizado')),
        (AUDIENCE_ROLE_RETAIL_NETWORK, _('Rede varejista')),
        (AUDIENCE_ROLE_STORE_MANAGER, _('Gerente de loja')),
        (AUDIENCE_ROLE_IT_MANAGER, _('Gerente de informática')),
        (AUDIENCE_ROLE_SALESPERSON, _('Atendente / vendedor')),
        (AUDIENCE_ROLE_TECHNICIAN, _('Técnico / especialista')),
        (AUDIENCE_ROLE_CANDIDATE, _('Candidato / pessoa interessada')),
    ]

    KIND_STORE = 'store'
    KIND_SHOPPING = 'shopping'
    KIND_NETWORK = 'network'
    KIND_STANDALONE = 'standalone'
    KIND_CORPORATE_PAGE = 'corporate_page'
    KIND_CHOICES = [
        (KIND_STORE, _('Loja específica')),
        (KIND_SHOPPING, _('Totem de shopping')),
        (KIND_NETWORK, _('Rede multi-unidade')),
        (KIND_STANDALONE, _('Unidade isolada')),
        (KIND_CORPORATE_PAGE, _('Página corporativa')),
    ]

    MODE_MATCH = 'match'
    MODE_CHOICES = [(MODE_MATCH, _('Porta Match (MatchCo)'))]

    STATE_DRAFT = 'draft'
    STATE_TESTED = 'tested'
    STATE_ACTIVE = 'active'
    STATE_COMPROMISED = 'compromised'
    STATE_REVOKED = 'revoked'
    STATE_CHOICES = [
        (STATE_DRAFT, _('Rascunho')),
        (STATE_TESTED, _('Testado, aguardando ativação')),
        (STATE_ACTIVE, _('Ativo em produção')),
        (STATE_COMPROMISED, _('Comprometido')),
        (STATE_REVOKED, _('Revogado')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, related_name='entry_points', on_delete=models.CASCADE
    )
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)

    # Escopo territorial (um dos três abaixo, conforme kind).
    scope_store = models.ForeignKey(
        BusinessUnit,
        null=True,
        blank=True,
        related_name='entry_points',
        on_delete=models.CASCADE,
    )
    scope_shopping_id = models.CharField(
        max_length=64,
        blank=True,
        help_text=_('Identificador do shopping quando kind=shopping'),
    )
    scope_network_id = models.CharField(
        max_length=64,
        blank=True,
        help_text=_('Identificador da rede quando kind=network'),
    )

    # Geo para cálculo de raio no feed territorial (Fase 8).
    geo_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    geo_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    geo_radius_m = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Raio de alcance sugerido em metros (só para standalone)'),
    )

    # Modo sugerido; a loja pode sobrescrever por Opportunity (Fase 2).
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default=MODE_MATCH)

    # Experiência pública resolvida pelo QR. O template continua compartilhado;
    # estes campos apenas definem o contexto e a personalização da organização.
    experience_template = models.CharField(
        max_length=24, choices=EXPERIENCE_CHOICES, default=EXPERIENCE_GENERIC,
    )
    brand_name = models.CharField(max_length=160, blank=True)
    brand_logo_url = models.URLField(blank=True)
    headline = models.CharField(max_length=220, blank=True)
    subheadline = models.TextField(blank=True)
    accent_color = models.CharField(max_length=20, default='#f97316')

    # Contexto de programa omnichannel: o QR pode abrir contratação,
    # conteúdo, capacitação ou relacionamento sem criar outra conta.
    purpose = models.CharField(
        max_length=24, choices=PURPOSE_CHOICES, default=PURPOSE_RECRUITMENT,
    )
    audience = models.CharField(
        max_length=24, choices=AUDIENCE_CHOICES, default=AUDIENCE_ALL,
    )
    audience_role = models.CharField(
        max_length=24, choices=AUDIENCE_ROLE_CHOICES,
        default=AUDIENCE_ROLE_CANDIDATE,
    )
    program = models.ForeignKey(
        Program, null=True, blank=True, related_name='entry_points',
        on_delete=models.SET_NULL,
    )
    program_name = models.CharField(max_length=160, blank=True)
    campaign_name = models.CharField(max_length=160, blank=True)
    channel_name = models.CharField(max_length=160, blank=True)
    participant_free = models.BooleanField(
        default=True,
        help_text=_('Participante final acessa gratuitamente; organização financia o programa.'),
    )

    # PIAG — Point Integrity Acceptance Gate (SISTEMA_MATCHCO_CANONICO §7).
    canonical_destination_url = models.URLField(
        help_text=_('URL canônica MatchCo que o QR resolve (HTTPS obrigatório)'),
    )
    tamper_evidence_hash = models.CharField(
        max_length=128,
        blank=True,
        help_text=_('Hash do artefato físico para detecção de adulteração'),
    )
    activation_tested_at = models.DateTimeField(null=True, blank=True)
    state = models.CharField(
        max_length=15, choices=STATE_CHOICES, default=STATE_DRAFT, db_index=True
    )

    # Autoria e responsabilidade.
    label = models.CharField(
        max_length=160,
        blank=True,
        help_text=_('Rótulo humano-legível (ex.: "Vitrine da Loja X")'),
    )
    managed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name='managed_entry_points',
        on_delete=models.SET_NULL,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Ponto de entrada (QR)')
        verbose_name_plural = _('Pontos de entrada (QR)')
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['scope_store', 'mode'],
                condition=models.Q(scope_store__isnull=False, state='active'),
                name='uniq_active_entry_point_per_store_mode',
            ),
            models.CheckConstraint(
                check=models.Q(scope_store__isnull=True) | models.Q(mode__in=['match', 'vaga']),
                name='store_entry_point_only_match_or_vaga',
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'state']),
            models.Index(fields=['kind', 'state']),
        ]

    def __str__(self):
        return self.label or f'{self.get_kind_display()} · {self.id}'

    @property
    def is_active(self):
        return self.state == self.STATE_ACTIVE

    def can_activate(self):
        """Regra PIAG mínima para virar ACTIVE.

        Version 1 exige: destino canônico HTTPS + teste de ativação
        registrado. Restante do PIAG (canal de incidente, monitoramento
        de destino) entra em fases posteriores.
        """
        return bool(
            self.canonical_destination_url.startswith('https://')
            and self.activation_tested_at
        )


# ---------------------------------------------------------------------------
# Porta Match — Relation (máquina de estados bilateral)
# ---------------------------------------------------------------------------
#
# Agregado central da Porta Match. Toda transição vive aqui.
# Ver SISTEMA_MATCHCO_CANONICO §2.3, §3.4.


class RelationStateError(Exception):
    """Transição inválida na máquina de estados de Relation."""


class Relation(models.Model):
    """Candidato × Opportunity × Versão da Opportunity.

    Uma Relation por (candidate, opportunity, opportunity_version).
    Transição estritamente crescente, sem retorno. Ver
    SISTEMA_MATCHCO_CANONICO §2 (máquina de estados) e §3.4.
    """

    # Estados canônicos (§2.3).
    STATE_NOTICE_DELIVERED = 'notice_delivered'
    STATE_NOTICE_EXPIRED = 'notice_expired'
    STATE_PERSON_INTERESTED = 'person_interested'
    STATE_EMPLOYER_INTEREST_VIEW = 'employer_interest_view'
    STATE_EMPLOYER_INTERESTED = 'employer_interested'
    STATE_NO_EMPLOYER_INTEREST = 'no_employer_interest'
    STATE_MATCHED = 'matched'
    STATE_CONTACT_ENABLED = 'contact_enabled'
    STATE_RESPONSE_CREATED = 'response_created'
    STATE_CLOSED = 'closed'
    STATE_DECLINED = 'declined'
    STATE_CHOICES = [
        (STATE_NOTICE_DELIVERED, _('Notícia entregue')),
        (STATE_NOTICE_EXPIRED, _('Convite expirado')),
        (STATE_PERSON_INTERESTED, _('Pessoa manifestou interesse')),
        (STATE_EMPLOYER_INTEREST_VIEW, _('Empregador vê projeção')),
        (STATE_EMPLOYER_INTERESTED, _('Empregador manifestou interesse')),
        (STATE_NO_EMPLOYER_INTEREST, _('Empregador declinou')),
        (STATE_MATCHED, _('Match — interesse bilateral')),
        (STATE_CONTACT_ENABLED, _('Contato liberado')),
        (STATE_RESPONSE_CREATED, _('Resposta criada')),
        (STATE_CLOSED, _('Encerrada')),
        (STATE_DECLINED, _('Candidato declinou')),
    ]

    # Estados terminais que não sofrem novas transições.
    TERMINAL_STATES = frozenset({
        STATE_CLOSED, STATE_DECLINED, STATE_NOTICE_EXPIRED, STATE_NO_EMPLOYER_INTEREST,
    })

    # Transições permitidas — grafo estritamente crescente.
    ALLOWED_TRANSITIONS = {
        STATE_NOTICE_DELIVERED: {STATE_PERSON_INTERESTED, STATE_DECLINED, STATE_NOTICE_EXPIRED},
        STATE_PERSON_INTERESTED: {STATE_EMPLOYER_INTEREST_VIEW},
        STATE_EMPLOYER_INTEREST_VIEW: {
            STATE_EMPLOYER_INTERESTED, STATE_NO_EMPLOYER_INTEREST,
        },
        STATE_EMPLOYER_INTERESTED: {STATE_MATCHED},
        STATE_MATCHED: {STATE_CONTACT_ENABLED},
        STATE_CONTACT_ENABLED: {STATE_RESPONSE_CREATED},
        STATE_RESPONSE_CREATED: {STATE_CLOSED},
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    candidate = models.ForeignKey(
        CandidateProfile,
        related_name='relations',
        on_delete=models.CASCADE,
    )
    opportunity = models.ForeignKey(
        Position,
        related_name='relations',
        on_delete=models.CASCADE,
    )
    opportunity_version = models.PositiveIntegerField(
        help_text=_('Versão da Opportunity no momento da relação'),
    )

    state = models.CharField(
        max_length=30,
        choices=STATE_CHOICES,
        default=STATE_NOTICE_DELIVERED,
        db_index=True,
    )

    # Timestamps de cada transição — mantidos para auditoria e debug.
    notice_delivered_at = models.DateTimeField(default=timezone.now)
    notice_expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    notice_expired_at = models.DateTimeField(null=True, blank=True)
    employer_decision_expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    negotiation_state = models.CharField(max_length=16, default='none')
    negotiation_fields = models.JSONField(default=list, blank=True)
    negotiation_proposal = models.JSONField(default=dict, blank=True)
    person_interested_at = models.DateTimeField(null=True, blank=True)
    employer_interest_view_at = models.DateTimeField(null=True, blank=True)
    employer_interested_at = models.DateTimeField(null=True, blank=True)
    no_employer_interest_at = models.DateTimeField(null=True, blank=True)
    matched_at = models.DateTimeField(null=True, blank=True)
    contact_enabled_at = models.DateTimeField(null=True, blank=True)
    response_created_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    declined_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Relation (candidato × oportunidade)')
        verbose_name_plural = _('Relations')
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['candidate', 'opportunity', 'opportunity_version'],
                name='uniq_relation_candidate_opp_version',
            ),
        ]
        indexes = [
            models.Index(fields=['opportunity', 'state']),
            models.Index(fields=['candidate', 'state']),
            models.Index(fields=['state', '-created_at']),
        ]

    def __str__(self):
        return f'{self.candidate_id}×{self.opportunity_id}v{self.opportunity_version} [{self.state}]'

    def clean(self):
        errors = {}
        if self.candidate_id and self.opportunity_id:
            if self.candidate.organization_id != self.opportunity.organization_id:
                errors['candidate'] = _(
                    'O Perfil deve pertencer à mesma organização da oportunidade.'
                )
        if self.opportunity_id and self.opportunity.business_unit_id:
            if self.opportunity.business_unit.organization_id != self.opportunity.organization_id:
                errors['opportunity'] = _(
                    'A oportunidade possui uma unidade fora da sua organização.'
                )
        if errors:
            raise ValidationError(errors)

    # ------------------------------------------------------------------
    # Máquina de estados
    # ------------------------------------------------------------------
    def is_terminal(self):
        return self.state in self.TERMINAL_STATES

    def can_transition_to(self, next_state):
        allowed = self.ALLOWED_TRANSITIONS.get(self.state, set())
        return next_state in allowed

    _STATE_TIMESTAMP_FIELD = {
        STATE_NOTICE_EXPIRED: 'notice_expired_at',
        STATE_PERSON_INTERESTED: 'person_interested_at',
        STATE_EMPLOYER_INTEREST_VIEW: 'employer_interest_view_at',
        STATE_EMPLOYER_INTERESTED: 'employer_interested_at',
        STATE_NO_EMPLOYER_INTEREST: 'no_employer_interest_at',
        STATE_MATCHED: 'matched_at',
        STATE_CONTACT_ENABLED: 'contact_enabled_at',
        STATE_RESPONSE_CREATED: 'response_created_at',
        STATE_CLOSED: 'closed_at',
        STATE_DECLINED: 'declined_at',
    }

    def transition(self, next_state, *, at=None):
        """Aplica transição validada. Levanta RelationStateError se inválida."""
        if not self.can_transition_to(next_state):
            raise RelationStateError(
                f'Transição inválida: {self.state} → {next_state}'
            )
        ts = at or timezone.now()
        self.state = next_state
        ts_field = self._STATE_TIMESTAMP_FIELD.get(next_state)
        if ts_field:
            setattr(self, ts_field, ts)
        self.save(update_fields=['state', 'updated_at'] + ([ts_field] if ts_field else []))


class RelationTransitionEvent(models.Model):
    """Registro imutável de cada transição de Relation.

    Feed direto para o Ledger (Fase 4). Mantido em tabela própria para
    auditoria mesmo antes do Ledger canônico estar completo.
    """

    relation = models.ForeignKey(
        Relation, related_name='transitions', on_delete=models.CASCADE,
    )
    from_state = models.CharField(max_length=30)
    to_state = models.CharField(max_length=30)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    actor_type = models.CharField(
        max_length=20,
        choices=[
            ('candidate', 'candidate'),
            ('employer_actor', 'employer_actor'),
            ('ops', 'ops'),
            ('system', 'system'),
        ],
        default='system',
    )
    authority_scope = models.CharField(
        max_length=10, blank=True,
        help_text=_('Escopo AA-x usado (AA-7, AA-8 etc.)'),
    )
    metadata = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = _('Transição de Relation')
        verbose_name_plural = _('Transições de Relation')
        ordering = ['-occurred_at']
        indexes = [
            models.Index(fields=['relation', '-occurred_at']),
            models.Index(fields=['to_state', '-occurred_at']),
        ]

    def __str__(self):
        return f'{self.relation_id}: {self.from_state}→{self.to_state}'


# ---------------------------------------------------------------------------
# Porta Match — EmployerActor + Ledger append-only
# ---------------------------------------------------------------------------
#
# EmployerActor: ator humano do lado empregador com escopos de autoridade
# AA-1..AA-8. Ver SISTEMA_MATCHCO_CANONICO §5.
#
# Ledger: evento imutável e append-only. Ver SISTEMA_MATCHCO_CANONICO §3.7, §14.


class AuthorityScope:
    """Escopos AA-1..AA-8 (SISTEMA_MATCHCO_CANONICO §5)."""
    AA1_DECLARE_NEED = 'AA-1'
    AA2_STRUCTURE_OPPORTUNITY = 'AA-2'
    AA3_ACTIVATE_OPPORTUNITY = 'AA-3'
    AA4_MODIFY_OPPORTUNITY = 'AA-4'
    AA5_CLOSE_OPPORTUNITY = 'AA-5'
    AA6_VIEW_EMPLOYER_INTEREST_VIEW = 'AA-6'
    AA7_DECLARE_EMPLOYER_INTEREST = 'AA-7'
    AA8_RECEIVE_CONTACT_CHANNEL = 'AA-8'

    ALL = [
        AA1_DECLARE_NEED, AA2_STRUCTURE_OPPORTUNITY, AA3_ACTIVATE_OPPORTUNITY,
        AA4_MODIFY_OPPORTUNITY, AA5_CLOSE_OPPORTUNITY,
        AA6_VIEW_EMPLOYER_INTEREST_VIEW, AA7_DECLARE_EMPLOYER_INTEREST,
        AA8_RECEIVE_CONTACT_CHANNEL,
    ]


class AuthorityError(Exception):
    """Ator sem escopo de autoridade suficiente."""


class EmployerActor(models.Model):
    """Ator humano do lado empregador com escopos AA-1..AA-8.

    Um `User` do Django pode ser EmployerActor em múltiplas operações
    (loja/rede/unidade) com escopos distintos em cada.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='employer_actor_profiles',
        on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(
        Organization, related_name='employer_actors', on_delete=models.CASCADE,
    )
    business_unit = models.ForeignKey(
        BusinessUnit, related_name='employer_actors',
        null=True, blank=True, on_delete=models.CASCADE,
        help_text=_('Loja/unidade em que o ator age; nulo = escopo organização'),
    )

    authority_scopes = models.JSONField(
        default=list,
        help_text=_('Lista de escopos AA-1..AA-8 concedidos'),
    )
    human_verified_at = models.DateTimeField(
        null=True, blank=True,
        help_text=_('Verificação humana obrigatória para AA-7/AA-8'),
    )
    active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Ator empregador (AA)')
        verbose_name_plural = _('Atores empregadores')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'organization', 'business_unit'],
                name='uniq_employer_actor_user_org_unit',
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'active']),
        ]

    def __str__(self):
        return f'{self.user} @ {self.business_unit or self.organization}'

    def has_scope(self, scope):
        if not self.active:
            return False
        if scope not in (self.authority_scopes or []):
            return False
        # AA-7 e AA-8 exigem verificação humana explícita.
        if scope in (AuthorityScope.AA7_DECLARE_EMPLOYER_INTEREST,
                     AuthorityScope.AA8_RECEIVE_CONTACT_CHANNEL):
            return self.human_verified_at is not None
        return True

    def require_scope(self, scope):
        if not self.has_scope(scope):
            raise AuthorityError(
                f'Ator {self.user_id} não tem escopo {scope}'
            )


class LedgerAppendOnlyError(Exception):
    """Tentativa de UPDATE ou DELETE em Ledger."""


class LedgerQuerySet(models.QuerySet):
    def update(self, *args, **kwargs):
        raise LedgerAppendOnlyError('Ledger é append-only — UPDATE bloqueado')

    def delete(self):
        raise LedgerAppendOnlyError('Ledger é append-only — DELETE bloqueado')


class LedgerManager(models.Manager.from_queryset(LedgerQuerySet)):
    pass


class Ledger(models.Model):
    """Evento canônico imutável (SISTEMA_MATCHCO_CANONICO §3.7, §14).

    Regra: INSERT-only. UPDATE e DELETE proibidos via Manager e save() override.
    Correções são novos eventos do tipo CORRECTION.
    """

    # Tipos canônicos de evento.
    EVENT_PROFILE_CREATED = 'PROFILE_CREATED'
    EVENT_PROFILE_ANONYMIZED = 'PROFILE_ANONYMIZED'
    EVENT_CONSENT_GRANTED = 'CONSENT_GRANTED'
    EVENT_CONSENT_REVOKED = 'CONSENT_REVOKED'
    EVENT_OPPORTUNITY_STRUCTURED = 'OPPORTUNITY_STRUCTURED'
    EVENT_OPPORTUNITY_ACTIVATED = 'OPPORTUNITY_ACTIVATED'
    EVENT_OPPORTUNITY_VERSION_BUMP = 'OPPORTUNITY_VERSION_BUMP'
    EVENT_OPPORTUNITY_CLOSED = 'OPPORTUNITY_CLOSED'
    EVENT_NOTICE_DELIVERED = 'NOTICE_DELIVERED'
    EVENT_PERSON_INTERESTED = 'PERSON_INTERESTED'
    EVENT_EMPLOYER_INTERESTED = 'EMPLOYER_INTERESTED'
    EVENT_MATCHED = 'MATCHED'
    EVENT_CONTACT_ENABLED = 'CONTACT_ENABLED'
    EVENT_RESPONSE_CREATED = 'RESPONSE_CREATED'
    EVENT_CLOSED = 'CLOSED'
    EVENT_DECLINED = 'DECLINED'
    EVENT_POINT_ACTIVATED = 'POINT_ACTIVATED'
    EVENT_POINT_COMPROMISED = 'POINT_COMPROMISED'
    EVENT_POINT_REVOKED = 'POINT_REVOKED'
    EVENT_RIGHTS_REQUEST = 'RIGHTS_REQUEST'
    EVENT_AUTHORITY_VIOLATION = 'AUTHORITY_VIOLATION'
    EVENT_CORRECTION = 'CORRECTION'

    ACTOR_CANDIDATE = 'candidate'
    ACTOR_EMPLOYER_ACTOR = 'employer_actor'
    ACTOR_OPS = 'ops'
    ACTOR_SYSTEM = 'system'
    ACTOR_TYPE_CHOICES = [
        (ACTOR_CANDIDATE, 'candidate'),
        (ACTOR_EMPLOYER_ACTOR, 'employer_actor'),
        (ACTOR_OPS, 'ops'),
        (ACTOR_SYSTEM, 'system'),
    ]

    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=40, db_index=True)

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    actor_type = models.CharField(max_length=20, choices=ACTOR_TYPE_CHOICES, default=ACTOR_SYSTEM)
    authority_scope = models.CharField(max_length=10, blank=True)

    # Referências opcionais para reconstruir o contexto.
    relation = models.ForeignKey(
        Relation, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
    )
    opportunity = models.ForeignKey(
        Position, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
    )
    opportunity_version = models.PositiveIntegerField(null=True, blank=True)
    candidate = models.ForeignKey(
        CandidateProfile, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    entry_point = models.ForeignKey(
        EntryPoint, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
    )

    policy_version = models.PositiveIntegerField(default=1)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=400, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)

    objects = LedgerManager()

    class Meta:
        verbose_name = _('Ledger event')
        verbose_name_plural = _('Ledger')
        ordering = ['-occurred_at']
        indexes = [
            models.Index(fields=['event_type', '-occurred_at']),
            models.Index(fields=['actor', '-occurred_at']),
            models.Index(fields=['relation', '-occurred_at']),
            models.Index(fields=['opportunity', '-occurred_at']),
            models.Index(fields=['candidate', '-occurred_at']),
        ]

    def __str__(self):
        return f'{self.event_type} @ {self.occurred_at:%Y-%m-%d %H:%M:%S}'

    def save(self, *args, **kwargs):
        # Append-only: uma vez persistido, nunca mais.
        if self._state.adding is False:
            raise LedgerAppendOnlyError(
                'Ledger é append-only — evento já persistido não pode ser modificado'
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise LedgerAppendOnlyError('Ledger é append-only — DELETE bloqueado')


# ---------------------------------------------------------------------------
# Porta Match — ContactChannel (SISTEMA_MATCHCO_CANONICO §3.6)
# ---------------------------------------------------------------------------
#
# Emitido só quando a Relation atinge CONTACT_ENABLED. Contém endpoint
# validado de cada lado. Nunca antes do MATCHED + AA-8.


class ContactChannel(models.Model):
    """Canal de contato liberado após MATCHED + AA-8.

    Uma entrada por Relation. Endpoints validados dos dois lados. Nunca
    exposto antes de CONTACT_ENABLED.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    relation = models.OneToOneField(
        Relation, related_name='contact_channel', on_delete=models.CASCADE,
    )

    candidate_mobile = models.CharField(_('Telefone do candidato'), max_length=30)
    employer_contact_name = models.CharField(max_length=160, blank=True)
    employer_mobile = models.CharField(_('Telefone do empregador'), max_length=30, blank=True)
    employer_email = models.EmailField(blank=True)

    # Ator empregador (AA-8) que recebeu o canal.
    released_to_actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    released_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = _('Contact Channel')
        verbose_name_plural = _('Contact Channels')

    def __str__(self):
        return f'ContactChannel({self.relation_id})'


# ---------------------------------------------------------------------------
# LGPD — RightsCase (SISTEMA_MATCHCO_CANONICO §6.3)
# ---------------------------------------------------------------------------


class RightsCase(models.Model):
    """Pedido de direito do titular via canal de e-mail (§6.3).

    Canal principal é e-mail (não depende do app estar operacional).
    Endpoint no app é atalho, não canal oficial.
    """

    TYPE_ACCESS = 'access'
    TYPE_CORRECTION = 'correction'
    TYPE_DELETION = 'deletion'
    TYPE_BLOCKING = 'blocking'
    TYPE_OBJECTION = 'objection'
    TYPE_PORTABILITY = 'portability'
    TYPE_CHOICES = [
        (TYPE_ACCESS, _('Acesso')),
        (TYPE_CORRECTION, _('Correção')),
        (TYPE_DELETION, _('Exclusão')),
        (TYPE_BLOCKING, _('Bloqueio')),
        (TYPE_OBJECTION, _('Oposição')),
        (TYPE_PORTABILITY, _('Portabilidade')),
    ]

    VERIFICATION_PENDING = 'pending'
    VERIFICATION_VERIFIED = 'verified'
    VERIFICATION_REJECTED = 'rejected'
    VERIFICATION_CHOICES = [
        (VERIFICATION_PENDING, _('Aguardando verificação')),
        (VERIFICATION_VERIFIED, _('Verificado')),
        (VERIFICATION_REJECTED, _('Rejeitado')),
    ]

    ACTION_OPEN = 'open'
    ACTION_IN_PROGRESS = 'in_progress'
    ACTION_DONE = 'done'
    ACTION_ARCHIVED = 'archived'
    ACTION_CHOICES = [
        (ACTION_OPEN, _('Aberto')),
        (ACTION_IN_PROGRESS, _('Em andamento')),
        (ACTION_DONE, _('Concluído')),
        (ACTION_ARCHIVED, _('Arquivado')),
    ]

    case_ref = models.CharField(
        max_length=32, unique=True,
        help_text=_('Referência pública curta enviada ao titular'),
    )
    requester_email = models.EmailField()
    identity = models.ForeignKey(
        CandidateIdentity, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='rights_cases',
    )
    request_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    verification_state = models.CharField(
        max_length=15, choices=VERIFICATION_CHOICES, default=VERIFICATION_PENDING,
    )
    action_state = models.CharField(
        max_length=15, choices=ACTION_CHOICES, default=ACTION_OPEN,
    )
    notes = models.TextField(blank=True)
    evidence = models.JSONField(default=list, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('Rights case (LGPD)')
        verbose_name_plural = _('Rights cases (LGPD)')
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['action_state', '-received_at']),
            models.Index(fields=['request_type', 'action_state']),
        ]

    def __str__(self):
        return f'{self.case_ref} · {self.get_request_type_display()}'


# ---------------------------------------------------------------------------
# LGPD — retention classes RT-01..RT-06 (SISTEMA_MATCHCO_CANONICO §6.2)
# ---------------------------------------------------------------------------


class RetentionClass:
    """Classes de retenção. Prazos numéricos sob revisão jurídica."""
    RT01_ACTIVE_RELATION = 'RT-01'
    RT02_POST_CLOSURE = 'RT-02'
    RT03_LEDGER_AUDIT = 'RT-03'
    RT04_SECURITY_INCIDENT = 'RT-04'   # ≥ 5 anos (ANPD)
    RT05_TECHNICAL_LOGS = 'RT-05'
    RT06_AGE_GATE_FAILURE = 'RT-06'    # sem retenção

    # Defaults executáveis em produção; ajustar após revisão jurídica.
    DEFAULT_DAYS = {
        RT01_ACTIVE_RELATION: None,   # enquanto ativa
        RT02_POST_CLOSURE: 365,
        RT03_LEDGER_AUDIT: 365 * 5,
        RT04_SECURITY_INCIDENT: 365 * 5,
        RT05_TECHNICAL_LOGS: 180,
        RT06_AGE_GATE_FAILURE: 0,
    }


# ---------------------------------------------------------------------------
# Porta Match — Response (RC-01..RC-05) obrigatória no encerramento
# ---------------------------------------------------------------------------
#
# Ver SISTEMA_MATCHCO_CANONICO §15. Interesse merece resposta honesta.
# Silêncio bloqueia novas declarações do mesmo empregador.


class ResponseClass:
    RC01_SEGUE_ESTA_PESSOA = 'RC-01'
    RC02_SEGUE_OUTRA_PESSOA = 'RC-02'
    RC03_ADIADA_OU_CANCELADA = 'RC-03'
    RC04_MUDOU_PERFIL = 'RC-04'
    RC05_OUTRO_MOTIVO = 'RC-05'

    ALL = [RC01_SEGUE_ESTA_PESSOA, RC02_SEGUE_OUTRA_PESSOA,
           RC03_ADIADA_OU_CANCELADA, RC04_MUDOU_PERFIL, RC05_OUTRO_MOTIVO]

    LABELS = {
        RC01_SEGUE_ESTA_PESSOA: _('Seguirei com esta pessoa'),
        RC02_SEGUE_OUTRA_PESSOA: _('Seguirei com outra pessoa'),
        RC03_ADIADA_OU_CANCELADA: _('Adiei ou cancelei a necessidade'),
        RC04_MUDOU_PERFIL: _('Mudou o perfil que preciso'),
        RC05_OUTRO_MOTIVO: _('Outro motivo (nota obrigatória)'),
    }


class ResponseValidationError(Exception):
    """Resposta inválida (classe fora de RC-01..05 ou nota vazia em RC-05)."""


class Response(models.Model):
    """Resposta obrigatória do empregador no encerramento da Relation.

    Motivos inventados/genéricos não são aceitos. Silêncio bloqueia novas
    declarações do empregador até resposta gerada.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    relation = models.OneToOneField(
        Relation, related_name='response', on_delete=models.CASCADE,
    )
    response_class = models.CharField(
        max_length=8,
        choices=[(c, ResponseClass.LABELS[c]) for c in ResponseClass.ALL],
    )
    note = models.TextField(
        blank=True,
        help_text=_('Nota curta e honesta. Obrigatória para RC-05.'),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Response (RC-01..05)')
        verbose_name_plural = _('Responses (RC-01..05)')
        indexes = [
            models.Index(fields=['response_class', '-created_at']),
        ]

    def __str__(self):
        return f'{self.response_class} · {self.relation_id}'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.response_class not in ResponseClass.ALL:
            raise ValidationError(f'response_class inválida: {self.response_class}')
        if self.response_class == ResponseClass.RC05_OUTRO_MOTIVO and not (self.note or '').strip():
            raise ValidationError('RC-05 exige nota curta e honesta')


# ---------------------------------------------------------------------------
# Porta Match — OTP passwordless (Rodada B1)
# ---------------------------------------------------------------------------
#
# Ver SISTEMA_MATCHCO_CANONICO §11. Autenticação por celular validado +
# OTP. Hoje registro fica no DB; o envio real é responsabilidade do
# `notification` port.


class OtpCode(models.Model):
    """Código OTP emitido para um mobile. Hash-armazenado."""

    STATE_PENDING = 'pending'
    STATE_USED = 'used'
    STATE_EXPIRED = 'expired'
    STATE_FAILED = 'failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mobile = models.CharField(max_length=30, db_index=True)
    code_hash = models.CharField(max_length=128)
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=5)
    state = models.CharField(max_length=10, default=STATE_PENDING, db_index=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('OTP code')
        verbose_name_plural = _('OTP codes')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['mobile', 'state', '-created_at']),
        ]

    def is_valid(self, now=None):
        now = now or timezone.now()
        return self.state == self.STATE_PENDING and now < self.expires_at


# ---------------------------------------------------------------------------
# Convite de lojista (Rodada Demo)
# ---------------------------------------------------------------------------

class LojistaInvite(models.Model):
    """Convite emitido pelo sponsor para um lojista criar sua conta."""

    STATE_PENDING = 'pending'
    STATE_PENDING_APPROVAL = 'pending_approval'
    STATE_ACCEPTED = 'accepted'
    STATE_EXPIRED = 'expired'
    STATE_REVOKED = 'revoked'
    STATE_CHOICES = [
        (STATE_PENDING, _('Pendente')),
        (STATE_PENDING_APPROVAL, _('Aguardando aprovação')),
        (STATE_ACCEPTED, _('Aceito')),
        (STATE_EXPIRED, _('Expirado')),
        (STATE_REVOKED, _('Revogado')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, related_name='lojista_invites', on_delete=models.CASCADE,
    )
    business_unit = models.ForeignKey(
        BusinessUnit, null=True, blank=True, related_name='invites',
        on_delete=models.CASCADE,
    )
    email = models.EmailField(db_index=True)
    scopes = models.JSONField(default=list)
    token = models.CharField(max_length=64, unique=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    state = models.CharField(max_length=24, choices=STATE_CHOICES, default=STATE_PENDING, db_index=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Convite de lojista')
        verbose_name_plural = _('Convites de lojista')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.email} · {self.state}'

    def is_valid(self, now=None):
        now = now or timezone.now()
        return self.state == self.STATE_PENDING and now < self.expires_at


# ---------------------------------------------------------------------------
# Porta Match — ProfileSignal (freshness F0/F1/F2) + circulation state
# ---------------------------------------------------------------------------
#
# Ver SISTEMA_MATCHCO_CANONICO §3.2 e §8. Freshness ≠ circulação.


class FreshnessClass:
    F0_DURABLE = 'F0'            # sem expiração periódica
    F1_DYNAMIC = 'F1'            # 90 dias
    F2_HIGHLY_DYNAMIC = 'F2'     # 30 dias

    EXPIRY_DAYS = {F0_DURABLE: None, F1_DYNAMIC: 90, F2_HIGHLY_DYNAMIC: 30}

    CHOICES = [
        (F0_DURABLE, _('F0 — durável')),
        (F1_DYNAMIC, _('F1 — dinâmico (90d)')),
        (F2_HIGHLY_DYNAMIC, _('F2 — muito dinâmico (30d)')),
    ]


class SignalOrigin:
    SELF_DECLARED = 'self_declared'
    COURSE_COMPLETION = 'course_completion'
    CERTIFICATION = 'certification'
    TEST_RESULT = 'test_result'
    OPS_CORRECTION = 'ops_correction'
    TALK_INTERACTION = 'talk_interaction'
    CHOICES = [
        (SELF_DECLARED, 'self_declared'),
        (COURSE_COMPLETION, 'course_completion'),
        (CERTIFICATION, 'certification'),
        (TEST_RESULT, 'test_result'),
        (OPS_CORRECTION, 'ops_correction'),
        (TALK_INTERACTION, 'talk_interaction'),
    ]


class ProfileSignal(models.Model):
    """Sinal do Perfil com freshness explícita (SISTEMA_MATCHCO_CANONICO §3.2)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        'CandidateProfile', related_name='signals', on_delete=models.CASCADE,
    )
    key = models.CharField(
        max_length=80,
        help_text=_('Chave do sinal (ex: geography_possibility, availability, course_atendimento)'),
    )
    value = models.JSONField(default=dict, blank=True)
    origin = models.CharField(max_length=30, choices=SignalOrigin.CHOICES,
                              default=SignalOrigin.SELF_DECLARED)
    freshness_class = models.CharField(max_length=5, choices=FreshnessClass.CHOICES,
                                       default=FreshnessClass.F1_DYNAMIC)
    confirmed_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    label = models.CharField(
        max_length=200, blank=True,
        help_text=_('Descrição humano-legível para exibição por extenso'),
    )

    class Meta:
        verbose_name = _('Profile signal')
        verbose_name_plural = _('Profile signals')
        indexes = [
            models.Index(fields=['profile', 'key']),
            models.Index(fields=['freshness_class', 'confirmed_at']),
        ]

    def __str__(self):
        return f'{self.profile_id}/{self.key} [{self.freshness_class}]'

    def is_stale(self, now=None):
        days = FreshnessClass.EXPIRY_DAYS[self.freshness_class]
        if days is None:
            return False
        now = now or timezone.now()
        return (now - self.confirmed_at).days >= days

    def save(self, *args, **kwargs):
        # Calcula expires_at para F1/F2 automaticamente.
        days = FreshnessClass.EXPIRY_DAYS[self.freshness_class]
        if days is not None:
            self.expires_at = self.confirmed_at + timedelta(days=days)
        else:
            self.expires_at = None
        super().save(*args, **kwargs)
