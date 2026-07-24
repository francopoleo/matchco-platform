import datetime
import random

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


def random_indication_code():
    return str(random.randint(100000, 999999))


class Organization(models.Model):
    name = models.CharField(_('Name'), max_length=160)
    slug = models.SlugField(_('Slug'), max_length=180, unique=True)
    active = models.BooleanField(_('Active'), default=True)

    class Meta:
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')
        ordering = ('name',)

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='memberships', on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, related_name='memberships', on_delete=models.CASCADE)
    company = models.ForeignKey(Company, related_name='memberships', on_delete=models.CASCADE)
    business_unit = models.ForeignKey(BusinessUnit, related_name='memberships', null=True, blank=True, on_delete=models.CASCADE)
    operational_unit = models.ForeignKey(OperationalUnit, related_name='memberships', null=True, blank=True, on_delete=models.CASCADE)
    channels = models.ManyToManyField(BusinessChannel, related_name='memberships', blank=True)
    functions = models.ManyToManyField(JobFunction, related_name='memberships', blank=True)
    person_type = models.ForeignKey(PersonType, related_name='memberships', null=True, blank=True, on_delete=models.SET_NULL)
    is_primary = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Membership')
        verbose_name_plural = _('Memberships')
        constraints = [models.UniqueConstraint(fields=('user', 'company', 'business_unit', 'operational_unit'), name='unique_user_membership_scope')]

    def __str__(self):
        return f'{self.user} · {self.company}'


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
