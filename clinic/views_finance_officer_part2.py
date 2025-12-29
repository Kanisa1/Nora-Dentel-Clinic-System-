# clinic/views_finance_officer_part2.py
"""
Financial Officer Views - Part 2
Store Management, Expenses, Profit/Loss, Balance Sheet
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Sum, Count, Q, F, DecimalField, Value
from datetime import datetime, timedelta, date
from django.contrib import messages
from django.http import JsonResponse

from clinic.models import Invoice, ClinicUser, Department, Payment
from clinic.models_financial import (
    Expense, Purchase, FixedAsset, ConsumableInventory, 
    ConsumableUsage, FinancialPeriod, StockAlert
)


def is_finance_officer(user):
    """Check if user is a financial officer"""
    if not user.is_authenticated:
        return False
    try:
        return user.clinicuser.role == 'finance' or user.is_superuser
    except:
        return user.is_superuser


# ==================== EXPENSE MANAGEMENT ====================

@login_required
@user_passes_test(is_finance_officer)
def expense_list(request):
    """List all expenses with filtering"""
    status = request.GET.get('status')
    category = request.GET.get('category')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    expenses = Expense.objects.all().select_related(
        'requested_by__user', 'approved_by__user', 'department'
    )
    
    if status:
        expenses = expenses.filter(status=status)
    if category:
        expenses = expenses.filter(category=category)
    if start_date:
        expenses = expenses.filter(expense_date__gte=start_date)
    if end_date:
        expenses = expenses.filter(expense_date__lte=end_date)
    
    expenses = expenses.order_by('-expense_date', '-created_at')
    
    # Summary statistics
    summary = expenses.aggregate(
        total=Sum('amount', default=0, output_field=DecimalField()),
        count=Count('id')
    )
    
    # Pending count
    pending_count = Expense.objects.filter(status='pending').count()
    
    context = {
        'expenses': expenses,
        'total_amount': float(summary['total'] or 0),
        'expense_count': summary['count'],
        'pending_count': pending_count,
        'status_filter': status,
        'category_filter': category,
        'start_date': start_date,
        'end_date': end_date,
        'expense_categories': Expense.CATEGORY_CHOICES,
    }
    
    return render(request, 'finance/expense_list.html', context)


@login_required
@user_passes_test(is_finance_officer)
def expense_create(request):
    """Create new expense"""
    if request.method == 'POST':
        try:
            clinic_user = request.user.clinicuser
        except:
            messages.error(request, 'User profile not found')
            return redirect('expense_list')
        
        expense = Expense.objects.create(
            category=request.POST.get('category'),
            description=request.POST.get('description'),
            amount=request.POST.get('amount'),
            expense_date=request.POST.get('expense_date'),
            requested_by=clinic_user,
            department_id=request.POST.get('department') if request.POST.get('department') else None,
            notes=request.POST.get('notes'),
        )
        
        if 'receipt_file' in request.FILES:
            expense.receipt_file = request.FILES['receipt_file']
            expense.save()
        
        messages.success(request, 'Expense created successfully')
        return redirect('expense_list')
    
    departments = Department.objects.all()
    
    context = {
        'expense_categories': Expense.CATEGORY_CHOICES,
        'departments': departments,
    }
    
    return render(request, 'finance/expense_form.html', context)


@login_required
@user_passes_test(is_finance_officer)
def expense_approve(request, expense_id):
    """Approve an expense"""
    expense = get_object_or_404(Expense, id=expense_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        try:
            clinic_user = request.user.clinicuser
        except:
            messages.error(request, 'User profile not found')
            return redirect('expense_list')
        
        if action == 'approve':
            expense.status = 'approved'
            expense.approved_by = clinic_user
            expense.approved_at = timezone.now()
            expense.save()
            messages.success(request, 'Expense approved successfully')
        
        elif action == 'reject':
            expense.status = 'rejected'
            expense.approved_by = clinic_user
            expense.approved_at = timezone.now()
            expense.rejection_reason = request.POST.get('rejection_reason')
            expense.save()
            messages.warning(request, 'Expense rejected')
        
        elif action == 'mark_paid':
            expense.status = 'paid'
            expense.paid_at = timezone.now()
            expense.payment_reference = request.POST.get('payment_reference')
            expense.save()
            messages.success(request, 'Expense marked as paid')
        
        return redirect('expense_list')
    
    context = {
        'expense': expense,
    }
    
    return render(request, 'finance/expense_approve.html', context)


# ==================== PURCHASE MANAGEMENT ====================

@login_required
@user_passes_test(is_finance_officer)
def purchase_list(request):
    """List all purchases"""
    purchase_type = request.GET.get('type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    purchases = Purchase.objects.all().select_related(
        'entered_by__user', 'department', 'inventory_item', 'fixed_asset'
    )
    
    if purchase_type:
        purchases = purchases.filter(purchase_type=purchase_type)
    if start_date:
        purchases = purchases.filter(purchase_date__gte=start_date)
    if end_date:
        purchases = purchases.filter(purchase_date__lte=end_date)
    
    purchases = purchases.order_by('-purchase_date', '-entry_date')
    
    # Summary
    summary = purchases.aggregate(
        total_cost=Sum('total_cost', default=0, output_field=DecimalField()),
        count=Count('id')
    )
    
    context = {
        'purchases': purchases,
        'total_cost': float(summary['total_cost'] or 0),
        'purchase_count': summary['count'],
        'type_filter': purchase_type,
        'start_date': start_date,
        'end_date': end_date,
        'purchase_types': Purchase.PURCHASE_TYPE_CHOICES,
    }
    
    return render(request, 'finance/purchase_list.html', context)


@login_required
@user_passes_test(is_finance_officer)
def purchase_create(request):
    """Register new purchase"""
    if request.method == 'POST':
        try:
            clinic_user = request.user.clinicuser
        except:
            messages.error(request, 'User profile not found')
            return redirect('purchase_list')
        
        purchase = Purchase.objects.create(
            purchase_type=request.POST.get('purchase_type'),
            item_name=request.POST.get('item_name'),
            supplier_name=request.POST.get('supplier_name'),
            supplier_contact=request.POST.get('supplier_contact'),
            quantity=request.POST.get('quantity'),
            unit=request.POST.get('unit'),
            price_per_unit=request.POST.get('price_per_unit'),
            purchase_date=request.POST.get('purchase_date'),
            expiry_date=request.POST.get('expiry_date') if request.POST.get('expiry_date') else None,
            entered_by=clinic_user,
            department_id=request.POST.get('department') if request.POST.get('department') else None,
            invoice_number=request.POST.get('invoice_number'),
            notes=request.POST.get('notes'),
        )
        
        if 'invoice_file' in request.FILES:
            purchase.invoice_file = request.FILES['invoice_file']
            purchase.save()
        
        # If consumable, update inventory
        if purchase.purchase_type in ['consumable', 'medicine', 'supplies']:
            # Check if consumable inventory exists or create
            item_name = purchase.item_name
            consumable, created = ConsumableInventory.objects.get_or_create(
                item_name=item_name,
                defaults={
                    'category': 'medicine' if purchase.purchase_type == 'medicine' else 'dental_supply',
                    'unit': purchase.unit,
                    'quantity_in_stock': 0,
                    'department': purchase.department,
                }
            )
            
            # Update stock
            consumable.quantity_in_stock += purchase.quantity
            consumable.last_entry_date = purchase.purchase_date
            if purchase.expiry_date:
                consumable.expiry_date = purchase.expiry_date
            
            # Update average cost
            total_value = (consumable.quantity_in_stock - purchase.quantity) * consumable.average_unit_cost
            total_value += purchase.total_cost
            consumable.average_unit_cost = total_value / consumable.quantity_in_stock
            consumable.save()
            
            # Link purchase to inventory
            purchase.inventory_item_id = consumable.id
            purchase.save()
        
        messages.success(request, 'Purchase registered successfully')
        return redirect('purchase_list')
    
    departments = Department.objects.all()
    
    context = {
        'purchase_types': Purchase.PURCHASE_TYPE_CHOICES,
        'departments': departments,
    }
    
    return render(request, 'finance/purchase_form.html', context)


# ==================== INVENTORY MANAGEMENT ====================

@login_required
@user_passes_test(is_finance_officer)
def inventory_dashboard(request):
    """Inventory overview"""
    # Consumables
    consumables = ConsumableInventory.objects.all()
    
    total_consumables = consumables.count()
    low_stock = consumables.filter(
        quantity_in_stock__lte=F('minimum_stock_level')
    ).count()
    
    total_inventory_value = sum(item.total_value() for item in consumables)
    
    # Fixed Assets
    fixed_assets = FixedAsset.objects.filter(status='active')
    total_assets = fixed_assets.count()
    total_asset_value = sum(asset.current_value() for asset in fixed_assets)
    
    # Recent stock movements
    recent_usage = ConsumableUsage.objects.select_related(
        'consumable', 'used_by__user', 'department'
    ).order_by('-usage_date', '-created_at')[:20]
    
    # Alerts
    active_alerts = StockAlert.objects.filter(status='active').order_by('-created_at')[:10]
    
    context = {
        'total_consumables': total_consumables,
        'low_stock_count': low_stock,
        'total_inventory_value': float(total_inventory_value),
        'total_assets': total_assets,
        'total_asset_value': float(total_asset_value),
        'recent_usage': recent_usage,
        'active_alerts': active_alerts,
    }
    
    return render(request, 'finance/inventory_dashboard.html', context)


@login_required
@user_passes_test(is_finance_officer)
def consumable_inventory_list(request):
    """List all consumable inventory"""
    category = request.GET.get('category')
    low_stock = request.GET.get('low_stock')
    
    consumables = ConsumableInventory.objects.all().select_related('department')
    
    if category:
        consumables = consumables.filter(category=category)
    if low_stock == 'yes':
        consumables = consumables.filter(quantity_in_stock__lte=F('minimum_stock_level'))
    
    consumables = consumables.order_by('item_name')
    
    # Calculate total value
    total_value = sum(item.total_value() for item in consumables)
    
    context = {
        'consumables': consumables,
        'total_value': float(total_value),
        'category_filter': category,
        'low_stock_filter': low_stock,
    }
    
    return render(request, 'finance/consumable_list.html', context)


@login_required
@user_passes_test(is_finance_officer)
def consumable_create(request):
    """Create new consumable item"""
    if request.method == 'POST':
        ConsumableInventory.objects.create(
            item_name=request.POST.get('item_name'),
            item_code=request.POST.get('item_code'),
            category=request.POST.get('category'),
            unit=request.POST.get('unit'),
            quantity_in_stock=request.POST.get('quantity_in_stock', 0),
            minimum_stock_level=request.POST.get('minimum_stock_level', 0),
            expiry_date=request.POST.get('expiry_date') if request.POST.get('expiry_date') else None,
            department_id=request.POST.get('department') if request.POST.get('department') else None,
            average_unit_cost=request.POST.get('average_unit_cost', 0),
            notes=request.POST.get('notes'),
        )
        
        messages.success(request, 'Consumable item created successfully')
        return redirect('consumable_list')
    
    departments = Department.objects.all()
    
    context = {
        'departments': departments,
    }
    
    return render(request, 'finance/consumable_form.html', context)


@login_required
@user_passes_test(is_finance_officer)
def fixed_asset_list(request):
    """List all fixed assets"""
    asset_type = request.GET.get('type')
    status = request.GET.get('status')
    
    assets = FixedAsset.objects.all().select_related('department')
    
    if asset_type:
        assets = assets.filter(asset_type=asset_type)
    if status:
        assets = assets.filter(status=status)
    
    assets = assets.order_by('asset_name')
    
    # Calculate total values
    total_purchase_cost = assets.aggregate(
        total=Sum('purchase_cost', default=0, output_field=DecimalField())
    )['total'] or 0
    
    total_current_value = sum(asset.current_value() for asset in assets)
    
    context = {
        'assets': assets,
        'total_purchase_cost': float(total_purchase_cost),
        'total_current_value': float(total_current_value),
        'type_filter': asset_type,
        'status_filter': status,
        'asset_types': FixedAsset.ASSET_TYPE_CHOICES,
    }
    
    return render(request, 'finance/fixed_asset_list.html', context)


@login_required
@user_passes_test(is_finance_officer)
def fixed_asset_create(request):
    """Create new fixed asset"""
    if request.method == 'POST':
        asset = FixedAsset.objects.create(
            asset_type=request.POST.get('asset_type'),
            asset_name=request.POST.get('asset_name'),
            asset_code=request.POST.get('asset_code'),
            description=request.POST.get('description'),
            purchase_date=request.POST.get('purchase_date'),
            purchase_cost=request.POST.get('purchase_cost'),
            supplier=request.POST.get('supplier'),
            useful_life_years=request.POST.get('useful_life_years', 5),
            salvage_value=request.POST.get('salvage_value', 0),
            location=request.POST.get('location'),
            department_id=request.POST.get('department') if request.POST.get('department') else None,
            serial_number=request.POST.get('serial_number'),
            warranty_expiry=request.POST.get('warranty_expiry') if request.POST.get('warranty_expiry') else None,
            notes=request.POST.get('notes'),
        )
        
        if 'invoice_file' in request.FILES:
            asset.invoice_file = request.FILES['invoice_file']
        if 'photo' in request.FILES:
            asset.photo = request.FILES['photo']
        
        asset.save()
        
        messages.success(request, 'Fixed asset created successfully')
        return redirect('fixed_asset_list')
    
    departments = Department.objects.all()
    
    context = {
        'asset_types': FixedAsset.ASSET_TYPE_CHOICES,
        'departments': departments,
    }
    
    return render(request, 'finance/fixed_asset_form.html', context)


# ==================== PROFIT/LOSS & BALANCE SHEET ====================

@login_required
@user_passes_test(is_finance_officer)
def profit_loss_statement(request):
    """Comprehensive Profit & Loss Statement"""
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    period = request.GET.get('period', 'monthly')
    
    today = timezone.now().date()
    
    # Date range
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    elif period == 'monthly':
        start_date = today.replace(day=1)
        end_date = today
    elif period == 'quarterly':
        # Get current quarter
        quarter = (today.month - 1) // 3
        start_date = date(today.year, quarter * 3 + 1, 1)
        end_date = today
    else:  # annual
        start_date = today.replace(month=1, day=1)
        end_date = today
    
    # REVENUE
    invoices = Invoice.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    revenue_data = invoices.aggregate(
        insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
        private=Sum('total_private', default=0, output_field=DecimalField())
    )
    
    total_revenue = (revenue_data['insurance'] or 0) + (revenue_data['private'] or 0)
    
    # Revenue by department
    revenue_by_dept = invoices.values(
        'visit__department__name'
    ).annotate(
        total=Sum(F('total_insurance') + F('total_private'), output_field=DecimalField())
    ).order_by('-total')
    
    # COST OF GOODS SOLD (Consumables used)
    consumable_usage = ConsumableUsage.objects.filter(
        usage_date__gte=start_date,
        usage_date__lte=end_date
    ).select_related('consumable')
    
    cogs = sum(
        usage.quantity_used * usage.consumable.average_unit_cost 
        for usage in consumable_usage
    )
    
    # GROSS PROFIT
    gross_profit = total_revenue - cogs
    gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # OPERATING EXPENSES
    expenses = Expense.objects.filter(
        expense_date__gte=start_date,
        expense_date__lte=end_date,
        status='paid'
    )
    
    # Breakdown by category
    expenses_by_category = expenses.values('category').annotate(
        total=Sum('amount', default=0, output_field=DecimalField())
    ).order_by('-total')
    
    total_expenses = expenses.aggregate(
        total=Sum('amount', default=0, output_field=DecimalField())
    )['total'] or 0
    
    # Depreciation (Fixed Assets)
    active_assets = FixedAsset.objects.filter(status='active')
    annual_depreciation = 0
    for asset in active_assets:
        if asset.useful_life_years > 0:
            annual_depreciation += (asset.purchase_cost - asset.salvage_value) / asset.useful_life_years
    
    # Pro-rate for period
    days_in_period = (end_date - start_date).days + 1
    depreciation_expense = (annual_depreciation / 365) * days_in_period
    
    total_operating_expenses = total_expenses + depreciation_expense
    
    # NET PROFIT/LOSS
    net_profit = gross_profit - total_operating_expenses
    net_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'period': period,
        
        # Revenue
        'total_revenue': float(total_revenue),
        'insurance_revenue': float(revenue_data['insurance'] or 0),
        'private_revenue': float(revenue_data['private'] or 0),
        'revenue_by_dept': revenue_by_dept,
        
        # Costs
        'cogs': float(cogs),
        'gross_profit': float(gross_profit),
        'gross_margin': float(gross_margin),
        
        # Expenses
        'expenses_by_category': expenses_by_category,
        'total_expenses': float(total_expenses),
        'depreciation_expense': float(depreciation_expense),
        'total_operating_expenses': float(total_operating_expenses),
        
        # Profit
        'net_profit': float(net_profit),
        'net_margin': float(net_margin),
    }
    
    return render(request, 'finance/profit_loss_statement.html', context)


@login_required
@user_passes_test(is_finance_officer)
def balance_sheet(request):
    """Balance Sheet"""
    as_of_date = request.GET.get('as_of_date')
    
    if as_of_date:
        as_of_date = datetime.strptime(as_of_date, '%Y-%m-%d').date()
    else:
        as_of_date = timezone.now().date()
    
    # ASSETS
    # Current Assets
    # Cash (from payments)
    cash_balance = Payment.objects.filter(
        paid_at__date__lte=as_of_date,
        method__in=['cash', 'momo', 'card']
    ).aggregate(
        total=Sum('amount', default=0, output_field=DecimalField())
    )['total'] or 0
    
    # Accounts Receivable (unpaid insurance invoices)
    accounts_receivable = Invoice.objects.filter(
        created_at__date__lte=as_of_date,
        paid=False,
        visit__patient__is_insured=True
    ).aggregate(
        total=Sum('total_insurance', default=0, output_field=DecimalField())
    )['total'] or 0
    
    # Inventory (Consumables)
    consumables = ConsumableInventory.objects.all()
    inventory_value = sum(item.total_value() for item in consumables)
    
    total_current_assets = cash_balance + accounts_receivable + inventory_value
    
    # Fixed Assets
    fixed_assets = FixedAsset.objects.filter(status='active')
    fixed_assets_value = sum(asset.current_value() for asset in fixed_assets)
    
    total_assets = total_current_assets + fixed_assets_value
    
    # LIABILITIES
    # Accounts Payable (pending/approved expenses)
    accounts_payable = Expense.objects.filter(
        expense_date__lte=as_of_date,
        status__in=['pending', 'approved']
    ).aggregate(
        total=Sum('amount', default=0, output_field=DecimalField())
    )['total'] or 0
    
    total_liabilities = accounts_payable
    
    # EQUITY
    # Calculate retained earnings (net profit to date)
    all_revenue = Invoice.objects.filter(
        created_at__date__lte=as_of_date
    ).aggregate(
        insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
        private=Sum('total_private', default=0, output_field=DecimalField())
    )
    total_historical_revenue = (all_revenue['insurance'] or 0) + (all_revenue['private'] or 0)
    
    all_expenses = Expense.objects.filter(
        expense_date__lte=as_of_date,
        status='paid'
    ).aggregate(
        total=Sum('amount', default=0, output_field=DecimalField())
    )['total'] or 0
    
    retained_earnings = total_historical_revenue - all_expenses
    
    total_equity = retained_earnings
    
    # Total Liabilities + Equity
    total_liabilities_equity = total_liabilities + total_equity
    
    # Check if balanced
    is_balanced = abs(total_assets - total_liabilities_equity) < 1  # Allow for rounding
    
    context = {
        'as_of_date': as_of_date,
        
        # Current Assets
        'cash_balance': float(cash_balance),
        'accounts_receivable': float(accounts_receivable),
        'inventory_value': float(inventory_value),
        'total_current_assets': float(total_current_assets),
        
        # Fixed Assets
        'fixed_assets_value': float(fixed_assets_value),
        
        # Total Assets
        'total_assets': float(total_assets),
        
        # Liabilities
        'accounts_payable': float(accounts_payable),
        'total_liabilities': float(total_liabilities),
        
        # Equity
        'retained_earnings': float(retained_earnings),
        'total_equity': float(total_equity),
        
        # Total
        'total_liabilities_equity': float(total_liabilities_equity),
        'is_balanced': is_balanced,
    }
    
    return render(request, 'finance/balance_sheet.html', context)


# ==================== STOCK OUT MANAGEMENT ====================

@login_required
@user_passes_test(is_finance_officer)
def stock_alert_list(request):
    """List all stock alerts"""
    alert_type = request.GET.get('type')
    status = request.GET.get('status')
    
    all_alerts = StockAlert.objects.all().select_related(
        'consumable', 'acknowledged_by__user'
    )
    
    # Calculate alert counts by type
    alert_counts = {
        'out_of_stock': all_alerts.filter(alert_type='out_of_stock').count(),
        'low_stock': all_alerts.filter(alert_type='low_stock').count(),
        'expiring_soon': all_alerts.filter(alert_type='expiring_soon').count(),
        'expired': all_alerts.filter(alert_type='expired').count(),
    }
    
    alerts = all_alerts
    if alert_type:
        alerts = alerts.filter(alert_type=alert_type)
    if status:
        alerts = alerts.filter(status=status)
    
    alerts = alerts.order_by('-created_at')
    
    context = {
        'alerts': alerts,
        'alert_counts': alert_counts,
        'type_filter': alert_type,
        'status_filter': status,
    }
    
    return render(request, 'finance/stock_alert_list.html', context)


@login_required
@user_passes_test(is_finance_officer)
def check_and_create_alerts(request):
    """Check inventory and create alerts for low stock and expiring items"""
    today = timezone.now().date()
    alerts_created = 0
    
    # Check for low stock
    low_stock_items = ConsumableInventory.objects.filter(
        quantity_in_stock__lte=F('minimum_stock_level')
    )
    
    for item in low_stock_items:
        # Check if alert already exists
        existing = StockAlert.objects.filter(
            consumable=item,
            alert_type='low_stock',
            status='active'
        ).exists()
        
        if not existing:
            if item.quantity_in_stock == 0:
                StockAlert.objects.create(
                    alert_type='out_of_stock',
                    consumable=item,
                    message=f"{item.item_name} is OUT OF STOCK"
                )
            else:
                StockAlert.objects.create(
                    alert_type='low_stock',
                    consumable=item,
                    message=f"{item.item_name} is below minimum stock level. Current: {item.quantity_in_stock} {item.unit}"
                )
            alerts_created += 1
    
    # Check for expiring items (within 30 days)
    expiring_date = today + timedelta(days=30)
    expiring_items = ConsumableInventory.objects.filter(
        expiry_date__lte=expiring_date,
        expiry_date__gte=today
    )
    
    for item in expiring_items:
        existing = StockAlert.objects.filter(
            consumable=item,
            alert_type='expiring_soon',
            status='active'
        ).exists()
        
        if not existing:
            days_until_expiry = (item.expiry_date - today).days
            StockAlert.objects.create(
                alert_type='expiring_soon',
                consumable=item,
                message=f"{item.item_name} expires in {days_until_expiry} days ({item.expiry_date})"
            )
            alerts_created += 1
    
    # Check for expired items
    expired_items = ConsumableInventory.objects.filter(
        expiry_date__lt=today
    )
    
    for item in expired_items:
        existing = StockAlert.objects.filter(
            consumable=item,
            alert_type='expired',
            status='active'
        ).exists()
        
        if not existing:
            StockAlert.objects.create(
                alert_type='expired',
                consumable=item,
                message=f"{item.item_name} has EXPIRED (Expiry: {item.expiry_date})"
            )
            alerts_created += 1
    
    messages.success(request, f'{alerts_created} new alerts created')
    return redirect('stock_alert_list')
