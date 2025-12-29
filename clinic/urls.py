from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet
from . import views_dashboards
from . import views_patient_workflow
from . import views_cashier
from . import views_pharmacy
from . import views_inventory

router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')

urlpatterns = [
    path('', include(router.urls)),
]

# Patient Workflow URLs (Reception, Doctor, Clinical, Billing)
workflow_urls = [
    # Reception: Create visits and send to doctor
    path('api/reception/create-visit/', views_patient_workflow.reception_create_visit, name='reception_create_visit'),
    
    # Doctor: Patient list and clinical records
    path('doctor/patients/', views_patient_workflow.doctor_patient_list, name='doctor_patient_list'),
    path('doctor/patient/<int:visit_id>/clinical-record/', views_patient_workflow.doctor_clinical_record, name='doctor_clinical_record'),
    path('doctor/patient/<int:visit_id>/add-billing/', views_patient_workflow.doctor_add_billing, name='doctor_add_billing'),
    path('doctor/invoice/<int:invoice_id>/', views_patient_workflow.doctor_invoice_view, name='doctor_invoice_view'),
    
    # API Endpoints
    path('doctors-by-department/', views_patient_workflow.api_get_doctors_by_department, name='api_doctors_by_department'),
    path('api/patient-info/', views_patient_workflow.api_get_patient_info, name='api_patient_info'),
    path('api/tariff-prices/', views_patient_workflow.api_get_tariff_prices, name='api_tariff_prices'),
    path('api/add-billing-item/', views_patient_workflow.api_add_billing_item, name='api_add_billing_item'),
    path('api/remove-billing-item/', views_patient_workflow.api_remove_billing_item, name='api_remove_billing_item'),
    path('api/invoice/<int:invoice_id>/', views_patient_workflow.api_get_invoice_data, name='api_invoice_data'),
]

urlpatterns += workflow_urls

# Dashboard URLs
urlpatterns += [
    # Admin Dashboard
    path('admin/dashboard/', views_dashboards.admin_dashboard, name='admin_dashboard'),
    
    # Doctor Dashboard - Include enhanced doctor URLs
    path('doctor/', include('clinic.urls_doctor')),
    
    # Reception Dashboard
    path('reception/dashboard/', views_dashboards.reception_dashboard, name='reception_dashboard'),
    path('reception/register-patient/', views_dashboards.reception_dashboard, name='reception_register_patient'),
    path('reception/patients/', views_dashboards.reception_dashboard, name='reception_patients'),
    path('reception/appointments/', views_dashboards.reception_appointments, name='reception_appointments'),
    path('reception/today-appointments/', views_dashboards.reception_dashboard, name='reception_today_appointments'),
    path('reception/profile/', views_dashboards.reception_dashboard, name='reception_profile'),
    path('reception/schedule-appointment/', views_dashboards.reception_schedule_appointment_form, name='reception_schedule_appointment_form'),
    path('reception/schedule-appointment/save/', views_dashboards.reception_schedule_appointment, name='reception_schedule_appointment'),
    
    # Cashier Dashboard
    path('cashier/login/', views_cashier.cashier_login, name='cashier_login'),
    path('cashier/logout/', views_cashier.cashier_logout, name='cashier_logout'),
    path('cashier/dashboard/', views_cashier.cashier_dashboard, name='cashier_dashboard'),
    path('cashier/invoice/<int:visit_id>/', views_cashier.view_invoice, name='view_invoice'),
    path('cashier/print/<int:visit_id>/', views_cashier.print_invoice, name='print_invoice'),
    path('cashier/mark-paid/<int:visit_id>/', views_cashier.mark_paid, name='mark_paid'),
    path('cashier/payments/', views_cashier.cashier_payments, name='cashier_payments'),
    path('cashier/reconciliation/', views_cashier.cashier_daily_reconciliation, name='cashier_reconciliation'),
    path('cashier/refunds/', views_cashier.refund_list, name='refund_list'),
    path('cashier/refund/request/', views_cashier.request_refund, name='request_refund'),
    path('cashier/refund/<int:refund_id>/process/', views_cashier.process_refund, name='process_refund'),
    path('cashier/receipts/', views_cashier.view_receipts, name='view_receipts'),
    path('cashier/prescription/<int:prescription_id>/print/', views_cashier.cashier_print_prescription, name='cashier_print_prescription'),
    
    # Pharmacy Dashboard
    path('pharmacy/login/', views_pharmacy.pharmacy_login, name='pharmacy_login'),
    path('pharmacy/logout/', views_pharmacy.pharmacy_logout, name='pharmacy_logout'),
    path('pharmacy/dashboard/', views_dashboards.pharmacy_dashboard, name='pharmacy_dashboard'),
    path('pharmacy/medicines/', views_pharmacy.pharmacy_medicines_view, name='pharmacy_medicines'),
    path('pharmacy/stock/', views_pharmacy.pharmacy_stock_view, name='pharmacy_stock'),
    path('pharmacy/dispensing/', views_pharmacy.pharmacy_dispensing_view, name='pharmacy_dispensing'),
    path('pharmacy/prescriptions/', views_pharmacy.pharmacy_prescriptions_view, name='pharmacy_prescriptions'),
    path('pharmacy/prescription/<int:prescription_id>/detail/', views_pharmacy.pharmacy_prescription_detail, name='pharmacy_prescription_detail'),
    path('pharmacy/prescription/<int:prescription_id>/print/', views_pharmacy.pharmacy_print_prescription, name='pharmacy_print_prescription'),
    path('pharmacy/prescription/<int:prescription_id>/dispense/', views_pharmacy.pharmacy_dispense_prescription, name='pharmacy_dispense_prescription'),
    path('pharmacy/reports/', views_pharmacy.pharmacy_reports_view, name='pharmacy_reports'),
    path('pharmacy/alerts/', views_pharmacy.pharmacy_alerts_view, name='pharmacy_alerts'),
    path('pharmacy/profile/', views_dashboards.pharmacy_dashboard, name='pharmacy_profile'),
    
    # Inventory Dashboard
    path('inventory/login/', views_inventory.inventory_login, name='inventory_login'),
    path('inventory/logout/', views_inventory.inventory_logout, name='inventory_logout'),
    path('inventory/dashboard/', views_dashboards.inventory_dashboard, name='inventory_dashboard'),
    path('inventory/items/', views_inventory.inventory_items_view, name='inventory_items'),
    path('inventory/stock/', views_inventory.inventory_stock_view, name='inventory_stock'),
    path('inventory/equipment/', views_inventory.inventory_equipment_view, name='inventory_equipment'),
    path('inventory/maintenance/', views_inventory.inventory_maintenance_view, name='inventory_maintenance'),
    path('inventory/consumables/', views_inventory.inventory_consumables_view, name='inventory_consumables'),
    path('inventory/reports/', views_inventory.inventory_reports_view, name='inventory_reports'),
    path('inventory/profile/', views_dashboards.inventory_dashboard, name='inventory_profile'),
    # Inventory Quick Actions
    path('inventory/add-item/', views_inventory.inventory_add_item_view, name='inventory_add_item'),
    path('inventory/add-equipment/', views_inventory.inventory_add_equipment_view, name='inventory_add_equipment'),
    path('inventory/stock-take/', views_inventory.inventory_stock_take_view, name='inventory_stock_take'),
    path('inventory/maintenance-log/', views_inventory.inventory_maintenance_log_view, name='inventory_maintenance_log'),
    
    # Financial Dashboard
    path('financial/dashboard/', views_dashboards.financial_dashboard, name='financial_dashboard'),
    path('financial/revenue/', views_dashboards.financial_dashboard, name='financial_revenue'),
    path('financial/invoices/', views_dashboards.financial_dashboard, name='financial_invoices'),
    path('financial/expenses/', views_dashboards.financial_dashboard, name='financial_expenses'),
    path('financial/budget/', views_dashboards.financial_dashboard, name='financial_budget'),
    path('financial/reports/', views_dashboards.financial_dashboard, name='financial_reports'),
    path('financial/analytics/', views_dashboards.financial_dashboard, name='financial_analytics'),
    path('financial/department-report/', views_dashboards.financial_dashboard, name='financial_department_report'),
    path('financial/doctor-report/', views_dashboards.financial_dashboard, name='financial_doctor_report'),
    path('financial/insurance-report/', views_dashboards.financial_dashboard, name='financial_insurance_report'),
    
    # Reports Dashboard
    path('reports/dashboard/', views_dashboards.reports_dashboard, name='reports_dashboard'),
    path('reports/daily/', views_dashboards.reports_dashboard, name='reports_daily'),
    path('reports/monthly/', views_dashboards.reports_dashboard, name='reports_monthly'),
    path('reports/analytics/', views_dashboards.reports_dashboard, name='reports_analytics'),
    path('reports/export/', views_dashboards.reports_dashboard, name='reports_export'),
]
