from configuration import random_indication_code
from django.contrib.auth.models import Group, AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    mobile = models.CharField(_('Mobile'), max_length=20, unique=True, blank=True, null=True)
    indication_code = models.CharField(_('Indication Code'), max_length=30, blank=True, null=True)
    is_demo = models.BooleanField(_('Demo account'), default=False)

    total_awarded_points = models.IntegerField(blank=True, null=True, verbose_name=_("Total awarded points"), default=0) 
    current_points = models.IntegerField(blank=True, null=True, verbose_name=_("Current points"), default=0)
    
    def save(self, *args, **kwargs):
        if not self.is_staff and not self.is_superuser:
            if not self.indication_code:
                self.indication_code = random_indication_code()

        if not self.email:
            self.email = self.username

        super(User, self).save(*args, **kwargs)

    def is_companyunit_manager_group(self):
        groups_user = list(self.groups.all())
        group_company_unit_manager = Group.objects.get(name='Company Unit Manager')

        return not self.is_superuser and group_company_unit_manager in groups_user

    def update_award_points(self, points):
        self.current_points += points
        
        if points > 0:
            self.total_awarded_points += points

        self.save()

    @property
    def primary_membership(self):
        return self.memberships.filter(active=True, is_primary=True).select_related(
            'organization', 'company', 'business_unit', 'operational_unit'
        ).first() or self.memberships.filter(active=True).select_related(
            'organization', 'company', 'business_unit', 'operational_unit'
        ).first()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    current_time_zone = models.CharField(max_length=64, blank=True, default='UTC')
    avatar = models.ImageField(upload_to='users/avatars/', blank=True, null=True)

    def __str__(self):
        return f'Profile: {self.user}'


class InvitationCode(models.Model):
    """A manager-issued code that opens a scoped registration request."""

    code = models.CharField(max_length=80, unique=True)
    organization = models.ForeignKey('configuration.Organization', on_delete=models.CASCADE, related_name='invitation_codes')
    company = models.ForeignKey('configuration.Company', null=True, blank=True, on_delete=models.CASCADE, related_name='invitation_codes')
    business_unit = models.ForeignKey('configuration.BusinessUnit', null=True, blank=True, on_delete=models.CASCADE, related_name='invitation_codes')
    operational_unit = models.ForeignKey('configuration.OperationalUnit', null=True, blank=True, on_delete=models.CASCADE, related_name='invitation_codes')
    person_type = models.ForeignKey('configuration.PersonType', null=True, blank=True, on_delete=models.SET_NULL, related_name='invitation_codes')
    issued_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='issued_invitation_codes')
    max_uses = models.PositiveIntegerField(default=1)
    uses_count = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    @property
    def available(self):
        from django.utils import timezone
        return self.active and self.uses_count < self.max_uses and (not self.expires_at or self.expires_at > timezone.now())

    def __str__(self):
        return f'{self.code} · {self.organization}'


class RegistrationRequest(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = ((PENDING, 'Pendente'), (APPROVED, 'Aprovado'), (REJECTED, 'Rejeitado'))

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='registration_request')
    invitation_code = models.ForeignKey(InvitationCode, null=True, on_delete=models.SET_NULL, related_name='registration_requests')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_registration_requests')
    reviewer_notes = models.TextField(blank=True)

    class Meta:
        ordering = ('-submitted_at',)

    def __str__(self):
        return f'{self.user} · {self.get_status_display()}'


class DemoVisit(models.Model):
    """Identifies a demo visitor even though the demo account is shared."""

    demo_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='demo_visits')
    session_key = models.CharField(max_length=64, unique=True)
    visitor_name = models.CharField(max_length=160)
    visitor_email = models.EmailField()
    visitor_company = models.CharField(max_length=160, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    page_views = models.PositiveIntegerField(default=0)
    last_path = models.CharField(max_length=500, blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ('-last_seen_at',)

    def __str__(self):
        return f'{self.visitor_name} · {self.visitor_email}'
