# clinic/views_cashier.py
"""Cashier dashboard and payment processing"""

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta, date
from clinic.models import Invoice, BillingItem, Patient, ClinicUser, Visit, Payment, Refund
from django.db.models import Sum, Count, Q
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages


COMPLETED_STATUSES = ['completed', 'awaiting_payment']


def _sync_invoice_totals(invoice: Invoice) -> float:
    """Recalculate and persist invoice totals, returning the combined amount."""
    billing_items = invoice.visit.billing_items.all()
    total_private = sum(item.qty * item.price_private_snapshot for item in billing_items)
    total_insurance = sum(item.qty * (item.price_insurance_snapshot or 0) for item in billing_items)
    invoice.total_private = total_private
    invoice.total_insurance = total_insurance
    invoice.save(update_fields=['total_private', 'total_insurance'])
    return (total_private or 0) + (total_insurance or 0)


@require_http_methods(["GET", "POST"])
def cashier_login(request):
    """Custom login page for cashier staff"""
    if request.user.is_authenticated:
        # If already logged in, redirect to dashboard
        return redirect('/cashier/')
    
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user is cashier
            try:
                clinic_user = user.clinicuser
                if clinic_user.role == 'cashier':
                    login(request, user)
                    return redirect('/cashier/')
                else:
                    return render(request, 'cashier/login.html', {
                        'error': 'You do not have cashier privileges. Please contact your administrator.'
                    })
            except ClinicUser.DoesNotExist:
                return render(request, 'cashier/login.html', {
                    'error': 'You do not have cashier privileges. Please contact your administrator.'
                })
        else:
            return render(request, 'cashier/login.html', {
                'error': 'Invalid username or password.'
            })
    
    return render(request, 'cashier/login.html')


@login_required(login_url='/cashier/login/')
def cashier_dashboard(request):
    """Cashier dashboard for payment tracking"""
    # Check if user is cashier
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'cashier':
        messages.error(request, 'Access denied. Cashier role required.')
        logout(request)
        return redirect('cashier_login')
    
    today = timezone.now().date()
    
    # Get cashier user info
    cashier_name = "Cashier"
    cashier_username = ""
    cashier_email = ""
    if hasattr(request.user, 'clinicuser'):
        clinic_user = request.user.clinicuser
        cashier_name = clinic_user.user.get_full_name() or clinic_user.user.username
        cashier_username = clinic_user.user.username
        cashier_email = clinic_user.user.email or ""
    
    # Get visits that are completed but still unpaid (invoice missing or unpaid)
    awaiting_payment = (
        Visit.objects.filter(status__in=COMPLETED_STATUSES, billing_items__isnull=False)
        .filter(Q(invoice__paid=False) | Q(invoice__isnull=True))
        .select_related('patient', 'doctor')
        .prefetch_related('billing_items__tariff', 'triage')
        .order_by('-created_at')
        .distinct()
    )
    
    # Today's payments - sum both total_private and total_insurance
    today_invoices = Invoice.objects.filter(created_at__date=today)
    today_private = today_invoices.aggregate(total=Sum('total_private'))['total'] or 0
    today_insurance = today_invoices.aggregate(total=Sum('total_insurance'))['total'] or 0
    today_revenue = today_private + today_insurance
    today_count = today_invoices.count()
    
    # This week
    week_start = today - timedelta(days=today.weekday())
    week_invoices = Invoice.objects.filter(created_at__date__gte=week_start)
    week_private = week_invoices.aggregate(total=Sum('total_private'))['total'] or 0
    week_insurance = week_invoices.aggregate(total=Sum('total_insurance'))['total'] or 0
    week_revenue = week_private + week_insurance
    
    # This month
    month_start = today.replace(day=1)
    month_invoices = Invoice.objects.filter(created_at__date__gte=month_start)
    month_private = month_invoices.aggregate(total=Sum('total_private'))['total'] or 0
    month_insurance = month_invoices.aggregate(total=Sum('total_insurance'))['total'] or 0
    month_revenue = month_private + month_insurance
    
    # Payment methods - get from Payment model
    payment_methods = Payment.objects.filter(
        paid_at__date=today
    ).values('method').annotate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    # Outstanding/pending payments
    pending = Invoice.objects.filter(
        paid=False,
        created_at__date=today
    )
    
    # Today's transactions (completed payments)
    today_transactions = Payment.objects.filter(
        paid_at__date=today
    ).select_related('invoice__visit__patient').order_by('-paid_at')[:10]
    
    # Recent transactions
    recent = Invoice.objects.select_related('visit__patient').order_by('-created_at')[:15]
    
    context = {
        'cashier_name': cashier_name,
        'cashier_username': cashier_username,
        'cashier_email': cashier_email,
        'awaiting_payment': awaiting_payment,
        'payment_method_choices': Payment.METHOD_CHOICES,
        'today_revenue': today_revenue,
        'today_count': today_count,
        'week_revenue': week_revenue,
        'month_revenue': month_revenue,
        'payment_methods': payment_methods,
        'pending_count': pending.count(),
        'recent_invoices': recent,
        'today_transactions': today_transactions,
    }
    
    return render(request, 'cashier/dashboard_professional.html', context)


@login_required(login_url='/cashier/login/')
def cashier_payments(request):
    """View and manage payments"""
    # Check if user is cashier
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'cashier':
        messages.error(request, 'Access denied. Cashier role required.')
        return redirect('cashier_login')
    
    invoices = Invoice.objects.select_related('visit__patient').order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status', 'all')
    if status == 'paid':
        invoices = invoices.filter(paid=True)
    elif status == 'pending':
        invoices = invoices.filter(paid=False)
    
    context = {
        'invoices': invoices,
        'status': status,
    }
    
    return render(request, 'cashier/payments.html', context)


@login_required(login_url='/cashier/login/')
def cashier_daily_reconciliation(request):
    """Daily payment reconciliation"""
    # Check if user is cashier
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'cashier':
        messages.error(request, 'Access denied. Cashier role required.')
        return redirect('cashier_login')
    
    today = timezone.now().date()
    
    invoices = Invoice.objects.filter(created_at__date=today)
    
    # Calculate total from private and insurance amounts
    total_private = invoices.aggregate(total=Sum('total_private'))['total'] or 0
    total_insurance = invoices.aggregate(total=Sum('total_insurance'))['total'] or 0
    total = total_private + total_insurance
    
    # Get payment method totals from Payment model
    payments_today = Payment.objects.filter(invoice__created_at__date=today)
    cash = payments_today.filter(method='cash').aggregate(total=Sum('amount'))['total'] or 0
    card = payments_today.filter(method='card').aggregate(total=Sum('amount'))['total'] or 0
    insurance = payments_today.filter(method='insurance').aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'date': today,
        'total': total,
        'total_private': total_private,
        'total_insurance': total_insurance,
        'cash': cash,
        'card': card,
        'insurance': insurance,
        'invoices': invoices,
    }
    
    return render(request, 'cashier/daily_reconciliation.html', context)


@login_required(login_url='/cashier/login/')
def view_invoice(request, visit_id):
    """View invoice details for a visit"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'cashier':
        messages.error(request, 'Access denied. Cashier role required.')
        return redirect('cashier_login')
    
    # Allow viewing invoices regardless of status (awaiting_payment or completed)
    visit = get_object_or_404(Visit, id=visit_id)
    
    # Get or create invoice
    try:
        invoice = visit.invoice
    except Invoice.DoesNotExist:
        from django.utils.crypto import get_random_string
        invoice = Invoice.objects.create(
            visit=visit,
            receipt_number=get_random_string(12)
        )
    
    # Calculate totals
    billing_items = BillingItem.objects.filter(visit=visit).select_related('tariff')
    total_private = sum(item.qty * item.price_private_snapshot for item in billing_items)
    total_insurance = sum(item.qty * (item.price_insurance_snapshot or 0) for item in billing_items)
    
    # Insurance calculation
    coverage_pct = visit.patient.insurance_coverage_pct if visit.patient.is_insured else 0
    insurance_pays = (total_insurance * coverage_pct) / 100
    patient_pays_insurance = total_insurance - insurance_pays
    patient_pays_total = patient_pays_insurance
    
    # Get prescriptions for this visit
    from .models import Prescription
    prescriptions = Prescription.objects.filter(visit=visit).prefetch_related('items')
    
    context = {
        'visit': visit,
        'invoice': invoice,
        'billing_items': billing_items,
        'total_private': total_private,
        'total_insurance': total_insurance,
        'coverage_pct': coverage_pct,
        'insurance_pays': insurance_pays,
        'patient_pays_insurance': patient_pays_insurance,
        'patient_pays_total': patient_pays_total,
        'payment_method_choices': Payment.METHOD_CHOICES,
        'prescriptions': prescriptions,
    }
    
    return render(request, 'cashier/invoice.html', context)


@login_required(login_url='/cashier/login/')
def print_invoice(request, visit_id):
    """Generate printable invoice"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'cashier':
        messages.error(request, 'Access denied. Cashier role required.')
        return redirect('cashier_login')
    
    visit = get_object_or_404(Visit, id=visit_id)
    
    # Get or create invoice
    try:
        invoice = visit.invoice
    except Invoice.DoesNotExist:
        from django.utils.crypto import get_random_string
        invoice = Invoice.objects.create(
            visit=visit,
            receipt_number=get_random_string(12)
        )
    
    # Calculate totals
    billing_items = BillingItem.objects.filter(visit=visit).select_related('tariff')
    
    # Add subtotal to each billing item
    items_with_subtotal = []
    for item in billing_items:
        if visit.patient.is_insured:
            subtotal = item.qty * (item.price_insurance_snapshot or 0)
        else:
            subtotal = item.qty * item.price_private_snapshot
        items_with_subtotal.append({
            'item': item,
            'subtotal': subtotal
        })
    
    total_private = sum(item.qty * item.price_private_snapshot for item in billing_items)
    total_insurance = sum(item.qty * (item.price_insurance_snapshot or 0) for item in billing_items)
    
    # Insurance calculation
    coverage_pct = visit.patient.insurance_coverage_pct if visit.patient.is_insured else 0
    insurance_pays = (total_insurance * coverage_pct) / 100
    patient_pays_insurance = total_insurance - insurance_pays
    patient_pays_total = patient_pays_insurance
    
    context = {
        'visit': visit,
        'invoice': invoice,
        'billing_items': items_with_subtotal,
        'total_private': total_private,
        'total_insurance': total_insurance,
        'coverage_pct': coverage_pct,
        'insurance_pays': insurance_pays,
        'patient_pays_insurance': patient_pays_insurance,
        'patient_pays_total': patient_pays_total,
    }
    
    return render(request, 'cashier/print_invoice.html', context)


@login_required(login_url='/cashier/login/')
@require_http_methods(["POST"])
def mark_paid(request, visit_id):
    """Mark invoice as paid"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'cashier':
        messages.error(request, 'Access denied. Cashier role required.')
        return redirect('cashier_login')
    
    visit = get_object_or_404(Visit, id=visit_id)

    # Ensure an invoice exists so payment can be tracked
    from django.utils.crypto import get_random_string
    try:
        invoice = visit.invoice
    except Invoice.DoesNotExist:
        invoice = Invoice.objects.create(
            visit=visit,
            receipt_number=get_random_string(12)
        )

    raw_method = request.POST.get('method', '')
    method = raw_method.strip() if isinstance(raw_method, str) else ''
    raw_reference = request.POST.get('reference', '')
    reference = raw_reference.strip() if isinstance(raw_reference, str) else ''

    valid_methods = dict(Payment.METHOD_CHOICES)
    if method not in valid_methods:
        messages.error(request, 'Select a valid payment method before recording the transaction.')
        return redirect('cashier_dashboard')

    if invoice.paid:
        messages.info(
            request,
            f'Invoice for {visit.patient.first_name} {visit.patient.last_name} is already marked as paid.'
        )
        return redirect('cashier_dashboard')

    # Accept both legacy awaiting_payment and new completed statuses
    if visit.status not in COMPLETED_STATUSES:
        messages.error(request, f'This visit is not ready for payment. Current status: {visit.status}')
        return redirect('cashier_dashboard')

    amount_due = _sync_invoice_totals(invoice)
    if amount_due <= 0:
        messages.error(request, 'Unable to record payment because no billable items were found on this visit.')
        return redirect('cashier_dashboard')

    Payment.objects.create(
        invoice=invoice,
        amount=amount_due,
        method=method,
        reference=reference or None,
    )

    invoice_fields = ['paid', 'paid_at']

    if Payment.clears_invoice_immediately(method):
        invoice.paid = True
        invoice.paid_at = timezone.now()
        invoice.save(update_fields=invoice_fields)
        if visit.status != 'completed':
            visit.status = 'completed'
            visit.save(update_fields=['status'])
        messages.success(
            request,
            f'Payment recorded via {valid_methods[method]}. Invoice closed and ready for printing.'
        )
    else:
        invoice.paid = False
        invoice.paid_at = None
        invoice.save(update_fields=invoice_fields)
        if visit.status != 'awaiting_payment':
            visit.status = 'awaiting_payment'
            visit.save(update_fields=['status'])
        messages.info(
            request,
            'Insurance payment recorded. Invoice will remain pending until the insurer confirms settlement.'
        )
    
    return redirect('cashier_dashboard')


def cashier_logout(request):
    """Logout cashier"""
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('cashier_login')


@login_required(login_url='/cashier/login/')
def refund_list(request):
    """View all refund requests"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'cashier':
        messages.error(request, 'Access denied. Cashier role required.')
        return redirect('cashier_login')
    
    status_filter = request.GET.get('status', 'all')
    
    refunds = Refund.objects.select_related('invoice__visit__patient', 'requested_by', 'processed_by').all()
    
    if status_filter != 'all':
        refunds = refunds.filter(status=status_filter)
    
    refunds = refunds.order_by('-requested_at')
    
    context = {
        'refunds': refunds,
        'status_filter': status_filter,
    }
    
    return render(request, 'cashier/refunds.html', context)


@login_required(login_url='/cashier/login/')
def request_refund(request):
    """Request a refund for an invoice"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'cashier':
        messages.error(request, 'Access denied. Cashier role required.')
        return redirect('cashier_login')
    
    if request.method == 'POST':
        invoice_id = request.POST.get('invoice_id')
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')
        
        try:
            invoice = Invoice.objects.get(id=invoice_id)
            
            # Validate amount
            total_amount = invoice.total_private + invoice.total_insurance
            if float(amount) > float(total_amount):
                messages.error(request, 'Refund amount cannot exceed invoice total.')
                return redirect('request_refund')
            
            # Create refund
            refund = Refund.objects.create(
                invoice=invoice,
                amount=amount,
                reason=reason,
                requested_by=request.user.clinicuser,
                status='completed'  # Auto-approve for cashiers
            )
            
            messages.success(request, f'Refund request created successfully. Refund ID: {refund.id}')
            return redirect('refund_list')
            
        except Invoice.DoesNotExist:
            messages.error(request, 'Invoice not found.')
        except Exception as e:
            messages.error(request, f'Error creating refund: {str(e)}')
    
    # Get paid invoices for refund
    invoices = Invoice.objects.filter(paid=True).select_related('visit__patient').order_by('-created_at')[:50]
    
    context = {
        'invoices': invoices,
    }
    
    return render(request, 'cashier/request_refund.html', context)


@login_required(login_url='/cashier/login/')
def process_refund(request, refund_id):
    """Process/approve a refund request"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'cashier':
        messages.error(request, 'Access denied. Cashier role required.')
        return redirect('cashier_login')
    
    refund = get_object_or_404(Refund, id=refund_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action == 'approve':
            refund.status = 'completed'
            refund.processed_by = request.user.clinicuser
            refund.processed_at = timezone.now()
            refund.notes = notes
            refund.save()
            messages.success(request, 'Refund approved and completed.')
        elif action == 'reject':
            refund.status = 'rejected'
            refund.processed_by = request.user.clinicuser
            refund.processed_at = timezone.now()
            refund.notes = notes
            refund.save()
            messages.warning(request, 'Refund rejected.')
        
        return redirect('refund_list')
    
    context = {
        'refund': refund,
    }
    
    return render(request, 'cashier/process_refund.html', context)


@login_required(login_url='/cashier/login/')
def view_receipts(request):
    """View all receipts/invoices with search and filter"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'cashier':
        messages.error(request, 'Access denied. Cashier role required.')
        return redirect('cashier_login')
    
    # Get filter parameters
    date_filter = request.GET.get('date', 'all')
    payment_status = request.GET.get('payment', 'all')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    invoices = Invoice.objects.select_related('visit__patient', 'created_by').all()
    
    # Apply date filter
    today = timezone.now().date()
    if date_filter == 'today':
        invoices = invoices.filter(created_at__date=today)
    elif date_filter == 'week':
        week_ago = today - timedelta(days=7)
        invoices = invoices.filter(created_at__date__gte=week_ago)
    elif date_filter == 'month':
        month_ago = today - timedelta(days=30)
        invoices = invoices.filter(created_at__date__gte=month_ago)
    
    # Apply payment status filter
    if payment_status == 'paid':
        invoices = invoices.filter(paid=True)
    elif payment_status == 'unpaid':
        invoices = invoices.filter(paid=False)
    
    # Apply search filter
    if search_query:
        invoices = invoices.filter(
            Q(receipt_number__icontains=search_query) |
            Q(visit__patient__first_name__icontains=search_query) |
            Q(visit__patient__last_name__icontains=search_query) |
            Q(visit__patient__phone__icontains=search_query) |
            Q(visit__patient__national_id__icontains=search_query)
        )
    
    # Order by most recent first
    invoices = invoices.order_by('-created_at')
    
    # Calculate statistics
    total_receipts = invoices.count()
    total_amount = sum((inv.total_private + inv.total_insurance) for inv in invoices)
    paid_receipts = invoices.filter(paid=True).count()
    unpaid_receipts = invoices.filter(paid=False).count()
    
    context = {
        'invoices': invoices,
        'date_filter': date_filter,
        'payment_status': payment_status,
        'search_query': search_query,
        'total_receipts': total_receipts,
        'total_amount': total_amount,
        'paid_receipts': paid_receipts,
        'unpaid_receipts': unpaid_receipts,
    }
    
    return render(request, 'cashier/receipts.html', context)


@login_required(login_url='/cashier/login/')
def cashier_print_prescription(request, prescription_id):
    """Print prescription - accessible by cashier"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'cashier':
        messages.error(request, 'Access denied. Cashier role required.')
        return redirect('cashier_login')
    
    from .models import Prescription
    
    prescription = get_object_or_404(
        Prescription.objects.select_related(
            'visit', 
            'visit__patient',
            'visit__patient__user',
            'doctor',
            'doctor__user'
        ).prefetch_related('items__inventory_item'),
        id=prescription_id
    )
    
    context = {
        'prescription': prescription,
        'print_date': timezone.now(),
    }
    return render(request, 'doctor/prescription_print.html', context)
