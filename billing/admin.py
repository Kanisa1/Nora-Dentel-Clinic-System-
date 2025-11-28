from django.contrib import admin
from .models import Tariff


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    """Admin configuration for Tariff model."""

    list_display = ('act_name', 'department', 'price', 'is_active', 'created_at')
    list_filter = ('department', 'is_active')
    search_fields = ('act_name', 'description')
    ordering = ('department', 'act_name')
