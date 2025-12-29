"""
Middleware to bypass authentication for development/testing.
This allows all views to be accessed without login.
"""
from django.contrib.auth.models import User
from clinic.models import ClinicUser, Department


class BypassAuthenticationMiddleware:
    """
    Middleware that bypasses authentication checks.
    Creates a default test user if none exists and assigns it to the request.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._ensure_test_user()
    
    def _ensure_test_user(self):
        """Ensure a test user exists in the database."""
        try:
            User.objects.get(username='test_admin')
        except User.DoesNotExist:
            # Create test_admin user
            user = User.objects.create_user(
                username='test_admin',
                email='admin@clinic.com',
                password='admin123'
            )
            user.is_staff = True
            user.is_superuser = True
            user.save()
            
            # Create ClinicUser
            dept, _ = Department.objects.get_or_create(name="General")
            ClinicUser.objects.create(
                user=user,
                role='admin',
                department=dept
            )
    
    def __call__(self, request):
        # Only bypass authentication for admin URLs
        if request.path.startswith('/admin/'):
            # Attach test_admin user to admin requests
            try:
                request.user = User.objects.get(username='test_admin')
            except User.DoesNotExist:
                self._ensure_test_user()
                request.user = User.objects.get(username='test_admin')
        
        response = self.get_response(request)
        return response
