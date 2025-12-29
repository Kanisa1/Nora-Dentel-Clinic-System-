from django.urls import path
from . import views_admin, views_financial, views_cashier, views_inventory, views_pharmacy, views_reports

app_name = 'dashboard'

urlpatterns = [
    # Admin URLs
    path('login/', views_admin.admin_login, name='admin_login'),
    path('', views_admin.admin_dashboard, name='admin_dashboard'),
    path('users/', views_admin.admin_users, name='users'),
    path('departments/', views_admin.admin_departments, name='departments'),
    
    # Financial URLs
    path('financial/', views_financial.financial_dashboard, name='financial_dashboard'),
    path('financial/department/<int:dept_id>/', views_financial.financial_reports_by_department, name='financial_by_dept'),
    path('financial/department/', views_financial.financial_reports_by_department, name='financial_by_dept_default'),
    path('financial/doctor/<int:doctor_id>/', views_financial.financial_reports_by_doctor, name='financial_by_doctor'),
    path('financial/doctor/', views_financial.financial_reports_by_doctor, name='financial_by_doctor_default'),
    path('financial/insurance/<str:insurance_type>/', views_financial.financial_reports_by_insurance, name='financial_by_insurance'),
    path('financial/insurance/', views_financial.financial_reports_by_insurance, name='financial_by_insurance_default'),
    path('financial/period/<str:period>/', views_financial.financial_reports_by_period, name='financial_by_period'),
    path('financial/payment/<int:payment_id>/', views_financial.financial_payment_details, name='payment_details'),
    
    # Cashier URLs
    path('cashier/', views_cashier.cashier_dashboard, name='cashier_dashboard'),
    path('cashier/payments/', views_cashier.cashier_payments, name='cashier_payments'),
    path('cashier/reconciliation/', views_cashier.cashier_daily_reconciliation, name='cashier_reconciliation'),
    
    # Inventory URLs
    path('inventory/', views_inventory.inventory_dashboard, name='inventory_dashboard'),
    path('inventory/items/', views_inventory.inventory_items, name='inventory_items'),
    path('inventory/department/<int:dept_id>/', views_inventory.inventory_by_department, name='inventory_by_dept'),
    
    # Pharmacy URLs
    path('pharmacy/', views_pharmacy.pharmacy_dashboard, name='pharmacy_dashboard'),
    path('pharmacy/medications/', views_pharmacy.pharmacy_medications, name='pharmacy_medications'),
    path('pharmacy/prescriptions/', views_pharmacy.pharmacy_prescriptions, name='pharmacy_prescriptions'),
    
    # Reports URLs
    path('reports/', views_reports.reports_hub, name='reports_hub'),
    path('reports/patient/', views_reports.reports_patient, name='reports_patient'),
    path('reports/clinical/', views_reports.reports_clinical, name='reports_clinical'),
]
