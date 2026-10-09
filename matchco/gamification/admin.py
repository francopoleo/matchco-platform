from django.contrib import admin

from .models import Badges


@admin.register(Badges)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'qty_points')
    list_filter = ('name', 'qty_points')
    search_fields = ('name',)
