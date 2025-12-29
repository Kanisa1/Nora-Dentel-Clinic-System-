from django.utils import timezone

def admin_stats(request):
    """Add statistics to admin context"""
    if request.path.startswith('/admin/'):
        try:
            from clinic.models import Patient, ClinicUser, Appointment, Visit
            today = timezone.now().date()
            
            return {
                'total_patients': Patient.objects.count(),
                'total_doctors': ClinicUser.objects.filter(role='doctor').count(),
                'today_appointments': Appointment.objects.filter(scheduled_at__date=today).count(),
                'total_staff': ClinicUser.objects.count(),
                'today_visits': Visit.objects.filter(created_at__date=today).count(),
            }
        except:
            pass
    return {}
