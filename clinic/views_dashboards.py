from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Q, Sum, Count, F, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta, datetime
from clinic.models import (
    Patient, Visit, WaitingQueueEntry, Appointment, 
    Invoice, BillingItem, Department, ClinicUser, TariffAct,
    PharmacyStock, PharmacyDispense, Prescription, PrescriptionItem,
    InventoryItem, StockMovement
)
from clinic.models_financial import (
    FixedAsset, ConsumableInventory, ConsumableUsage
)

# Admin Dashboard
def admin_dashboard(request):
    # Restrict access to authenticated staff only
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('dashboard:admin_login')
    # Get statistics
    total_patients = Patient.objects.count()
    today = timezone.now().date()
    today_visits = Visit.objects.filter(created_at__date=today).count()
    total_doctors = ClinicUser.objects.filter(role='doctor').count()
    # Financial data
    pending_invoices = Invoice.objects.filter(paid=False).count()
    revenue_data = Invoice.objects.aggregate(
        private=Coalesce(Sum('total_private'), Value(0, output_field=DecimalField())),
        insurance=Coalesce(Sum('total_insurance'), Value(0, output_field=DecimalField()))
    )
    total_revenue = (revenue_data['private'] or 0) + (revenue_data['insurance'] or 0)
    # Recent data
    recent_patients = Patient.objects.order_by('-created_at')[:5]
    recent_invoices = Invoice.objects.select_related('visit', 'visit__patient').order_by('-created_at')[:5]
    departments = Department.objects.all()
    context = {
        'total_patients': total_patients,
        'today_visits': today_visits,
        'total_doctors': total_doctors,
        'pending_invoices': pending_invoices,
        'total_revenue': total_revenue,
        'recent_patients': recent_patients,
        'recent_invoices': recent_invoices,
        'departments': departments,
    }
    return render(request, 'admin/dashboard.html', context)

# Doctor Dashboard
def doctor_dashboard(request):
    # Get first doctor as default
    clinic_user = ClinicUser.objects.filter(role='doctor').first()
    if not clinic_user:
        return render(request, 'doctor/dashboard.html', {'error': 'No doctor found'})
    today = timezone.now().date()
    
    # Get visits
    all_visits = Visit.objects.filter(
        doctor=clinic_user
    ).select_related('patient', 'department').order_by('-created_at')
    
    today_visits = all_visits.filter(created_at__date=today)
    completed_today = today_visits.filter(status='closed').count()
    
    # Waiting queue
    waiting_queue = WaitingQueueEntry.objects.filter(
        visit__doctor=clinic_user,
        status__in=['waiting', 'in_consultation']
    ).select_related('visit', 'visit__patient', 'visit__department').order_by('position')
    
    # Scheduled appointments for today
    scheduled_appointments = Appointment.objects.filter(
        doctor=clinic_user,
        scheduled_at__date=today,
        status__in=['scheduled', 'checked_in']
    ).select_related('patient', 'department').order_by('scheduled_at')
    
    # Pending invoices
    pending_invoices = Invoice.objects.filter(
        visit__doctor=clinic_user,
        status='pending'
    ).count()
    
    context = {
        'waiting_queue_count': waiting_queue.count(),
        'scheduled_appointments_count': scheduled_appointments.count(),
        'visits_today': today_visits.count(),
        'completed_today': completed_today,
        'pending_invoices': pending_invoices,
        'waiting_queue': waiting_queue[:10],
        'scheduled_appointments': scheduled_appointments[:10],
        'today_visits': today_visits[:10],
        'doctor_department': clinic_user.department,
    }
    
    return render(request, 'doctor/dashboard.html', context)

# Reception Dashboard
def reception_dashboard(request):
    today = timezone.now().date()
    
    # Statistics
    patients_today = Visit.objects.filter(created_at__date=today).values('patient_id').distinct().count()
    scheduled_appointments = Appointment.objects.filter(
        status='scheduled',
        scheduled_at__date__gte=today
    ).count()
    total_registered_patients = Patient.objects.count()
    checked_in_today = WaitingQueueEntry.objects.filter(
        checked_in_at__date=today
    ).values('visit_id').distinct().count()
    
    # Queue and appointments
    today_queue = WaitingQueueEntry.objects.filter(
        checked_in_at__date=today
    ).select_related('visit', 'visit__patient', 'visit__doctor').order_by('position')
    
    appointments = Appointment.objects.filter(
        scheduled_at__date__gte=today
    ).select_related('patient', 'doctor').order_by('scheduled_at')[:10]
    
    context = {
        'patients_today': patients_today,
        'scheduled_appointments': scheduled_appointments,
        'total_registered_patients': total_registered_patients,
        'checked_in_today': checked_in_today,
        'today_queue': today_queue[:10],
        'appointments': appointments,
        'today': today,
    }
    
    return render(request, 'reception/dashboard.html', context)

# Cashier Dashboard
def cashier_dashboard(request):
    today = timezone.now().date()
    
    # Statistics
    pending_invoices_count = Invoice.objects.filter(paid=False).count()
    paid_today = Invoice.objects.filter(
        paid=True,
        paid_at__date=today
    ).count()
    
    today_revenue_data = Invoice.objects.filter(
        paid=True,
        paid_at__date=today
    ).aggregate(
        private=Coalesce(Sum('total_private'), Value(0, output_field=DecimalField())),
        insurance=Coalesce(Sum('total_insurance'), Value(0, output_field=DecimalField()))
    )
    total_revenue_today = (today_revenue_data['private'] or 0) + (today_revenue_data['insurance'] or 0)
    
    outstanding_data = Invoice.objects.filter(paid=False).aggregate(
        private=Coalesce(Sum('total_private'), Value(0, output_field=DecimalField())),
        insurance=Coalesce(Sum('total_insurance'), Value(0, output_field=DecimalField()))
    )
    total_outstanding = (outstanding_data['private'] or 0) + (outstanding_data['insurance'] or 0)
    
    # Lists
    pending_invoices_list = Invoice.objects.filter(
        paid=False
    ).select_related('visit', 'visit__patient').order_by('-created_at')[:10]
    
    today_transactions = Invoice.objects.filter(
        paid=True,
        paid_at__date=today
    ).select_related('visit', 'visit__patient').order_by('-paid_at')[:10]
    
    context = {
        'pending_invoices': pending_invoices_count,
        'paid_today': paid_today,
        'total_revenue_today': total_revenue_today,
        'total_outstanding': total_outstanding,
        'pending_invoices_list': pending_invoices_list,
        'today_transactions': today_transactions,
    }
    
    return render(request, 'cashier/dashboard.html', context)

# Pharmacy Dashboard
def pharmacy_dashboard(request):
    today = timezone.now().date()
    
    # Total stock items
    total_medicines = PharmacyStock.objects.count()
    
    # Low stock items (less than 10 units)
    low_stock_items = PharmacyStock.objects.filter(
        qty_available__lte=10
    ).select_related('item').order_by('qty_available')[:10]
    low_stock_count = low_stock_items.count()
    
    # Expired or expiring soon (within 30 days)
    expiry_threshold = today + timedelta(days=30)
    expired_items = PharmacyStock.objects.filter(
        expiry_date__lte=expiry_threshold,
        expiry_date__isnull=False
    ).select_related('item').order_by('expiry_date')[:10]
    expired_count = expired_items.count()
    
    # Today's dispensing activity
    today_dispensing = PharmacyDispense.objects.filter(
        dispensed_at__date=today
    ).select_related('prescription', 'prescription__patient', 'pharmacy_stock', 'pharmacy_stock__item')
    today_dispensed = today_dispensing.count()
    
    # Pending prescriptions (prescriptions not fully dispensed)
    pending_prescriptions = Prescription.objects.filter(
        visit__status__in=['in_progress', 'closed'],
        prescription_type='clinic'
    ).select_related('patient', 'doctor', 'visit').order_by('-created_at')[:10]
    
    # Recent prescriptions
    recent_prescriptions = Prescription.objects.select_related(
        'patient', 'doctor', 'visit'
    ).order_by('-created_at')[:10]
    
    # Stock alerts - items that are both low stock and expiring
    critical_items = PharmacyStock.objects.filter(
        Q(qty_available__lte=5) | Q(expiry_date__lte=expiry_threshold, expiry_date__isnull=False)
    ).select_related('item').distinct()[:10]
    
    context = {
        'total_medicines': total_medicines,
        'low_stock_count': low_stock_count,
        'today_dispensed': today_dispensed,
        'expired_count': expired_count,
        'low_stock_items': low_stock_items,
        'expired_items': expired_items,
        'today_dispensing': today_dispensing[:10],
        'pending_prescriptions': pending_prescriptions,
        'recent_prescriptions': recent_prescriptions,
        'critical_items': critical_items,
    }
    
    return render(request, 'pharmacy/dashboard.html', context)

# Inventory Dashboard
def inventory_dashboard(request):
    today = timezone.now().date()
    
    # Total inventory items
    total_items = InventoryItem.objects.count()
    
    # Fixed Assets (Equipment)
    equipment_count = FixedAsset.objects.filter(status='active').count()
    damaged_items = FixedAsset.objects.filter(status='damaged').count()
    maintenance_assets = FixedAsset.objects.filter(status='maintenance').count()
    
    # Consumable Inventory
    total_consumables = ConsumableInventory.objects.count()
    low_stock_consumables = ConsumableInventory.objects.filter(
        quantity_in_stock__lte=F('minimum_stock_level')
    ).order_by('quantity_in_stock')[:10]
    low_stock_count = low_stock_consumables.count()
    
    # Expired consumables
    expired_consumables = ConsumableInventory.objects.filter(
        expiry_date__lte=today,
        expiry_date__isnull=False
    ).order_by('expiry_date')[:10]
    expired_count = expired_consumables.count()
    
    # Expiring soon (within 30 days)
    expiry_threshold = today + timedelta(days=30)
    expiring_soon = ConsumableInventory.objects.filter(
        expiry_date__lte=expiry_threshold,
        expiry_date__gt=today,
        expiry_date__isnull=False
    ).order_by('expiry_date')[:10]
    
    # Recent stock movements
    recent_movements = StockMovement.objects.select_related(
        'inventory_item', 'performed_by'
    ).order_by('-movement_date')[:15]
    
    # Today's consumable usage
    today_usage = ConsumableUsage.objects.filter(
        usage_date=today
    ).select_related('consumable', 'used_by', 'department')
    today_usage_count = today_usage.aggregate(
        total=Coalesce(Sum('quantity_used'), Value(0, output_field=DecimalField()))
    )['total'] or 0
    
    # Fixed assets by type
    assets_by_type = FixedAsset.objects.values('asset_type').annotate(
        count=Count('id'),
        total_value=Sum('purchase_cost')
    ).order_by('-count')
    
    # Equipment list with status
    equipment_list = FixedAsset.objects.filter(
        status__in=['active', 'maintenance']
    ).order_by('-purchase_date')[:10]
    
    # Calculate total inventory value
    total_consumable_value = ConsumableInventory.objects.aggregate(
        total=Coalesce(
            Sum(F('quantity_in_stock') * F('average_unit_cost')),
            Value(0, output_field=DecimalField())
        )
    )['total'] or 0
    
    total_asset_value = FixedAsset.objects.filter(
        status__in=['active', 'maintenance']
    ).aggregate(
        total=Coalesce(Sum('purchase_cost'), Value(0, output_field=DecimalField()))
    )['total'] or 0
    
    total_inventory_value = total_consumable_value + total_asset_value
    
    context = {
        'total_items': total_items,
        'equipment_count': equipment_count,
        'maintenance_due': maintenance_assets,
        'damaged_items': damaged_items,
        'total_consumables': total_consumables,
        'low_stock_count': low_stock_count,
        'expired_count': expired_count,
        'total_inventory_value': total_inventory_value,
        'total_consumable_value': total_consumable_value,
        'total_asset_value': total_asset_value,
        'equipment_list': equipment_list,
        'low_stock_consumables': low_stock_consumables,
        'expired_consumables': expired_consumables,
        'expiring_soon': expiring_soon,
        'recent_movements': recent_movements,
        'today_usage': today_usage[:10],
        'today_usage_count': today_usage_count,
        'assets_by_type': assets_by_type,
    }
    
    return render(request, 'inventory/dashboard.html', context)

# Financial Dashboard
def financial_dashboard(request):
    # Revenue calculations
    total_invoices = Invoice.objects.all()
    revenue_data = total_invoices.aggregate(
        private=Coalesce(Sum('total_private'), Value(0, output_field=DecimalField())),
        insurance=Coalesce(Sum('total_insurance'), Value(0, output_field=DecimalField()))
    )
    total_revenue = (revenue_data['private'] or 0) + (revenue_data['insurance'] or 0)
    
    paid_data = total_invoices.filter(paid=True).aggregate(
        private=Coalesce(Sum('total_private'), Value(0, output_field=DecimalField())),
        insurance=Coalesce(Sum('total_insurance'), Value(0, output_field=DecimalField()))
    )
    paid_amount = (paid_data['private'] or 0) + (paid_data['insurance'] or 0)
    
    outstanding_data = total_invoices.filter(paid=False).aggregate(
        private=Coalesce(Sum('total_private'), Value(0, output_field=DecimalField())),
        insurance=Coalesce(Sum('total_insurance'), Value(0, output_field=DecimalField()))
    )
    outstanding_amount = (outstanding_data['private'] or 0) + (outstanding_data['insurance'] or 0)
    
    pending_invoices_count = total_invoices.filter(paid=False).count()
    
    # Insurance vs Private
    insurance_count = Patient.objects.filter(is_insured=True).count()
    private_count = Patient.objects.filter(is_insured=False).count()
    total_count = insurance_count + private_count
    
    insurance_revenue = BillingItem.objects.aggregate(
        total=Coalesce(Sum('price_insurance_snapshot'), Value(0, output_field=DecimalField()))
    )['total'] or 0
    
    private_revenue = BillingItem.objects.aggregate(
        total=Coalesce(Sum('price_private_snapshot'), Value(0, output_field=DecimalField()))
    )['total'] or 0
    
    total_patient_revenue = insurance_revenue + private_revenue or 1
    
    context = {
        'total_revenue': total_revenue,
        'paid_amount': paid_amount,
        'outstanding_amount': outstanding_amount,
        'pending_invoices_count': pending_invoices_count,
        'insurance_count': insurance_count,
        'private_count': private_count,
        'insurance_revenue': insurance_revenue,
        'private_revenue': private_revenue,
        'insurance_percentage': round((insurance_revenue / total_patient_revenue * 100)) if total_patient_revenue else 0,
        'private_percentage': round((private_revenue / total_patient_revenue * 100)) if total_patient_revenue else 0,
        'department_revenue': [],
        'doctor_revenue': [],
    }
    
    return render(request, 'finance/dashboard_new.html', context)

# Reports Dashboard
def reports_dashboard(request):
    total_visits = Visit.objects.count()
    total_patients = Patient.objects.count()
    
    # Calculate return patients
    repeat_patient_visits = Visit.objects.values('patient_id').annotate(
        visit_count=Count('id')
    ).filter(visit_count__gt=1)
    repeat_patients_pct = (repeat_patient_visits.count() / total_patients * 100) if total_patients else 0
    
    context = {
        'total_visits': total_visits,
        'total_patients': total_patients,
        'repeat_patients_pct': round(repeat_patients_pct),
        'avg_visit_time': 15,  # Placeholder
        'top_treatments': [],
        'visit_stats': [],
        'demographics': [],
    }
    
    return render(request, 'reports/dashboard.html', context)


# Appointment Scheduling Views
def reception_schedule_appointment_form(request):
    """Display form to schedule new appointment"""
    patients = Patient.objects.all().order_by('first_name', 'last_name')
    departments = Department.objects.all().order_by('name')
    today = timezone.now().date()
    
    context = {
        'patients': patients,
        'departments': departments,
        'today': today,
    }
    return render(request, 'reception/schedule_appointment.html', context)


def get_doctors_by_department(request):
    """AJAX endpoint to get doctors filtered by department"""
    department_id = request.GET.get('department_id')
    
    if department_id:
        doctors = ClinicUser.objects.filter(
            role='doctor',
            department_id=department_id
        ).select_related('user', 'department')
        
        doctors_list = []
        for doctor in doctors:
            # Get full name or fallback to username
            first_name = doctor.user.first_name or ''
            last_name = doctor.user.last_name or ''
            full_name = f"{first_name} {last_name}".strip()
            
            if not full_name:
                full_name = doctor.user.username
            
            doctors_list.append({
                'id': doctor.id,
                'name': full_name,
                'department': doctor.department.name if doctor.department else 'No Department'
            })
        
        return JsonResponse({'doctors': doctors_list})
    
    return JsonResponse({'doctors': []})


def reception_schedule_appointment(request):
    """Handle appointment scheduling form submission"""
    if request.method == 'POST':
        from django.contrib import messages
        from datetime import datetime
        
        try:
            patient_id = request.POST.get('patient_id')
            doctor_id = request.POST.get('doctor_id')
            scheduled_date = request.POST.get('scheduled_date')
            scheduled_time = request.POST.get('scheduled_time')
            notes = request.POST.get('notes', '')
            
            # Validate inputs
            if not all([patient_id, doctor_id, scheduled_date, scheduled_time]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('reception_schedule_appointment_form')
            
            # Get patient and doctor
            patient = Patient.objects.get(id=patient_id)
            doctor = ClinicUser.objects.get(id=doctor_id, role='doctor')
            
            # Combine date and time into datetime
            scheduled_datetime = datetime.strptime(
                f"{scheduled_date} {scheduled_time}", 
                "%Y-%m-%d %H:%M"
            )
            scheduled_datetime = timezone.make_aware(scheduled_datetime)
            
            # Create appointment
            scheduled_by = None
            if request.user.is_authenticated and hasattr(request.user, 'clinicuser'):
                scheduled_by = request.user.clinicuser
            
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                department=doctor.department,
                scheduled_by=scheduled_by,
                scheduled_at=scheduled_datetime,
                notes=notes,
                status='scheduled'
            )
            
            messages.success(
                request, 
                f'Appointment scheduled successfully for {patient.first_name} {patient.last_name} '
                f'with Dr. {doctor.user.get_full_name()}'
            )
            # Redirect to confirmation page with print option
            return redirect('reception_appointment_confirmation', appointment_id=appointment.id)
            
        except Patient.DoesNotExist:
            messages.error(request, 'Selected patient not found.')
        except ClinicUser.DoesNotExist:
            messages.error(request, 'Selected doctor not found.')
        except Exception as e:
            messages.error(request, f'Error scheduling appointment: {str(e)}')
        
        return redirect('reception_schedule_appointment_form')
    
    return redirect('reception_schedule_appointment_form')


def reception_appointments(request):
    """View all appointments (today and upcoming)"""
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Get appointments for today and upcoming
    today_appointments = Appointment.objects.filter(
        scheduled_at__date=today,
        status__in=['scheduled', 'checked_in']
    ).select_related('patient', 'doctor', 'department').order_by('scheduled_at')
    
    upcoming_appointments = Appointment.objects.filter(
        scheduled_at__date__gte=tomorrow,
        status='scheduled'
    ).select_related('patient', 'doctor', 'department').order_by('scheduled_at')[:10]
    
    context = {
        'today_appointments': today_appointments,
        'upcoming_appointments': upcoming_appointments,
        'today': today,
    }
    return render(request, 'reception/appointments_list.html', context)


def reception_appointment_confirmation(request, appointment_id):
    """Show appointment confirmation page with print option"""
    appointment = Appointment.objects.select_related(
        'patient', 'doctor__user', 'department', 'scheduled_by__user'
    ).get(id=appointment_id)
    
    context = {
        'appointment': appointment,
    }
    return render(request, 'reception/appointment_confirmation.html', context)


def print_appointment(request, appointment_id):
    """Generate printable appointment slip"""
    appointment = Appointment.objects.select_related(
        'patient', 'doctor__user', 'department', 'scheduled_by__user'
    ).get(id=appointment_id)
    
    context = {
        'appointment': appointment,
        'print_date': timezone.now(),
    }
    return render(request, 'reception/print_appointment.html', context)
