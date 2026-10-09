from django.contrib import admin
from .models import TenantUser, TenantOrganization, TenantCompany

@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    search_fields = ['username', 'email']
    list_display = ['username', 'email', 'user_id']

@admin.register(TenantOrganization)
class TenantOrganizationAdmin(admin.ModelAdmin):
    search_fields = ['name', 'slug']
    list_display = ['name', 'slug', 'organization_id']

@admin.register(TenantCompany)
class TenantCompanyAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name', 'company_id']
