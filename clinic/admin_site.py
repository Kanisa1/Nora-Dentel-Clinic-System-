from django.contrib import admin
from django.utils import timezone
from clinic.models import Patient, ClinicUser, Appointment

class CustomAdminSite(admin.AdminSite):
    site_title = "Nora Dental Clinic"
    site_header = "Nora Dental Clinic Administration"
    index_title = "Dashboard"

    def each_context(self, request):
        """Add custom context to all admin pages"""
        context = super().each_context(request)
        
        # Add statistics for dashboard
        try:
            from clinic.models import Patient, ClinicUser, Appointment
            today = timezone.now().date()
            
            context.update({
                'total_patients': Patient.objects.count(),
                'total_doctors': ClinicUser.objects.filter(role='doctor').count(),
                'today_appointments': Appointment.objects.filter(scheduled_at__date=today).count(),
                'total_staff': ClinicUser.objects.count(),
            })
        except:
            pass
        
        return context

# Create custom admin site instance
admin_site = CustomAdminSite(name='noraadmin')
