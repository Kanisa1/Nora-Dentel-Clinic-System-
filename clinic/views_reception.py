from django.shortcuts import render, redirect
from clinic.models import Patient, Appointment, Department, ClinicUser
from clinic.forms import PatientForm
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_http_methods
from datetime import datetime


@require_http_methods(["GET", "POST"])
def reception_login(request):
    """Custom login page for reception staff."""
    if request.method == 'POST':
        # CRITICAL: Log out any existing user BEFORE authenticating the new one
        if request.user.is_authenticated:
            print(f"DEBUG: Logging out existing user: {request.user.username}")
            logout(request)
        
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        print(f"DEBUG: Attempting login for username: {username}")
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            print(f"DEBUG: Authentication successful for: {username}")
            # Check if user has a clinic profile and the correct role
            if hasattr(user, 'clinicuser'):
                print(f"DEBUG: User has ClinicUser with role: {user.clinicuser.role}")
                if user.clinicuser.role == 'reception':
                    login(request, user)
                    print(f"DEBUG: Login successful, redirecting to dashboard")
                    return redirect('reception_dashboard')
                else:
                    print(f"DEBUG: User role is '{user.clinicuser.role}', not 'reception'")
                    return render(request, 'reception/login.html', {
                        'error': 'You do not have reception privileges.'
                    })
            else:
                print(f"DEBUG: User has no ClinicUser profile")
                return render(request, 'reception/login.html', {
                    'error': 'You do not have reception privileges.'
                })
        else:
            print(f"DEBUG: Authentication failed for username: {username}")
            # Invalid username or password
            return render(request, 'reception/login.html', {
                'error': 'Invalid username or password.'
            })
    
    # For a GET request, log out any existing user and show the login form
    if request.user.is_authenticated:
        print(f"DEBUG: GET request - logging out existing user: {request.user.username}")
        logout(request)
    
    return render(request, 'reception/login.html')


def reception_dashboard(request):
    # Instead of a decorator, we perform all checks inside the view.
    # 1. Is the user even logged in?
    if not request.user.is_authenticated:
        print("DEBUG: User not authenticated, redirecting to login")
        return redirect('reception_login')

    # 2. Does the user have a clinic profile and the correct role?
    print(f"DEBUG: User {request.user.username} is authenticated")
    print(f"DEBUG: Has clinicuser: {hasattr(request.user, 'clinicuser')}")
    
    if hasattr(request.user, 'clinicuser'):
        print(f"DEBUG: User role: {request.user.clinicuser.role}")
        
    if not hasattr(request.user, 'clinicuser') or request.user.clinicuser.role != 'reception':
        print(f"DEBUG: User failed role check, logging out")
        logout(request) # Log out the user to be safe
        return redirect('reception_login')

    print(f"DEBUG: All checks passed, rendering dashboard")
    # If all checks pass, render the dashboard.
    today = timezone.now().date()
    
    # Get reception user info
    clinic_user = request.user.clinicuser
    reception_name = clinic_user.user.get_full_name() or clinic_user.user.username
    reception_username = clinic_user.user.username
    reception_email = clinic_user.user.email or ""
    
    # Get statistics for dashboard cards
    from clinic.models import Visit, WaitingQueueEntry
    
    # Today's patients (unique patients with visits today)
    patients_today = Visit.objects.filter(
        created_at__date=today
    ).values('patient').distinct().count()
    
    # Scheduled appointments (today and future)
    scheduled_appointments = Appointment.objects.filter(
        scheduled_at__date__gte=today,
        status='scheduled'
    ).count()
    
    # Total registered patients
    total_registered_patients = Patient.objects.count()
    
    # Checked in today (patients currently in waiting queue)
    checked_in_today = WaitingQueueEntry.objects.filter(
        checked_in_at__date=today
    ).values('visit__patient').distinct().count()
    
    # Get today's queue with related data
    today_queue = WaitingQueueEntry.objects.filter(
        checked_in_at__date=today
    ).select_related('visit', 'visit__patient', 'visit__doctor', 'visit__doctor__user').order_by('position')[:10]
    
    # Get upcoming appointments (today and next 7 days)
    from datetime import timedelta
    next_week = today + timedelta(days=7)
    appointments = Appointment.objects.filter(
        scheduled_at__date__range=[today, next_week],
        status__in=['scheduled', 'checked_in']
    ).select_related('patient', 'doctor', 'doctor__user').order_by('scheduled_at')[:10]
    
    # Get data for tables
    patients = Patient.objects.all()
    doctors = ClinicUser.objects.filter(role='doctor')
    
    return render(request, "reception/dashboard.html", {
        "reception_name": reception_name,
        "reception_username": reception_username,
        "reception_email": reception_email,
        "patients_today": patients_today,
        "scheduled_appointments": scheduled_appointments,
        "total_registered_patients": total_registered_patients,
        "checked_in_today": checked_in_today,
        "today_queue": today_queue,
        "appointments": appointments,
        "todays_appointments": Appointment.objects.filter(
            scheduled_at__date=today
        ).count(),
        "total_patients": Patient.objects.count(),
        "patients": patients,
        "doctors": doctors,
    })


def schedule_appointment(request):
    """Separate page for scheduling appointments"""
    if request.method == "POST":
        patient_id = request.POST.get('patient_id')
        doctor_id = request.POST.get('doctor_id')
        department_id = request.POST.get('department_id')
        scheduled_date = request.POST.get('scheduled_date')
        scheduled_time = request.POST.get('scheduled_time')
        notes = request.POST.get('notes', '')
        
        if patient_id and doctor_id and scheduled_date and scheduled_time:
            patient = Patient.objects.get(id=patient_id)
            doctor = ClinicUser.objects.get(id=doctor_id)
            department = None
            if department_id:
                department = Department.objects.get(id=department_id)
            
            from datetime import datetime
            scheduled_at = datetime.strptime(f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M")
            # Make timezone aware
            scheduled_at = timezone.make_aware(scheduled_at)

            scheduler = None
            if request.user.is_authenticated and hasattr(request.user, 'clinicuser'):
                scheduler = request.user.clinicuser
            
            Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                department=department,
                scheduled_at=scheduled_at,
                scheduled_by=scheduler,
                notes=notes,
                status='scheduled'
            )
            return redirect('reception_appointments_today')

    # Get data for the form
    patients = Patient.objects.all().order_by('first_name')
    doctors = ClinicUser.objects.filter(role='doctor').order_by('user__first_name')
    departments = Department.objects.all()
    
    return render(request, "reception/schedule_appointment.html", {
        "patients": patients,
        "doctors": doctors,
        "departments": departments,
    })


def reception_register_patient(request):
    if request.method == "POST":
        # Convert is_insured string to boolean
        data = request.POST.copy()
        data['is_insured'] = data.get('is_insured', 'false').lower() == 'true'
        
        # If not insured, clear insurance fields
        if not data['is_insured']:
            data['insurer'] = ''
            data['insurer_other'] = ''
            data['membership_number'] = ''
            data['insurance_coverage_pct'] = 0
        else:
            # Set insurance coverage percentage if provided
            if data.get('insurance_coverage_pct'):
                data['insurance_coverage_pct'] = int(data['insurance_coverage_pct'])
            else:
                data['insurance_coverage_pct'] = 0
        
        form = PatientForm(data)
        
        if form.is_valid():
            patient = form.save()
            return redirect("reception_patient_list")
    else:
        form = PatientForm()

    # Get insurance coverage percentages from 0 to 100 in increments of 5
    insurance_percentages = [(i, f"{i}%") for i in range(0, 101, 5)]

    return render(request, "reception/register_patient.html", {
        "form": form,
        "insurance_percentages": insurance_percentages,
    })


def reception_patient_list(request):
    patients = Patient.objects.all().order_by('-created_at')
    return render(request, "reception/patient_list.html", {"patients": patients})


def reception_appointments_today(request):
    """Display today's queue - patients who have checked in"""
    today = timezone.now().date()
    
    # Get waiting queue entries for today
    today_queue = WaitingQueueEntry.objects.filter(
        checked_in_at__date=today
    ).select_related('visit__patient', 'visit__doctor__user').order_by('position', 'checked_in_at')
    
    # Also get appointments for reference
    appointments = Appointment.objects.filter(
        scheduled_at__date=today
    ).select_related('patient', 'doctor__user', 'department').order_by('scheduled_at')

    return render(request, "reception/today_appointments.html", {
        "today_queue": today_queue,
        "appointments": appointments
    })


from django.shortcuts import render
from clinic.models import Patient

def reception_patients(request):
    query = request.GET.get("q", "")

    if query:
        patients = Patient.objects.filter(
            first_name__icontains=query
        ) | Patient.objects.filter(
            last_name__icontains=query
        ) | Patient.objects.filter(
            phone__icontains=query
        ) | Patient.objects.filter(
            national_id__icontains=query
        )
    else:
        patients = Patient.objects.all().order_by("-created_at")

    return render(request, "reception/patient_list.html", {
        "patients": patients,
        "query": query,
    })

from django.utils import timezone
from clinic.models import Appointment

def today_appointments(request):
    """Display today's queue - patients who have checked in"""
    today = timezone.now().date()
    
    # Get waiting queue entries for today
    today_queue = WaitingQueueEntry.objects.filter(
        checked_in_at__date=today
    ).select_related('visit__patient', 'visit__doctor__user').order_by('position', 'checked_in_at')
    
    # Also get appointments for reference
    appointments = Appointment.objects.filter(
        scheduled_at__date=today
    ).select_related('patient', 'doctor__user', 'department').order_by('scheduled_at')

    return render(request, "reception/today_appointments.html", {
        "today_queue": today_queue,
        "appointments": appointments
    })

from django.shortcuts import redirect, get_object_or_404
from clinic.models import Appointment, Visit, WaitingQueueEntry

def reception_check_in(request, appointment_id):
    appt = get_object_or_404(Appointment, id=appointment_id)

    # create visit
    visit = Visit.objects.create(
        patient=appt.patient,
        department=appt.department,
        doctor=appt.doctor,
        status="open"
    )

    # add to waiting queue
    next_position = WaitingQueueEntry.objects.count() + 1

    WaitingQueueEntry.objects.create(
        visit=visit,
        position=next_position,
        receptionist=request.user.clinicuser,
        status="waiting"
    )

    # Update appointment status:
    appt.status = "checked_in"
    appt.save()

    return redirect("reception_today_appointments")


def patient_detail(request, patient_id):
    """View patient full information (accessible from reception and doctor areas)"""
    from django.shortcuts import get_object_or_404
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Get patient's appointments
    appointments = Appointment.objects.filter(patient=patient).order_by('-scheduled_at')
    
    # Get patient's visits
    visits = patient.visit_set.all().order_by('-created_at')
    
    context = {
        'patient': patient,
        'appointments': appointments,
        'visits': visits,
    }
    
    return render(request, 'reception/patient_detail.html', context)


def send_patient_to_doctor(request, patient_id):
    """Quick send to doctor - creates a same-day appointment"""
    from django.shortcuts import get_object_or_404
    from django.http import JsonResponse
    from datetime import datetime, timedelta
    
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Get default doctor (or first available doctor)
    doctor = ClinicUser.objects.filter(role='doctor').first()
    if not doctor:
        return JsonResponse({'success': False, 'message': 'No doctors available'}, status=400)
    
    # Create appointment for same day, 30 minutes from now
    now = timezone.now()
    scheduled_at = now + timedelta(minutes=30)
    
    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        department=doctor.department,
        scheduled_at=scheduled_at,
        notes='Quick referral from reception',
        scheduled_by=request.user.clinicuser if request.user.is_authenticated and hasattr(request.user, 'clinicuser') else None,
    )
    
    # Optionally auto check-in and create visit
    try:
        # Create visit immediately
        from clinic.models import Visit, WaitingQueueEntry
        visit = Visit.objects.create(
            patient=patient,
            doctor=doctor,
            status='open'
        )
        
        # Add to waiting queue
        next_position = WaitingQueueEntry.objects.count() + 1
        WaitingQueueEntry.objects.create(
            visit=visit,
            position=next_position,
            status='waiting'
        )
        
        # Update appointment status
        appointment.status = 'checked_in'
        appointment.save()
        
        message = f'Patient {patient.first_name} {patient.last_name} sent to doctor {doctor.user.first_name} and added to waiting queue'
    except Exception as e:
        message = f'Appointment created but error adding to waiting queue: {str(e)}'
    
    return JsonResponse({'success': True, 'message': message, 'appointment_id': appointment.id})


def edit_appointment(request, appointment_id):
    """Edit an existing appointment"""
    from django.shortcuts import get_object_or_404
    from django.contrib import messages
    from datetime import datetime
    
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            scheduled_date = request.POST.get('scheduled_date')
            scheduled_time = request.POST.get('scheduled_time')
            department_id = request.POST.get('department')
            doctor_id = request.POST.get('doctor')
            notes = request.POST.get('notes', '')
            status = request.POST.get('status', 'scheduled')
            
            # Update appointment with timezone-aware datetime
            scheduled_dt = datetime.strptime(f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M")
            appointment.scheduled_at = timezone.make_aware(scheduled_dt)
            appointment.notes = notes
            appointment.status = status
            
            if department_id:
                appointment.department = Department.objects.get(id=department_id)
            
            if doctor_id:
                appointment.doctor = ClinicUser.objects.get(id=doctor_id)
            
            appointment.save()
            
            messages.success(request, f'Appointment updated successfully for {appointment.patient.first_name} {appointment.patient.last_name}')
            return redirect('reception_appointments')
            
        except Exception as e:
            messages.error(request, f'Error updating appointment: {str(e)}')
    
    # Get data for form
    departments = Department.objects.all()
    doctors = ClinicUser.objects.filter(role='doctor').select_related('department', 'user')
    
    context = {
        'appointment': appointment,
        'departments': departments,
        'doctors': doctors,
    }
    
    return render(request, 'reception/edit_appointment.html', context)


def cancel_appointment(request, appointment_id):
    """Cancel an appointment"""
    from django.shortcuts import get_object_or_404
    from django.contrib import messages
    from django.http import JsonResponse
    
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'message': f'Appointment cancelled for {appointment.patient.first_name} {appointment.patient.last_name}'
            })
        
        messages.success(request, f'Appointment cancelled for {appointment.patient.first_name} {appointment.patient.last_name}')
        return redirect('reception_appointments')
    
    return redirect('reception_appointments')


def patient_profile(request, patient_id):
    """View detailed patient profile with visit history"""
    from django.shortcuts import get_object_or_404
    
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Get patient's visits with related data
    visits = patient.visit_set.all().select_related('doctor', 'department').order_by('-created_at')[:20]
    
    # Get patient's appointments
    appointments = Appointment.objects.filter(patient=patient).select_related('doctor', 'department').order_by('-scheduled_at')[:10]
    
    context = {
        'patient': patient,
        'visits': visits,
        'appointments': appointments,
    }
    
    return render(request, 'reception/patient_profile.html', context)


def reception_profile(request):
    """View and edit reception staff profile"""
    from django.contrib.auth.models import User
    
    # Get or create clinic user
    try:
        clinic_user = request.user.clinicuser
    except:
        # If no clinic user exists, create a basic one
        clinic_user = ClinicUser.objects.create(
            user=request.user,
            role='reception'
        )
    
    # Get activity statistics
    from clinic.models import Visit, Appointment
    patients_registered = Patient.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30)).count()
    appointments_scheduled = Appointment.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30)).count()
    visits_created = Visit.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30)).count()
    
    context = {
        'patients_registered': patients_registered,
        'appointments_scheduled': appointments_scheduled,
        'visits_created': visits_created,
    }
    
    return render(request, 'reception/profile.html', context)


def reception_update_profile(request):
    """Update reception staff profile information"""
    if request.method == 'POST':
        from django.contrib import messages
        
        try:
            user = request.user
            
            # Update user information
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            
            # Update or create clinic user
            clinic_user, created = ClinicUser.objects.get_or_create(user=user)
            clinic_user.phone = request.POST.get('phone', '')
            if not clinic_user.role:
                clinic_user.role = 'reception'
            clinic_user.save()
            
            # Handle password change
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            if new_password:
                if current_password and user.check_password(current_password):
                    if new_password == confirm_password:
                        if len(new_password) >= 8:
                            user.set_password(new_password)
                            messages.success(request, 'Password changed successfully! Please login again.')
                        else:
                            messages.error(request, 'Password must be at least 8 characters long.')
                            return redirect('reception_profile')
                    else:
                        messages.error(request, 'New passwords do not match.')
                        return redirect('reception_profile')
                else:
                    messages.error(request, 'Current password is incorrect.')
                    return redirect('reception_profile')
            
            user.save()
            messages.success(request, 'Profile updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    return redirect('reception_profile')


def reception_update_profile_picture(request):
    """Update profile picture"""
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        from django.contrib import messages
        
        try:
            clinic_user, created = ClinicUser.objects.get_or_create(user=request.user)
            if not clinic_user.role:
                clinic_user.role = 'reception'
            
            # Delete old profile picture if exists
            if clinic_user.profile_picture:
                clinic_user.profile_picture.delete()
            
            # Save new profile picture
            clinic_user.profile_picture = request.FILES['profile_picture']
            clinic_user.save()
            
            messages.success(request, 'Profile picture updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating profile picture: {str(e)}')
    
    return redirect('reception_profile')


def queue_call_patient(request, queue_id):
    """Call a patient from the waiting queue (change status to in_consultation)"""
    from django.http import JsonResponse
    
    if request.method == 'POST':
        try:
            queue_entry = WaitingQueueEntry.objects.get(id=queue_id)
            queue_entry.status = 'in_consultation'
            queue_entry.save()
            
            # Update visit status
            queue_entry.visit.status = 'in_consultation'
            queue_entry.visit.save()
            
            patient_name = f"{queue_entry.visit.patient.first_name} {queue_entry.visit.patient.last_name}"
            return JsonResponse({
                'success': True,
                'message': f'Patient {patient_name} called to consultation'
            })
        except WaitingQueueEntry.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Queue entry not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)


def queue_update_status(request, queue_id):
    """Update the status of a queue entry"""
    from django.http import JsonResponse
    import json
    
    if request.method == 'POST':
        try:
            queue_entry = WaitingQueueEntry.objects.get(id=queue_id)
            data = json.loads(request.body)
            new_status = data.get('status')
            
            if new_status in ['waiting', 'in_consultation', 'finished']:
                queue_entry.status = new_status
                queue_entry.save()
                
                # Update visit status accordingly
                if new_status == 'finished':
                    queue_entry.visit.status = 'completed'
                elif new_status == 'in_consultation':
                    queue_entry.visit.status = 'in_consultation'
                else:
                    queue_entry.visit.status = 'open'
                queue_entry.visit.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Status updated to {new_status}'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid status'
                }, status=400)
        except WaitingQueueEntry.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Queue entry not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

