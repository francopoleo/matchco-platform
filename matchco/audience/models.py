from django.db import models

from tenants_core.models import TenantOrganization


class AudiencePolicy(models.Model):
    """Reusable, backend-owned rules that define who can see content."""

    ALL = 'all'
    ANY = 'any'
    MATCH_MODES = (
        (ALL, 'All rules'),
        (ANY, 'Any rule'),
    )

    name = models.CharField(max_length=160)
    organization = models.ForeignKey(TenantOrganization, null=True, blank=True, related_name='audience_policies', on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    match_mode = models.CharField(max_length=3, choices=MATCH_MODES, default=ALL)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class AudienceRule(models.Model):
    """One atomic audience condition.

    Values are stored as identifiers rather than model objects so the policy
    engine remains independent from CMS/admin implementations.
    """

    policy = models.ForeignKey(
        AudiencePolicy,
        related_name='rules',
        on_delete=models.CASCADE,
    )
    dimension = models.CharField(max_length=64)
    operator = models.CharField(max_length=32, default='in')
    values = models.JSONField(default=list)
    negate = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)

    TENANT = 'organization'
    COMPANY = 'company'
    BUSINESS_UNIT = 'business_unit'
    OPERATIONAL_UNIT = 'operational_unit'
    CHANNEL = 'channel'
    FUNCTION = 'function'
    PROGRAM = 'program'
    PERSON_TYPE = 'person_type'
    MEMBERSHIP_ROLE = 'membership_role'
    DIMENSIONS = (TENANT, COMPANY, BUSINESS_UNIT, OPERATIONAL_UNIT, CHANNEL, FUNCTION, PROGRAM, PERSON_TYPE, MEMBERSHIP_ROLE)

    class Meta:
        ordering = ('position', 'id')

    def __str__(self):
        return f'{self.policy}: {self.dimension} {self.operator}'
