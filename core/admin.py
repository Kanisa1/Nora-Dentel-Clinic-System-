from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, InsuranceCompany, Patient, TariffCategory, Tariff,
    MedicalRecord, Invoice, InvoiceItem, Payment,
    DrugCategory, Drug, Prescription,
    StoreCategory, StoreItem, StoreTransaction
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone', 'address')}),
    )


@admin.register(InsuranceCompany)
class InsuranceCompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'contact_person', 'phone', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'phone', 'insurance_company', 'insurance_percentage']
    list_filter = ['gender', 'insurance_company']
    search_fields = ['first_name', 'last_name', 'phone', 'national_id']


@admin.register(TariffCategory)
class TariffCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'unit_price', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'name']


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'visit_date', 'diagnosis']
    list_filter = ['doctor', 'visit_date']
    search_fields = ['patient__first_name', 'patient__last_name', 'diagnosis']


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'patient', 'subtotal', 'status', 'invoice_date']
    list_filter = ['status', 'invoice_date']
    search_fields = ['invoice_number', 'patient__first_name', 'patient__last_name']
    inlines = [InvoiceItemInline, PaymentInline]


@admin.register(DrugCategory)
class DrugCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']


@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'stock_quantity', 'unit_price', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'name', 'generic_name']


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['drug', 'medical_record', 'quantity', 'is_dispensed']
    list_filter = ['is_dispensed']


@admin.register(StoreCategory)
class StoreCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']


@admin.register(StoreItem)
class StoreItemAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'stock_quantity', 'unit_price', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'name']


@admin.register(StoreTransaction)
class StoreTransactionAdmin(admin.ModelAdmin):
    list_display = ['item', 'transaction_type', 'quantity', 'performed_by', 'transaction_date']
    list_filter = ['transaction_type', 'transaction_date']
