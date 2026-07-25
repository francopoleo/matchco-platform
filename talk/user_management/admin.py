from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import (
    AdminPasswordChangeForm, UserChangeForm
)
from .models import DemoVisit, InvitationCode, RegistrationRequest, User
from .forms import UserCreationForm


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form_template = 'admin/auth/user/add_form.html'
    change_user_password_template = None
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'mobile', 'indication_code', 'is_demo')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'first_name', 'last_name', 'email', 'mobile', 'indication_code',
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'),
        }),
    )

    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ('username', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_demo', 'groups')
    search_fields = ('username', 'first_name', 'last_name')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions',)


@admin.register(InvitationCode)
class InvitationCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'organization', 'company', 'uses_count', 'max_uses', 'active', 'expires_at')
    list_filter = ('organization', 'active')
    search_fields = ('code', 'organization__name', 'company__name')


@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'invitation_code', 'submitted_at', 'reviewed_by')
    list_filter = ('status', 'invitation_code__organization')
    search_fields = ('user__username', 'user__email', 'invitation_code__code')


@admin.register(DemoVisit)
class DemoVisitAdmin(admin.ModelAdmin):
    list_display = ('visitor_name', 'visitor_email', 'visitor_company', 'started_at', 'duration_seconds', 'page_views', 'last_seen_at')
    list_filter = ('started_at',)
    search_fields = ('visitor_name', 'visitor_email', 'visitor_company', 'last_path')
    readonly_fields = tuple(field.name for field in DemoVisit._meta.fields)
