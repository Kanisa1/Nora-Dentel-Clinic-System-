# clinic/views_doctor_enhanced.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.timezone import localtime
from django.db.models import Q, Count
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
from .models import *
from .models_medical_records import *
import pandas as pd
def load_tariff_from_csv(insurance=None):
    """Load tariff acts and prices for all insurances from CSV."""
    print("=== USING NEW CSV LOADER ===")
    path = r"c:/Users/HP/Nora-Dentel-Clinic-System-/assets/new - NEW TALLIF RAMA & PRIVATE INSURANCE.csv"
    df = pd.read_csv(path, skiprows=2)
    tariffs = []
    PUBLIC_INSURANCES = ['RAMA', 'MMI', 'MIS/UR', 'RSSB']
    PRIVATE_INSURANCES = ['PRIME', 'BRITAM', 'EDENCARE', 'OLDMUTUAL', 'SANLAM', 'RADIANT', 'OTHER']
    for _, row in df.iterrows():
        code = str(row.get('RHIC')).strip()
        name = str(row.get('Procedure name')).strip()
        price_rama = row.get('RAMA, MMI, MIS/UR')
        price_private = row.get('PRIVATE INSURANCE& OTHER INSURANCE')
        # Convert to float, handle missing or dash
        try:
            price_rama = float(str(price_rama).replace(',', '').replace('-', '0').strip())
        except:
            price_rama = 0.0
        try:
            price_private = float(str(price_private).replace(',', '').replace('-', '0').strip())
        except:
            price_private = 0.0
        if code and name:
            tariff = {
                'code': code,
                'name': name,
                'RAMA_MMI_MISUR': price_rama,
                'PRIVATE_INSURANCE_OTHER': price_private,
            }
            # Select price based on insurance
            if insurance:
                ins = insurance.upper().replace(' ', '').replace('-', '')
                if ins in PUBLIC_INSURANCES:
                    tariff['selected_price'] = price_rama
                elif ins in PRIVATE_INSURANCES:
                    tariff['selected_price'] = price_private
                else:
                    # Default: treat as private
                    tariff['selected_price'] = price_private
            else:
                tariff['selected_price'] = price_private
            tariffs.append(tariff)
    return tariffs
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import io

COMPLETED_STATUSES = ['completed', 'awaiting_payment']


def _redirect_after_workspace_action(request, visit_id, default='doctor_dashboard_enhanced'):
    """Route back to dashboard or visit detail based on request parameters."""
    target = request.POST.get('return_to') or request.GET.get('return_to')
    if target == 'visit_detail':
        return redirect('doctor-visit-detail', visit_id=visit_id)
    if target == 'dashboard':
        return redirect('doctor_dashboard_enhanced')
    if target:
        return redirect(target)
    return redirect(default)


@login_required(login_url='/doctor/login/')
def doctor_dashboard_enhanced(request):
    """Enhanced doctor dashboard showing only their patients"""
    # Check if user has doctor role
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to access the doctor dashboard.')
        return redirect('doctor-login')
    
    if not hasattr(request.user, 'clinicuser'):
        messages.error(request, 'Your account is not associated with a clinic user.')
        return redirect('doctor-login')
    
    clinic_user = request.user.clinicuser
    
    if clinic_user.role != 'doctor':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('doctor-login')
    
    current_moment = timezone.now()
    today = current_moment.date()
    week_ago = today - timedelta(days=7)
    
    # Get doctor's patients (from visits)
    my_visits_today = Visit.objects.filter(
        doctor=clinic_user,
        created_at__date=today
    ).select_related('patient', 'department').order_by('-created_at')
    
    # Get all active visits for this doctor (base query without slice for statistics)
    # Include 'open' status which is set when reception creates a visit
    active_visits_query = (
        Visit.objects.filter(
            doctor=clinic_user,
            status__in=['open', 'waiting', 'in_consultation']
        )
        .select_related('patient', 'department', 'triage', 'medical_record')
        .prefetch_related(
            'billing_items__tariff',
            'prescriptions__doctor',
            'prescriptions__items__inventory_item',
            'certificates',
            'medical_record__attachments'
        )
        .order_by('-created_at')
    )
    
    # Statistics (calculated before slicing)
    total_patients_today = my_visits_today.count()
    completed_today = my_visits_today.filter(status__in=COMPLETED_STATUSES).count()
    
    # Waiting count includes 'open' (newly assigned) and 'waiting' status
    waiting_count = active_visits_query.filter(status__in=['open', 'waiting']).count()
    in_consultation_count = active_visits_query.filter(status='in_consultation').count()
    
    # Weekly statistics
    weekly_visits_queryset = list(
        Visit.objects.filter(
            doctor=clinic_user,
            created_at__date__gte=week_ago
        ).select_related('patient')
    )
    total_weekly = len(weekly_visits_queryset)
    weekly_completed = sum(1 for visit in weekly_visits_queryset if visit.status in COMPLETED_STATUSES)
    
    # Revenue statistics - sum of private and insurance amounts from paid invoices
    total_revenue_today = 0
    try:
        from django.db.models import Sum
        invoices_today = Invoice.objects.filter(
            visit__doctor=clinic_user,
            created_at__date=today,
            paid=True
        )
        # Calculate total from private and insurance amounts
        for invoice in invoices_today:
            total_revenue_today += (invoice.total_private or 0) + (invoice.total_insurance or 0)
    except Exception as e:
        print(f"Revenue calculation error: {e}")
        pass
    
    # Now slice for display
    active_visits = list(active_visits_query[:20])

    patient_ids = [visit.patient_id for visit in active_visits]
    appointments_map = defaultdict(list)

    if patient_ids:
        patient_appointments = (
            Appointment.objects.filter(patient_id__in=patient_ids)
            .select_related('doctor__user', 'department')
            .order_by('-scheduled_at')
        )
        for appt in patient_appointments:
            appointments_map[appt.patient_id].append(appt)

    for visit in active_visits:
        try:
            record = visit.medical_record
        except MedicalRecord.DoesNotExist:
            record = None
        if not record:
            record = MedicalRecord(visit=visit)
        setattr(visit, 'cached_medical_record', record)

        try:
            triage = visit.triage
        except Triage.DoesNotExist:
            triage = None
        if not triage:
            triage = Triage(visit=visit)
        setattr(visit, 'cached_triage', triage)

        setattr(visit, 'cached_appointments', appointments_map.get(visit.patient_id, []))

        billing_items = list(visit.billing_items.all())
        setattr(visit, 'cached_billing_items', billing_items)

        private_total = sum(((item.price_private_snapshot or Decimal('0')) * item.qty) for item in billing_items)
        insurance_total = sum(
            ((item.price_insurance_snapshot or item.price_private_snapshot or Decimal('0')) * item.qty)
            for item in billing_items
        )
        setattr(visit, 'billing_snapshot', {
            'private_total': private_total,
            'insurance_total': insurance_total,
            'grand_total': private_total + insurance_total,
        })
    
    # Get patients with pending medical records
    pending_records = Visit.objects.filter(
        doctor=clinic_user,
        status='in_consultation'
    ).exclude(
        id__in=MedicalRecord.objects.values_list('visit_id', flat=True)
    ).select_related('patient')[:10]
    
    # Recent appointments
    my_appointments = list(
        Appointment.objects.filter(
            doctor=clinic_user,
            scheduled_at__gte=today
        ).select_related('patient', 'doctor__user', 'department').order_by('scheduled_at')[:10]
    )
    
    # Recent medical records
    recent_records = MedicalRecord.objects.filter(
        visit__doctor=clinic_user
    ).select_related('visit', 'visit__patient').order_by('-created_at')[:5]
    
    # Shared reference data for forms
    # Do not set tariff_acts from DB here. Only set in billing_sheet view from CSV loader.
    pharmacy_stock = PharmacyStock.objects.select_related('item').filter(qty_available__gt=0).order_by('item__name')[:120]
    departments = Department.objects.all().order_by('name')
    peer_doctors = ClinicUser.objects.filter(role='doctor').exclude(id=clinic_user.id).select_related('user', 'department').order_by('user__first_name', 'user__last_name')
    hmis_classifications = HMISClassification.objects.all()
    idsr_choices = MedicalRecord._meta.get_field('idsr_disease').choices

    next_appointment = my_appointments[0] if my_appointments else None

    hourly_total = defaultdict(int)
    hourly_completed = defaultdict(int)
    for visit in my_visits_today:
        label = localtime(visit.created_at).strftime('%H:%M')
        hourly_total[label] += 1
        if visit.status in COMPLETED_STATUSES:
            hourly_completed[label] += 1

    health_curve_labels = sorted(hourly_total.keys())
    if not health_curve_labels:
        fallback_label = localtime(timezone.now()).strftime('%H:%M')
        health_curve_labels = [fallback_label]
        hourly_total[fallback_label] = 0
        hourly_completed[fallback_label] = 0

    health_curve = {
        'labels': health_curve_labels,
        'total': [hourly_total.get(label, 0) for label in health_curve_labels],
        'completed': [hourly_completed.get(label, 0) for label in health_curve_labels],
    }

    weekly_counts_map = defaultdict(int)
    weekly_new_patients_map = defaultdict(set)
    for visit in weekly_visits_queryset:
        visit_day = visit.created_at.date()
        weekly_counts_map[visit_day] += 1
        weekly_new_patients_map[visit_day].add(visit.patient_id)

    weekly_labels = []
    weekly_visit_counts = []
    weekly_new_counts = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        weekly_labels.append(day.strftime('%b %d'))
        weekly_visit_counts.append(weekly_counts_map.get(day, 0))
        weekly_new_counts.append(len(weekly_new_patients_map.get(day, set())))

    appointments_trend = {
        'labels': weekly_labels,
        'counts': weekly_visit_counts,
    }
    new_patients_trend = {
        'labels': weekly_labels,
        'counts': weekly_new_counts,
    }
    new_patients_week_total = sum(weekly_new_counts)

    patient_overview_values = [waiting_count, in_consultation_count, completed_today]
    patient_overview = {
        'labels': ['Waiting', 'In consultation', 'Completed'],
        'values': patient_overview_values,
    }

    status_total = max(sum(patient_overview_values), 1)
    hospital_management = []
    for label, value, gradient in [
        ('Waiting', waiting_count, 'linear-gradient(90deg, #f97316, #fbbf24)'),
        ('In consultation', in_consultation_count, 'linear-gradient(90deg, #0ea5e9, #38bdf8)'),
        ('Completed today', completed_today, 'linear-gradient(90deg, #10b981, #34d399)'),
    ]:
        hospital_management.append({
            'label': label,
            'value': value,
            'percent': round((value / status_total) * 100, 1) if status_total else 0,
            'gradient': gradient,
        })

    progress_lookup = {
        'completed': 100,
        'awaiting_payment': 100,
        'in_consultation': 72,
        'waiting': 38,
        'open': 24,
    }
    patient_progress_list = []
    for visit in active_visits[:7]:
        patient = visit.patient
        full_name = f"{patient.first_name or ''} {patient.last_name or ''}".strip()
        if not full_name:
            full_name = f"Visit #{visit.id}"
        status_label = visit.get_status_display() if hasattr(visit, 'get_status_display') else visit.status.replace('_', ' ').title()
        patient_progress_list.append({
            'name': full_name,
            'status': status_label,
            'progress': progress_lookup.get(visit.status, 50),
        })

    appointment_dates = {appt.scheduled_at.date(): appt for appt in my_appointments}

    focus_week_start = today - timedelta(days=today.weekday())
    calendar_focus_week = []
    for offset in range(7):
        day = focus_week_start + timedelta(days=offset)
        calendar_focus_week.append({
            'label': day.strftime('%a'),
            'day': day.day,
            'is_today': day == today,
            'has_event': day in appointment_dates,
        })

    first_day_month = today.replace(day=1)
    days_to_prev_sunday = (first_day_month.weekday() + 1) % 7
    calendar_grid_start = first_day_month - timedelta(days=days_to_prev_sunday)
    total_cells = 42  # 6 weeks * 7 days grid like reference UI
    calendar_cells = []
    for cell_index in range(total_cells):
        day = calendar_grid_start + timedelta(days=cell_index)
        calendar_cells.append({
            'label': day.strftime('%a'),
            'day': day.day,
            'is_today': day == today,
            'in_month': day.month == first_day_month.month,
            'has_event': day in appointment_dates,
        })

    calendar_weeks = [
        calendar_cells[idx:idx + 7]
        for idx in range(0, len(calendar_cells), 7)
    ]

    calendar_meta = {
        'month': first_day_month.strftime('%B'),
        'year': first_day_month.strftime('%Y'),
        'weekdays': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    }

    medical_sections = [
        {'name': 'chief_complaint', 'label': 'Chief complain', 'rows': 3},
        {'name': 'history_presenting_illness', 'label': 'History of presenting illness', 'rows': 4},
        {'name': 'past_medical_history', 'label': 'Past medical history', 'rows': 3},
        {'name': 'past_dental_history', 'label': 'Past dental history', 'rows': 3},
        {'name': 'current_medications', 'label': 'Current medications', 'rows': 3},
        {'name': 'allergies', 'label': 'Allergies', 'rows': 2},
        {'name': 'social_history', 'label': 'Social history', 'rows': 3},
        {'name': 'family_history', 'label': 'Family history', 'rows': 3},
        {'name': 'review_of_systems', 'label': 'Review of system', 'rows': 4},
        {'name': 'general_examination', 'label': 'General medical & dental examination', 'rows': 4},
        {'name': 'oral_examination', 'label': 'Dental specialty examination', 'rows': 4},
        {'name': 'specialty_examination', 'label': 'Medical specialty examination', 'rows': 4},
        {'name': 'investigations', 'label': 'Investigations (lab & radiographs)', 'rows': 4},
        {'name': 'diagnosis', 'label': 'Diagnosis', 'rows': 3},
        {'name': 'treatment_plan', 'label': 'Treatment plan', 'rows': 4},
    ]

    # Get doctor's display name
    doctor_name = clinic_user.user.get_full_name() or clinic_user.user.username
    
    context = {
        'clinic_user': clinic_user,
        'doctor_name': doctor_name,
        'doctor_department': clinic_user.department,
        'today': today,
        'current_moment': current_moment,
        'my_visits_today': my_visits_today,
        'active_visits': active_visits,
        'pending_records': pending_records,
        'total_patients_today': total_patients_today,
        'completed_today': completed_today,
        'waiting_count': waiting_count,
        'in_consultation_count': in_consultation_count,
        'my_appointments': my_appointments,
        'total_weekly': total_weekly,
        'weekly_completed': weekly_completed,
        'total_revenue_today': total_revenue_today,
        'recent_records': recent_records,
        'pharmacy_stock': pharmacy_stock,
        'departments': departments,
        'peer_doctors': peer_doctors,
        'hmis_classifications': hmis_classifications,
        'idsr_choices': idsr_choices,
        'medical_sections': medical_sections,
        'health_curve': health_curve,
        'appointments_trend': appointments_trend,
        'new_patients_trend': new_patients_trend,
        'new_patients_week_total': new_patients_week_total,
        'patient_overview': patient_overview,
        'patient_progress_list': patient_progress_list,
        'hospital_management': hospital_management,
        'calendar_weeks': calendar_weeks,
        'calendar_meta': calendar_meta,
        'calendar_focus_week': calendar_focus_week,
        'next_appointment': next_appointment,
    }
    
    return render(request, 'doctor/dashboard_enhanced_clean.html', context)


@login_required(login_url='/doctor/login/')
def medical_record_form(request, visit_id):
    """Create or edit comprehensive medical record for a visit"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'doctor':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('doctor-login')
    
    clinic_user = request.user.clinicuser
    
    visit = get_object_or_404(Visit, id=visit_id, doctor=clinic_user)
    
    # Get or create medical record
    try:
        medical_record = visit.medical_record
    except MedicalRecord.DoesNotExist:
        medical_record = None
    
    # Get or create triage
    try:
        triage = visit.triage
    except Triage.DoesNotExist:
        triage = None
    
    # Get HMIS classifications
    hmis_classifications = HMISClassification.objects.all()
    
    if request.method == 'POST':
        # Create or update triage
        if not triage:
            triage = Triage(visit=visit, recorded_by=clinic_user)
        
        # Update triage fields
        temp = request.POST.get('temperature_c')
        pulse = request.POST.get('pulse')
        bp = request.POST.get('blood_pressure')
        symptoms = request.POST.get('symptoms')
        
        if temp:
            triage.temperature_c = float(temp)
        if pulse:
            triage.pulse = int(pulse)
        if bp:
            triage.blood_pressure = bp
        if symptoms:
            triage.symptoms = symptoms
        
        triage.save()
        
        # Create or update medical record
        if not medical_record:
            medical_record = MedicalRecord(visit=visit)
        
        # Update all fields
        medical_record.chief_complaint = request.POST.get('chief_complaint', '')
        medical_record.history_presenting_illness = request.POST.get('history_presenting_illness', '')
        medical_record.past_medical_history = request.POST.get('past_medical_history', '')
        medical_record.past_dental_history = request.POST.get('past_dental_history', '')
        medical_record.current_medications = request.POST.get('current_medications', '')
        medical_record.allergies = request.POST.get('allergies', '')
        medical_record.social_history = request.POST.get('social_history', '')
        medical_record.family_history = request.POST.get('family_history', '')
        medical_record.review_of_systems = request.POST.get('review_of_systems', '')
        medical_record.general_examination = request.POST.get('general_examination', '')
        medical_record.oral_examination = request.POST.get('oral_examination', '')
        medical_record.specialty_examination = request.POST.get('specialty_examination', '')
        medical_record.investigations = request.POST.get('investigations', '')
        medical_record.diagnosis = request.POST.get('diagnosis', '')
        medical_record.treatment_plan = request.POST.get('treatment_plan', '')
        medical_record.hmis_classification = request.POST.get('hmis_classification', '')
        medical_record.idsr_disease = request.POST.get('idsr_disease', '')
        
        medical_record.save()
        
        # Handle file uploads
        if 'attachments' in request.FILES:
            for file in request.FILES.getlist('attachments'):
                attachment = MedicalRecordAttachment(
                    medical_record=medical_record,
                    file=file,
                    file_type=request.POST.get('file_type', 'document'),
                    description=request.POST.get('file_description', ''),
                    uploaded_by=clinic_user
                )
                attachment.save()
        
        messages.success(request, 'Medical record and triage saved successfully!')
        return redirect('doctor_dashboard_enhanced')
    
    context = {
        'clinic_user': clinic_user,
        'visit': visit,
        'medical_record': medical_record,
        'triage': triage,
        'hmis_classifications': hmis_classifications,
        'idsr_diseases': MedicalRecord._meta.get_field('idsr_disease').choices,
    }
    
    return render(request, 'doctor/medical_record_form.html', context)


@login_required(login_url='/doctor/login/')
def billing_sheet(request, visit_id):
    print("=== USING PATCHED BILLING SHEET VIEW ===")
    """Billing sheet for selecting tariff acts (Excel-based, insurance-aware)"""
    # Force tariffs to always come from CSV loader, never DB
    # DEBUG: Print loaded tariffs to server log
    insurance = None
    tariff_acts = []
    try:
        insurance = None
        # insurance will be set below after visit is loaded
    except Exception as e:
        print(f"[DEBUG] Error loading insurance: {e}")
    # The rest of the function will set insurance and load tariffs
    # The debug print will be after tariff_acts is loaded
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'doctor':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('doctor-login')
    clinic_user = request.user.clinicuser
    visit = get_object_or_404(Visit, id=visit_id, doctor=clinic_user)
    billing_items = BillingItem.objects.filter(visit=visit)
    insurance = visit.patient.insurer if visit.patient.is_insured else None
    tariff_acts = load_tariff_from_csv(insurance)
    print("[DEBUG] Loaded tariffs from CSV:")
    for t in tariff_acts[:10]:
        print(f"  Code: {t['code']}, Name: {t['name']}, Insurance: {t['RAMA_MMI_MISUR']}, Private: {t['PRIVATE_INSURANCE_OTHER']}")
    if request.method == 'POST':
        # Add billing item by code (from Excel, not DB)
        tariff_code = request.POST.get('tariff_id')
        qty = int(request.POST.get('qty', 1))
        notes = request.POST.get('notes', '').strip()
        if tariff_code:
            if not notes:
                messages.error(request, 'Details/Notes are required for each act.')
                return redirect('billing_sheet', visit_id=visit_id)
            print(f"[DEBUG] Selected tariff_code from POST: {tariff_code}")
            # Find tariff in loaded tariffs
            tariff = next((t for t in tariff_acts if str(t['code']) == str(tariff_code)), None)
            if tariff:
                # Use correct price for insurance and private
                price_private = float(tariff.get('PRIVATE_INSURANCE_OTHER', 0))
                price_insurance = float(tariff.get('RAMA_MMI_MISUR', 0))
                # Use public/private insurance logic for price selection
                PUBLIC_INSURANCES = ['RAMA', 'MMI', 'MIS/UR', 'RSSB']
                PRIVATE_INSURANCES = ['PRIME', 'BRITAM', 'EDENCARE', 'OLDMUTUAL', 'SANLAM', 'RADIANT', 'OTHER']
                price_selected = price_private
                if insurance:
                    ins = insurance.upper().replace(' ', '').replace('-', '')
                    if ins in PUBLIC_INSURANCES:
                        price_selected = price_insurance
                    elif ins in PRIVATE_INSURANCES:
                        price_selected = price_private
                # (price_selected is not used directly, but logic is now consistent)
                item = BillingItem.objects.create(
                    visit=visit,
                    tariff=None,
                    qty=qty,
                    price_private_snapshot=price_private,
                    price_insurance_snapshot=price_insurance,
                    notes=notes
                )
                item.code = tariff.get('code')
                item.name = tariff.get('name')
                messages.success(request, f"Added {tariff['name']} to billing")
            else:
                messages.error(request, 'Tariff not found in CSV')
            return redirect('billing_sheet', visit_id=visit_id)
    # Calculate totals
    total_private = sum(item.qty * (item.price_private_snapshot or 0) for item in billing_items)
    total_insurance = sum(item.qty * (item.price_insurance_snapshot or 0) for item in billing_items)
    coverage_pct = visit.patient.insurance_coverage_pct if visit.patient.is_insured else 0
    insurance_pays = (total_insurance * coverage_pct) / 100
    patient_pays_insurance = total_insurance - insurance_pays
    patient_pays_total = total_private + patient_pays_insurance
    # Patch code/name for display if not present (for all items)
    # No legacy DB code/name patching; only use CSV codes/names
    context = {
        'visit': visit,
        'patient': visit.patient,
        'billing_items': billing_items,
        'tariff_acts': tariff_acts,
        'total_private': total_private,
        'total_insurance': total_insurance,
        'coverage_pct': coverage_pct,
        'insurance_pays': insurance_pays,
        'patient_pays_insurance': patient_pays_insurance,
        'patient_pays_total': patient_pays_total,
        'insurance': insurance,
    }
    return render(request, 'doctor/billing_sheet.html', context)
@login_required(login_url='/doctor/login/')
def delete_billing_item(request, item_id):
    """Delete a billing item"""
    try:
        if request.user.is_authenticated and hasattr(request.user, 'clinicuser'):
            clinic_user = request.user.clinicuser
        else:
            clinic_user = ClinicUser.objects.filter(role='doctor').first()
            if not clinic_user:
                return JsonResponse({'success': False, 'error': 'No doctor found'})
    except:
        return JsonResponse({'success': False, 'error': 'Error accessing profile'})
    
    item = get_object_or_404(BillingItem, id=item_id)
    
    # Verify doctor owns this visit
    if item.visit.doctor != clinic_user:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    item.delete()
    return JsonResponse({'success': True})


@login_required(login_url='/doctor/login/')
def generate_medical_certificate(request, visit_id):
    """Generate printable medical certificate"""
    try:
        if request.user.is_authenticated and hasattr(request.user, 'clinicuser'):
            clinic_user = request.user.clinicuser
        else:
            clinic_user = ClinicUser.objects.filter(role='doctor').first()
            if not clinic_user:
                messages.error(request, 'No doctor users found.')
                return redirect('home')
    except:
        messages.error(request, 'Error accessing doctor profile.')
        return redirect('home')
    
    visit = get_object_or_404(Visit, id=visit_id, doctor=clinic_user)
    
    if request.method == 'POST':
        certificate_type = request.POST.get('certificate_type', 'fitness')
        diagnosis = request.POST.get('diagnosis', '')
        recommendations = request.POST.get('recommendations', '')
        duration_days = request.POST.get('duration_days', None)
        
        if duration_days:
            duration_days = int(duration_days)
            valid_until = timezone.now().date() + timedelta(days=duration_days)
        else:
            valid_until = None
        
        # Create certificate record
        certificate = MedicalCertificate.objects.create(
            visit=visit,
            patient=visit.patient,
            doctor=clinic_user,
            certificate_type=certificate_type,
            diagnosis=diagnosis,
            recommendations=recommendations,
            duration_days=duration_days,
            valid_until=valid_until
        )
        
        # Generate PDF
        return generate_certificate_pdf(certificate)
    
    # GET - show form
    context = {
        'visit': visit,
        'patient': visit.patient,
    }
    
    return render(request, 'doctor/medical_certificate_form.html', context)


def generate_certificate_pdf(certificate):
    """Generate PDF for medical certificate"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Add decorative border
    p.setStrokeColorRGB(0.48, 0.23, 0.93)  # Purple color
    p.setLineWidth(3)
    p.rect(0.5*inch, 0.5*inch, width - 1*inch, height - 1*inch, stroke=1, fill=0)
    
    # Inner border
    p.setStrokeColorRGB(0.48, 0.23, 0.93)
    p.setLineWidth(1)
    p.rect(0.6*inch, 0.6*inch, width - 1.2*inch, height - 1.2*inch, stroke=1, fill=0)
    
    # Try to add logo (if exists)
    try:
        from pathlib import Path
        logo_path = Path(__file__).resolve().parent.parent / 'static' / 'images' / 'logo.png'
        if logo_path.exists():
            p.drawImage(str(logo_path), 1*inch, height - 1.5*inch, width=1*inch, height=1*inch, preserveAspectRatio=True, mask='auto')
    except:
        pass
    
    # Header with clinic name
    p.setFillColorRGB(0.48, 0.23, 0.93)  # Purple color
    p.setFont("Helvetica-Bold", 24)
    p.drawCentredString(width/2, height - 1*inch, "NORA DENTAL CLINIC")
    
    # Tagline
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.setFont("Helvetica-Oblique", 11)
    p.drawCentredString(width/2, height - 1.3*inch, "Excellence in Dental Care")
    
    # Address and contact info
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica", 10)
    p.drawCentredString(width/2, height - 1.6*inch, "KG 123 Street, Kigali, Rwanda")
    p.drawCentredString(width/2, height - 1.8*inch, "Tel: +250 788 123 456 | Email: info@noradental.rw | www.noradental.rw")
    
    # Horizontal line
    p.setStrokeColorRGB(0.48, 0.23, 0.93)
    p.setLineWidth(2)
    p.line(1*inch, height - 2*inch, width - 1*inch, height - 2*inch)
    
    # Certificate Title with background
    p.setFillColorRGB(0.48, 0.23, 0.93)
    p.rect(1.5*inch, height - 2.5*inch, width - 3*inch, 0.4*inch, stroke=0, fill=1)
    
    p.setFillColorRGB(1, 1, 1)  # White text
    p.setFont("Helvetica-Bold", 16)
    cert_title = certificate.get_certificate_type_display().upper()
    p.drawCentredString(width/2, height - 2.4*inch, cert_title)
    
    # Certificate Number
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.setFont("Helvetica", 9)
    p.drawCentredString(width/2, height - 2.7*inch, f"Certificate No: CERT-{certificate.id:06d}")
    
    # Date
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica", 11)
    p.drawString(1*inch, height - 3.1*inch, f"Issue Date: {certificate.issue_date.strftime('%d %B %Y')}")
    
    # Patient details section
    y = height - 3.6*inch
    p.setFillColorRGB(0.48, 0.23, 0.93)
    p.setFont("Helvetica-Bold", 13)
    p.drawString(1*inch, y, "PATIENT INFORMATION")
    
    # Underline
    p.setStrokeColorRGB(0.48, 0.23, 0.93)
    p.setLineWidth(1)
    p.line(1*inch, y - 0.05*inch, 3*inch, y - 0.05*inch)
    
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica", 11)
    y -= 0.35*inch
    p.drawString(1*inch, y, f"Full Name:")
    p.setFont("Helvetica-Bold", 11)
    p.drawString(2.2*inch, y, f"{certificate.patient.first_name} {certificate.patient.last_name}")
    
    p.setFont("Helvetica", 11)
    y -= 0.25*inch
    p.drawString(1*inch, y, f"Age:")
    p.setFont("Helvetica-Bold", 11)
    p.drawString(2.2*inch, y, f"{certificate.patient.age} years")
    
    p.setFont("Helvetica", 11)
    y -= 0.25*inch
    p.drawString(1*inch, y, f"Gender:")
    p.setFont("Helvetica-Bold", 11)
    p.drawString(2.2*inch, y, f"{certificate.patient.gender or 'N/A'}")
    
    p.setFont("Helvetica", 11)
    y -= 0.25*inch
    p.drawString(1*inch, y, f"ID/Passport:")
    p.setFont("Helvetica-Bold", 11)
    p.drawString(2.2*inch, y, f"{certificate.patient.national_id or 'N/A'}")
    
    # Medical information section
    y -= 0.5*inch
    p.setFillColorRGB(0.48, 0.23, 0.93)
    p.setFont("Helvetica-Bold", 13)
    p.drawString(1*inch, y, "MEDICAL INFORMATION")
    
    # Underline
    p.setStrokeColorRGB(0.48, 0.23, 0.93)
    p.setLineWidth(1)
    p.line(1*inch, y - 0.05*inch, 3.2*inch, y - 0.05*inch)
    
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 11)
    y -= 0.35*inch
    p.drawString(1*inch, y, "Diagnosis:")
    
    p.setFont("Helvetica", 11)
    y -= 0.25*inch
    # Word wrap diagnosis
    lines = []
    current_line = ""
    for word in certificate.diagnosis.split():
        if len(current_line + word) < 75:
            current_line += word + " "
        else:
            lines.append(current_line)
            current_line = word + " "
    if current_line:
        lines.append(current_line)
    
    for line in lines:
        p.drawString(1.2*inch, y, line.strip())
        y -= 0.2*inch
    
    if certificate.recommendations:
        y -= 0.1*inch
        p.setFont("Helvetica-Bold", 11)
        p.drawString(1*inch, y, "Recommendations:")
        
        p.setFont("Helvetica", 11)
        y -= 0.25*inch
        # Word wrap recommendations
        lines = certificate.recommendations.split('\n')
        for line in lines:
            if len(line) > 75:
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line + word) < 75:
                        current_line += word + " "
                    else:
                        p.drawString(1.2*inch, y, current_line.strip())
                        y -= 0.2*inch
                        current_line = word + " "
                if current_line:
                    p.drawString(1.2*inch, y, current_line.strip())
                    y -= 0.2*inch
            else:
                p.drawString(1.2*inch, y, line)
                y -= 0.2*inch
    
    if certificate.duration_days:
        y -= 0.1*inch
        p.setFont("Helvetica-Bold", 11)
        p.drawString(1*inch, y, f"Duration of Leave: {certificate.duration_days} days")
        y -= 0.25*inch
        p.setFont("Helvetica", 11)
        p.drawString(1*inch, y, f"Valid Until: {certificate.valid_until.strftime('%d %B %Y')}")
    
    # Doctor signature section
    y = 2.5*inch
    p.setFont("Helvetica-Bold", 11)
    p.drawString(4.5*inch, y, "Authorized By:")
    
    y -= 0.5*inch
    p.setStrokeColorRGB(0, 0, 0)
    p.setLineWidth(1)
    p.line(4.5*inch, y, 7*inch, y)
    
    y -= 0.25*inch
    p.setFont("Helvetica-Bold", 12)
    p.drawString(4.5*inch, y, f"Dr. {certificate.doctor.user.get_full_name()}")
    
    y -= 0.2*inch
    p.setFont("Helvetica", 10)
    p.drawString(4.5*inch, y, f"Medical License No: [License]")
    
    y -= 0.2*inch
    p.drawString(4.5*inch, y, f"Signature & Official Stamp")
    
    # QR Code placeholder (optional)
    p.setStrokeColorRGB(0.7, 0.7, 0.7)
    p.setLineWidth(1)
    p.rect(1*inch, 1.5*inch, 0.8*inch, 0.8*inch, stroke=1, fill=0)
    p.setFont("Helvetica", 7)
    p.drawString(1*inch, 1.35*inch, "QR Code")
    
    # Footer with verification info
    p.setFillColorRGB(0.48, 0.23, 0.93)
    p.setFont("Helvetica-Bold", 9)
    p.drawCentredString(width/2, 1*inch, "CERTIFICATE VERIFICATION")
    
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Oblique", 8)
    p.drawCentredString(width/2, 0.85*inch, "This is an official medical document issued by Nora Dental Clinic")
    p.drawCentredString(width/2, 0.7*inch, f"Verify online at: www.noradental.rw/verify/{certificate.id}")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    
    # Update certificate as printed
    certificate.printed = True
    certificate.printed_at = timezone.now()
    certificate.save()
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="medical_certificate_{certificate.id}.pdf"'
    
    return response


@login_required(login_url='/doctor/login/')
def transfer_patient(request, visit_id):
    """Transfer patient to another doctor/department"""
    try:
        if request.user.is_authenticated and hasattr(request.user, 'clinicuser'):
            clinic_user = request.user.clinicuser
        else:
            clinic_user = ClinicUser.objects.filter(role='doctor').first()
            if not clinic_user:
                messages.error(request, 'No doctor users found.')
                return redirect('home')
    except:
        messages.error(request, 'Error accessing doctor profile.')
        return redirect('home')
    
    visit = get_object_or_404(Visit, id=visit_id, doctor=clinic_user)
    
    if request.method == 'POST':
        to_department_id = request.POST.get('to_department')
        to_doctor_id = request.POST.get('to_doctor')
        reason = request.POST.get('reason', '')
        notes = request.POST.get('notes', '')
        
        to_department = get_object_or_404(Department, id=to_department_id) if to_department_id else None
        to_doctor = get_object_or_404(ClinicUser, id=to_doctor_id, role='doctor') if to_doctor_id else None
        
        # Create transfer record
        transfer = PatientTransfer.objects.create(
            visit=visit,
            from_doctor=clinic_user,
            to_doctor=to_doctor,
            from_department=visit.department,
            to_department=to_department,
            reason=reason,
            notes=notes
        )
        
        # Update visit
        if to_doctor:
            visit.doctor = to_doctor
        if to_department:
            visit.department = to_department
        visit.status = 'waiting'  # Back to waiting for new doctor
        visit.save()
        
        messages.success(request, f'Patient transferred successfully to {to_doctor.user.get_full_name() if to_doctor else to_department.name}')
        return _redirect_after_workspace_action(request, visit_id)
    
    # GET - show form
    departments = Department.objects.all()
    doctors = ClinicUser.objects.filter(role='doctor').exclude(id=clinic_user.id).select_related('user', 'department')
    
    context = {
        'visit': visit,
        'patient': visit.patient,
        'departments': departments,
        'doctors': doctors,
    }
    
    return render(request, 'doctor/transfer_patient.html', context)


@login_required(login_url='/doctor/login/')
def create_followup_appointment(request, visit_id):
    """Inline endpoint for creating follow-up appointments from the dashboard."""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'doctor':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('doctor-login')

    clinic_user = request.user.clinicuser
    visit = get_object_or_404(Visit, id=visit_id, doctor=clinic_user)

    if request.method != 'POST':
        return _redirect_after_workspace_action(request, visit_id)

    date_str = request.POST.get('appointment_date')
    time_str = request.POST.get('appointment_time')
    notes = request.POST.get('appointment_notes', '').strip()
    dept_id = request.POST.get('department') or visit.department_id
    doctor_id = request.POST.get('doctor') or clinic_user.id

    if not date_str or not time_str:
        messages.error(request, 'Please select both date and time for the appointment.')
        return _redirect_after_workspace_action(request, visit_id)

    try:
        scheduled_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        scheduled_time = datetime.strptime(time_str, '%H:%M').time()
        scheduled_at = datetime.combine(scheduled_date, scheduled_time)
        if timezone.is_naive(scheduled_at):
            scheduled_at = timezone.make_aware(scheduled_at, timezone.get_current_timezone())
    except ValueError:
        messages.error(request, 'Invalid appointment date or time provided.')
        return _redirect_after_workspace_action(request, visit_id)

    department = None
    if dept_id:
        department = Department.objects.filter(id=dept_id).first()

    doctor = get_object_or_404(ClinicUser, id=doctor_id, role='doctor')

    Appointment.objects.create(
        patient=visit.patient,
        doctor=doctor,
        scheduled_by=clinic_user,
        department=department or visit.department,
        scheduled_at=scheduled_at,
        notes=notes,
    )

    messages.success(request, 'Follow-up appointment scheduled successfully.')
    return _redirect_after_workspace_action(request, visit_id)


@login_required(login_url='/doctor/login/')
def send_to_cashier(request, visit_id):
    """Send patient to cashier for payment after consultation"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'doctor':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('doctor-login')
    
    clinic_user = request.user.clinicuser
    visit = get_object_or_404(Visit, id=visit_id, doctor=clinic_user)
    redirect_hint = request.POST.get('return_to') or request.GET.get('return_to')
    
    # Verify that triage and billing items exist
    if not hasattr(visit, 'triage') or not visit.triage:
        messages.error(request, 'Please add triage information before sending to cashier.')
        if redirect_hint == 'visit_detail':
            return redirect('doctor-visit-detail', visit_id=visit_id)
        return redirect('medical_record_form', visit_id=visit_id)
    
    billing_items = BillingItem.objects.filter(visit=visit)
    if not billing_items.exists():
        messages.error(request, 'Please add at least one billing item before sending to cashier.')
        if redirect_hint == 'visit_detail':
            return redirect('doctor-visit-detail', visit_id=visit_id)
        return redirect('billing_sheet', visit_id=visit_id)
    
    # Mark visit as completed once billing is forwarded to cashier
    visit.status = 'completed'
    visit.save()
    
    patient_name = f'{visit.patient.first_name} {visit.patient.last_name}'
    messages.success(request, f'Patient {patient_name} sent to cashier for payment.')
    return _redirect_after_workspace_action(request, visit_id)


@login_required(login_url='/doctor/login/')
def my_patients_today(request):
    """View all patients for today"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'doctor':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('doctor-login')
    
    clinic_user = request.user.clinicuser
    today = timezone.now().date()
    
    visits_today = Visit.objects.filter(
        doctor=clinic_user,
        created_at__date=today
    ).select_related('patient', 'department').order_by('-created_at')
    
    context = {
        'patients': visits_today,  # Changed from 'visits' to 'patients' to match template
        'visits': visits_today,
        'clinic_user': clinic_user,
        'today': today,
    }
    return render(request, 'doctor/my_patients_today.html', context)


@login_required(login_url='/doctor/login/')
def waiting_queue(request):
    """View waiting queue"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'doctor':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('doctor-login')
    
    clinic_user = request.user.clinicuser
    
    waiting_patients = Visit.objects.filter(
        doctor=clinic_user,
        status__in=['open', 'waiting']
    ).select_related('patient', 'department').order_by('created_at')
    
    context = {
        'waiting_patients': waiting_patients,
        'clinic_user': clinic_user,
    }
    return render(request, 'doctor/waiting_queue.html', context)


@login_required(login_url='/doctor/login/')
def in_consultation_list(request):
    """View patients currently in consultation"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'doctor':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('doctor-login')
    
    clinic_user = request.user.clinicuser
    
    in_consultation = Visit.objects.filter(
        doctor=clinic_user,
        status='in_consultation'
    ).select_related('patient', 'department').order_by('created_at')
    
    context = {
        'in_consultation': in_consultation,
        'clinic_user': clinic_user,
    }
    return render(request, 'doctor/in_consultation.html', context)


@login_required(login_url='/doctor/login/')
def medical_records_list(request):
    """View all medical records created by this doctor"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'doctor':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('doctor-login')
    
    clinic_user = request.user.clinicuser
    
    # Get all medical records for this doctor's patients
    medical_records = MedicalRecord.objects.filter(
        visit__doctor=clinic_user
    ).select_related('visit', 'visit__patient').order_by('-created_at')
    
    context = {
        'medical_records': medical_records,
        'clinic_user': clinic_user,
    }
    return render(request, 'doctor/medical_records_list.html', context)


@login_required(login_url='/doctor/login/')
def my_statistics(request):
    """Comprehensive statistics dashboard with graphs"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'doctor':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('doctor-login')
    
    from django.db.models import Sum, Avg, Count
    from django.db.models.functions import TruncDate
    import json
    
    clinic_user = request.user.clinicuser
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Overall statistics
    total_patients = Visit.objects.filter(doctor=clinic_user).count()
    total_completed = Visit.objects.filter(doctor=clinic_user, status__in=COMPLETED_STATUSES).count()
    total_revenue = 0
    try:
        invoices = Invoice.objects.filter(visit__doctor=clinic_user, paid=True)
        for inv in invoices:
            total_revenue += (inv.total_private or 0) + (inv.total_insurance or 0)
    except:
        pass
    
    # Today's stats
    today_patients = Visit.objects.filter(doctor=clinic_user, created_at__date=today).count()
    today_completed = Visit.objects.filter(
        doctor=clinic_user,
        created_at__date=today,
        status__in=COMPLETED_STATUSES,
    ).count()
    
    # Weekly stats
    weekly_patients = Visit.objects.filter(doctor=clinic_user, created_at__date__gte=week_ago).count()
    weekly_completed = Visit.objects.filter(
        doctor=clinic_user,
        created_at__date__gte=week_ago,
        status__in=COMPLETED_STATUSES,
    ).count()
    
    # Monthly stats
    monthly_patients = Visit.objects.filter(doctor=clinic_user, created_at__date__gte=month_ago).count()
    monthly_completed = Visit.objects.filter(
        doctor=clinic_user,
        created_at__date__gte=month_ago,
        status__in=COMPLETED_STATUSES,
    ).count()
    
    # Daily patient count for last 30 days (for graph)
    daily_stats = Visit.objects.filter(
        doctor=clinic_user,
        created_at__date__gte=month_ago
    ).annotate(date=TruncDate('created_at')).values('date').annotate(
        total=Count('id')
    ).order_by('date')
    
    dates = [stat['date'].strftime('%Y-%m-%d') for stat in daily_stats]
    counts = [stat['total'] for stat in daily_stats]
    
    # Status distribution
    status_distribution = Visit.objects.filter(doctor=clinic_user).values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Most common diagnoses
    top_diagnoses = MedicalRecord.objects.filter(
        visit__doctor=clinic_user
    ).values('diagnosis').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Calculate completion rate
    completion_rate = (total_completed * 100 / total_patients) if total_patients > 0 else 0
    
    context = {
        'clinic_user': clinic_user,
        'total_patients': total_patients,
        'total_completed': total_completed,
        'total_revenue': total_revenue,
        'completion_rate': completion_rate,
        'today': timezone.now(),
        'today_patients': today_patients,
        'today_completed': today_completed,
        'weekly_patients': weekly_patients,
        'weekly_completed': weekly_completed,
        'monthly_patients': monthly_patients,
        'monthly_completed': monthly_completed,
        'dates_json': json.dumps(dates),
        'counts_json': json.dumps(counts),
        'status_distribution': list(status_distribution),
        'top_diagnoses': list(top_diagnoses),
    }
    return render(request, 'doctor/my_statistics.html', context)


@login_required(login_url='/doctor/login/')
def prescriptions_list(request):
    """View all prescriptions"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'doctor':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('doctor-login')
    
    clinic_user = request.user.clinicuser
    
    prescriptions = Prescription.objects.filter(
        visit__doctor=clinic_user
    ).select_related('visit', 'visit__patient').order_by('-id')
    
    context = {
        'prescriptions': prescriptions,
        'clinic_user': clinic_user,
    }
    return render(request, 'doctor/prescriptions_list.html', context)


@login_required(login_url='/doctor/login/')
def print_prescription(request, prescription_id):
    """Print prescription - accessible by doctor"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role not in ['doctor', 'cashier']:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
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
    
    # Check if user has permission to view this prescription
    clinic_user = request.user.clinicuser
    if clinic_user.role == 'doctor' and prescription.doctor != clinic_user:
        messages.error(request, 'You can only print your own prescriptions.')
        return redirect('prescriptions_list')
    
    context = {
        'prescription': prescription,
        'print_date': timezone.now(),
    }
    return render(request, 'doctor/prescription_print.html', context)


@login_required(login_url='/doctor/login/')
def medical_certificates_list(request):
    """View all medical certificates"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'doctor':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('doctor-login')
    
    clinic_user = request.user.clinicuser
    
    certificates = MedicalCertificate.objects.filter(
        visit__doctor=clinic_user
    ).select_related('visit', 'visit__patient').order_by('-created_at')
    
    context = {
        'certificates': certificates,
        'clinic_user': clinic_user,
    }
    return render(request, 'doctor/certificates_list.html', context)


@login_required(login_url='/doctor/login/')
def patient_transfers_list(request):
    """View all patient transfers"""
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'doctor':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('doctor-login')
    
    clinic_user = request.user.clinicuser
    
    transfers = PatientTransfer.objects.filter(
        referring_doctor=clinic_user
    ).select_related('patient', 'referring_facility').order_by('-transfer_date')
    
    context = {
        'transfers': transfers,
        'clinic_user': clinic_user,
    }
    return render(request, 'doctor/transfers_list.html', context)


@login_required(login_url='/doctor/login/')
def doctor_profile(request):
    """Display doctor profile with activity stats and preferences"""
    clinic_user, _ = ClinicUser.objects.get_or_create(
        user=request.user,
        defaults={'role': 'doctor'}
    )

    if clinic_user.role != 'doctor':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('doctor_dashboard_enhanced')

    now = timezone.now()
    last_month = now - timedelta(days=30)
    last_week = now - timedelta(days=7)

    waiting_count = Visit.objects.filter(
        doctor=clinic_user,
        status__in=['open', 'waiting']
    ).count()
    in_consultation_count = Visit.objects.filter(
        doctor=clinic_user,
        status='in_consultation'
    ).count()

    consultations_completed = Visit.objects.filter(
        doctor=clinic_user,
        status__in=COMPLETED_STATUSES,
        created_at__gte=last_month
    ).count()
    patients_this_week = Visit.objects.filter(
        doctor=clinic_user,
        created_at__gte=last_week
    ).values('patient_id').distinct().count()
    prescriptions_written = Prescription.objects.filter(
        doctor=clinic_user,
        created_at__gte=last_month
    ).count()

    upcoming_appointments = Appointment.objects.filter(
        doctor=clinic_user,
        scheduled_at__gte=now
    ).select_related('patient', 'department').order_by('scheduled_at')[:5]

    recent_patients = Visit.objects.filter(
        doctor=clinic_user
    ).select_related('patient').order_by('-created_at')[:5]

    context = {
        'clinic_user': clinic_user,
        'doctor_name': request.user.get_full_name() or request.user.username,
        'doctor_username': request.user.username,
        'doctor_email': request.user.email,
        'doctor_department': clinic_user.department,
        'waiting_count': waiting_count,
        'in_consultation_count': in_consultation_count,
        'consultations_completed': consultations_completed,
        'patients_this_week': patients_this_week,
        'prescriptions_written': prescriptions_written,
        'upcoming_appointments': upcoming_appointments,
        'recent_patients': recent_patients,
    }
    return render(request, 'doctor/profile.html', context)


@login_required(login_url='/doctor/login/')
def doctor_update_profile(request):
    """Update basic doctor profile information and password"""
    if request.method != 'POST':
        return redirect('doctor_profile')

    clinic_user, _ = ClinicUser.objects.get_or_create(
        user=request.user,
        defaults={'role': 'doctor'}
    )

    if clinic_user.role != 'doctor':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('doctor_dashboard_enhanced')

    user = request.user
    user.first_name = request.POST.get('first_name', '').strip()
    user.last_name = request.POST.get('last_name', '').strip()
    user.email = request.POST.get('email', '').strip()

    clinic_user.phone = request.POST.get('phone', '').strip()
    if not clinic_user.role:
        clinic_user.role = 'doctor'
    clinic_user.save()

    new_password = request.POST.get('new_password', '').strip()
    password_updated = False

    if new_password:
        current_password = request.POST.get('current_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not current_password or not user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('doctor_profile')

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('doctor_profile')

        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('doctor_profile')

        user.set_password(new_password)
        password_updated = True

    user.save()

    success_message = 'Profile information updated successfully.'
    if password_updated:
        update_session_auth_hash(request, user)
        success_message = 'Profile information and password updated successfully.'

    messages.success(request, success_message)
    return redirect('doctor_profile')


@login_required(login_url='/doctor/login/')
def doctor_update_profile_picture(request):
    """Handle profile picture uploads for doctors"""
    if request.method != 'POST' or 'profile_picture' not in request.FILES:
        messages.error(request, 'Please choose a picture to upload.')
        return redirect('doctor_profile')

    clinic_user, _ = ClinicUser.objects.get_or_create(
        user=request.user,
        defaults={'role': 'doctor'}
    )

    if clinic_user.role != 'doctor':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('doctor_dashboard_enhanced')

    if clinic_user.profile_picture:
        clinic_user.profile_picture.delete()

    clinic_user.profile_picture = request.FILES['profile_picture']
    clinic_user.save()

    messages.success(request, 'Profile picture updated successfully.')
    return redirect('doctor_profile')

