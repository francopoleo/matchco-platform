import datetime
import hashlib
import random
import secrets

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django_tenants.models import TenantMixin


def random_indication_code():
    return str(random.randint(100000, 999999))


class Organization(TenantMixin):
    MARKET_SHOPPING = 'shopping'
    MARKET_RETAIL = 'retail'
    MARKET_MANUFACTURER = 'manufacturer'
    MARKET_DISTRIBUTOR = 'distributor'
    MARKET_PHARMA = 'pharma'
    MARKET_HOSPITAL = 'hospital'
    MARKET_LOGISTICS = 'logistics'
    MARKET_EDUCATION = 'education'
    MARKET_SERVICES = 'services'
    MARKET_GENERAL = 'general'
    MARKET_CHOICES = (
        (MARKET_GENERAL, _('Empresa / organização')),
        (MARKET_SHOPPING, _('Shopping / território')),
        (MARKET_RETAIL, _('Varejo / rede de lojas')),
        (MARKET_MANUFACTURER, _('Fabricante / indústria')),
        (MARKET_DISTRIBUTOR, _('Distribuidor / canal')),
        (MARKET_PHARMA, _('Farmacêutica / ciências da vida')),
        (MARKET_HOSPITAL, _('Hospital / saúde')),
        (MARKET_LOGISTICS, _('Logística')),
        (MARKET_EDUCATION, _('Educação')),
        (MARKET_SERVICES, _('Serviços / franquias')),
    )
    ONBOARDING_DRAFT = 'draft'
    ONBOARDING_READY = 'ready'
    ONBOARDING_ACTIVE = 'active'
    ONBOARDING_CHOICES = (
        (ONBOARDING_DRAFT, _('Em configuração')),
        (ONBOARDING_READY, _('Pronta para teste')),
        (ONBOARDING_ACTIVE, _('Em produção')),
    )
    name = models.CharField(_('Name'), max_length=160)
    slug = models.SlugField(_('Slug'), max_length=180, unique=True)
    description = models.TextField(_('Description'), blank=True, default='')
    active = models.BooleanField(_('Active'), default=True)
    is_public = models.BooleanField(
        _('Public'),
        default=False,
        help_text=_('Public organizations are for external users (candidates, doctors, partners, students)')
    )
    market = models.CharField(max_length=24, choices=MARKET_CHOICES, default=MARKET_GENERAL)
    onboarding_status = models.CharField(max_length=12, choices=ONBOARDING_CHOICES, default=ONBOARDING_DRAFT)
    brand_name = models.CharField(max_length=160, blank=True)
    logo_url = models.URLField(blank=True)
    favicon_url = models.URLField(blank=True)
    primary_color = models.CharField(max_length=20, default='#f97316')
    custom_domain = models.CharField(max_length=253, blank=True)
    white_label_enabled = models.BooleanField(default=False)
    default_entry_template = models.CharField(max_length=24, default='generic')

    def save(self, *args, **kwargs):
        """Sempre persiste um schema válido para novas organizações.

        O wizard de setup já informa o schema explicitamente, mas integrações
        legadas podem criar a organização apenas com nome e slug. O fallback
        mantém essas entradas compatíveis sem alterar schemas já definidos.
        """
        if not self.schema_name:
            self.schema_name = (slugify(self.slug or self.name) or 'organization')[:63]
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')
        ordering = ['-is_public', 'name']

    def __str__(self):
        return self.name


class OrganizationServiceSubscription(models.Model):
    """Service capability enabled for an organization or one company.

    The organization hierarchy is always available. Product services such as
    Talk, training and Match are activated independently over that same
    hierarchy, so a Talk-only tenant does not acquire recruitment screens.
    An organization row is the default for its companies. A company row is an
    explicit override for that company, which keeps a shopping center and a
    network sharing one structure without mixing their commercial services.
    """

    SERVICE_CONTENT = 'content'
    SERVICE_TALK = 'talk'
    SERVICE_TRAINING = 'training'
    SERVICE_CERTIFICATION = 'certification'
    SERVICE_RECRUITMENT = 'recruitment'
    SERVICE_CAMPAIGNS = 'campaigns'
    SERVICE_OPERATIONS = 'operations'
    SERVICE_PARTNERS = 'partners'
    SERVICE_ANALYTICS = 'analytics'
    SERVICE_CHOICES = (
        (SERVICE_CONTENT, _('Content')),
        (SERVICE_TALK, _('Talk')),
        (SERVICE_TRAINING, _('Training')),
        (SERVICE_CERTIFICATION, _('Certification')),
        (SERVICE_RECRUITMENT, _('Recruitment Match')),
        (SERVICE_CAMPAIGNS, _('Campaigns and surveys')),
        (SERVICE_OPERATIONS, _('Operations')),
        (SERVICE_PARTNERS, _('Partners')),
        (SERVICE_ANALYTICS, _('Analytics')),
    )
    STATUS_ACTIVE = 'active'
    STATUS_SUSPENDED = 'suspended'
    STATUS_EXPIRED = 'expired'
    STATUS_CHOICES = (
        (STATUS_ACTIVE, _('Active')),
        (STATUS_SUSPENDED, _('Suspended')),
        (STATUS_EXPIRED, _('Expired')),
    )

    organization = models.ForeignKey(
        Organization, related_name='service_subscriptions', on_delete=models.CASCADE,
    )
    company = models.ForeignKey(
        'Company', related_name='service_subscriptions', null=True, blank=True,
        on_delete=models.CASCADE,
    )
    service_code = models.CharField(max_length=32, choices=SERVICE_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    plan_code = models.CharField(max_length=80, blank=True, default='')
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    configuration = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'service_code'],
                condition=models.Q(company__isnull=True),
                name='uniq_org_default_service_subscription',
            ),
            models.UniqueConstraint(
                fields=['organization', 'company', 'service_code'],
                condition=models.Q(company__isnull=False),
                name='uniq_company_service_subscription',
            ),
        ]
        ordering = ['organization', 'company', 'service_code']

    def clean(self):
        super().clean()
        if self.company_id and self.company.organization_id != self.organization_id:
            raise ValidationError({'company': _('A empresa precisa pertencer à organização selecionada.')})

    def __str__(self):
        scope = self.company.name if self.company_id else 'padrão da organização'
        return f'{self.organization} · {scope} · {self.get_service_code_display()}'


class SectorTemplate(models.Model):
    """Reusable onboarding defaults; domain objects remain organization-scoped."""

    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    defaults = models.JSONField(default=dict, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Domain(models.Model):
    """Domain mapping for multi-tenant routing."""
    domain = models.CharField(max_length=253, unique=True)
    tenant = models.ForeignKey(Organization, related_name='domains', on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Domain')
        verbose_name_plural = _('Domains')

    def __str__(self):
        return f'{self.domain} → {self.tenant.name}'


class OrganizationTerminology(models.Model):
    """Configurable labels for the enterprise hierarchy shown in the UI."""

    organization = models.OneToOneField(
        Organization,
        related_name='terminology',
        on_delete=models.CASCADE,
    )
    level_1_label = models.CharField(max_length=80, default='Empresa')
    level_1_description = models.CharField(max_length=240, blank=True, default='Organização empresarial ou grupo econômico.')
    level_2_label = models.CharField(max_length=80, default='Unidade de negócio')
    level_2_description = models.CharField(max_length=240, blank=True, default='Divisão, operação, filial ou localidade.')
    level_3_label = models.CharField(max_length=80, default='Unidade operacional')
    level_3_description = models.CharField(max_length=240, blank=True, default='Departamento, serviço ou equipe dentro da unidade.')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Terminologia da organização')
        verbose_name_plural = _('Terminologia das organizações')

    def __str__(self):
        return f'{self.organization} · terminologia'


class Company(models.Model):
    organization = models.ForeignKey(Organization, related_name='companies', null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(_('Name'), max_length=160)
    code = models.CharField(_('Code'), max_length=80, blank=True)
    active = models.BooleanField(_('Active'), default=True)

    # Dados legais
    legal_name = models.CharField(_('Legal Name'), max_length=255, blank=True)
    cnpj = models.CharField(_('CNPJ'), max_length=14, blank=True, unique=True, null=True)
    ie = models.CharField(_('IE (Inscrição Estadual)'), max_length=15, blank=True)

    # Correspondência
    endereco_correspondencia = models.CharField(_('Address for Correspondence'), max_length=255, blank=True)
    cep_correspondencia = models.CharField(_('CEP'), max_length=9, blank=True)
    city_correspondencia = models.CharField(_('City'), max_length=120, blank=True)
    state_correspondencia = models.CharField(_('State'), max_length=2, blank=True)

    # Contato geral
    email_geral = models.EmailField(_('General Email'), blank=True)
    telefone_geral = models.CharField(_('General Phone'), max_length=15, blank=True)
    website = models.URLField(_('Website'), blank=True)

    class Meta:
        verbose_name = _('Company')
        verbose_name_plural = _('Companies')
        ordering = ('name',)
        constraints = [models.UniqueConstraint(fields=('organization', 'name'), name='unique_company_per_organization')]

    def __str__(self):
        return self.name


class PhysicalLocation(models.Model):
    """Neutral real-world location shared by contextual business units."""

    external_key = models.CharField(max_length=160, unique=True)
    name = models.CharField(max_length=255)
    cep = models.CharField(max_length=9, blank=True)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=2, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name', 'id')

    def __str__(self):
        return self.name


class BusinessUnit(models.Model):
    UNIT_STORE = 'store'
    UNIT_KIOSK = 'kiosk'
    UNIT_SERVICE = 'service'
    UNIT_DISTRIBUTION = 'distribution'
    UNIT_FACTORY = 'factory'
    UNIT_OFFICE = 'office'
    UNIT_PARTNER = 'partner'
    UNIT_OTHER = 'other'
    UNIT_KIND_CHOICES = (
        (UNIT_STORE, _('Loja')),
        (UNIT_KIOSK, _('Quiosque')),
        (UNIT_SERVICE, _('Serviço')),
        (UNIT_DISTRIBUTION, _('Centro de distribuição')),
        (UNIT_FACTORY, _('Fábrica')),
        (UNIT_OFFICE, _('Escritório')),
        (UNIT_PARTNER, _('Unidade parceira')),
        (UNIT_OTHER, _('Outro')),
    )
    LOCATION_STREET = 'street'
    LOCATION_SHOPPING = 'shopping'
    LOCATION_CORPORATE = 'corporate'
    LOCATION_INDUSTRIAL = 'industrial'
    LOCATION_REMOTE = 'remote'
    LOCATION_CHOICES = (
        (LOCATION_STREET, _('Rua / endereço próprio')),
        (LOCATION_SHOPPING, _('Shopping / empreendimento')),
        (LOCATION_CORPORATE, _('Edifício corporativo')),
        (LOCATION_INDUSTRIAL, _('Área industrial')),
        (LOCATION_REMOTE, _('Sem endereço público')),
    )

    company = models.ForeignKey(Company, related_name='business_units', on_delete=models.CASCADE)
    name = models.CharField(_('Name'), max_length=160)
    trade_name = models.CharField(_('Nome comercial'), max_length=160, blank=True)
    code = models.CharField(_('Code'), max_length=80, blank=True)
    external_reference = models.CharField(_('Referência externa'), max_length=120, blank=True)
    unit_kind = models.CharField(_('Tipo de unidade'), max_length=20, choices=UNIT_KIND_CHOICES, default=UNIT_STORE)
    location_type = models.CharField(_('Tipo de localização'), max_length=20, choices=LOCATION_CHOICES, default=LOCATION_STREET)
    active = models.BooleanField(_('Active'), default=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='managed_business_units', null=True, blank=True, on_delete=models.SET_NULL)
    physical_location = models.ForeignKey(
        PhysicalLocation, related_name='business_unit_contexts', null=True, blank=True,
        on_delete=models.PROTECT,
    )
    shopping_name = models.CharField(_('Shopping / empreendimento'), max_length=160, blank=True)

    # Business channel (determines valid job functions for this unit)
    channel = models.ForeignKey('BusinessChannel', related_name='business_units', null=True, blank=True, on_delete=models.SET_NULL)

    # Endereço operacional
    endereco = models.CharField(_('Address'), max_length=255, blank=True)
    address_number = models.CharField(_('Número'), max_length=20, blank=True)
    address_complement = models.CharField(_('Complemento'), max_length=120, blank=True)
    neighborhood = models.CharField(_('Bairro'), max_length=120, blank=True)
    cep = models.CharField(_('CEP'), max_length=9, blank=True)
    city = models.CharField(_('City'), max_length=120, blank=True)
    state = models.CharField(_('State'), max_length=2, blank=True)

    # Contato direto
    telefone = models.CharField(_('Phone'), max_length=15, blank=True)
    email = models.EmailField(_('Email'), blank=True)
    contact_name = models.CharField(_('Responsável operacional'), max_length=160, blank=True)
    website = models.URLField(_('Website'), blank=True)
    tax_id = models.CharField(_('CNPJ da unidade'), max_length=18, blank=True)
    state_registration = models.CharField(_('Inscrição estadual'), max_length=30, blank=True)
    opening_hours = models.JSONField(_('Horário de funcionamento'), default=dict, blank=True)

    # Geolocalização (para match com candidatos)
    latitude = models.DecimalField(_('Latitude'), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_('Longitude'), max_digits=9, decimal_places=6, null=True, blank=True)

    # Flag para usar endereço da empresa na correspondência
    usar_endereco_empresa = models.BooleanField(
        _('Use Company Address for Correspondence'),
        default=False,
        help_text=_('If checked, use company address instead of this unit address')
    )

    class Meta:
        verbose_name = _('Business unit')
        verbose_name_plural = _('Business units')
        ordering = ('name',)

    def __str__(self):
        return self.name


class OperationalUnit(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, related_name='operational_units', on_delete=models.CASCADE)
    name = models.CharField(_('Name'), max_length=160)
    code = models.CharField(_('Code'), max_length=80, blank=True)
    active = models.BooleanField(_('Active'), default=True)

    class Meta:
        verbose_name = _('Operational unit')
        verbose_name_plural = _('Operational units')
        ordering = ('name',)

    def __str__(self):
        return self.name


class BusinessChannel(models.Model):
    company = models.ForeignKey(Company, related_name='channels', on_delete=models.CASCADE)
    name = models.CharField(_('Name'), max_length=120)
    active = models.BooleanField(_('Active'), default=True)

    class Meta:
        verbose_name = _('Business channel')
        verbose_name_plural = _('Business channels')
        ordering = ('name',)

    def __str__(self):
        return self.name


class JobFunction(models.Model):
    company = models.ForeignKey(Company, related_name='job_functions', on_delete=models.CASCADE)
    name = models.CharField(_('Name'), max_length=120)
    channels = models.ManyToManyField(BusinessChannel, related_name='job_functions', blank=True)
    active = models.BooleanField(_('Active'), default=True)

    class Meta:
        verbose_name = _('Job function')
        verbose_name_plural = _('Job functions')
        ordering = ('name',)

    def __str__(self):
        return self.name


class PersonType(models.Model):
    """Editable category of person for a tenant, independent of job function."""

    organization = models.ForeignKey(Organization, related_name='person_types', on_delete=models.CASCADE)
    code = models.SlugField(max_length=80)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('position', 'name')
        constraints = [models.UniqueConstraint(fields=('organization', 'code'), name='unique_person_type_per_organization')]

    def __str__(self):
        return self.name


class Membership(models.Model):
    """User's access in an organization with role and scope"""

    ROLE_CHOICES = (
        ('owner', _('Proprietário')),
        ('admin', _('Administrador')),
        ('member', _('Membro')),
        ('guest', _('Convidado')),
        ('viewer', _('Visualizador')),
    )

    COMPLIANCE_STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('overdue', _('Overdue')),
        ('failed', _('Failed')),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='memberships', on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, related_name='memberships', on_delete=models.CASCADE)
    company = models.ForeignKey(Company, related_name='memberships', null=True, blank=True, on_delete=models.CASCADE)
    business_unit = models.ForeignKey(BusinessUnit, related_name='memberships', null=True, blank=True, on_delete=models.CASCADE)
    operational_unit = models.ForeignKey(OperationalUnit, related_name='memberships', null=True, blank=True, on_delete=models.CASCADE)
    channels = models.ManyToManyField(BusinessChannel, related_name='memberships', blank=True)
    functions = models.ManyToManyField(JobFunction, related_name='memberships', blank=True)
    person_type = models.ForeignKey(PersonType, related_name='memberships', null=True, blank=True, on_delete=models.SET_NULL)

    # Role & Permissions
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default='member')

    # Membership state
    is_primary = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    # Compliance
    compliance_status = models.CharField(
        max_length=20,
        choices=COMPLIANCE_STATUS_CHOICES,
        default='pending',
        help_text=_('Compliance training status for this membership')
    )
    compliance_due_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When compliance training must be completed by')
    )
    compliance_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When user completed all compliance trainings')
    )

    # Audit trail
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='memberships_created', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='memberships_updated', null=True, blank=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Membership')
        verbose_name_plural = _('Memberships')
        constraints = [
            models.UniqueConstraint(fields=('user', 'company', 'business_unit', 'operational_unit'), name='unique_user_membership_scope'),
            models.UniqueConstraint(fields=('user',), condition=models.Q(is_primary=True), name='one_primary_per_user'),
        ]
        indexes = [
            models.Index(fields=['user', 'active']),
            models.Index(fields=['organization', 'active']),
            models.Index(fields=['user', 'organization']),
        ]

    def __str__(self):
        return f'{self.user} · {self.company} ({self.get_role_display()})'

    def clean(self):
        errors = {}
        if self.company_id and self.company.organization_id != self.organization_id:
            errors['company'] = _('A empresa precisa pertencer à organização da associação.')
        if self.business_unit_id:
            if self.business_unit.company.organization_id != self.organization_id:
                errors['business_unit'] = _('A unidade precisa pertencer à organização da associação.')
            if self.company_id and self.business_unit.company_id != self.company_id:
                errors['business_unit'] = _('A unidade precisa pertencer à empresa selecionada.')
        if self.operational_unit_id:
            if not self.business_unit_id or self.operational_unit.business_unit_id != self.business_unit_id:
                errors['operational_unit'] = _('A área precisa pertencer à unidade selecionada.')
        if self.person_type_id and self.person_type.organization_id != self.organization_id:
            errors['person_type'] = _('O tipo de público precisa pertencer à organização da associação.')
        if errors:
            raise ValidationError(errors)


class MembershipAudit(models.Model):
    """Complete audit trail of all membership changes"""

    ACTION_CHOICES = (
        ('created', _('Criado')),
        ('updated', _('Atualizado')),
        ('role_changed', _('Função alterada')),
        ('scope_changed', _('Escopo alterado')),
        ('activated', _('Ativado')),
        ('deactivated', _('Desativado')),
        ('deleted', _('Deletado')),
    )

    membership = models.ForeignKey(Membership, related_name='audit_logs', null=True, blank=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='membership_audit_logs', on_delete=models.PROTECT)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    reason = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Membership Audit')
        verbose_name_plural = _('Membership Audits')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['membership', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]

    def __str__(self):
        return f'{self.membership} · {self.get_action_display()} · {self.created_at}'


class TenantContextEvent(models.Model):
    """Append-only history of the tenant context used by an account.

    A context switch does not change memberships.  It only changes the
    workspace currently selected in the session, so it needs its own event
    stream to answer where a person was operating at a given time.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='tenant_context_events', on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='tenant_context_events_created', null=True, blank=True, on_delete=models.SET_NULL)
    from_organization = models.ForeignKey(Organization, related_name='+', null=True, blank=True, on_delete=models.SET_NULL)
    to_organization = models.ForeignKey(Organization, related_name='+', null=True, blank=True, on_delete=models.SET_NULL)
    from_company = models.ForeignKey(Company, related_name='+', null=True, blank=True, on_delete=models.SET_NULL)
    to_company = models.ForeignKey(Company, related_name='+', null=True, blank=True, on_delete=models.SET_NULL)
    from_membership = models.ForeignKey(Membership, related_name='+', null=True, blank=True, on_delete=models.SET_NULL)
    to_membership = models.ForeignKey(Membership, related_name='+', null=True, blank=True, on_delete=models.SET_NULL)
    reason = models.CharField(max_length=80, default='workspace_switch')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['to_organization', '-created_at']),
        ]


class ManagementAssignment(models.Model):
    """Defines who can administer people and reports inside an enterprise scope."""

    ROLE_CHOICES = (
        ('people_admin', _('Administrador de usuários')),
        ('report_viewer', _('Visualizador de relatórios')),
        ('audience_manager', _('Administrador de audiência')),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='management_assignments', on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, related_name='management_assignments', on_delete=models.CASCADE)
    company = models.ForeignKey(Company, null=True, blank=True, related_name='management_assignments', on_delete=models.CASCADE)
    business_unit = models.ForeignKey(BusinessUnit, null=True, blank=True, related_name='management_assignments', on_delete=models.CASCADE)
    operational_unit = models.ForeignKey(OperationalUnit, null=True, blank=True, related_name='management_assignments', on_delete=models.CASCADE)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('user__username', 'organization__name', 'company__name')

    def __str__(self):
        scope = self.operational_unit or self.business_unit or self.company or self.organization
        return f'{self.user} · {self.get_role_display()} · {scope}'


class Partner(models.Model):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'
    STATUS_CHOICES = ((ACTIVE, _('Ativo')), (INACTIVE, _('Inativo')), (SUSPENDED, _('Suspenso')))

    organization = models.ForeignKey(Organization, related_name='partners', on_delete=models.CASCADE)
    company = models.ForeignKey(Company, null=True, blank=True, related_name='partners', on_delete=models.SET_NULL)
    name = models.CharField(max_length=180)
    email = models.EmailField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=ACTIVE)
    assigned_manager = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='managed_partners', on_delete=models.SET_NULL)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)
        constraints = [models.UniqueConstraint(fields=('organization', 'name'), name='unique_partner_per_organization')]

    def __str__(self):
        return self.name


class PartnerMembership(models.Model):
    VIEWER = 'viewer'
    MANAGER = 'manager'
    ROLE_CHOICES = ((VIEWER, _('Visualizador')), (MANAGER, _('Gestor')))
    partner = models.ForeignKey(Partner, related_name='memberships', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='partner_memberships', on_delete=models.CASCADE)
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=VIEWER)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('partner', 'user'), name='unique_partner_membership')]


class IntegrationCredential(models.Model):
    """Hashed API credential scoped to one tenant and a finite set of capabilities."""

    organization = models.ForeignKey(Organization, related_name='integration_credentials', on_delete=models.CASCADE)
    partner = models.ForeignKey(Partner, null=True, blank=True, related_name='integration_credentials', on_delete=models.SET_NULL)
    name = models.CharField(max_length=160)
    key_prefix = models.CharField(max_length=16, db_index=True)
    key_hash = models.CharField(max_length=64, unique=True)
    scopes = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='integration_credentials_created', on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    rotated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)

    @staticmethod
    def hash_key(raw_key):
        return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

    @classmethod
    def issue(cls, *, organization, name, created_by, scopes=None, expires_at=None):
        raw_key = f'matchco_{secrets.token_urlsafe(32)}'
        credential = cls.objects.create(
            organization=organization,
            name=name,
            key_prefix=raw_key[:12],
            key_hash=cls.hash_key(raw_key),
            scopes=scopes or [],
            created_by=created_by,
            expires_at=expires_at,
        )
        return credential, raw_key

    def rotate(self):
        raw_key = f'matchco_{secrets.token_urlsafe(32)}'
        self.key_prefix = raw_key[:12]
        self.key_hash = self.hash_key(raw_key)
        self.rotated_at = datetime.datetime.now(datetime.timezone.utc)
        self.last_used_at = None
        self.save(update_fields=('key_prefix', 'key_hash', 'rotated_at', 'last_used_at'))
        return raw_key

    def allows(self, scope):
        return 'all' in self.scopes or scope in self.scopes


class IntegrationConnection(models.Model):
    """Configured provider connection; secrets stay outside normal settings."""

    HRIS = 'hris'
    CRM = 'crm'
    LMS = 'lms'
    SSO = 'sso'
    NOTIFICATIONS = 'notifications'
    TYPE_CHOICES = (
        (HRIS, _('HRIS / folha')),
        (CRM, _('CRM / canal')),
        (LMS, _('LMS externo')),
        (SSO, _('SSO / identidade')),
        (NOTIFICATIONS, _('Notificações')),
    )
    DRAFT = 'draft'
    TESTING = 'testing'
    ACTIVE = 'active'
    DISABLED = 'disabled'
    STATUS_CHOICES = (
        (DRAFT, _('Rascunho')), (TESTING, _('Em teste')),
        (ACTIVE, _('Ativa')), (DISABLED, _('Desativada')),
    )
    organization = models.ForeignKey(Organization, related_name='integration_connections', on_delete=models.CASCADE)
    name = models.CharField(max_length=160)
    connection_type = models.CharField(max_length=24, choices=TYPE_CHOICES)
    provider = models.CharField(max_length=80)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=DRAFT)
    base_url = models.URLField(blank=True)
    configuration = models.JSONField(default=dict, blank=True)
    secret_reference = models.CharField(max_length=240, blank=True)
    scopes = models.JSONField(default=list, blank=True)
    last_tested_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='integration_connections_created', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('connection_type', 'name')
        constraints = [models.UniqueConstraint(fields=('organization', 'name'), name='unique_integration_connection_per_org')]

    def __str__(self):
        return f'{self.organization} · {self.name}'


class WebhookSubscription(models.Model):
    """Outbound event destination owned by an organization."""

    organization = models.ForeignKey(Organization, related_name='webhook_subscriptions', on_delete=models.CASCADE)
    name = models.CharField(max_length=160)
    endpoint = models.URLField(max_length=1000)
    secret = models.CharField(max_length=180, blank=True)
    events = models.JSONField(default=list, blank=True)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='webhook_subscriptions_created', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    last_delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('name',)


class WebhookDelivery(models.Model):
    PENDING = 'pending'
    SENT = 'sent'
    FAILED = 'failed'
    STATUS_CHOICES = ((PENDING, _('Pendente')), (SENT, _('Enviada')), (FAILED, _('Falhou')))
    subscription = models.ForeignKey(WebhookSubscription, related_name='deliveries', on_delete=models.CASCADE)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=PENDING)
    attempts = models.PositiveIntegerField(default=0)
    response_code = models.PositiveSmallIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [models.Index(fields=('status', 'created_at')), models.Index(fields=('subscription', 'created_at'))]


class UserGroup(models.Model):
    """Groups of users with relationships (parents, alumni, departments)"""

    GROUP_TYPE_CHOICES = (
        ('parents', _('Parents/Guardians')),
        ('alumni', _('Alumni/Graduates')),
        ('department', _('Department')),
        ('custom', _('Custom Group')),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='user_groups'
    )
    name = models.CharField(_('Name'), max_length=200)
    slug = models.SlugField(_('Slug'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    group_type = models.CharField(
        _('Group Type'),
        max_length=20,
        choices=GROUP_TYPE_CHOICES,
        default='custom'
    )

    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('Custom data: {graduation_year, school_name, etc}')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('User Group')
        verbose_name_plural = _('User Groups')
        unique_together = [['organization', 'slug']]
        ordering = ['group_type', 'name']
        indexes = [
            models.Index(fields=['organization', 'group_type']),
            models.Index(fields=['organization', 'slug']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_group_type_display()})"


class GroupMembership(models.Model):
    """User membership in groups"""

    ROLE_CHOICES = (
        ('admin', _('Group Admin')),
        ('member', _('Member')),
        ('viewer', _('Viewer Only')),
    )

    STATUS_CHOICES = (
        ('active', _('Active')),
        ('pending', _('Pending Approval')),
        ('inactive', _('Inactive')),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='group_memberships'
    )
    group = models.ForeignKey(
        UserGroup,
        on_delete=models.CASCADE,
        related_name='members'
    )

    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='member'
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    linked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='group_linked_by',
        help_text=_('For parent groups: link to student')
    )

    joined_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='group_memberships_created'
    )

    class Meta:
        verbose_name = _('Group Membership')
        verbose_name_plural = _('Group Memberships')
        ordering = ['-joined_at']
        indexes = [
            models.Index(fields=['group', 'status']),
            models.Index(fields=['user', 'status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'group', 'linked_user'],
                name='unique_group_membership_with_link'
            ),
        ]

    def __str__(self):
        return f"{self.user.email} → {self.group.name}"


class GroupAccess(models.Model):
    """Content access permissions for groups"""

    ACCESS_LEVEL_CHOICES = (
        ('none', _('No Access')),
        ('view', _('View Only')),
        ('view_progress', _('View Progress')),
        ('download', _('Download')),
        ('manage', _('Full Access')),
    )

    CONTENT_TYPE_CHOICES = (
        ('trail', _('Trail')),
        ('course', _('Course')),
        ('publication', _('Publication')),
        ('organization', _('All Organization Content')),
    )

    group = models.ForeignKey(
        UserGroup,
        on_delete=models.CASCADE,
        related_name='access_rules'
    )

    content_type = models.CharField(
        _('Content Type'),
        max_length=50,
        choices=CONTENT_TYPE_CHOICES,
        help_text=_('Type of content to grant access to')
    )

    object_id = models.IntegerField(
        _('Object ID'),
        null=True,
        blank=True,
        help_text=_('ID of Trail/Course/Publication (null for all)')
    )

    access_level = models.CharField(
        _('Access Level'),
        max_length=20,
        choices=ACCESS_LEVEL_CHOICES,
        default='view'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='group_access_rules_created'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Group Access')
        verbose_name_plural = _('Group Access Rules')
        unique_together = [['group', 'content_type', 'object_id']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['group', 'content_type']),
        ]

    def __str__(self):
        content = self.get_content_type_display()
        access = self.get_access_level_display()
        return f"{self.group.name} → {content}: {access}"


class GroupHierarchyType(models.Model):
    """Generic hierarchy type (parents, alumni, departments, custom) with configurable labels."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='group_hierarchy_types'
    )
    code = models.SlugField(_('Code'), max_length=100)
    name = models.CharField(_('Name'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    max_levels = models.PositiveIntegerField(
        _('Max Levels'),
        default=3,
        help_text=_('Maximum hierarchy depth (e.g., 3 for L1→L2→L3)')
    )
    allow_links = models.BooleanField(
        _('Allow User Linking'),
        default=False,
        help_text=_('If True, can use linked_user field (e.g., parent→student)')
    )
    auto_create_on = models.CharField(
        _('Auto Create Trigger'),
        max_length=100,
        blank=True,
        default='',
        help_text=_('Signal trigger for auto-creation (e.g., "graduation", or empty for manual)')
    )
    active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Group Hierarchy Type')
        verbose_name_plural = _('Group Hierarchy Types')
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'code'],
                name='unique_hierarchy_type_per_org'
            ),
        ]
        ordering = ['organization', 'code']
        indexes = [
            models.Index(fields=['organization', 'active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class GroupHierarchyTerminology(models.Model):
    """Configurable labels for each hierarchy type (like OrganizationTerminology)."""

    hierarchy_type = models.OneToOneField(
        GroupHierarchyType,
        on_delete=models.CASCADE,
        related_name='terminology'
    )
    level_1_label = models.CharField(
        _('Level 1 Label'),
        max_length=100,
        default=_('Level 1')
    )
    level_1_description = models.CharField(
        _('Level 1 Description'),
        max_length=300,
        blank=True,
        default=''
    )
    level_2_label = models.CharField(
        _('Level 2 Label'),
        max_length=100,
        default=_('Level 2')
    )
    level_2_description = models.CharField(
        _('Level 2 Description'),
        max_length=300,
        blank=True,
        default=''
    )
    level_3_label = models.CharField(
        _('Level 3 Label'),
        max_length=100,
        default=_('Level 3')
    )
    level_3_description = models.CharField(
        _('Level 3 Description'),
        max_length=300,
        blank=True,
        default=''
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Group Hierarchy Terminology')
        verbose_name_plural = _('Group Hierarchy Terminologies')

    def __str__(self):
        return f"Terminology for {self.hierarchy_type.name}"


class GroupNode(models.Model):
    """Node in a hierarchical group structure (replaces UserGroup for new system)."""

    hierarchy_type = models.ForeignKey(
        GroupHierarchyType,
        on_delete=models.CASCADE,
        related_name='nodes'
    )
    parent_node = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text=_('Parent node in hierarchy (null for root)')
    )
    name = models.CharField(_('Name'), max_length=200)
    code = models.CharField(_('Code'), max_length=100, blank=True)
    description = models.TextField(_('Description'), blank=True)
    level = models.PositiveIntegerField(
        _('Level'),
        default=1,
        help_text=_('Hierarchy level (1=root, 2=under root, etc.)')
    )
    position = models.PositiveIntegerField(
        _('Position'),
        default=0,
        help_text=_('Display order within same parent')
    )
    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('Custom data: graduation_year, manager_id, etc.')
    )
    active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Group Node')
        verbose_name_plural = _('Group Nodes')
        constraints = [
            models.UniqueConstraint(
                fields=['hierarchy_type', 'parent_node', 'code'],
                name='unique_node_per_parent'
            ),
        ]
        ordering = ['hierarchy_type', 'position', 'name']
        indexes = [
            models.Index(fields=['hierarchy_type', 'parent_node']),
            models.Index(fields=['hierarchy_type', 'active']),
            models.Index(fields=['parent_node', 'active']),
        ]

    def __str__(self):
        return f"{self.name} (Level {self.level})"

    def get_root(self):
        """Get the root node of this hierarchy."""
        node = self
        while node.parent_node:
            node = node.parent_node
        return node

    def get_ancestors(self):
        """Get all ancestor nodes (parents up to root)."""
        ancestors = []
        node = self
        while node.parent_node:
            ancestors.append(node.parent_node)
            node = node.parent_node
        return ancestors


class UserGroupMembership(models.Model):
    """Generic user membership in a group node (replaces GroupMembership for new system)."""

    ROLE_CHOICES = (
        ('admin', _('Group Admin')),
        ('member', _('Member')),
        ('viewer', _('Viewer Only')),
    )

    STATUS_CHOICES = (
        ('active', _('Active')),
        ('pending', _('Pending Approval')),
        ('inactive', _('Inactive')),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hierarchy_memberships'
    )
    group_node = models.ForeignKey(
        GroupNode,
        on_delete=models.CASCADE,
        related_name='members'
    )
    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='member'
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    linked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_by_hierarchy',
        help_text=_('For relationships like parent→student, manager→direct report')
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hierarchy_memberships_created'
    )

    class Meta:
        verbose_name = _('User Group Hierarchy Membership')
        verbose_name_plural = _('User Group Hierarchy Memberships')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'group_node', 'linked_user'],
                name='unique_hierarchy_membership_with_link'
            ),
        ]
        ordering = ['-joined_at']
        indexes = [
            models.Index(fields=['group_node', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'group_node']),
        ]

    def __str__(self):
        if self.linked_user:
            return f"{self.user.email} → {self.group_node.name} (linked to {self.linked_user.email})"
        return f"{self.user.email} → {self.group_node.name}"


class GroupNodeAccess(models.Model):
    """Content access permissions for group nodes (replaces GroupAccess for new system)."""

    ACCESS_LEVEL_CHOICES = (
        ('none', _('No Access')),
        ('view', _('View Only')),
        ('view_progress', _('View Progress')),
        ('download', _('Download')),
        ('manage', _('Full Access')),
    )

    CONTENT_TYPE_CHOICES = (
        ('trail', _('Trail')),
        ('course', _('Course')),
        ('publication', _('Publication')),
        ('organization', _('All Organization Content')),
    )

    group_node = models.ForeignKey(
        GroupNode,
        on_delete=models.CASCADE,
        related_name='access_rules'
    )
    content_type = models.CharField(
        _('Content Type'),
        max_length=50,
        choices=CONTENT_TYPE_CHOICES,
        help_text=_('Type of content to grant access to')
    )
    object_id = models.IntegerField(
        _('Object ID'),
        null=True,
        blank=True,
        help_text=_('ID of Trail/Course/Publication (null for all)')
    )
    access_level = models.CharField(
        _('Access Level'),
        max_length=20,
        choices=ACCESS_LEVEL_CHOICES,
        default='view'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='group_node_access_rules_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Group Node Access')
        verbose_name_plural = _('Group Node Access Rules')
        constraints = [
            models.UniqueConstraint(
                fields=['group_node', 'content_type', 'object_id'],
                name='unique_node_access_rule'
            ),
        ]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['group_node', 'content_type']),
        ]

    def __str__(self):
        content = self.get_content_type_display()
        access = self.get_access_level_display()
        return f"{self.group_node.name} → {content}: {access}"


class CustomEntry(models.Model):
    body = models.TextField(verbose_name=_('body'))
    tags = models.ManyToManyField('publishing.Tag', blank=True, related_name='configuration_entries')
    date = models.DateTimeField(verbose_name=_('Post date'), default=datetime.datetime.today)
    header_image = models.ImageField(upload_to='configuration/headers/', verbose_name=_('Header image'), null=True, blank=True)
    video = models.ForeignKey('videos.VideoContent', null=True, blank=True, on_delete=models.SET_NULL, related_name='entry', verbose_name=_('Video'))
    categories = models.ManyToManyField('publishing.Tag', blank=True, related_name='configuration_categories')
    excerpt = models.TextField(verbose_name=_('excerpt'), blank=True)
    num_comments = models.IntegerField(default=0, editable=False)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.CASCADE)
    company_ids = models.ManyToManyField(Company, verbose_name=_('Companies'), blank=True)
    business_unit_ids = models.ManyToManyField(BusinessUnit, verbose_name=_('Business units'), blank=True)
    operational_unit_ids = models.ManyToManyField(OperationalUnit, verbose_name=_('Operational units'), blank=True)
    channel_ids = models.ManyToManyField(BusinessChannel, verbose_name=_('Business channels'), blank=True)
    function_ids = models.ManyToManyField(JobFunction, verbose_name=_('Job functions'), blank=True)

    class Meta:
        abstract = True


class HierarchyAuditLog(models.Model):
    """Audit log for hierarchy management actions (Company, BusinessUnit, OperationalUnit)."""

    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_INACTIVATE = 'inactivate'
    ACTION_ACTIVATE = 'activate'
    ACTION_DELETE = 'delete'

    ACTION_CHOICES = [
        (ACTION_CREATE, _('Created')),
        (ACTION_UPDATE, _('Updated')),
        (ACTION_INACTIVATE, _('Inactivated')),
        (ACTION_ACTIVATE, _('Activated')),
        (ACTION_DELETE, _('Deleted')),
    ]

    RESOURCE_COMPANY = 'company'
    RESOURCE_BUSINESS_UNIT = 'business_unit'
    RESOURCE_OPERATIONAL_UNIT = 'operational_unit'

    RESOURCE_CHOICES = [
        (RESOURCE_COMPANY, _('Company')),
        (RESOURCE_BUSINESS_UNIT, _('Business Unit')),
        (RESOURCE_OPERATIONAL_UNIT, _('Operational Unit')),
    ]

    organization = models.ForeignKey(
        Organization,
        related_name='hierarchy_audit_logs',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name='hierarchy_audit_logs',
        on_delete=models.SET_NULL,
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_CHOICES)
    resource_id = models.PositiveIntegerField()
    resource_name = models.CharField(max_length=160, help_text=_('Name of the resource for display'))
    
    # Details of what changed
    changes = models.JSONField(default=dict, blank=True, help_text=_('Before/after values of changed fields'))
    reason = models.TextField(blank=True, help_text=_('Reason for the action (e.g., "Company closure")'))
    
    # Cascade info
    affected_count = models.PositiveIntegerField(default=1, help_text=_('Number of related resources affected (for cascading actions)'))
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', '-created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
        verbose_name = _('Hierarchy Audit Log')
        verbose_name_plural = _('Hierarchy Audit Logs')

    def __str__(self):
        return f'{self.get_action_display()} {self.get_resource_type_display()} "{self.resource_name}" at {self.created_at.strftime("%Y-%m-%d %H:%M")}'

    @classmethod
    def log_action(cls, organization, user, action, resource_type, resource_id, resource_name, changes=None, reason='', affected_count=1):
        """Create an audit log entry."""
        return cls.objects.create(
            organization=organization,
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            changes=changes or {},
            reason=reason,
            affected_count=affected_count,
        )
