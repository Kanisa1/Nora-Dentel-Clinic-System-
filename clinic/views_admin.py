# clinic/views_admin.py
"""Admin dashboard and management views"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
from clinic.models import (
    Patient, Appointment, Visit, ClinicUser, Invoice, 
    BillingItem, Department, TariffAct, WaitingQueueEntry
)
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import TruncDate


def admin_dashboard(request):
    """Main admin dashboard with system overview"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('dashboard:admin_login')
    
    today = timezone.now().date()
    
    # Get key metrics
    total_patients = Patient.objects.count()
    total_doctors = ClinicUser.objects.filter(role='doctor').count()
    total_staff = ClinicUser.objects.count()
    
    # Today's stats
    today_appointments = Appointment.objects.filter(scheduled_at__date=today).count()
    today_visits = Visit.objects.filter(created_at__date=today).count()
    today_revenue = Invoice.objects.filter(
        created_at__date=today
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Recent activity
    recent_appointments = Appointment.objects.order_by('-scheduled_at')[:5]
    recent_patients = Patient.objects.order_by('-created_at')[:5]
    
    # Doctors overview
    doctors = ClinicUser.objects.filter(role='doctor').select_related('user')
    doctor_stats = []
    for doctor in doctors:
        visits = Visit.objects.filter(doctor=doctor, created_at__date=today).count()
        revenue = Invoice.objects.filter(
            created_at__date=today
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        doctor_stats.append({
            'doctor': doctor,
            'visits': visits,
            'revenue': revenue
        })
    
    # Department overview
    departments = Department.objects.all()
    dept_stats = []
    for dept in departments:
        visits = Visit.objects.filter(department=dept, created_at__date=today).count()
        dept_stats.append({
            'department': dept,
            'visits': visits
        })
    
    context = {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_staff': total_staff,
        'today_appointments': today_appointments,
        'today_visits': today_visits,
        'today_revenue': today_revenue,
        'recent_appointments': recent_appointments,
        'recent_patients': recent_patients,
        'doctor_stats': doctor_stats,
        'dept_stats': dept_stats,
    }
    
    return render(request, 'admin/dashboard.html', context)


def admin_users(request):
    """Manage users and staff"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('dashboard:admin_login')
    users = ClinicUser.objects.select_related('user').all()
    context = {
        'users': users,
    }
    return render(request, 'admin/users.html', context)


def admin_departments(request):
    """Manage departments"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('dashboard:admin_login')
    departments = Department.objects.all()
    context = {
        'departments': departments,
    }
    return render(request, 'admin/departments.html', context)


# Admin Login View
from django.contrib.auth import authenticate, login
from django import forms

class AdminLoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput)

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    form = AdminLoginForm(request.POST or None)
    error = None
    if request.method == 'POST':
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None and user.is_staff:
                login(request, user)
                return redirect('admin_dashboard')
            else:
                error = 'Invalid credentials or not an admin user.'
    return render(request, 'admin/login.html', {'form': form, 'error': error})
