
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView
from config.views import RoleBasedRedirectView, custom_logout_view

class HomeTemplateView(TemplateView):
    template_name = 'home.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['home_page'] = True
        return context

urlpatterns = [
    # Authentication
    path('auth/', include('django.contrib.auth.urls')),
    # Custom logout
    path('logout/', custom_logout_view, name='logout'),
    # Profile redirect (from login page) - redirect based on role
    path('accounts/profile/', RoleBasedRedirectView.as_view(), name='profile_redirect'),
    # Home
    path('', HomeTemplateView.as_view(), name='home'),
    # Admin
    path('admin/', admin.site.urls),
    # Dashboard Shortcuts
    path('cashier/login/', RedirectView.as_view(url='/dashboard/cashier/login/', permanent=False)),
    path('cashier/', RedirectView.as_view(url='/dashboard/cashier/dashboard/', permanent=False)),
    path('pharmacy/', RedirectView.as_view(url='/dashboard/pharmacy/dashboard/', permanent=False)),
    path('inventory/', RedirectView.as_view(url='/dashboard/inventory/dashboard/', permanent=False)),
    path('financial/', RedirectView.as_view(url='/dashboard/financial/dashboard/', permanent=False)),
    path('reports/', RedirectView.as_view(url='/dashboard/reports/dashboard/', permanent=False)),
    path('admin-dashboard/', RedirectView.as_view(url='/dashboard/admin/dashboard/', permanent=False)),
    # Doctor Dashboard (main doctor interface)
    path('doctor/', include('clinic.urls_doctor')),
    # Financial Officer
    path('', include('clinic.urls_finance')),
    # Other Dashboards
    path('dashboard/', include('clinic.urls')),
    path('api/', include('clinic.urls')),  # Also include under /api/ for compatibility
    path('reception/', include('clinic.urls_reception')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
