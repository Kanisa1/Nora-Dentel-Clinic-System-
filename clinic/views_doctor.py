# clinic/views_doctor.py

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from clinic.models import (
    Visit,
    Triage,
    BillingItem,
    TariffAct,
    ClinicUser,
    WaitingQueueEntry,
    PharmacyStock,
    Prescription,
    PrescriptionItem,
    Appointment,
    Department,
)
from clinic.models_medical_records import MedicalRecord, HMISClassification


COMPLETED_STATUSES = ['completed', 'awaiting_payment']


def _require_doctor_user(request):
    if not request.user.is_authenticated:
        raise PermissionDenied("Doctor login required")
    try:
        clinic_user = request.user.clinicuser
    except ClinicUser.DoesNotExist:
        raise PermissionDenied("Doctor profile not linked to this account")

    if clinic_user.role != 'doctor' and not request.user.is_superuser:
        raise PermissionDenied("You do not have doctor privileges")
    return clinic_user


def _ensure_visit_access(visit, clinic_user, request):
    if request.user.is_superuser:
        return
    if visit.doctor and clinic_user.role == 'doctor' and visit.doctor != clinic_user:
        raise PermissionDenied("You are not assigned to this visit")


def _redirect_after_doctor_action(request, visit_id):
    """Return to dashboard when actions originate from the enhanced workspace."""
    target = request.POST.get('return_to') or request.GET.get('return_to')
    next_url = request.POST.get('next') or request.GET.get('next')

    if target == 'dashboard':
        return redirect('doctor_dashboard_enhanced')
    if next_url:
        return redirect(next_url)
    return redirect("doctor-visit-detail", visit_id=visit_id)

@require_http_methods(["GET", "POST"])
def doctor_login(request):
    """Custom login page for doctors"""
    # Check if already logged in as a doctor
    if request.user.is_authenticated:
        if hasattr(request.user, 'clinicuser') and request.user.clinicuser.role == 'doctor':
            # Already logged in as doctor, redirect to dashboard
            return redirect('doctor-dashboard')
        else:
            # Logged in as non-doctor, logout first
            from django.contrib.auth import logout
            logout(request)
    
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user is a doctor
            try:
                clinic_user = user.clinicuser
                if clinic_user.role == 'doctor':
                    login(request, user)
                    return redirect('doctor-dashboard')
                else:
                    return render(request, 'doctor/login.html', {
                        'error': 'You do not have doctor privileges. Please contact your administrator.'
                    })
            except ClinicUser.DoesNotExist:
                return render(request, 'doctor/login.html', {
                    'error': 'You do not have doctor privileges. Please contact your administrator.'
                })
        else:
            return render(request, 'doctor/login.html', {
                'error': 'Invalid username or password.'
            })
    
    return render(request, 'doctor/login.html')

def doctor_dashboard(request):
    """Doctor dashboard showing their today's visits and waiting queue"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return redirect('doctor-login')
    
    # Check if user is a doctor
    try:
        clinic_user = request.user.clinicuser
        if clinic_user.role != 'doctor':
            return render(request, 'doctor/unauthorized.html', status=403)
    except ClinicUser.DoesNotExist:
        # Create a test ClinicUser if it doesn't exist (for development only)
        from django.contrib.auth.models import User
        clinic_user = ClinicUser.objects.create(
            user=request.user,
            role='doctor'
        )
    
    # Get today's visits for this doctor
    from django.utils import timezone
    today = timezone.now().date()
    
    # Get ALL visits for this doctor (not just today) - fetched from Django database
    all_visits = Visit.objects.filter(
        doctor=clinic_user
    ).select_related('patient', 'department').order_by('-created_at')
    
    # Also get today's visits separately for stats
    today_visits = Visit.objects.filter(
        doctor=clinic_user,
        created_at__date=today
    ).select_related('patient', 'department').order_by('-created_at')
    
    # Get waiting queue entries for this doctor - fetched from Django database
    waiting_queue = WaitingQueueEntry.objects.filter(
        visit__doctor=clinic_user,
        status='waiting'
    ).select_related('visit', 'visit__patient', 'visit__department').order_by('position')
    
    # Calculate counts
    completed_today = today_visits.filter(status__in=COMPLETED_STATUSES).count()
    total_all_time = all_visits.count()
    completed_all_time = all_visits.filter(status__in=COMPLETED_STATUSES).count()
    
    # Get scheduled appointments for today
    scheduled_appointments = Appointment.objects.filter(
        doctor=clinic_user,
        scheduled_at__date=today
    ).select_related('patient').order_by('scheduled_at')
    
    # Get pending invoices count
    pending_invoices = Invoice.objects.filter(
        visit__doctor=clinic_user,
        paid=False
    ).count()
    
    # Get doctor's display name
    doctor_name = clinic_user.user.get_full_name() or clinic_user.user.username
    
    context = {
        'doctor': clinic_user,
        'doctor_name': doctor_name,
        'doctor_username': clinic_user.user.username,
        'doctor_email': clinic_user.user.email,
        'visits': all_visits,
        'today_visits': today_visits,
        'waiting_queue': waiting_queue,
        'today_visits_count': today_visits.count(),
        'completed_today': completed_today,
        'waiting_count': waiting_queue.count(),
        'waiting_queue_count': waiting_queue.count(),
        'doctor_department': clinic_user.department,
        'active_visits': all_visits.filter(status='open').count(),
        'total_all_time': total_all_time,
        'completed_all_time': completed_all_time,
        'scheduled_appointments': scheduled_appointments,
        'scheduled_appointments_count': scheduled_appointments.count(),
        'pending_invoices': pending_invoices,
    }
    
    return render(request, 'doctor/dashboard.html', context)

@login_required
def visit_detail(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id)
    clinic_user = _require_doctor_user(request)
    _ensure_visit_access(visit, clinic_user, request)

    patient = visit.patient
    triage, _ = Triage.objects.get_or_create(visit=visit)
    medical_record, _ = MedicalRecord.objects.get_or_create(visit=visit)

    if request.method == "POST" and 'save_medical_record' in request.POST:
        medical_record.chief_complaint = request.POST.get("chief_complaint", "")
        medical_record.history_presenting_illness = request.POST.get("history_present_illness", "")
        medical_record.past_medical_history = request.POST.get("past_medical_history", "")

        social_family = request.POST.get("social_family_history", "")
        medical_record.social_history = social_family
        medical_record.family_history = social_family

        medical_record.review_of_systems = request.POST.get("review_systems", "")
        medical_record.general_examination = request.POST.get("general_examination", "")
        medical_record.specialty_examination = request.POST.get("specialty_examination", "")
        medical_record.investigations = request.POST.get("investigations", "")
        medical_record.diagnosis = request.POST.get("diagnosis", "")
        medical_record.treatment_plan = request.POST.get("treatment_plan", "")
        medical_record.hmis_classification = request.POST.get("hmis_classification", "")
        medical_record.idsr_disease = request.POST.get("idsr_classification", "")

        medical_record.save()

        messages.success(request, 'Medical record saved successfully!')
        return redirect("doctor-visit-detail", visit_id=visit_id)

    billing_items = visit.billing_items.select_related("tariff").all()
    private_total = sum((item.price_private_snapshot or Decimal('0')) * item.qty for item in billing_items)
    insurance_total = sum(
        ((item.price_insurance_snapshot or item.price_private_snapshot or Decimal('0'))) * item.qty
        for item in billing_items
    )

    tariffs = TariffAct.objects.filter(active=True).order_by('name')
    pharmacy_stock = PharmacyStock.objects.select_related('item').filter(qty_available__gt=0).order_by('item__name')
    prescriptions = visit.prescriptions.select_related('doctor').prefetch_related('items__inventory_item').order_by('-created_at')
    departments = Department.objects.all().order_by('name')
    peer_doctors = ClinicUser.objects.filter(role='doctor').exclude(id=clinic_user.id).select_related('user', 'department').order_by('user__first_name', 'user__last_name')
    hmis_classifications = HMISClassification.objects.all()
    idsr_choices = MedicalRecord._meta.get_field('idsr_disease').choices
    appointments = (
        Appointment.objects.filter(patient=patient)
        .select_related('doctor__user', 'department')
        .order_by('-scheduled_at')[:10]
    )
    certificates = visit.certificates.select_related('doctor__user').order_by('-issue_date')[:5]
    transfer_history = visit.transfers.select_related(
        'from_doctor__user',
        'to_doctor__user',
        'from_department',
        'to_department',
    ).order_by('-transferred_at')[:5]

    context = {
        "visit": visit,
        "patient": patient,
        "triage": triage,
        "medical_record": medical_record,
        "billing_items": billing_items,
        "tariffs": tariffs,
        "pharmacy_stock": pharmacy_stock,
        "prescriptions": prescriptions,
        "billing_totals": {
            "private_total": private_total,
            "insurance_total": insurance_total,
        },
        "departments": departments,
        "peer_doctors": peer_doctors,
        "hmis_classifications": hmis_classifications,
        "idsr_choices": idsr_choices,
        "appointments": appointments,
        "certificates": certificates,
        "transfer_history": transfer_history,
    }
    return render(request, "doctor/visit_detail.html", context)


@login_required
@require_http_methods(["POST"])
def add_act(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id)
    clinic_user = _require_doctor_user(request)
    _ensure_visit_access(visit, clinic_user, request)

    if request.method == "POST":
        tariff_id = request.POST.get("tariff")
        qty_raw = request.POST.get("qty", 1)
        details = request.POST.get("details", "").strip()

        try:
            qty = max(1, int(qty_raw))
        except (TypeError, ValueError):
            messages.error(request, 'Invalid quantity provided')
            return _redirect_after_doctor_action(request, visit_id)

        try:
            tariff = TariffAct.objects.get(id=tariff_id, active=True)
        except TariffAct.DoesNotExist:
            messages.error(request, 'Selected medical act could not be found')
            return _redirect_after_doctor_action(request, visit_id)

        BillingItem.objects.create(
            visit=visit,
            tariff=tariff,
            qty=qty,
            price_private_snapshot=tariff.price_private,
            price_insurance_snapshot=tariff.price_insurance or Decimal('0'),
            notes=details
        )
        
        messages.success(request, f'{tariff.name} added to billing sheet!')
        return _redirect_after_doctor_action(request, visit_id)
    
    return _redirect_after_doctor_action(request, visit_id)

@login_required
def save_triage(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id)
    clinic_user = _require_doctor_user(request)
    _ensure_visit_access(visit, clinic_user, request)
    triage, _ = Triage.objects.get_or_create(visit=visit)

    if request.method == "POST":
        temp = request.POST.get("temperature")
        if temp:
            try:
                triage.temperature_c = Decimal(temp)
            except (InvalidOperation, TypeError):
                messages.error(request, 'Temperature must be a number')
                return _redirect_after_doctor_action(request, visit_id)

        pulse = request.POST.get("pulse")
        if pulse:
            try:
                triage.pulse = int(pulse)
            except ValueError:
                messages.error(request, 'Pulse must be numeric')
                return _redirect_after_doctor_action(request, visit_id)

        resp = request.POST.get("respiratory_rate")
        if resp:
            try:
                triage.respiratory_rate = int(resp)
            except ValueError:
                messages.error(request, 'Respiratory rate must be numeric')
                return _redirect_after_doctor_action(request, visit_id)

        triage.blood_pressure = request.POST.get("blood_pressure", "").strip()

        notes = request.POST.get("notes", "").strip()
        triage.notes = notes or None
        if notes:
            triage.symptoms = notes

        triage.recorded_by = clinic_user

        weight = request.POST.get("weight")
        if weight:
            try:
                visit.weight_kg = Decimal(weight)
                visit.save(update_fields=['weight_kg'])
            except (InvalidOperation, TypeError):
                messages.error(request, 'Weight must be numeric')
                return _redirect_after_doctor_action(request, visit_id)

        triage.save()

        messages.success(request, 'Vital signs saved successfully!')

        return _redirect_after_doctor_action(request, visit_id)

    return _redirect_after_doctor_action(request, visit_id)

@login_required
def save_prescription(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id)
    clinic_user = _require_doctor_user(request)
    _ensure_visit_access(visit, clinic_user, request)
    patient = visit.patient

    if request.method == "POST":
        prescription_type = request.POST.get("prescription_type")

        if prescription_type == "written":
            instructions = request.POST.get("prescription_text", "").strip()
            if not instructions:
                messages.error(request, 'Please write the prescription details before saving')
                return _redirect_after_doctor_action(request, visit_id)

            Prescription.objects.create(
                visit=visit,
                patient=patient,
                doctor=clinic_user,
                prescription_type='written',
                instructions=instructions,
            )
            messages.success(request, 'Written prescription saved successfully!')
            return _redirect_after_doctor_action(request, visit_id)

        if prescription_type == "clinic":
            import json
            
            # Check if it's the new multi-medicine format
            medicines_data_json = request.POST.get("medicines_data")
            
            if medicines_data_json:
                # New format: multiple medicines in one prescription
                try:
                    medicines_data = json.loads(medicines_data_json)
                    
                    if not medicines_data:
                        messages.error(request, 'No medicines in cart')
                        return _redirect_after_doctor_action(request, visit_id)
                    
                    with transaction.atomic():
                        # Create one prescription for all medicines
                        prescription = Prescription.objects.create(
                            visit=visit,
                            patient=patient,
                            doctor=clinic_user,
                            prescription_type='clinic',
                            instructions='Multiple medications prescribed',
                        )
                        
                        # Add each medicine as a prescription item
                        for medicine_data in medicines_data:
                            stock_id = medicine_data.get('id')
                            quantity = int(medicine_data.get('quantity', 1))
                            dosage = medicine_data.get('dosage', '').strip()
                            frequency = medicine_data.get('frequency', '').strip()
                            duration = medicine_data.get('duration', '').strip()
                            instructions = medicine_data.get('instructions', '').strip()
                            
                            stock = (
                                PharmacyStock.objects.select_for_update()
                                .select_related('item')
                                .get(id=stock_id)
                            )
                            
                            if stock.qty_available < quantity:
                                messages.error(
                                    request,
                                    f"Not enough stock for {stock.item.name}. Available: {stock.qty_available}",
                                )
                                raise ValueError("Insufficient stock")
                            
                            PrescriptionItem.objects.create(
                                prescription=prescription,
                                inventory_item=stock.item,
                                custom_name=stock.item.name,
                                quantity=quantity,
                                dosage=dosage,
                                frequency=frequency,
                                duration=duration,
                                instructions=instructions,
                                dosage_instructions=f"{dosage} {frequency} {duration}".strip(),
                            )
                            
                            stock.qty_available -= quantity
                            stock.save(update_fields=['qty_available'])
                        
                        messages.success(request, f'Prescription with {len(medicines_data)} medicine(s) recorded successfully!')
                        return _redirect_after_doctor_action(request, visit_id)
                        
                except (json.JSONDecodeError, ValueError, PharmacyStock.DoesNotExist) as e:
                    messages.error(request, f'Error processing prescription: {str(e)}')
                    return _redirect_after_doctor_action(request, visit_id)
            
            # Old format: single medicine (kept for backward compatibility)
            stock_id = request.POST.get("medicine_id")
            quantity_raw = request.POST.get("quantity")
            dosage = request.POST.get("dosage", "").strip()
            frequency = request.POST.get("frequency", "").strip()
            duration = request.POST.get("duration", "").strip()
            instructions = request.POST.get("instructions", "").strip()

            try:
                quantity = max(1, int(quantity_raw))
            except (TypeError, ValueError):
                messages.error(request, 'Quantity must be numeric')
                return _redirect_after_doctor_action(request, visit_id)

            try:
                with transaction.atomic():
                    stock = (
                        PharmacyStock.objects.select_for_update()
                        .select_related('item')
                        .get(id=stock_id)
                    )

                    if stock.qty_available < quantity:
                        messages.error(
                            request,
                            f"Not enough stock for {stock.item.name}. Available: {stock.qty_available}",
                        )
                        return _redirect_after_doctor_action(request, visit_id)

                    prescription = Prescription.objects.create(
                        visit=visit,
                        patient=patient,
                        doctor=clinic_user,
                        prescription_type='clinic',
                        instructions=instructions or dosage,
                    )

                    PrescriptionItem.objects.create(
                        prescription=prescription,
                        inventory_item=stock.item,
                        custom_name=stock.item.name,
                        quantity=quantity,
                        dosage=dosage,
                        frequency=frequency,
                        duration=duration,
                        instructions=instructions,
                        dosage_instructions=f"{dosage} {frequency} {duration}".strip(),
                    )

                    stock.qty_available -= quantity
                    stock.save(update_fields=['qty_available'])

                messages.success(request, 'Clinic store prescription recorded successfully!')
                return _redirect_after_doctor_action(request, visit_id)
            except PharmacyStock.DoesNotExist:
                messages.error(request, 'Selected medicine is no longer available in stock')
                return _redirect_after_doctor_action(request, visit_id)

        messages.error(request, 'Please select a prescription type to continue')
        return _redirect_after_doctor_action(request, visit_id)

    return _redirect_after_doctor_action(request, visit_id)

@login_required
def delete_prescription(request, prescription_id):
    """Delete a prescription"""
    clinic_user = _require_doctor_user(request)
    
    try:
        prescription = Prescription.objects.select_related('visit').get(id=prescription_id)
        
        # Check if the doctor has access to this visit
        _ensure_visit_access(prescription.visit, clinic_user, request)
        
        visit_id = prescription.visit.id
        
        # Delete the prescription (items will be deleted automatically due to CASCADE)
        prescription.delete()
        
        messages.success(request, 'Prescription deleted successfully!')
    except Prescription.DoesNotExist:
        messages.error(request, 'Prescription not found')
        return redirect('doctor-patients')
    
    return _redirect_after_doctor_action(request, visit_id)

@login_required
def delete_billing_item(request, item_id):
    """Delete a billing item"""
    item = get_object_or_404(BillingItem, id=item_id)
    visit = item.visit
    clinic_user = _require_doctor_user(request)
    _ensure_visit_access(visit, clinic_user, request)

    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Billing item removed successfully!')
    else:
        messages.error(request, 'Invalid request method')
    return _redirect_after_doctor_action(request, visit.id)

@login_required
def close_visit(request, visit_id):
    """Send visit to cashier for payment/invoice generation"""
    visit = get_object_or_404(Visit, id=visit_id)
    clinic_user = _require_doctor_user(request)
    _ensure_visit_access(visit, clinic_user, request)

    billing_items = BillingItem.objects.filter(visit=visit)
    if not billing_items.exists():
        messages.error(request, 'Cannot send to cashier: No billing items added yet!')
        return redirect("doctor-visit-detail", visit_id=visit.id)

    total_private = Decimal('0')
    total_insurance = Decimal('0')

    for item in billing_items:
        qty = item.qty
        total_private += (item.price_private_snapshot or Decimal('0')) * qty
        total_insurance += (item.price_insurance_snapshot or item.price_private_snapshot or Decimal('0')) * qty

    patient = visit.patient
    insurance_percentage = patient.insurance_coverage_pct or 0

    insurance_cover = (total_insurance * Decimal(insurance_percentage)) / Decimal('100')
    private_cover = total_private + (total_insurance - insurance_cover)

    from clinic.models import Invoice
    invoice, created = Invoice.objects.get_or_create(
        visit=visit,
        defaults={
            'total_private': private_cover,
            'total_insurance': insurance_cover,
            'status': 'outpatient',
            'created_by': clinic_user
        }
    )
    
    if not created:
        invoice.total_private = private_cover
        invoice.total_insurance = insurance_cover
        invoice.save(update_fields=['total_private', 'total_insurance'])

    visit.status = "billed"
    visit.save(update_fields=['status'])

    messages.success(request, f'Visit sent to cashier! Total: {private_cover:,.0f} RWF')
    return redirect("doctor-dashboard")

