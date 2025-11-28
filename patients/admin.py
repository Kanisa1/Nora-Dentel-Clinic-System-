from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """Admin configuration for Patient model."""

    list_display = ('first_name', 'last_name', 'phone_number', 'department', 'insurance_percentage', 'created_at')
    list_filter = ('department', 'gender')
    search_fields = ('first_name', 'last_name', 'email', 'phone_number')
    ordering = ('-created_at',)
