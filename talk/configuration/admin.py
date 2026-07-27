from django.contrib import admin

from .models import (
    Organization, OrganizationTerminology, Company, BusinessUnit, OperationalUnit,
    BusinessChannel, JobFunction, PersonType, Membership, MembershipAudit,
    ManagementAssignment, Partner, PartnerMembership,
    IntegrationCredential, WebhookDelivery, WebhookSubscription,
    UserGroup, GroupMembership, GroupAccess,
    GroupHierarchyType, GroupHierarchyTerminology, GroupNode,
    UserGroupMembership, GroupNodeAccess,
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


class MembershipAuditInline(admin.TabularInline):
    model = MembershipAudit
    extra = 0
    fields = ('action', 'user', 'old_values', 'new_values', 'reason', 'created_at')
    readonly_fields = fields
    can_delete = False


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'company', 'business_unit', 'is_primary', 'active', 'compliance_status', 'compliance_due_date', 'created_at')
    list_filter = ('organization', 'company', 'role', 'active', 'is_primary', 'compliance_status', 'compliance_due_date', 'created_at')
    search_fields = ('user__username', 'user__email', 'company__name', 'business_unit__name', 'operational_unit__name')
    filter_horizontal = ('channels', 'functions')
    readonly_fields = ('created_by', 'created_at', 'updated_by', 'updated_at', 'compliance_completed_at')

    fieldsets = (
        ('Membership', {
            'fields': ('user', 'organization', 'company', 'business_unit', 'operational_unit')
        }),
        ('Access', {
            'fields': ('role', 'channels', 'functions', 'person_type')
        }),
        ('Status', {
            'fields': ('is_primary', 'active')
        }),
        ('Compliance', {
            'fields': ('compliance_status', 'compliance_due_date', 'compliance_completed_at'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [MembershipAuditInline]


@admin.register(MembershipAudit)
class MembershipAuditAdmin(admin.ModelAdmin):
    list_display = ('id', 'membership', 'action', 'user', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('membership__user__username', 'user__username')
    readonly_fields = ('membership', 'user', 'action', 'old_values', 'new_values', 'reason', 'ip_address', 'user_agent', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0
    raw_id_fields = ('user', 'linked_user', 'created_by')
    fields = ('user', 'linked_user', 'role', 'status', 'joined_at', 'created_by')
    readonly_fields = ('joined_at', 'created_by')


class GroupAccessInline(admin.TabularInline):
    model = GroupAccess
    extra = 0
    fields = ('content_type', 'object_id', 'access_level', 'created_by', 'created_at')
    readonly_fields = ('created_by', 'created_at')


@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'group_type', 'organization', 'member_count', 'created_at')
    list_filter = ('group_type', 'organization', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    inlines = [GroupMembershipInline, GroupAccessInline]

    fieldsets = (
        ('Basic Info', {
            'fields': ('organization', 'name', 'slug', 'group_type')
        }),
        ('Description', {
            'fields': ('description', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def member_count(self, obj):
        return obj.members.filter(status='active').count()
    member_count.short_description = 'Active Members'


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'role', 'status', 'joined_at', 'created_by')
    list_filter = ('group', 'role', 'status', 'joined_at')
    search_fields = ('user__email', 'user__username', 'group__name')
    raw_id_fields = ('user', 'linked_user', 'created_by')
    readonly_fields = ('joined_at', 'created_by')

    fieldsets = (
        ('Membership Info', {
            'fields': ('user', 'group', 'linked_user')
        }),
        ('Access', {
            'fields': ('role', 'status')
        }),
        ('Audit', {
            'fields': ('joined_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GroupAccess)
class GroupAccessAdmin(admin.ModelAdmin):
    list_display = ('group', 'content_type', 'object_id', 'access_level', 'created_at', 'created_by')
    list_filter = ('group', 'content_type', 'access_level', 'created_at')
    search_fields = ('group__name',)
    readonly_fields = ('created_at', 'updated_at', 'created_by')

    fieldsets = (
        ('Access Rule', {
            'fields': ('group', 'content_type', 'object_id', 'access_level')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Phase 3.3B: Generic Hierarchy System (New)

class GroupHierarchyTerminologyInline(admin.TabularInline):
    model = GroupHierarchyTerminology
    extra = 0
    fields = ('level_1_label', 'level_1_description', 'level_2_label', 'level_2_description', 'level_3_label', 'level_3_description')


class UserGroupMembershipInline(admin.TabularInline):
    model = UserGroupMembership
    extra = 0
    raw_id_fields = ('user', 'linked_user', 'created_by')
    fields = ('user', 'linked_user', 'role', 'status', 'joined_at', 'created_by')
    readonly_fields = ('joined_at', 'created_by')


class GroupNodeAccessInline(admin.TabularInline):
    model = GroupNodeAccess
    extra = 0
    fields = ('content_type', 'object_id', 'access_level', 'created_by', 'created_at')
    readonly_fields = ('created_by', 'created_at')


class GroupNodeInline(admin.TabularInline):
    model = GroupNode
    extra = 0
    fields = ('name', 'code', 'level', 'position', 'active')
    ordering = ('level', 'position', 'name')


@admin.register(GroupHierarchyType)
class GroupHierarchyTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'organization', 'max_levels', 'allow_links', 'active', 'created_at')
    list_filter = ('organization', 'active', 'allow_links')
    search_fields = ('name', 'code', 'description', 'organization__name')
    prepopulated_fields = {'code': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    inlines = [GroupHierarchyTerminologyInline]

    fieldsets = (
        ('Basic Info', {
            'fields': ('organization', 'name', 'code', 'description')
        }),
        ('Configuration', {
            'fields': ('max_levels', 'allow_links', 'auto_create_on')
        }),
        ('Status', {
            'fields': ('active',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GroupNode)
class GroupNodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'hierarchy_type', 'level', 'parent_node', 'position', 'active', 'created_at')
    list_filter = ('hierarchy_type', 'level', 'active', 'hierarchy_type__organization')
    search_fields = ('name', 'code', 'description', 'hierarchy_type__name')
    readonly_fields = ('level', 'created_at', 'updated_at')
    inlines = [UserGroupMembershipInline, GroupNodeAccessInline]

    fieldsets = (
        ('Basic Info', {
            'fields': ('hierarchy_type', 'parent_node', 'name', 'code', 'level')
        }),
        ('Description', {
            'fields': ('description', 'metadata', 'position')
        }),
        ('Status', {
            'fields': ('active',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('hierarchy_type', 'parent_node')


@admin.register(UserGroupMembership)
class UserGroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'group_node', 'role', 'status', 'linked_user', 'joined_at', 'created_by')
    list_filter = ('group_node__hierarchy_type', 'role', 'status', 'joined_at')
    search_fields = ('user__email', 'user__username', 'group_node__name', 'linked_user__email')
    raw_id_fields = ('user', 'group_node', 'linked_user', 'created_by')
    readonly_fields = ('joined_at', 'created_by')

    fieldsets = (
        ('Membership Info', {
            'fields': ('user', 'group_node', 'linked_user')
        }),
        ('Access', {
            'fields': ('role', 'status')
        }),
        ('Audit', {
            'fields': ('joined_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GroupNodeAccess)
class GroupNodeAccessAdmin(admin.ModelAdmin):
    list_display = ('group_node', 'content_type', 'object_id', 'access_level', 'created_at', 'created_by')
    list_filter = ('group_node__hierarchy_type', 'content_type', 'access_level', 'created_at')
    search_fields = ('group_node__name', 'group_node__hierarchy_type__name')
    readonly_fields = ('created_at', 'updated_at', 'created_by')

    fieldsets = (
        ('Access Rule', {
            'fields': ('group_node', 'content_type', 'object_id', 'access_level')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
