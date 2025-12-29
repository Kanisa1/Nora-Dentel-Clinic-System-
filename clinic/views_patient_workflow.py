"""
Patient Workflow Views for Reception and Clinical
- Reception: Create visits, assign to doctors
- Doctor: Fill clinical records, add billing items
- Invoice generation
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Q, Max
from django.utils import timezone
from django.contrib import messages
from datetime import datetime
import json

from clinic.models import (
    Patient, Visit, Appointment, WaitingQueueEntry, ClinicUser, 
    Department, TariffAct, BillingItem, Invoice, Triage
)


# ============================================================================
# RECEPTION: Create Visit and Send Patient to Doctor
# ============================================================================

def reception_create_visit(request):
    """Reception creates a visit (patient registration for appointment)"""
    
    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        doctor_id = request.POST.get('doctor_id')
        department_id = request.POST.get('department_id')
        insurance_coverage_pct = request.POST.get('insurance_coverage_pct', 0)
        
        try:
            patient = Patient.objects.get(id=patient_id)
            doctor = ClinicUser.objects.get(id=doctor_id, role='doctor')
            department = Department.objects.get(id=department_id)
            
            # Get receptionist (if available)
            receptionist = None
            if hasattr(request.user, 'clinicuser'):
                receptionist = request.user.clinicuser
            
            # Create visit
            visit = Visit.objects.create(
                patient=patient,
                doctor=doctor,
                department=department,
                status='open'
            )
            
            # Add to waiting queue
            last_position = WaitingQueueEntry.objects.filter(
                checked_in_at__date=timezone.now().date()
            ).aggregate(Max('position'))['position__max'] or 0
            
            queue_entry = WaitingQueueEntry.objects.create(
                visit=visit,
                position=last_position + 1,
                status='waiting',
                receptionist=receptionist
            )
            
            # Get doctor's display name
            doctor_name = doctor.user.get_full_name() or doctor.user.username
            
            messages.success(
                request,
                f'Patient {patient.first_name} {patient.last_name} sent to Dr. {doctor_name}'
            )
            return redirect('reception_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error creating visit: {str(e)}')
    
    patients = Patient.objects.all().order_by('-created_at')
    doctors = ClinicUser.objects.filter(role='doctor').select_related('department', 'user')
    departments = Department.objects.all()
    insurance_percentages = list(range(0, 101, 5))  # 0 to 100 in increments of 5
    
    context = {
        'patients': patients,
        'doctors': doctors,
        'departments': departments,
        'insurance_percentages': insurance_percentages,
    }
    return render(request, 'reception/create_visit.html', context)


# ============================================================================
# DOCTOR: Access Patient and Fill Clinical Record
# ============================================================================

def doctor_patient_list(request):
    """Show list of patients assigned to this doctor"""
    # Check if user has clinicuser
    if not hasattr(request.user, 'clinicuser'):
        return JsonResponse({'error': 'User does not have clinic access'}, status=403)
    
    clinic_user = request.user.clinicuser
    today = timezone.now().date()
    
    # Get patients in waiting queue for this doctor today
    waiting_patients = WaitingQueueEntry.objects.filter(
        visit__doctor=clinic_user,
        checked_in_at__date=today,
        status__in=['waiting', 'in_consultation']
    ).select_related('visit', 'visit__patient', 'visit__department').order_by('position')
    
    # Get all visits assigned to this doctor
    all_visits = Visit.objects.filter(
        doctor=clinic_user,
        status='open'
    ).select_related('patient', 'department').order_by('-created_at')
    
    context = {
        'waiting_patients': waiting_patients,
        'all_visits': all_visits,
    }
    return render(request, 'doctor/patient_list.html', context)


def doctor_clinical_record(request, visit_id):
    """Doctor fills clinical record for patient"""
    # Check if user has clinicuser
    if not hasattr(request.user, 'clinicuser'):
        messages.error(request, 'User does not have clinic access')
        return redirect('home')
    
    visit = get_object_or_404(Visit, id=visit_id, doctor=request.user.clinicuser)
    
    if request.method == 'POST':
        # Save clinical record
        chief_complaint = request.POST.get('chief_complaint', '')
        history_present_illness = request.POST.get('history_present_illness', '')
        past_medical_history = request.POST.get('past_medical_history', '')
        social_family_history = request.POST.get('social_family_history', '')
        review_systems = request.POST.get('review_systems', '')
        general_examination = request.POST.get('general_examination', '')
        dental_examination = request.POST.get('dental_examination', '')
        investigations = request.POST.get('investigations', '')
        diagnosis = request.POST.get('diagnosis', '')
        treatment_plan = request.POST.get('treatment_plan', '')
        
        # Store in visit notes (or create clinical record model if needed)
        visit.notes = f"""
CHIEF COMPLAINT: {chief_complaint}
HISTORY OF PRESENT ILLNESS: {history_present_illness}
PAST MEDICAL/DENTAL HISTORY: {past_medical_history}
SOCIAL/FAMILY HISTORY: {social_family_history}
REVIEW OF SYSTEMS: {review_systems}
GENERAL EXAMINATION: {general_examination}
DENTAL EXAMINATION: {dental_examination}
INVESTIGATIONS: {investigations}
DIAGNOSIS: {diagnosis}
TREATMENT PLAN: {treatment_plan}
        """
        visit.save()
        
        messages.success(request, 'Clinical record saved successfully')
        return redirect('doctor_add_billing', visit_id=visit_id)
    
    context = {
        'visit': visit,
        'patient': visit.patient,
    }
    return render(request, 'doctor/clinical_record.html', context)


def doctor_add_billing(request, visit_id):
    """Doctor selects tariff acts and adds billing items"""
    # Check if user has clinicuser
    if not hasattr(request.user, 'clinicuser'):
        messages.error(request, 'User does not have clinic access')
        return redirect('home')
    
    visit = get_object_or_404(Visit, id=visit_id, doctor=request.user.clinicuser)
    
    if request.method == 'POST':
        tariff_ids = request.POST.getlist('tariff_ids')
        
        for tariff_id in tariff_ids:
            try:
                tariff = TariffAct.objects.get(id=tariff_id)
                
                # Determine which price to use based on patient insurance
                if visit.patient.is_insured:
                    price = tariff.price_insurance or tariff.price_private
                else:
                    price = tariff.price_private
                
                BillingItem.objects.create(
                    visit=visit,
                    tariff=tariff,
                    qty=1,
                    price_private_snapshot=tariff.price_private,
                    price_insurance_snapshot=tariff.price_insurance
                )
            except TariffAct.DoesNotExist:
                continue
        
        # Mark visit as billed and generate invoice
        visit.status = 'billed'
        visit.save()
        
        # Generate invoice
        invoice = generate_invoice(visit)
        
        messages.success(request, 'Billing items added and invoice generated')
        return redirect('doctor_invoice_view', invoice_id=invoice.id)
    
    # Get all tariff acts in department
    tariff_acts = TariffAct.objects.filter(
        department=visit.department,
        active=True
    ).order_by('code')
    
    existing_items = visit.billing_items.all()
    
    context = {
        'visit': visit,
        'patient': visit.patient,
        'tariff_acts': tariff_acts,
        'existing_items': existing_items,
    }
    return render(request, 'doctor/add_billing.html', context)


# ============================================================================
# Invoice Generation
# ============================================================================

def generate_invoice(visit):
    """Generate invoice from billing items"""
    invoice, created = Invoice.objects.get_or_create(visit=visit)
    
    # Calculate totals
    billing_items = visit.billing_items.all()
    
    total_private = 0
    total_insurance = 0
    
    for item in billing_items:
        total_private += item.price_private_snapshot * item.qty
        if item.price_insurance_snapshot:
            total_insurance += item.price_insurance_snapshot * item.qty
    
    invoice.total_private = total_private
    invoice.total_insurance = total_insurance
    invoice.created_by = visit.doctor
    invoice.save()
    
    return invoice


def doctor_invoice_view(request, invoice_id):
    """View and print invoice"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    visit = invoice.visit
    
    billing_items = visit.billing_items.all()
    
    context = {
        'invoice': invoice,
        'visit': visit,
        'patient': visit.patient,
        'doctor': visit.doctor,
        'billing_items': billing_items,
    }
    return render(request, 'invoices/invoice_detail.html', context)


# ============================================================================
# API Endpoints (JSON responses for AJAX)
# ============================================================================

def api_get_doctors_by_department(request):
    """Get doctors for selected department"""
    department_id = request.GET.get('department_id')
    
    doctors = ClinicUser.objects.filter(
        department_id=department_id,
        role='doctor'
    ).select_related('user').order_by('user__username')
    
    doctor_list = []
    for doc in doctors:
        # Try to get full name, fall back to username if names are empty
        first_name = doc.user.first_name.strip()
        last_name = doc.user.last_name.strip()
        
        if first_name or last_name:
            name = f"{first_name} {last_name}".strip()
        else:
            name = doc.user.username
        
        doctor_list.append({
            'id': doc.id,
            'name': name
        })
    
    return JsonResponse({'doctors': doctor_list})


def api_get_patient_info(request):
    """Get patient details for display"""
    patient_id = request.GET.get('patient_id')
    
    try:
        patient = Patient.objects.get(id=patient_id)
        return JsonResponse({
            'id': patient.id,
            'name': f"{patient.first_name} {patient.last_name}",
            'age': patient.age,
            'phone': patient.phone,
            'is_insured': patient.is_insured,
            'insurer': patient.insurer,
            'membership_number': patient.membership_number,
        })
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)


def api_get_tariff_prices(request):
    """Get tariff prices and details"""
    tariff_id = request.GET.get('tariff_id')
    
    try:
        tariff = TariffAct.objects.get(id=tariff_id)
        return JsonResponse({
            'id': tariff.id,
            'name': tariff.name,
            'code': tariff.code,
            'price_private': float(tariff.price_private),
            'price_insurance': float(tariff.price_insurance or 0),
        })
    except TariffAct.DoesNotExist:
        return JsonResponse({'error': 'Tariff not found'}, status=404)


def api_add_billing_item(request):
    """API to add billing item via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    data = json.loads(request.body)
    visit_id = data.get('visit_id')
    tariff_id = data.get('tariff_id')
    qty = data.get('qty', 1)
    
    try:
        visit = Visit.objects.get(id=visit_id)
        tariff = TariffAct.objects.get(id=tariff_id)
        
        # Check if already added
        item, created = BillingItem.objects.get_or_create(
            visit=visit,
            tariff=tariff,
            defaults={
                'qty': qty,
                'price_private_snapshot': tariff.price_private,
                'price_insurance_snapshot': tariff.price_insurance or 0,
            }
        )
        
        if not created:
            item.qty += qty
            item.save()
        
        return JsonResponse({
            'success': True,
            'item_id': item.id,
            'total_items': visit.billing_items.count(),
        })
    except (Visit.DoesNotExist, TariffAct.DoesNotExist) as e:
        return JsonResponse({'error': str(e)}, status=404)


def api_remove_billing_item(request):
    """API to remove billing item via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    data = json.loads(request.body)
    item_id = data.get('item_id')
    
    try:
        item = BillingItem.objects.get(id=item_id)
        item.delete()
        
        return JsonResponse({'success': True})
    except BillingItem.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)


def api_get_invoice_data(request, invoice_id):
    """Get invoice data in JSON format"""
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        visit = invoice.visit
        
        billing_items = [
            {
                'code': item.tariff.code,
                'name': item.tariff.name,
                'qty': item.qty,
                'price_private': float(item.price_private_snapshot),
                'price_insurance': float(item.price_insurance_snapshot or 0),
                'total_private': float(item.price_private_snapshot * item.qty),
                'total_insurance': float((item.price_insurance_snapshot or 0) * item.qty),
            }
            for item in visit.billing_items.all()
        ]
        
        return JsonResponse({
            'invoice_id': invoice.id,
            'patient_name': f"{visit.patient.first_name} {visit.patient.last_name}",
            'patient_id': visit.patient.id,
            'doctor_name': visit.doctor.user.get_full_name(),
            'department': visit.department.name,
            'created_at': invoice.created_at.isoformat(),
            'total_private': float(invoice.total_private),
            'total_insurance': float(invoice.total_insurance),
            'billing_items': billing_items,
        })
    except Invoice.DoesNotExist:
        return JsonResponse({'error': 'Invoice not found'}, status=404)
