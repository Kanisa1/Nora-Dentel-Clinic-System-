# clinic/views_financial.py
"""Financial reports and dashboards"""

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta, date
from clinic.models import (
    Invoice, BillingItem, Patient, Visit, ClinicUser, 
    Department, TariffAct, Payment
)
from django.db.models import Sum, Count, Q, F, DecimalField, Value
from django.db.models.functions import TruncDate, TruncMonth, TruncYear, Coalesce


def financial_dashboard(request):
    """Main financial dashboard with revenue overview - UPDATED"""
    today = timezone.now().date()
    
    # Revenue this month
    month_start = today.replace(day=1)
    month_invoices = Invoice.objects.filter(
        created_at__date__gte=month_start,
        created_at__date__lte=today
    )
    
    # Calculate total revenue (insurance + private)
    month_revenue_data = month_invoices.aggregate(
        insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
        private=Sum('total_private', default=0, output_field=DecimalField())
    )
    month_revenue = (month_revenue_data['insurance'] or 0) + (month_revenue_data['private'] or 0)
    
    # Revenue today
    today_data = Invoice.objects.filter(
        created_at__date=today
    ).aggregate(
        insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
        private=Sum('total_private', default=0, output_field=DecimalField())
    )
    today_revenue = (today_data['insurance'] or 0) + (today_data['private'] or 0)
    
    # Revenue this year
    year_start = today.replace(month=1, day=1)
    year_data = Invoice.objects.filter(
        created_at__date__gte=year_start,
        created_at__date__lte=today
    ).aggregate(
        insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
        private=Sum('total_private', default=0, output_field=DecimalField())
    )
    year_revenue = (year_data['insurance'] or 0) + (year_data['private'] or 0)
    
    # Insurance vs Private
    insured_revenue = month_revenue_data['insurance'] or 0
    private_revenue = month_revenue_data['private'] or 0
    
    # Payment methods breakdown
    payment_breakdown = Payment.objects.filter(
        paid_at__date__gte=month_start,
        paid_at__date__lte=today
    ).values('method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Recent invoices
    recent_invoices = Invoice.objects.select_related(
        'visit__patient'
    ).order_by('-created_at')[:10]
    
    context = {
        'today_revenue': float(today_revenue),
        'month_revenue': float(month_revenue),
        'year_revenue': float(year_revenue),
        'insured_revenue': float(insured_revenue),
        'private_revenue': float(private_revenue),
        'payment_breakdown': payment_breakdown,
        'recent_invoices': recent_invoices,
    }
    
    return render(request, 'financial/dashboard.html', context)


def financial_reports_by_department(request, dept_id=None):
    """Financial reports grouped by department"""
    today = timezone.now().date()
    
    departments = Department.objects.all()
    selected_dept = None
    
    if dept_id:
        selected_dept = get_object_or_404(Department, id=dept_id)
    else:
        selected_dept = departments.first()
    
    # Get invoices for department
    invoices = Invoice.objects.filter(
        visit__department=selected_dept
    ).select_related('visit__patient', 'visit__doctor__user')
    
    # Summary stats
    summary_data = invoices.aggregate(
        insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
        private=Sum('total_private', default=0, output_field=DecimalField()),
        count=Count('id')
    )
    
    total_amount = (summary_data['insurance'] or 0) + (summary_data['private'] or 0)
    total_count = summary_data['count']
    avg_invoice = total_amount / total_count if total_count > 0 else 0
    
    insured_amount = summary_data['insurance'] or 0
    private_amount = summary_data['private'] or 0
    
    # By doctor
    doctor_revenue = invoices.values(
        'visit__doctor__user__first_name',
        'visit__doctor__user__last_name'
    ).annotate(
        total_insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
        total_private=Sum('total_private', default=0, output_field=DecimalField()),
        count=Count('id')
    ).order_by('-total_insurance', '-total_private')
    
    # Add total field to doctor_revenue for easier template iteration
    for item in doctor_revenue:
        item['total'] = (item['total_insurance'] or 0) + (item['total_private'] or 0)
    
    # By insurance provider
    insurance_revenue = invoices.filter(
        visit__patient__is_insured=True
    ).values(
        'visit__patient__insurer'
    ).annotate(
        total_insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
        total_private=Sum('total_private', default=0, output_field=DecimalField()),
        count=Count('id'),
        avg_coverage=Coalesce(F('visit__patient__insurance_coverage_pct'), Value(0))
    ).order_by('-total_insurance')
    
    for item in insurance_revenue:
        item['total'] = (item['total_insurance'] or 0) + (item['total_private'] or 0)
    
    context = {
        'departments': departments,
        'selected_dept': selected_dept,
        'invoices': invoices,
        'total_amount': float(total_amount),
        'total_count': total_count,
        'avg_invoice': float(avg_invoice),
        'insured_amount': float(insured_amount),
        'private_amount': float(private_amount),
        'doctor_revenue': doctor_revenue,
        'insurance_revenue': insurance_revenue,
    }
    
    return render(request, 'financial/reports_by_department.html', context)


def financial_reports_by_doctor(request, doctor_id=None):
    """Financial reports for each doctor"""
    today = timezone.now().date()
    
    doctors = ClinicUser.objects.filter(role='doctor').select_related('user')
    selected_doctor = None
    
    if doctor_id:
        selected_doctor = get_object_or_404(ClinicUser, id=doctor_id, role='doctor')
    else:
        selected_doctor = doctors.first()
    
    if selected_doctor:
        # Get invoices for doctor
        invoices = Invoice.objects.filter(
            visit__doctor=selected_doctor
        ).select_related('visit__patient', 'visit__department')
        
        # Summary stats
        summary_data = invoices.aggregate(
            insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
            private=Sum('total_private', default=0, output_field=DecimalField()),
            count=Count('id')
        )
        
        total_amount = (summary_data['insurance'] or 0) + (summary_data['private'] or 0)
        total_count = summary_data['count']
        avg_invoice = total_amount / total_count if total_count > 0 else 0
        
        insured_amount = summary_data['insurance'] or 0
        private_amount = summary_data['private'] or 0
        
        # By department
        dept_revenue = invoices.values(
            'visit__department__name'
        ).annotate(
            total_insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
            total_private=Sum('total_private', default=0, output_field=DecimalField()),
            count=Count('id')
        ).order_by('-total_insurance')
        
        for item in dept_revenue:
            item['total'] = (item['total_insurance'] or 0) + (item['total_private'] or 0)
        
        # By insurance provider
        insurance_breakdown = invoices.filter(
            visit__patient__is_insured=True
        ).values(
            'visit__patient__insurer'
        ).annotate(
            total=Sum('total_insurance', default=0, output_field=DecimalField()),
            count=Count('id')
        ).order_by('-total')
        
        # Patient payments detail
        patient_payments = invoices.values(
            'visit__patient__first_name',
            'visit__patient__last_name',
            'visit__patient__phone',
            'visit__patient__is_insured',
            'visit__patient__insurer',
            'visit__patient__insurance_coverage_pct'
        ).annotate(
            total_insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
            total_private=Sum('total_private', default=0, output_field=DecimalField()),
            count=Count('id')
        ).order_by('-total_insurance')
        
        for item in patient_payments:
            item['total'] = (item['total_insurance'] or 0) + (item['total_private'] or 0)
    else:
        invoices = None
        total_amount = 0
        total_count = 0
        avg_invoice = 0
        insured_amount = 0
        private_amount = 0
        dept_revenue = []
        insurance_breakdown = []
        patient_payments = []
    
    context = {
        'doctors': doctors,
        'selected_doctor': selected_doctor,
        'invoices': invoices,
        'total_amount': float(total_amount) if total_amount else 0,
        'total_count': total_count,
        'avg_invoice': float(avg_invoice) if avg_invoice else 0,
        'insured_amount': float(insured_amount) if insured_amount else 0,
        'private_amount': float(private_amount) if private_amount else 0,
        'dept_revenue': dept_revenue,
        'insurance_breakdown': insurance_breakdown,
        'patient_payments': patient_payments,
    }
    
    return render(request, 'financial/reports_by_doctor.html', context)


def financial_reports_by_insurance(request, insurance_type=None):
    """Financial reports grouped by insurance provider"""
    today = timezone.now().date()
    
    # Get unique insurers
    insurers = Invoice.objects.filter(
        visit__patient__is_insured=True
    ).values_list('visit__patient__insurer', flat=True).distinct()
    
    selected_insurer = insurance_type or insurers.first()
    
    if selected_insurer:
        # Get invoices for insurer
        invoices = Invoice.objects.filter(
            visit__patient__is_insured=True,
            visit__patient__insurer=selected_insurer
        ).select_related('visit__patient', 'visit__doctor__user', 'visit__department')
        
        # Summary stats
        summary_data = invoices.aggregate(
            insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
            private=Sum('total_private', default=0, output_field=DecimalField()),
            count=Count('id')
        )
        
        total_amount = (summary_data['insurance'] or 0) + (summary_data['private'] or 0)
        total_count = summary_data['count']
        avg_invoice = total_amount / total_count if total_count > 0 else 0
        
        # Insurance pays calculation
        # Need to calculate based on coverage %
        insurance_pays_total = 0
        patient_pays_total = 0
        
        for inv in invoices:
            coverage_pct = inv.visit.patient.insurance_coverage_pct or 0
            total = inv.total_insurance + inv.total_private
            insurance_pays_total += total * (coverage_pct / 100)
            patient_pays_total += total * ((100 - coverage_pct) / 100)
        
        # By doctor
        doctor_invoices = invoices.values(
            'visit__doctor__user__first_name',
            'visit__doctor__user__last_name'
        ).annotate(
            total=Sum(
                F('total_insurance') + F('total_private'),
                output_field=DecimalField()
            ),
            count=Count('id')
        ).order_by('-total')
        
        # By department
        dept_invoices = invoices.values(
            'visit__department__name'
        ).annotate(
            total=Sum(
                F('total_insurance') + F('total_private'),
                output_field=DecimalField()
            ),
            count=Count('id')
        ).order_by('-total')
    else:
        invoices = None
        total_amount = 0
        total_count = 0
        avg_invoice = 0
        insurance_pays_total = 0
        patient_pays_total = 0
        doctor_invoices = []
        dept_invoices = []
    
    context = {
        'insurers': insurers,
        'selected_insurer': selected_insurer,
        'invoices': invoices,
        'total_amount': float(total_amount) if total_amount else 0,
        'total_count': total_count,
        'avg_invoice': float(avg_invoice) if avg_invoice else 0,
        'insurance_pays_total': float(insurance_pays_total),
        'patient_pays_total': float(patient_pays_total),
        'doctor_invoices': doctor_invoices,
        'dept_invoices': dept_invoices,
    }
    
    return render(request, 'financial/reports_by_insurance.html', context)


def financial_reports_by_period(request, period='daily'):
    """Financial reports by time period (daily, monthly, annual)"""
    today = timezone.now().date()
    
    if period == 'daily':
        # Last 30 days
        start_date = today - timedelta(days=30)
        invoices = Invoice.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=today
        )
        
        period_data = invoices.annotate(
            period=TruncDate('created_at')
        ).values('period').annotate(
            insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
            private=Sum('total_private', default=0, output_field=DecimalField()),
            count=Count('id')
        ).order_by('period')
        
        for item in period_data:
            item['total'] = (item['insurance'] or 0) + (item['private'] or 0)
        
        title = 'Daily Revenue Report (Last 30 Days)'
        
    elif period == 'monthly':
        # Last 12 months
        start_date = today - timedelta(days=365)
        invoices = Invoice.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=today
        )
        
        period_data = invoices.annotate(
            period=TruncMonth('created_at')
        ).values('period').annotate(
            insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
            private=Sum('total_private', default=0, output_field=DecimalField()),
            count=Count('id')
        ).order_by('period')
        
        for item in period_data:
            item['total'] = (item['insurance'] or 0) + (item['private'] or 0)
        
        title = 'Monthly Revenue Report (Last 12 Months)'
        
    else:  # annual
        # All time
        invoices = Invoice.objects.all()
        
        period_data = invoices.annotate(
            period=TruncYear('created_at')
        ).values('period').annotate(
            insurance=Sum('total_insurance', default=0, output_field=DecimalField()),
            private=Sum('total_private', default=0, output_field=DecimalField()),
            count=Count('id')
        ).order_by('period')
        
        for item in period_data:
            item['total'] = (item['insurance'] or 0) + (item['private'] or 0)
        
        title = 'Annual Revenue Report'
    
    summary = invoices.aggregate(
        insurance_total=Sum('total_insurance', default=0, output_field=DecimalField()),
        private_total=Sum('total_private', default=0, output_field=DecimalField())
    )
    total_revenue = (summary['insurance_total'] or 0) + (summary['private_total'] or 0)
    
    context = {
        'period': period,
        'period_data': period_data,
        'total_revenue': float(total_revenue),
        'title': title,
    }
    
    return render(request, 'financial/reports_by_period.html', context)


def financial_payment_details(request, payment_id=None):
    """Detailed payment information"""
    if payment_id:
        invoice = get_object_or_404(Invoice, id=payment_id)
        billing_items = BillingItem.objects.filter(visit=invoice.visit)
        payments = Payment.objects.filter(invoice=invoice)
    else:
        invoice = None
        billing_items = None
        payments = None
    
    context = {
        'invoice': invoice,
        'billing_items': billing_items,
        'payments': payments,
    }
    
    return render(request, 'financial/payment_details.html', context)
