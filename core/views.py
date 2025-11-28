from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import (
    User, InsuranceCompany, Patient, TariffCategory, Tariff,
    MedicalRecord, Invoice, InvoiceItem, Payment,
    DrugCategory, Drug, Prescription,
    StoreCategory, StoreItem, StoreTransaction
)
from .serializers import (
    UserSerializer, UserCreateSerializer, InsuranceCompanySerializer,
    PatientSerializer, TariffCategorySerializer, TariffSerializer,
    MedicalRecordSerializer, InvoiceSerializer, InvoiceCreateSerializer,
    InvoiceItemSerializer, PaymentSerializer,
    DrugCategorySerializer, DrugSerializer, PrescriptionSerializer,
    StoreCategorySerializer, StoreItemSerializer, StoreTransactionSerializer
)


class IsAdminOrReadOnly(permissions.BasePermission):
    """Custom permission for admin users to modify, others to read."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == User.Role.ADMIN


class RoleBasedPermission(permissions.BasePermission):
    """Permission class for role-based access."""
    
    role_permissions = {
        'admin': ['admin'],
        'receptionist': ['admin', 'receptionist'],
        'doctor': ['admin', 'doctor'],
        'cashier': ['admin', 'cashier'],
        'finance': ['admin', 'finance'],
    }
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return True


class InvoicePermission(permissions.BasePermission):
    """Permission class for invoice access - admin, doctor, and cashier roles."""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # Read access for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write access only for admin, doctor, and cashier
        allowed_roles = [User.Role.ADMIN, User.Role.DOCTOR, User.Role.CASHIER]
        return request.user.role in allowed_roles


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model."""
    
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def get_queryset(self):
        queryset = User.objects.all()
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        return queryset
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user info."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def doctors(self, request):
        """Get all doctors."""
        doctors = User.objects.filter(role=User.Role.DOCTOR, is_active=True)
        serializer = UserSerializer(doctors, many=True)
        return Response(serializer.data)


class InsuranceCompanyViewSet(viewsets.ModelViewSet):
    """ViewSet for InsuranceCompany model."""
    
    queryset = InsuranceCompany.objects.all()
    serializer_class = InsuranceCompanySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = InsuranceCompany.objects.all()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class PatientViewSet(viewsets.ModelViewSet):
    """ViewSet for Patient model."""
    
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Patient.objects.select_related('insurance_company').all()
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(national_id__icontains=search)
            )
        insurance = self.request.query_params.get('insurance_company')
        if insurance:
            queryset = queryset.filter(insurance_company_id=insurance)
        return queryset


class TariffCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for TariffCategory model."""
    
    queryset = TariffCategory.objects.all()
    serializer_class = TariffCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class TariffViewSet(viewsets.ModelViewSet):
    """ViewSet for Tariff model."""
    
    queryset = Tariff.objects.select_related('category').all()
    serializer_class = TariffSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Tariff.objects.select_related('category').all()
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search)
            )
        return queryset


class MedicalRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for MedicalRecord model."""
    
    queryset = MedicalRecord.objects.select_related('patient', 'doctor').all()
    serializer_class = MedicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = MedicalRecord.objects.select_related('patient', 'doctor').all()
        patient = self.request.query_params.get('patient')
        if patient:
            queryset = queryset.filter(patient_id=patient)
        doctor = self.request.query_params.get('doctor')
        if doctor:
            queryset = queryset.filter(doctor_id=doctor)
        return queryset
    
    def perform_create(self, serializer):
        # Auto-assign current user as doctor if they are a doctor
        if self.request.user.role == User.Role.DOCTOR:
            serializer.save(doctor=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def create_invoice(self, request, pk=None):
        """Auto-generate invoice from medical record with selected tariffs."""
        medical_record = self.get_object()
        tariff_ids = request.data.get('tariffs', [])
        
        if not tariff_ids:
            return Response(
                {'error': 'No tariffs selected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create invoice
        invoice = Invoice.objects.create(
            patient=medical_record.patient,
            medical_record=medical_record,
            created_by=request.user
        )
        
        # Add invoice items from selected tariffs
        tariffs = Tariff.objects.filter(id__in=tariff_ids, is_active=True)
        for tariff in tariffs:
            InvoiceItem.objects.create(
                invoice=invoice,
                tariff=tariff,
                description=tariff.name,
                quantity=1,
                unit_price=tariff.unit_price
            )
        
        # Calculate totals
        invoice.calculate_totals()
        
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InvoiceViewSet(viewsets.ModelViewSet):
    """ViewSet for Invoice model."""
    
    queryset = Invoice.objects.select_related('patient', 'medical_record', 'created_by').all()
    permission_classes = [InvoicePermission]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InvoiceCreateSerializer
        return InvoiceSerializer
    
    def get_queryset(self):
        queryset = Invoice.objects.select_related(
            'patient', 'medical_record', 'created_by'
        ).prefetch_related('items', 'payments').all()
        
        patient = self.request.query_params.get('patient')
        if patient:
            queryset = queryset.filter(patient_id=patient)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_payment(self, request, pk=None):
        """Add payment to invoice."""
        invoice = self.get_object()
        
        amount = Decimal(str(request.data.get('amount', 0)))
        if amount <= 0:
            return Response(
                {'error': 'Invalid payment amount'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            payment_method=request.data.get('payment_method', 'cash'),
            reference_number=request.data.get('reference_number', ''),
            received_by=request.user,
            notes=request.data.get('notes', '')
        )
        
        serializer = PaymentSerializer(payment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel invoice."""
        invoice = self.get_object()
        if invoice.status == Invoice.Status.PAID:
            return Response(
                {'error': 'Cannot cancel a paid invoice'},
                status=status.HTTP_400_BAD_REQUEST
            )
        invoice.status = Invoice.Status.CANCELLED
        invoice.save()
        serializer = self.get_serializer(invoice)
        return Response(serializer.data)


class InvoiceItemViewSet(viewsets.ModelViewSet):
    """ViewSet for InvoiceItem model."""
    
    queryset = InvoiceItem.objects.select_related('invoice', 'tariff').all()
    serializer_class = InvoiceItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = InvoiceItem.objects.select_related('invoice', 'tariff').all()
        invoice = self.request.query_params.get('invoice')
        if invoice:
            queryset = queryset.filter(invoice_id=invoice)
        return queryset


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for Payment model."""
    
    queryset = Payment.objects.select_related('invoice', 'received_by').all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Payment.objects.select_related('invoice', 'received_by').all()
        invoice = self.request.query_params.get('invoice')
        if invoice:
            queryset = queryset.filter(invoice_id=invoice)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(received_by=self.request.user)


# Pharmacy ViewSets
class DrugCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for DrugCategory model."""
    
    queryset = DrugCategory.objects.all()
    serializer_class = DrugCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class DrugViewSet(viewsets.ModelViewSet):
    """ViewSet for Drug model."""
    
    queryset = Drug.objects.select_related('category').all()
    serializer_class = DrugSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Drug.objects.select_related('category').all()
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        low_stock = self.request.query_params.get('low_stock')
        if low_stock and low_stock.lower() == 'true':
            queryset = queryset.filter(stock_quantity__lte=F('reorder_level'))
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(generic_name__icontains=search)
            )
        return queryset
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get drugs with low stock."""
        drugs = Drug.objects.filter(stock_quantity__lte=F('reorder_level'))
        serializer = self.get_serializer(drugs, many=True)
        return Response(serializer.data)


class PrescriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for Prescription model."""
    
    queryset = Prescription.objects.select_related('medical_record', 'drug').all()
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Prescription.objects.select_related(
            'medical_record', 'drug', 'medical_record__patient'
        ).all()
        medical_record = self.request.query_params.get('medical_record')
        if medical_record:
            queryset = queryset.filter(medical_record_id=medical_record)
        is_dispensed = self.request.query_params.get('is_dispensed')
        if is_dispensed is not None:
            queryset = queryset.filter(is_dispensed=is_dispensed.lower() == 'true')
        return queryset
    
    @action(detail=True, methods=['post'])
    def dispense(self, request, pk=None):
        """Mark prescription as dispensed."""
        prescription = self.get_object()
        if prescription.is_dispensed:
            return Response(
                {'error': 'Prescription already dispensed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update drug stock
        if prescription.drug and prescription.drug.stock_quantity >= prescription.quantity:
            prescription.drug.stock_quantity -= prescription.quantity
            prescription.drug.save()
        
        prescription.is_dispensed = True
        prescription.dispensed_at = timezone.now()
        prescription.dispensed_by = request.user
        prescription.save()
        
        serializer = self.get_serializer(prescription)
        return Response(serializer.data)


# Store ViewSets
class StoreCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for StoreCategory model."""
    
    queryset = StoreCategory.objects.all()
    serializer_class = StoreCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class StoreItemViewSet(viewsets.ModelViewSet):
    """ViewSet for StoreItem model."""
    
    queryset = StoreItem.objects.select_related('category').all()
    serializer_class = StoreItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = StoreItem.objects.select_related('category').all()
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        low_stock = self.request.query_params.get('low_stock')
        if low_stock and low_stock.lower() == 'true':
            queryset = queryset.filter(stock_quantity__lte=F('reorder_level'))
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search)
            )
        return queryset
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get items with low stock."""
        items = StoreItem.objects.filter(stock_quantity__lte=F('reorder_level'))
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)


class StoreTransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for StoreTransaction model."""
    
    queryset = StoreTransaction.objects.select_related('item', 'performed_by').all()
    serializer_class = StoreTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = StoreTransaction.objects.select_related('item', 'performed_by').all()
        item = self.request.query_params.get('item')
        if item:
            queryset = queryset.filter(item_id=item)
        transaction_type = self.request.query_params.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(performed_by=self.request.user)
