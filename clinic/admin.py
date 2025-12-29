from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import *
from .utils.pdf import generate_invoice_pdf_bytes
from .models_medical_records import (
    MedicalRecord, 
    MedicalRecordAttachment, 
    MedicalCertificate, 
    PatientTransfer,
    HMISClassification
)
from .models_financial import (
    Expense,
    Purchase,
    FixedAsset,
    ConsumableInventory,
    ConsumableUsage,
    FinancialPeriod,
    StockAlert
)

# Configure admin site
admin.site.site_header = "Nora Dental Clinic Administration"
admin.site.site_title = "Nora Clinic Admin"
admin.site.index_title = "Healthcare Management Dashboard"

# Require login for admin site
admin.site.login = login_required(admin.site.login)

@admin.action(description="Regenerate PDF for selected invoices")
def regenerate_pdf(modeladmin, request, queryset):
    for invoice in queryset:
        pdf_bytes = generate_invoice_pdf_bytes(invoice)
        filename = f"invoice_{invoice.id}.pdf"
        invoice.pdf_file.save(filename, ContentFile(pdf_bytes))
        invoice.save()

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'visit', 'created_at', 'total_private', 'paid', 'pdf_download')
    actions = [regenerate_pdf]

    def pdf_download(self, obj):
        if obj.pdf_file:
            return format_html('<a href="{}" target="_blank">Download / Print</a>', obj.pdf_file.url)
        return "-"

    pdf_download.short_description = "Invoice PDF"

class PatientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'national_id', 'phone', 'gender', 'is_insured', 'insurer')
    list_filter = ('is_insured', 'gender', 'insurer')
    search_fields = ('first_name', 'last_name', 'national_id', 'phone')
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'national_id', 'parent_name', 'gender', 'dob')
        }),
        ('Address & Location', {
            'fields': ('nationality', 'province', 'district', 'sector', 'cell', 'village')
        }),
        ('Employment & Social', {
            'fields': ('occupation', 'affiliation', 'religion', 'phone')
        }),
        ('Insurance Information', {
            'fields': ('is_insured', 'insurer', 'insurer_other', 'membership_number', 'insurance_coverage_pct')
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at',)

class ClinicUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department', 'phone', 'status_badge')
    list_filter = ('role', 'department')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')
    fieldsets = (
        ('User Account', {
            'fields': ('user', 'role')
        }),
        ('Department Assignment', {
            'fields': ('department',),
            'description': 'IMPORTANT: Doctors MUST have a department assigned to appear in reception forms!'
        }),
        ('Contact Information', {
            'fields': ('phone', 'profile_picture')
        }),
    )
    
    def status_badge(self, obj):
        if obj.role == 'doctor':
            color = '#4CAF50' if obj.department else '#F44336'
            status = '✓ Active' if obj.department else '⚠ No Dept'
            return format_html(
                '<span style="background:{}; color:white; padding:4px 12px; border-radius:12px; font-weight:600;">{}</span>',
                color, status
            )
        return format_html('<span style="color:#666;">—</span>')
    status_badge.short_description = 'Status'

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'doctor_count', 'patient_count')
    search_fields = ('name',)
    
    def doctor_count(self, obj):
        count = ClinicUser.objects.filter(department=obj, role='doctor').count()
        return format_html('<strong style="color:#8B3A8B;">{}</strong> doctors', count)
    doctor_count.short_description = 'Doctors'
    
    def patient_count(self, obj):
        count = Visit.objects.filter(department=obj).values('patient').distinct().count()
        return format_html('<strong style="color:#2196F3;">{}</strong> patients', count)
    patient_count.short_description = 'Patients Served'

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'department', 'scheduled_at', 'status', 'status_badge')
    list_filter = ('status', 'department', 'scheduled_at')
    search_fields = ('patient__first_name', 'patient__last_name', 'doctor__user__first_name')
    date_hierarchy = 'scheduled_at'
    
    def status_badge(self, obj):
        colors = {
            'scheduled': '#2196F3',
            'checked_in': '#FF9800',
            'completed': '#4CAF50',
            'cancelled': '#F44336',
            'no_show': '#9E9E9E'
        }
        return format_html(
            '<span style="background:{}; color:white; padding:4px 12px; border-radius:12px; font-size:11px; font-weight:600; text-transform:uppercase;">{}</span>',
            colors.get(obj.status, '#666'), obj.status.replace('_', ' ')
        )
    status_badge.short_description = 'Status Badge'

class VisitAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'department', 'status', 'created_at', 'status_badge')
    list_filter = ('status', 'department', 'created_at')
    search_fields = ('patient__first_name', 'patient__last_name')
    date_hierarchy = 'created_at'
    
    def status_badge(self, obj):
        colors = {
            'open': '#2196F3',
            'waiting': '#FF9800',
            'in_consultation': '#9C27B0',
            'completed': '#4CAF50',
            'cancelled': '#F44336'
        }
        return format_html(
            '<span style="background:{}; color:white; padding:4px 12px; border-radius:12px; font-size:11px; font-weight:600; text-transform:uppercase;">{}</span>',
            colors.get(obj.status, '#666'), obj.status.replace('_', ' ')
        )
    status_badge.short_description = 'Status Badge'


class NotificationLogAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'category',
        'recipient',
        'status',
        'channel',
        'sent_at',
    )
    list_filter = ('category', 'status', 'channel')
    search_fields = ('recipient', 'recipient_name', 'provider_message_id', 'message')
    readonly_fields = (
        'category',
        'channel',
        'recipient',
        'recipient_name',
        'message',
        'status',
        'error_message',
        'provider_message_id',
        'metadata',
        'response_payload',
        'sent_at',
        'created_at',
    )
    ordering = ('-created_at',)

# register/rest of models
models_list = [PatientCard, Triage, WaitingQueueEntry,
               TariffAct, BillingItem, Invoice, Payment, Refund, Prescription, PrescriptionItem, InventoryItem, PharmacyStock,
               PharmacyDispense, StockMovement, MedicalRecord, MedicalRecordAttachment, 
               MedicalCertificate, PatientTransfer, HMISClassification,
               Expense, Purchase, FixedAsset, ConsumableInventory, ConsumableUsage, FinancialPeriod, StockAlert]
for m in models_list:
    try:
        if m is Invoice:
            admin.site.register(m, InvoiceAdmin)
        else:
            admin.site.register(m)
    except Exception:
        pass

# Register models with custom admin
admin.site.register(Patient, PatientAdmin)
admin.site.register(ClinicUser, ClinicUserAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Visit, VisitAdmin)
admin.site.register(NotificationLog, NotificationLogAdmin)
