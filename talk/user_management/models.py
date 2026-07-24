from configuration import random_indication_code
from django.contrib.auth.models import Group, AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    mobile = models.CharField(_('Mobile'), max_length=20, unique=True, blank=True, null=True)
    indication_code = models.CharField(_('Indication Code'), max_length=30, blank=True, null=True)

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
