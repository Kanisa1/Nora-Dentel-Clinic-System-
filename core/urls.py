from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import reports

router = DefaultRouter()

# Core viewsets
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'patients', views.PatientViewSet, basename='patient')
router.register(r'insurance-companies', views.InsuranceCompanyViewSet, basename='insurance-company')

# Tariffs
router.register(r'tariff-categories', views.TariffCategoryViewSet, basename='tariff-category')
router.register(r'tariffs', views.TariffViewSet, basename='tariff')

# Medical records
router.register(r'medical-records', views.MedicalRecordViewSet, basename='medical-record')

# Invoices and payments
router.register(r'invoices', views.InvoiceViewSet, basename='invoice')
router.register(r'invoice-items', views.InvoiceItemViewSet, basename='invoice-item')
router.register(r'payments', views.PaymentViewSet, basename='payment')

# Pharmacy
router.register(r'drug-categories', views.DrugCategoryViewSet, basename='drug-category')
router.register(r'drugs', views.DrugViewSet, basename='drug')
router.register(r'prescriptions', views.PrescriptionViewSet, basename='prescription')

# Store
router.register(r'store-categories', views.StoreCategoryViewSet, basename='store-category')
router.register(r'store-items', views.StoreItemViewSet, basename='store-item')
router.register(r'store-transactions', views.StoreTransactionViewSet, basename='store-transaction')

urlpatterns = [
    path('', include(router.urls)),
    
    # Reports
    path('reports/daily/', reports.DailyReportView.as_view(), name='daily-report'),
    path('reports/monthly/', reports.MonthlyReportView.as_view(), name='monthly-report'),
    path('reports/doctor-income/', reports.DoctorIncomeReportView.as_view(), name='doctor-income-report'),
    path('reports/insurance/', reports.InsuranceReportView.as_view(), name='insurance-report'),
    path('reports/hmis/', reports.HMISReportView.as_view(), name='hmis-report'),
    path('reports/idsr/', reports.IDSRReportView.as_view(), name='idsr-report'),
    path('dashboard/', reports.DashboardView.as_view(), name='dashboard'),
]
