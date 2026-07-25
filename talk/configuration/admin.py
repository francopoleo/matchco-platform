from django.contrib import admin

from .models import (
    Organization, OrganizationTerminology, Company, BusinessUnit, OperationalUnit,
    BusinessChannel, JobFunction, PersonType, Membership,
    ManagementAssignment, Partner, PartnerMembership,
    IntegrationCredential, WebhookDelivery, WebhookSubscription,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'active')
    list_filter = ('active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(OrganizationTerminology)
class OrganizationTerminologyAdmin(admin.ModelAdmin):
    list_display = ('organization', 'level_1_label', 'level_2_label', 'level_3_label', 'updated_at')
    list_filter = ('organization',)
    search_fields = ('organization__name', 'level_1_label', 'level_2_label', 'level_3_label')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'active')
    list_filter = ('organization', 'active')
    search_fields = ('name', 'code')


@admin.register(BusinessUnit)
class BusinessUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'active', 'manager')
    list_filter = ('company', 'active')
    search_fields = ('name', 'code', 'company__name')


@admin.register(OperationalUnit)
class OperationalUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_unit', 'active')
    list_filter = ('business_unit', 'active')
    search_fields = ('name', 'code', 'business_unit__name')


@admin.register(BusinessChannel)
class BusinessChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'active')
    list_filter = ('company', 'active')
    search_fields = ('name', 'company__name')


@admin.register(JobFunction)
class JobFunctionAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'active')
    list_filter = ('company', 'active')
    search_fields = ('name', 'company__name')
    filter_horizontal = ('channels',)


@admin.register(PersonType)
class PersonTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'organization', 'active', 'position')
    list_filter = ('organization', 'active')
    search_fields = ('name', 'code', 'organization__name')
    prepopulated_fields = {'code': ('name',)}


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'person_type', 'company', 'business_unit', 'operational_unit', 'is_primary', 'active')
    list_filter = ('organization', 'company', 'active', 'is_primary')
    search_fields = ('user__username', 'user__email', 'company__name', 'business_unit__name', 'operational_unit__name', 'person_type__name')
    filter_horizontal = ('channels', 'functions')


@admin.register(ManagementAssignment)
class ManagementAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'organization', 'company', 'business_unit', 'operational_unit', 'active')
    list_filter = ('role', 'organization', 'company', 'active')
    search_fields = ('user__username', 'user__email', 'company__name', 'business_unit__name', 'operational_unit__name')


@admin.register(IntegrationCredential)
class IntegrationCredentialAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'partner', 'key_prefix', 'active', 'expires_at', 'last_used_at')
    list_filter = ('organization', 'active')
    search_fields = ('name', 'key_prefix')
    readonly_fields = ('key_prefix', 'key_hash', 'created_at', 'rotated_at', 'last_used_at')


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'company', 'status', 'assigned_manager', 'updated_at')
    list_filter = ('organization', 'status')
    search_fields = ('name', 'email', 'company__name')


@admin.register(PartnerMembership)
class PartnerMembershipAdmin(admin.ModelAdmin):
    list_display = ('partner', 'user', 'role', 'active', 'created_at')
    list_filter = ('role', 'active', 'partner__organization')
    search_fields = ('partner__name', 'user__username', 'user__email')


@admin.register(WebhookSubscription)
class WebhookSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'endpoint', 'active', 'last_delivered_at')
    list_filter = ('organization', 'active')
    search_fields = ('name', 'endpoint')
    readonly_fields = ('created_at', 'last_delivered_at')


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'subscription', 'status', 'attempts', 'response_code', 'created_at', 'delivered_at')
    list_filter = ('status', 'event_type', 'created_at')
    readonly_fields = ('created_at', 'delivered_at')
