import datetime
import hashlib
import random
import secrets

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


def random_indication_code():
    return str(random.randint(100000, 999999))


class Organization(models.Model):
    name = models.CharField(_('Name'), max_length=160)
    slug = models.SlugField(_('Slug'), max_length=180, unique=True)
    description = models.TextField(_('Description'), blank=True, default='')
    active = models.BooleanField(_('Active'), default=True)
    is_public = models.BooleanField(
        _('Public'),
        default=False,
        help_text=_('Public organizations are for external users (candidates, doctors, partners, students)')
    )

    class Meta:
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')
        ordering = ['-is_public', 'name']

    def __str__(self):
        return self.name


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
        verbose_name = 'Terminologia da organização'
        verbose_name_plural = 'Terminologia das organizações'

    def __str__(self):
        return f'{self.organization} · terminologia'


class Company(models.Model):
    organization = models.ForeignKey(Organization, related_name='companies', null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(_('Name'), max_length=160)
    code = models.CharField(_('Code'), max_length=80, blank=True)
    active = models.BooleanField(_('Active'), default=True)

    class Meta:
        verbose_name = _('Company')
        verbose_name_plural = _('Companies')
        ordering = ('name',)
        constraints = [models.UniqueConstraint(fields=('organization', 'name'), name='unique_company_per_organization')]

    def __str__(self):
        return self.name


class BusinessUnit(models.Model):
    company = models.ForeignKey(Company, related_name='business_units', on_delete=models.CASCADE)
    name = models.CharField(_('Name'), max_length=160)
    code = models.CharField(_('Code'), max_length=80, blank=True)
    active = models.BooleanField(_('Active'), default=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='managed_business_units', null=True, blank=True, on_delete=models.SET_NULL)

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
        ('owner', 'Proprietário'),
        ('admin', 'Administrador'),
        ('member', 'Membro'),
        ('guest', 'Convidado'),
        ('viewer', 'Visualizador'),
    )

    COMPLIANCE_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('failed', 'Failed'),
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


class MembershipAudit(models.Model):
    """Complete audit trail of all membership changes"""

    ACTION_CHOICES = (
        ('created', 'Criado'),
        ('updated', 'Atualizado'),
        ('role_changed', 'Função alterada'),
        ('scope_changed', 'Escopo alterado'),
        ('activated', 'Ativado'),
        ('deactivated', 'Desativado'),
        ('deleted', 'Deletado'),
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


class ManagementAssignment(models.Model):
    """Defines who can administer people and reports inside an enterprise scope."""

    ROLE_CHOICES = (
        ('people_admin', 'Administrador de usuários'),
        ('report_viewer', 'Visualizador de relatórios'),
        ('audience_manager', 'Administrador de audiência'),
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
    STATUS_CHOICES = ((ACTIVE, 'Ativo'), (INACTIVE, 'Inativo'), (SUSPENDED, 'Suspenso'))

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
    ROLE_CHOICES = ((VIEWER, 'Visualizador'), (MANAGER, 'Gestor'))
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
        raw_key = f'talk_{secrets.token_urlsafe(32)}'
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
        raw_key = f'talk_{secrets.token_urlsafe(32)}'
        self.key_prefix = raw_key[:12]
        self.key_hash = self.hash_key(raw_key)
        self.rotated_at = datetime.datetime.now(datetime.timezone.utc)
        self.last_used_at = None
        self.save(update_fields=('key_prefix', 'key_hash', 'rotated_at', 'last_used_at'))
        return raw_key

    def allows(self, scope):
        return 'all' in self.scopes or scope in self.scopes


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
    STATUS_CHOICES = ((PENDING, 'Pendente'), (SENT, 'Enviada'), (FAILED, 'Falhou'))
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
