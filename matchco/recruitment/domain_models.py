"""Persistence owned by recruitment.

These models intentionally store stable external identifiers instead of using
foreign keys to configuration. The ``legacy_id`` fields are only migration
bridges and can be removed after the old installation is retired.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class RecruitmentPhysicalUnit(models.Model):
    """Real-world location shared by one or more commercial representations."""

    external_key = models.CharField(max_length=160, unique=True)
    name = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=9, blank=True)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=2, blank=True)
    active = models.BooleanField(default=True, db_index=True)
    candidate_response_hours_override = models.PositiveIntegerField(null=True, blank=True)
    employer_decision_hours_override = models.PositiveIntegerField(null=True, blank=True)
    invite_batch_size_override = models.PositiveIntegerField(null=True, blank=True)
    round_wait_hours_override = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name', 'id']
        verbose_name = _('Recruitment physical unit')
        verbose_name_plural = _('Recruitment physical units')

    def __str__(self):
        return self.name


class RecruitmentOrganization(models.Model):
    legacy_id = models.PositiveIntegerField(null=True, blank=True, unique=True, db_index=True)
    external_id = models.CharField(max_length=160, unique=True)
    slug = models.SlugField(max_length=160, unique=True)
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Recruitment organization')
        verbose_name_plural = _('Recruitment organizations')

    def __str__(self):
        return self.name


class RecruitmentOrganizationRelation(models.Model):
    """Explicit relationship between tenant-level commercial organizations."""

    RELATION_SPONSOR = 'sponsor'
    RELATION_NETWORK = 'network'
    RELATION_OPERATOR = 'operator'
    RELATION_BRAND = 'brand'
    RELATION_PARTNER = 'partner'
    RELATION_CHOICES = [
        (RELATION_SPONSOR, _('Sponsor / shopping')),
        (RELATION_NETWORK, _('Rede')),
        (RELATION_OPERATOR, _('Operadora')),
        (RELATION_BRAND, _('Marca')),
        (RELATION_PARTNER, _('Parceira')),
    ]

    organization = models.ForeignKey(
        RecruitmentOrganization, related_name='outgoing_relations', on_delete=models.CASCADE,
    )
    related_organization = models.ForeignKey(
        RecruitmentOrganization, related_name='incoming_relations', on_delete=models.CASCADE,
    )
    relation_type = models.CharField(max_length=20, choices=RELATION_CHOICES)
    active = models.BooleanField(default=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['organization__name', 'related_organization__name']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'related_organization', 'relation_type'],
                name='uniq_recruitment_org_relation',
            ),
        ]

    def clean(self):
        if self.organization_id and self.organization_id == self.related_organization_id:
            raise ValidationError({'related_organization': _('Uma organização não pode se relacionar consigo mesma.')})

    def __str__(self):
        return f'{self.organization} · {self.get_relation_type_display()} · {self.related_organization}'


class RecruitmentPlatformBinding(models.Model):
    """Explicit bridge to the shared Talk/courses tenant context.

    ``platform_organization_id`` deliberately remains an identifier instead
    of a cross-schema FK. The binding is the only approved bridge and can be
    revoked without copying recruitment data into courses or Talk.
    """

    recruitment_organization = models.ForeignKey(
        RecruitmentOrganization, related_name='platform_bindings', on_delete=models.CASCADE,
    )
    platform_organization_id = models.PositiveIntegerField(db_index=True)
    capabilities = models.JSONField(
        default=list, blank=True,
        help_text=_('Capacidades liberadas: talk, courses, certifications, audiences.'),
    )
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['recruitment_organization__name', 'platform_organization_id']
        constraints = [
            models.UniqueConstraint(
                fields=['recruitment_organization', 'platform_organization_id'],
                name='uniq_recruitment_platform_binding',
            ),
        ]

    def __str__(self):
        return f'{self.recruitment_organization} → plataforma {self.platform_organization_id}'


class RecruitmentCompany(models.Model):
    organization = models.ForeignKey(RecruitmentOrganization, related_name='companies', on_delete=models.CASCADE)
    legacy_id = models.PositiveIntegerField(null=True, blank=True, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=80, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        unique_together = [('organization', 'name')]

    def __str__(self):
        return self.name

class RecruitmentChannel(models.Model):
    company = models.ForeignKey(RecruitmentCompany, related_name='channels', on_delete=models.CASCADE)
    legacy_id = models.PositiveIntegerField(null=True, blank=True, unique=True, db_index=True)
    name = models.CharField(max_length=160)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        unique_together = [('company', 'name')]

    def __str__(self):
        return self.name

class RecruitmentStore(models.Model):
    organization = models.ForeignKey(RecruitmentOrganization, related_name='stores', on_delete=models.CASCADE)
    company = models.ForeignKey(RecruitmentCompany, related_name='stores', on_delete=models.CASCADE)
    channel = models.ForeignKey(RecruitmentChannel, null=True, blank=True, related_name='stores', on_delete=models.SET_NULL)
    physical_unit = models.ForeignKey(
        RecruitmentPhysicalUnit, null=True, blank=True,
        related_name='representations', on_delete=models.PROTECT,
    )
    legacy_id = models.PositiveIntegerField(null=True, blank=True, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=80, blank=True)
    active = models.BooleanField(default=True, db_index=True)
    postal_code = models.CharField(max_length=9, blank=True, db_index=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    candidate_response_hours_override = models.PositiveIntegerField(null=True, blank=True)
    employer_decision_hours_override = models.PositiveIntegerField(null=True, blank=True)
    invite_batch_size_override = models.PositiveIntegerField(null=True, blank=True)
    round_wait_hours_override = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['name']
        unique_together = [('company', 'name')]

    def __str__(self):
        return self.name

    def clean(self):
        errors = {}
        if self.company_id and self.company.organization_id != self.organization_id:
            errors['company'] = _('A empresa deve pertencer à organização da unidade.')
        if self.channel_id and self.channel.company_id != self.company_id:
            errors['channel'] = _('O canal deve pertencer à empresa da unidade.')
        if errors:
            raise ValidationError(errors)


class RecruitmentJobFunction(models.Model):
    organization = models.ForeignKey(RecruitmentOrganization, related_name='job_functions', on_delete=models.CASCADE)
    company = models.ForeignKey(RecruitmentCompany, related_name='job_functions', on_delete=models.CASCADE)
    legacy_id = models.PositiveIntegerField(null=True, blank=True, unique=True, db_index=True)
    name = models.CharField(max_length=160)
    active = models.BooleanField(default=True, db_index=True)
    channels = models.ManyToManyField(RecruitmentChannel, related_name='job_functions', blank=True)

    class Meta:
        ordering = ['name']
        unique_together = [('company', 'name')]

    def __str__(self):
        return self.name

    def clean(self):
        if self.company_id and self.company.organization_id != self.organization_id:
            raise ValidationError({'company': _('A função deve pertencer à organização da empresa.')})
