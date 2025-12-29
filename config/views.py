from django.shortcuts import redirect, render
from django.views import View
from django.contrib.auth import logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

class RoleBasedRedirectView(View):
    """Redirect users to their appropriate dashboard based on role"""
    
    def get(self, request):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Check if user has clinicuser
        if hasattr(request.user, 'clinicuser'):
            role = request.user.clinicuser.role
            
            # Redirect based on role
            if role == 'doctor':
                return redirect('doctor_dashboard')
            elif role == 'reception':
                return redirect('reception_dashboard')
            elif role == 'cashier':
                return redirect('/cashier/')
            elif role == 'pharmacy':
                return redirect('/pharmacy/')
            elif role == 'inventory':
                return redirect('/inventory/')
            elif role == 'finance':
                return redirect('/financial/')
            elif role == 'admin':
                return redirect('/admin/')
        
        # Check if superuser
        if request.user.is_superuser or request.user.is_staff:
            return redirect('/admin/')
        
        # Default redirect to home
        return redirect('home')


@login_required
@require_http_methods(["POST"])
def custom_logout_view(request):
    """Custom logout view that logs out and redirects to home"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')
