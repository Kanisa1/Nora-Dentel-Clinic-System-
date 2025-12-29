# clinic/urls_finance.py
"""
URL Configuration for Financial Officer Module
"""

from django.urls import path
from clinic import views_finance_officer as finance_views
from clinic import views_finance_officer_part2 as finance_views_2

urlpatterns = [
    # Main Dashboard
    path('finance/dashboard/', finance_views.finance_officer_dashboard, name='finance_dashboard'),
    
    # Income Reports
    path('finance/income-statement/', finance_views.income_statement, name='income_statement'),
    path('finance/department-report/', finance_views.department_financial_report, name='department_financial_report'),
    path('finance/department-report/<int:dept_id>/', finance_views.department_financial_report, name='department_financial_report_detail'),
    path('finance/doctor-report/', finance_views.doctor_financial_report, name='doctor_financial_report'),
    path('finance/doctor-report/<int:doctor_id>/', finance_views.doctor_financial_report, name='doctor_financial_report_detail'),
    path('finance/insurance-report/', finance_views.insurance_report, name='insurance_report'),
    
    # Expense Management
    path('finance/expenses/', finance_views_2.expense_list, name='expense_list'),
    path('finance/expenses/create/', finance_views_2.expense_create, name='expense_create'),
    path('finance/expenses/<int:expense_id>/approve/', finance_views_2.expense_approve, name='expense_approve'),
    
    # Purchase Management
    path('finance/purchases/', finance_views_2.purchase_list, name='purchase_list'),
    path('finance/purchases/create/', finance_views_2.purchase_create, name='purchase_create'),
    
    # Inventory Management
    path('finance/inventory/', finance_views_2.inventory_dashboard, name='inventory_dashboard'),
    path('finance/inventory/consumables/', finance_views_2.consumable_inventory_list, name='consumable_list'),
    path('finance/inventory/consumables/create/', finance_views_2.consumable_create, name='consumable_create'),
    path('finance/inventory/fixed-assets/', finance_views_2.fixed_asset_list, name='fixed_asset_list'),
    path('finance/inventory/fixed-assets/create/', finance_views_2.fixed_asset_create, name='fixed_asset_create'),
    
    # Financial Statements
    path('finance/profit-loss/', finance_views_2.profit_loss_statement, name='profit_loss_statement'),
    path('finance/balance-sheet/', finance_views_2.balance_sheet, name='balance_sheet'),
    
    # Stock Alerts
    path('finance/stock-alerts/', finance_views_2.stock_alert_list, name='stock_alert_list'),
    path('finance/stock-alerts/check/', finance_views_2.check_and_create_alerts, name='check_create_alerts'),
]
