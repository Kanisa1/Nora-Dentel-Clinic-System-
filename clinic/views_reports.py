# clinic/views_reports.py
"""Reports hub and system-wide reporting"""

from django.shortcuts import render
from clinic.models import Invoice, Visit, Patient, ClinicUser
from django.db.models import Sum, Count, Q
from django.utils import timezone


def reports_hub(request):
    """Central reports hub"""
    
    # Quick stats
    total_patients = Patient.objects.count()
    total_visits = Visit.objects.count()
    total_revenue = Invoice.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'total_patients': total_patients,
        'total_visits': total_visits,
        'total_revenue': total_revenue,
    }
    
    return render(request, 'reports/hub.html', context)


def reports_patient(request):
    """Patient-related reports"""
    
    # Patient statistics
    total_patients = Patient.objects.count()
    insured_patients = Patient.objects.filter(is_insured=True).count()
    private_patients = Patient.objects.filter(is_insured=False).count()
    
    # Insurance breakdown
    insurance_breakdown = Patient.objects.filter(
        is_insured=True
    ).values('insurer').annotate(count=Count('id')).order_by('-count')
    
    context = {
        'total_patients': total_patients,
        'insured_patients': insured_patients,
        'private_patients': private_patients,
        'insurance_breakdown': insurance_breakdown,
    }
    
    return render(request, 'reports/patient.html', context)


def reports_clinical(request):
    """Clinical reports - visits, treatments"""
    
    total_visits = Visit.objects.count()
    
    # Visit status breakdown
    visit_breakdown = Visit.objects.values('status').annotate(count=Count('id'))
    
    # By department
    by_department = Visit.objects.values(
        'department__name'
    ).annotate(count=Count('id')).order_by('-count')
    
    context = {
        'total_visits': total_visits,
        'visit_breakdown': visit_breakdown,
        'by_department': by_department,
    }
    
    return render(request, 'reports/clinical.html', context)
