# clinic/views_finance_officer.py
"""







































































































































































































































































































































































































































































































































































{% endblock %}</script>    }        alert('View receipts feature coming soon!');        // Implement view receipts    function viewReceipts() {        }        alert('View all transactions feature coming soon!');        // Implement view all transactions    function viewAllTransactions() {        }        document.getElementById('awaiting-payments').scrollIntoView({ behavior: 'smooth', block: 'start' });    function scrollToPayments() {    // Quick Actions Functions        });        }            }                }                    }                        display: false                    grid: {                x: {                },                    }                        color: 'rgba(0,0,0,0.05)'                    grid: {                    },                        }                            return value.toFixed(0) + ' RWF';                        callback: function(value) {                    ticks: {                    beginAtZero: true,                y: {            scales: {            },                }                    }                        }                            ];                                'Transactions: ' + paymentMethodsData.counts[index]                                'Amount: ' + context.parsed.y.toFixed(0) + ' RWF',                            return [                            const index = context.dataIndex;                        label: function(context) {                    callbacks: {                    padding: 12,                    backgroundColor: 'rgba(0,0,0,0.8)',                tooltip: {                },                    display: false                legend: {            plugins: {            maintainAspectRatio: true,            responsive: true,        options: {        },            }]                borderRadius: 8                borderWidth: 0,                ],                    'rgba(255, 165, 2, 0.8)'                    'rgba(46, 213, 115, 0.8)',                    'rgba(79, 172, 254, 0.8)',                    'rgba(245, 87, 108, 0.8)',                    'rgba(102, 126, 234, 0.8)',                backgroundColor: [                data: paymentMethodsData.amounts,                label: 'Amount (RWF)',            datasets: [{            labels: paymentMethodsData.labels,        data: {        type: 'bar',    const paymentMethodsChart = new Chart(paymentMethodsCtx, {        };        {% endif %}            counts: [0]            amounts: [0],            labels: ['No Data'],        {% else %}            counts: [{% for pm in payment_methods %}{{ pm.count }},{% endfor %}]            amounts: [{% for pm in payment_methods %}{{ pm.total|floatformat:0 }},{% endfor %}],            labels: [{% for pm in payment_methods %}'{{ pm.get_method_display }}',{% endfor %}],        {% if payment_methods %}    const paymentMethodsData = {        const paymentMethodsCtx = document.getElementById('paymentMethodsChart').getContext('2d');    // Payment Methods Chart<script><script src="https://cdn.jsdelivr.net/npm/chart.js"></script>{% block extra_js %}{% endblock %}</style>    .badge-default { background: #e5e5e5; color: #333; }    .badge-secondary { background: #747d8c; color: white; }    .badge-primary { background: #667eea; color: white; }    .badge-warning { background: #ffa502; color: white; }    .badge-info { background: #3742fa; color: white; }    .badge-success { background: #2ed573; color: white; }        }        display: inline-block;        font-weight: 600;        font-size: 12px;        border-radius: 6px;        padding: 6px 12px;    .badge {    /* Badge Styles */        }        background: #26be64;    .btn-small.btn-success:hover {        }        color: white;        background: #2ed573;    .btn-small.btn-success {        }        background: #5a6268;    .btn-small.btn-secondary:hover {        }        color: white;        background: #6c757d;    .btn-small.btn-secondary {        }        transform: translateY(-1px);        background: #5568d3;    .btn-small.btn-primary:hover {        }        color: white;        background: #667eea;    .btn-small.btn-primary {        }        cursor: pointer;        border: none;        transition: all 0.2s ease;        gap: 6px;        align-items: center;        display: inline-flex;        text-decoration: none;        font-weight: 600;        font-size: 13px;        border-radius: 6px;        padding: 8px 16px;    .btn-small {    /* Small Buttons */        }        min-width: 150px;        flex: 1;    .form-input-small {        }        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);        border-color: #667eea;    .form-select-small:focus, .form-input-small:focus {        }        outline: none;        font-size: 13px;        border-radius: 6px;        border: 1px solid #ddd;        padding: 8px 12px;    .form-select-small, .form-input-small {    /* Form Elements */        }        box-shadow: 0 8px 20px rgba(0,0,0,0.15);        transform: translateY(-2px);    .action-btn:hover {        }        gap: 10px;        justify-content: center;        align-items: center;        display: flex;        transition: transform 0.2s ease, box-shadow 0.2s ease;        cursor: pointer;        font-weight: 600;        font-size: 15px;        color: white;        padding: 15px 20px;        border-radius: 12px;        border: none;    .action-btn {    /* Action Buttons */        }        gap: 18px;        display: flex;        box-shadow: 0 4px 15px rgba(0,0,0,0.08);        padding: 25px;        border-radius: 16px;        background: white;    .stat-box {    /* Stat Box */        }        padding: 25px;    .chart-body {        }        margin: 0;        font-weight: 600;        font-size: 18px;        color: white;    .chart-title {        }        padding: 20px 25px;        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);    .chart-header {        }        overflow: hidden;        box-shadow: 0 4px 15px rgba(0,0,0,0.08);        border-radius: 16px;        background: white;    .chart-container {    /* Chart Container */        }        font-weight: 500;        opacity: 0.9;        font-size: 13px;    .metric-currency {        }        margin-bottom: 2px;        line-height: 1;        font-weight: 700;        font-size: 32px;    .metric-value {        }        margin-bottom: 8px;        opacity: 0.95;        letter-spacing: 1px;        text-transform: uppercase;        font-size: 12px;    .metric-label {        }        flex: 1;    .metric-content {        }        min-width: 60px;        opacity: 0.9;        font-size: 42px;    .metric-icon {        }        box-shadow: 0 15px 40px rgba(0,0,0,0.25);        transform: translateY(-5px);    .metric-card:hover {        }        transition: transform 0.3s ease, box-shadow 0.3s ease;        gap: 20px;        align-items: center;        display: flex;        box-shadow: 0 10px 30px rgba(0,0,0,0.15);        color: white;        padding: 25px;        border-radius: 16px;    .metric-card {    /* Metric Cards */<style>{% block extra_css %}{% endblock %}    </div>        {% endif %}        </div>            <p style="font-size: 14px; opacity: 0.7;">No patients awaiting payment at this time</p>            <p style="font-size: 18px; font-weight: 600;">All Caught Up!</p>            <i class="fas fa-check-circle" style="font-size: 60px; display: block; margin-bottom: 20px; opacity: 0.3; color: #2ed573;"></i>        <div style="text-align: center; padding: 80px; color: #999;">        {% else %}        </table>            </tbody>                {% endfor %}                </tr>                    </td>                        </div>                            </form>                                </button>                                    <i class="fas fa-check"></i> Record Payment                                <button type="submit" class="btn-small btn-success">                                <input type="text" name="reference" placeholder="Reference (optional)" class="form-input-small">                                </select>                                    {% endfor %}                                        <option value="{{ value }}">{{ label }}</option>                                    {% for value, label in payment_method_choices %}                                    <option value="">Payment Method</option>                                <select name="method" class="form-select-small" required>                                {% csrf_token %}                            <form method="post" action="{% url 'mark_paid' visit.id %}" style="display: flex; gap: 8px; flex-wrap: wrap;" onsubmit="return confirm('Confirm payment received?');">                            </div>                                </a>                                    <i class="fas fa-print"></i> Print                                <a href="{% url 'print_invoice' visit.id %}" target="_blank" class="btn-small btn-secondary">                                </a>                                    <i class="fas fa-file-invoice"></i> View Invoice                                <a href="{% url 'view_invoice' visit.id %}" class="btn-small btn-primary">                            <div style="display: flex; gap: 8px;">                        <div style="display: flex; flex-direction: column; gap: 12px;">                    <td>                    </td>                        <span class="badge badge-warning">Pending Payment</span>                    <td>                    </td>                        <span class="badge badge-info">{{ visit.billing_items.count }} items</span>                    <td>                    </td>                        <div style="font-size: 12px; color: #666;">{{ visit.created_at|time:"H:i" }}</div>                        <div>{{ visit.created_at|date:"M d, Y" }}</div>                    <td>                    </td>                        <div style="font-size: 12px; color: #666;">{{ visit.department.name|default:"N/A" }}</div>                        <div style="font-weight: 500;">Dr. {{ visit.doctor.user.get_full_name|default:visit.doctor.user.username }}</div>                    <td>                    </td>                        </div>                            </div>                                <div style="font-size: 12px; color: #666;">{{ visit.patient.phone|default:"N/A" }}</div>                                <div style="font-weight: 600;">{{ visit.patient.first_name }} {{ visit.patient.last_name }}</div>                            <div>                            </div>                                <i class="fas fa-user"></i>                            <div style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white;">                        <div style="display: flex; align-items: center; gap: 12px;">                    <td>                <tr>                {% for visit in awaiting_payment %}            <tbody>            </thead>                </tr>                    <th>Actions</th>                    <th>Status</th>                    <th>Items</th>                    <th>Visit Date</th>                    <th>Doctor</th>                    <th>Patient</th>                <tr>            <thead>        <table>        {% if awaiting_payment %}        </h3>            {% endif %}            </span>                <i class="fas fa-exclamation-circle"></i> Action Required            <span style="font-size: 14px; font-weight: normal; color: #ff9800;">            {% if awaiting_payment.count > 0 %}            </span>                <i class="fas fa-users"></i> Patients Awaiting Payment ({{ awaiting_payment.count }})            <span>        <h3 class="table-title" style="display: flex; justify-content: space-between; align-items: center;">    <div class="table-container" id="awaiting-payments">    <!-- Patients Awaiting Payment -->    </div>        {% endif %}        </div>            <p style="font-size: 14px; opacity: 0.7;">Completed payments will appear here</p>            <p style="font-size: 16px;">No transactions recorded today</p>            <i class="fas fa-inbox" style="font-size: 50px; display: block; margin-bottom: 15px; opacity: 0.3;"></i>        <div style="text-align: center; padding: 60px; color: #999;">        {% else %}        </div>            </table>                </tbody>                    {% endfor %}                    </tr>                        <td>{{ payment.reference|default:"—" }}</td>                        </td>                            {% endif %}                                <span class="badge badge-default">{{ payment.get_method_display }}</span>                            {% else %}                                <span class="badge badge-secondary">Bank Transfer</span>                            {% elif payment.method == 'bank' %}                                <span class="badge badge-primary">Card</span>                            {% elif payment.method == 'card' %}                                <span class="badge badge-info">Mobile Money</span>                            {% elif payment.method == 'momo' %}                                <span class="badge badge-success">Cash</span>                            {% if payment.method == 'cash' %}                        <td>                        <td><strong style="color: #2ed573;">{{ payment.amount|floatformat:0 }} RWF</strong></td>                        <td>{{ payment.invoice.visit.patient.first_name }} {{ payment.invoice.visit.patient.last_name }}</td>                        <td><strong>#{{ payment.invoice.id }}</strong></td>                        <td>{{ payment.paid_at|date:"H:i" }}</td>                    <tr>                    {% for payment in today_transactions %}                <tbody>                </thead>                    </tr>                        <th>Reference</th>                        <th>Method</th>                        <th>Amount</th>                        <th>Patient</th>                        <th>Invoice #</th>                        <th>Time</th>                    <tr>                <thead>            <table>        <div style="max-height: 400px; overflow-y: auto;">        {% if today_transactions %}        </h3>            <i class="fas fa-history"></i> Today's Transactions ({{ today_transactions.count }})        <h3 class="table-title">    <div class="table-container" style="margin-bottom: 30px;">    <!-- Today's Transactions -->    </div>        </div>            </div>                </button>                    <i class="fas fa-receipt"></i> View Receipts                <button class="action-btn" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);" onclick="viewReceipts()">                </button>                    <i class="fas fa-print"></i> Print Daily Report                <button class="action-btn" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);" onclick="window.print()">                </button>                    <i class="fas fa-list"></i> All Transactions                <button class="action-btn" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);" onclick="viewAllTransactions()">                </button>                    <i class="fas fa-money-bill-wave"></i> Process Payments                <button class="action-btn" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);" onclick="scrollToPayments()">            <div style="display: flex; flex-direction: column; gap: 12px;">            </h3>                <i class="fas fa-bolt"></i> Quick Actions            <h3 style="color: #8B3A8B; margin-bottom: 20px; font-size: 18px;">        <div class="stat-box" style="flex-direction: column; align-items: stretch;">        <!-- Quick Actions -->        </div>            </div>                <canvas id="paymentMethodsChart" height="100"></canvas>            <div class="chart-body">            </div>                </h3>                    <i class="fas fa-credit-card"></i> Today's Payment Methods                <h3 class="chart-title">            <div class="chart-header">        <div class="chart-container">        <!-- Payment Methods Chart -->    <div style="display: grid; grid-template-columns: 1.5fr 1fr; gap: 25px; margin-bottom: 30px;">    <!-- Payment Methods Breakdown -->    </div>        </div>            </div>                <div class="metric-currency">Invoices</div>                <div class="metric-value">{{ pending_count }}</div>                <div class="metric-label">Pending Payments</div>            <div class="metric-content">            </div>                <i class="fas fa-hourglass-half"></i>            <div class="metric-icon">        <div class="metric-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">        <!-- Pending Payments -->        </div>            </div>                <div class="metric-currency">RWF</div>                <div class="metric-value">{{ month_revenue|floatformat:0 }}</div>                <div class="metric-label">This Month</div>            <div class="metric-content">            </div>                <i class="fas fa-calendar-alt"></i>            <div class="metric-icon">        <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">        <!-- This Month -->        </div>            </div>                <div class="metric-currency">RWF</div>                <div class="metric-value">{{ week_revenue|floatformat:0 }}</div>                <div class="metric-label">This Week</div>            <div class="metric-content">            </div>                <i class="fas fa-calendar-week"></i>            <div class="metric-icon">        <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">        <!-- This Week -->        </div>            </div>                <div style="font-size: 12px; opacity: 0.9; margin-top: 5px;">{{ today_count }} transactions</div>                <div class="metric-currency">RWF</div>                <div class="metric-value">{{ today_revenue|floatformat:0 }}</div>                <div class="metric-label">Today's Revenue</div>            <div class="metric-content">            </div>                <i class="fas fa-coins"></i>            <div class="metric-icon">        <div class="metric-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">        <!-- Today's Revenue -->    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 30px;">    <!-- Quick Stats Cards -->    </div>        Welcome back, <strong>{{ cashier_name }}</strong> - Track and process all payment transactions    <div class="page-subtitle">{% block dashboard_content %}{% endblock %}    </li>        </a>            <i class="fas fa-file-alt"></i> Daily Report        <a href="{% url 'cashier_dashboard' %}" class="nav-link">    <li class="nav-item">    </li>        </a>            {% endif %}                <span class="badge badge-warning ml-2">{{ pending_count }}</span>            {% if pending_count > 0 %}            <i class="fas fa-users"></i> Pending Payments        <a href="{% url 'cashier_dashboard' %}" class="nav-link">    <li class="nav-item">    </li>        </a>            <i class="fas fa-receipt"></i> All Transactions        <a href="{% url 'cashier_dashboard' %}" class="nav-link">    <li class="nav-item">    </li>        </a>            <i class="fas fa-tachometer-alt"></i> Dashboard        <a href="{% url 'cashier_dashboard' %}" class="nav-link active">    <li class="nav-item">{% block nav_items %}{% endblock %}    <i class="fas fa-cash-register"></i> Cashier Portal{% block page_title %}{% block title %}Cashier Dashboard - Nora Dental Clinic{% endblock %}Comprehensive Financial Officer Views
Includes all financial reports, expense management, purchase tracking, inventory management
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Sum, Count, Q, F, DecimalField, Value, Avg
from django.db.models.functions import TruncDate, TruncMonth, TruncYear, Coalesce
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator

from clinic.models import (
    Invoice, BillingItem, Payment, Patient, Visit, ClinicUser, 
    Department, TariffAct
)
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


# ==================== MAIN DASHBOARD ====================

@login_required
@user_passes_test(is_finance_officer)
def finance_officer_dashboard(request):
    """Main dashboard for financial officer with comprehensive overview"""
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)
    
    # Revenue Summary
    # Today
    today_invoices = Invoice.objects.filter(created_at__date=today)
    today_revenue_data = today_invoices.aggregate(
        insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
        private=Sum('total_private', default=0, output_field=DecimalField())
    )
    today_revenue = (today_revenue_data['insurance'] or 0) + (today_revenue_data['private'] or 0)
    
    # Month
    month_invoices = Invoice.objects.filter(
        created_at__date__gte=month_start,
        created_at__date__lte=today
    )
    month_revenue_data = month_invoices.aggregate(
        insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
        private=Sum('total_private', default=0, output_field=DecimalField())
    )
    month_revenue = (month_revenue_data['insurance'] or 0) + (month_revenue_data['private'] or 0)
    
    # Year
    year_invoices = Invoice.objects.filter(
        created_at__date__gte=year_start,
        created_at__date__lte=today
    )
    year_revenue_data = year_invoices.aggregate(
        insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
        private=Sum('total_private', default=0, output_field=DecimalField())
    )
    year_revenue = (year_revenue_data['insurance'] or 0) + (year_revenue_data['private'] or 0)
    
    # Expenses Summary
    today_expenses = Expense.objects.filter(
        expense_date=today,
        status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    month_expenses = Expense.objects.filter(
        expense_date__gte=month_start,
        expense_date__lte=today,
        status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    year_expenses = Expense.objects.filter(
        expense_date__gte=year_start,
        expense_date__lte=today,
        status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Net Profit/Loss
    today_profit = today_revenue - today_expenses
    month_profit = month_revenue - month_expenses
    year_profit = year_revenue - year_expenses
    
    # Department Breakdown (Current Month)
    dept_revenue = month_invoices.values(
        'visit__department__name'
    ).annotate(
        total_insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
        total_private=Sum('total_private', default=0, output_field=DecimalField()),
        count=Count('id')
    ).order_by('-total_insurance')
    
    for item in dept_revenue:
        item['total'] = (item['total_insurance'] or 0) + (item['total_private'] or 0)
    
    # Pending Approvals
    pending_expenses = Expense.objects.filter(status='pending').count()
    
    # Stock Alerts
    active_alerts = StockAlert.objects.filter(status='active').count()
    low_stock_items = ConsumableInventory.objects.filter(
        quantity_in_stock__lte=F('minimum_stock_level')
    ).count()
    
    # Recent Transactions
    recent_invoices = Invoice.objects.select_related(
        'visit__patient', 'visit__doctor__user', 'visit__department'
    ).order_by('-created_at')[:10]
    
    recent_expenses = Expense.objects.select_related(
        'requested_by__user', 'department'
    ).order_by('-expense_date')[:10]
    
    context = {
        # Revenue
        'today_revenue': float(today_revenue),
        'month_revenue': float(month_revenue),
        'year_revenue': float(year_revenue),
        
        # Expenses
        'today_expenses': float(today_expenses),
        'month_expenses': float(month_expenses),
        'year_expenses': float(year_expenses),
        
        # Profit/Loss
        'today_profit': float(today_profit),
        'month_profit': float(month_profit),
        'year_profit': float(year_profit),
        
        # Breakdowns
        'dept_revenue': dept_revenue,
        
        # Alerts
        'pending_expenses': pending_expenses,
        'active_alerts': active_alerts,
        'low_stock_items': low_stock_items,
        
        # Recent
        'recent_invoices': recent_invoices,
        'recent_expenses': recent_expenses,
    }
    
    return render(request, 'finance/dashboard_new.html', context)


# ==================== INCOME REPORTS ====================

@login_required
@user_passes_test(is_finance_officer)
def income_statement(request):
    """Comprehensive income statement with filtering"""
    # Get filter parameters
    period = request.GET.get('period', 'monthly')  # daily, monthly, annual
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    department_id = request.GET.get('department')
    
    today = timezone.now().date()
    
    # Determine date range
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    elif period == 'daily':
        start_date = today
        end_date = today
    elif period == 'monthly':
        start_date = today.replace(day=1)
        end_date = today
    else:  # annual
        start_date = today.replace(month=1, day=1)
        end_date = today
    
    # Get invoices
    invoices = Invoice.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    if department_id:
        invoices = invoices.filter(visit__department_id=department_id)
    
    # Revenue Summary
    revenue_summary = invoices.aggregate(
        total_insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
        total_private=Sum('total_private', default=0, output_field=DecimalField()),
        count=Count('id')
    )
    
    total_revenue = (revenue_summary['total_insurance'] or 0) + (revenue_summary['total_private'] or 0)
    
    # Expenses
    expenses = Expense.objects.filter(
        expense_date__gte=start_date,
        expense_date__lte=end_date,
        status='paid'
    )
    
    if department_id:
        expenses = expenses.filter(department_id=department_id)
    
    expense_summary = expenses.aggregate(
        total=Sum('amount', default=0, output_field=DecimalField())
    )
    
    total_expenses = expense_summary['total'] or 0
    
    # Net Profit/Loss
    net_profit = total_revenue - total_expenses
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Revenue by Category
    revenue_by_dept = invoices.values(
        'visit__department__name'
    ).annotate(
        insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
        private=Sum('total_private', default=0, output_field=DecimalField()),
        count=Count('id')
    ).order_by('-insurance')
    
    for item in revenue_by_dept:
        item['total'] = (item['insurance'] or 0) + (item['private'] or 0)
        item['percentage'] = (item['total'] / total_revenue * 100) if total_revenue > 0 else 0
    
    # Expenses by Category
    expenses_by_category = expenses.values('category').annotate(
        total=Sum('amount', default=0, output_field=DecimalField()),
        count=Count('id')
    ).order_by('-total')
    
    for item in expenses_by_category:
        item['percentage'] = (item['total'] / total_expenses * 100) if total_expenses > 0 else 0
    
    # Payment Methods Breakdown
    payments = Payment.objects.filter(
        paid_at__date__gte=start_date,
        paid_at__date__lte=end_date
    )
    
    payment_methods = payments.values('method').annotate(
        total=Sum('amount', default=0, output_field=DecimalField()),
        count=Count('id')
    ).order_by('-total')
    
    departments = Department.objects.all()
    
    context = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'department_id': department_id,
        'departments': departments,
        
        # Summary
        'total_revenue': float(total_revenue),
        'total_expenses': float(total_expenses),
        'net_profit': float(net_profit),
        'profit_margin': float(profit_margin),
        'invoice_count': revenue_summary['count'],
        
        # Breakdowns
        'revenue_by_dept': revenue_by_dept,
        'expenses_by_category': expenses_by_category,
        'payment_methods': payment_methods,
        
        # Details
        'total_insurance_revenue': float(revenue_summary['total_insurance'] or 0),
        'total_private_revenue': float(revenue_summary['total_private'] or 0),
    }
    
    return render(request, 'finance/income_statement.html', context)


@login_required
@user_passes_test(is_finance_officer)
def department_financial_report(request, dept_id=None):
    """Detailed financial report by department (General Dentistry, Ortho, OMS, ODS)"""
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    period = request.GET.get('period', 'monthly')
    
    # Get dept_id from GET parameters if not in URL
    if not dept_id:
        dept_id = request.GET.get('dept_id')
    
    today = timezone.now().date()
    
    # Date range
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    elif period == 'daily':
        start_date = today
        end_date = today
    elif period == 'monthly':
        start_date = today.replace(day=1)
        end_date = today
    else:  # annual
        start_date = today.replace(month=1, day=1)
        end_date = today
    
    departments = Department.objects.all()
    selected_dept = None
    
    if dept_id:
        selected_dept = get_object_or_404(Department, id=dept_id)
    else:
        selected_dept = departments.first()
    
    if selected_dept:
        # Get invoices for department
        invoices = Invoice.objects.filter(
            visit__department=selected_dept,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).select_related('visit__patient', 'visit__doctor__user')
        
        # Revenue Summary
        revenue_data = invoices.aggregate(
            insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
            private=Sum('total_private', default=0, output_field=DecimalField()),
            count=Count('id')
        )
        
        total_revenue = (revenue_data['insurance'] or 0) + (revenue_data['private'] or 0)
        
        # Doctor Performance
        doctor_revenue = invoices.values(
            doctor_id=F('visit__doctor__id'),
            doctor_name=F('visit__doctor__user__first_name'),
            doctor_lastname=F('visit__doctor__user__last_name')
        ).annotate(
            insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
            private=Sum('total_private', default=0, output_field=DecimalField()),
            count=Count('id')
        ).order_by('-insurance')
        
        for item in doctor_revenue:
            item['total'] = (item['insurance'] or 0) + (item['private'] or 0)
            item['percentage'] = (item['total'] / total_revenue * 100) if total_revenue > 0 else 0
        
        # Insurance Breakdown
        insurance_revenue = invoices.filter(
            visit__patient__is_insured=True
        ).values(
            'visit__patient__insurer'
        ).annotate(
            insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
            private=Sum('total_private', default=0, output_field=DecimalField()),
            count=Count('id'),
            avg_coverage=Avg('visit__patient__insurance_coverage_pct')
        ).order_by('-insurance')
        
        for item in insurance_revenue:
            item['total'] = (item['insurance'] or 0) + (item['private'] or 0)
        
        # Beneficiary (Private Patients)
        private_patients = invoices.filter(
            visit__patient__is_insured=False
        ).aggregate(
            total=Sum(F('total_insurance') + F('total_private'), output_field=DecimalField()),
            count=Count('id')
        )
        
        # Payment Details
        payment_details = []
        for inv in invoices.order_by('-created_at')[:50]:
            payments = Payment.objects.filter(invoice=inv)
            payment_details.append({
                'invoice': inv,
                'patient': inv.visit.patient,
                'doctor': inv.visit.doctor,
                'amount': inv.total_insurance + inv.total_private,
                'insurance_amount': inv.total_insurance,
                'private_amount': inv.total_private,
                'insurance': inv.visit.patient.insurer if inv.visit.patient.is_insured else 'N/A',
                'coverage_pct': inv.visit.patient.insurance_coverage_pct if inv.visit.patient.is_insured else 0,
                'date': inv.created_at,
                'payments': payments,
            })
        
        # Expenses for this department
        dept_expenses = Expense.objects.filter(
            department=selected_dept,
            expense_date__gte=start_date,
            expense_date__lte=end_date,
            status='paid'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        net_profit = total_revenue - dept_expenses
        
    else:
        invoices = None
        revenue_data = {'insurance': 0, 'private': 0, 'count': 0}
        total_revenue = 0
        doctor_revenue = []
        insurance_revenue = []
        private_patients = {'total': 0, 'count': 0}
        payment_details = []
        dept_expenses = 0
        net_profit = 0
    
    context = {
        'departments': departments,
        'selected_dept': selected_dept,
        'start_date': start_date,
        'end_date': end_date,
        'period': period,
        
        # Summary
        'total_revenue': float(total_revenue),
        'total_insurance_revenue': float(revenue_data['insurance'] or 0),
        'total_private_revenue': float(revenue_data['private'] or 0),
        'invoice_count': revenue_data['count'],
        'dept_expenses': float(dept_expenses),
        'net_profit': float(net_profit),
        
        # Breakdowns
        'doctor_revenue': doctor_revenue,
        'insurance_revenue': insurance_revenue,
        'private_patients_total': float(private_patients['total'] or 0),
        'private_patients_count': private_patients['count'],
        
        # Details
        'payment_details': payment_details,
    }
    
    return render(request, 'finance/department_report.html', context)


@login_required
@user_passes_test(is_finance_officer)
def doctor_financial_report(request, doctor_id=None):
    """Financial report for individual or all doctors"""
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    period = request.GET.get('period', 'monthly')
    view_type = request.GET.get('view', 'individual')  # individual or general
    
    # Get doctor_id from GET parameters if not in URL
    if not doctor_id:
        doctor_id = request.GET.get('doctor_id')
    
    today = timezone.now().date()
    
    # Date range
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    elif period == 'daily':
        start_date = today
        end_date = today
    elif period == 'monthly':
        start_date = today.replace(day=1)
        end_date = today
    else:  # annual
        start_date = today.replace(month=1, day=1)
        end_date = today
    
    doctors = ClinicUser.objects.filter(role='doctor').select_related('user')
    
    if view_type == 'individual' and doctor_id:
        # Individual doctor report
        selected_doctor = get_object_or_404(ClinicUser, id=doctor_id, role='doctor')
        
        invoices = Invoice.objects.filter(
            visit__doctor=selected_doctor,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).select_related('visit__patient', 'visit__department')
        
        revenue_data = invoices.aggregate(
            insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
            private=Sum('total_private', default=0, output_field=DecimalField()),
            count=Count('id')
        )
        
        total_revenue = (revenue_data['insurance'] or 0) + (revenue_data['private'] or 0)
        
        # Department breakdown
        dept_revenue = invoices.values(
            'visit__department__name'
        ).annotate(
            total=Sum(F('total_insurance') + F('total_private'), output_field=DecimalField()),
            count=Count('id')
        ).order_by('-total')
        
        # Insurance breakdown
        insurance_breakdown = invoices.filter(
            visit__patient__is_insured=True
        ).values(
            'visit__patient__insurer'
        ).annotate(
            total=Sum('total_insurance', default=0, output_field=DecimalField()),
            count=Count('id')
        ).order_by('-total')
        
        doctor_data = [{
            'doctor': selected_doctor,
            'total_revenue': float(total_revenue),
            'insurance_revenue': float(revenue_data['insurance'] or 0),
            'private_revenue': float(revenue_data['private'] or 0),
            'invoice_count': revenue_data['count'],
            'dept_revenue': dept_revenue,
            'insurance_breakdown': insurance_breakdown,
        }]
        
    else:
        # General report for all doctors
        selected_doctor = None
        doctor_data = []
        
        for doctor in doctors:
            invoices = Invoice.objects.filter(
                visit__doctor=doctor,
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )
            
            revenue_data = invoices.aggregate(
                insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
                private=Sum('total_private', default=0, output_field=DecimalField()),
                count=Count('id')
            )
            
            total_revenue = (revenue_data['insurance'] or 0) + (revenue_data['private'] or 0)
            
            doctor_data.append({
                'doctor': doctor,
                'total_revenue': float(total_revenue),
                'insurance_revenue': float(revenue_data['insurance'] or 0),
                'private_revenue': float(revenue_data['private'] or 0),
                'invoice_count': revenue_data['count'],
            })
        
        # Sort by revenue
        doctor_data.sort(key=lambda x: x['total_revenue'], reverse=True)
    
    context = {
        'doctors': doctors,
        'selected_doctor': selected_doctor,
        'view_type': view_type,
        'start_date': start_date,
        'end_date': end_date,
        'period': period,
        'doctor_data': doctor_data,
    }
    
    return render(request, 'finance/doctor_report.html', context)


@login_required
@user_passes_test(is_finance_officer)
def insurance_report(request):
    """Comprehensive insurance report"""
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    period = request.GET.get('period', 'monthly')
    insurer = request.GET.get('insurer')
    
    today = timezone.now().date()
    
    # Date range
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    elif period == 'daily':
        start_date = today
        end_date = today
    elif period == 'monthly':
        start_date = today.replace(day=1)
        end_date = today
    else:  # annual
        start_date = today.replace(month=1, day=1)
        end_date = today
    
    # Get insured invoices
    invoices = Invoice.objects.filter(
        visit__patient__is_insured=True,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    if insurer:
        invoices = invoices.filter(visit__patient__insurer=insurer)
    
    # Get unique insurers
    insurers = Invoice.objects.filter(
        visit__patient__is_insured=True
    ).values_list('visit__patient__insurer', flat=True).distinct()
    
    # Summary by insurer
    insurer_summary = invoices.values(
        'visit__patient__insurer'
    ).annotate(
        total_billed=Sum(F('total_insurance') + F('total_private'), output_field=DecimalField()),
        insurance_portion=Sum('total_insurance', default=0, output_field=DecimalField()),
        patient_portion=Sum('total_private', default=0, output_field=DecimalField()),
        count=Count('id'),
        avg_coverage=Avg('visit__patient__insurance_coverage_pct')
    ).order_by('-insurance_portion')
    
    # Department breakdown per insurer
    dept_breakdown = invoices.values(
        'visit__patient__insurer',
        'visit__department__name'
    ).annotate(
        total=Sum(F('total_insurance') + F('total_private'), output_field=DecimalField()),
        count=Count('id')
    ).order_by('visit__patient__insurer', '-total')
    
    # Detailed invoice list
    detailed_invoices = invoices.select_related(
        'visit__patient', 'visit__doctor__user', 'visit__department'
    ).order_by('-created_at')[:100]
    
    invoice_details = []
    for inv in detailed_invoices:
        total = inv.total_insurance + inv.total_private
        coverage_pct = Decimal(str(inv.visit.patient.insurance_coverage_pct or 0))
        insurance_pays = total * (coverage_pct / Decimal('100'))
        patient_pays = total * ((Decimal('100') - coverage_pct) / Decimal('100'))
        
        invoice_details.append({
            'invoice': inv,
            'patient': inv.visit.patient,
            'doctor': inv.visit.doctor,
            'department': inv.visit.department,
            'total': float(total),
            'insurance_pays': float(insurance_pays),
            'patient_pays': float(patient_pays),
            'coverage_pct': coverage_pct,
            'date': inv.created_at,
        })
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'period': period,
        'selected_insurer': insurer,
        'insurers': insurers,
        'insurer_summary': insurer_summary,
        'dept_breakdown': dept_breakdown,
        'invoice_details': invoice_details,
    }
    
    return render(request, 'finance/insurance_report.html', context)


# Continue in next part...
