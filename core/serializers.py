from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import (
    User, InsuranceCompany, Patient, TariffCategory, Tariff,
    MedicalRecord, Invoice, InvoiceItem, Payment,
    DrugCategory, Drug, Prescription,
    StoreCategory, StoreItem, StoreTransaction
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone', 'address', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users with password."""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role', 'phone', 'address'
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords don't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class InsuranceCompanySerializer(serializers.ModelSerializer):
    """Serializer for InsuranceCompany model."""
    
    class Meta:
        model = InsuranceCompany
        fields = [
            'id', 'name', 'code', 'contact_person', 'phone',
            'email', 'address', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PatientSerializer(serializers.ModelSerializer):
    """Serializer for Patient model."""
    
    insurance_company_name = serializers.CharField(
        source='insurance_company.name', read_only=True
    )
    full_name = serializers.CharField(read_only=True)
    patient_pays_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )

    class Meta:
        model = Patient
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'date_of_birth',
            'gender', 'national_id', 'phone', 'email', 'address',
            'insurance_company', 'insurance_company_name', 'insurance_number',
            'insurance_percentage', 'patient_pays_percentage',
            'emergency_contact_name', 'emergency_contact_phone',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TariffCategorySerializer(serializers.ModelSerializer):
    """Serializer for TariffCategory model."""
    
    class Meta:
        model = TariffCategory
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TariffSerializer(serializers.ModelSerializer):
    """Serializer for Tariff model."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Tariff
        fields = [
            'id', 'code', 'name', 'description', 'category', 'category_name',
            'unit_price', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PrescriptionSerializer(serializers.ModelSerializer):
    """Serializer for Prescription model."""
    
    drug_name = serializers.CharField(source='drug.name', read_only=True)
    dispensed_by_name = serializers.CharField(
        source='dispensed_by.get_full_name', read_only=True
    )

    class Meta:
        model = Prescription
        fields = [
            'id', 'medical_record', 'drug', 'drug_name', 'dosage',
            'frequency', 'duration', 'quantity', 'instructions',
            'is_dispensed', 'dispensed_at', 'dispensed_by',
            'dispensed_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'dispensed_at']


class MedicalRecordSerializer(serializers.ModelSerializer):
    """Serializer for MedicalRecord model."""
    
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    prescriptions = PrescriptionSerializer(many=True, read_only=True)

    class Meta:
        model = MedicalRecord
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'visit_date', 'chief_complaint', 'history_of_present_illness',
            'past_medical_history', 'physical_examination', 'diagnosis',
            'treatment_plan', 'notes', 'prescriptions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'visit_date', 'created_at', 'updated_at']


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for InvoiceItem model."""
    
    tariff_code = serializers.CharField(source='tariff.code', read_only=True)
    tariff_name = serializers.CharField(source='tariff.name', read_only=True)

    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'invoice', 'tariff', 'tariff_code', 'tariff_name',
            'description', 'quantity', 'unit_price', 'total_price', 'created_at'
        ]
        read_only_fields = ['id', 'total_price', 'created_at']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    
    received_by_name = serializers.CharField(
        source='received_by.get_full_name', read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'amount', 'payment_method', 'reference_number',
            'received_by', 'received_by_name', 'payment_date', 'notes'
        ]
        read_only_fields = ['id', 'payment_date']


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model."""
    
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True
    )
    items = InvoiceItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    balance_due = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'patient', 'patient_name',
            'medical_record', 'created_by', 'created_by_name',
            'subtotal', 'insurance_coverage', 'patient_responsibility',
            'amount_paid', 'balance_due', 'status', 'notes',
            'invoice_date', 'due_date', 'items', 'payments',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'subtotal', 'insurance_coverage',
            'patient_responsibility', 'amount_paid', 'invoice_date',
            'created_at', 'updated_at'
        ]


class InvoiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating invoices with items."""
    
    items = InvoiceItemSerializer(many=True, write_only=True)

    class Meta:
        model = Invoice
        fields = ['patient', 'medical_record', 'notes', 'due_date', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        invoice = Invoice.objects.create(**validated_data)
        
        for item_data in items_data:
            item_data.pop('invoice', None)
            InvoiceItem.objects.create(invoice=invoice, **item_data)
        
        invoice.calculate_totals()
        return invoice


# Pharmacy Serializers
class DrugCategorySerializer(serializers.ModelSerializer):
    """Serializer for DrugCategory model."""
    
    class Meta:
        model = DrugCategory
        fields = ['id', 'name', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class DrugSerializer(serializers.ModelSerializer):
    """Serializer for Drug model."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Drug
        fields = [
            'id', 'code', 'name', 'generic_name', 'category', 'category_name',
            'dosage_form', 'strength', 'unit_of_measure', 'unit_price',
            'stock_quantity', 'reorder_level', 'is_low_stock', 'expiry_date',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Store Serializers
class StoreCategorySerializer(serializers.ModelSerializer):
    """Serializer for StoreCategory model."""
    
    class Meta:
        model = StoreCategory
        fields = ['id', 'name', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class StoreItemSerializer(serializers.ModelSerializer):
    """Serializer for StoreItem model."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = StoreItem
        fields = [
            'id', 'code', 'name', 'category', 'category_name', 'description',
            'unit_of_measure', 'unit_price', 'stock_quantity', 'reorder_level',
            'is_low_stock', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StoreTransactionSerializer(serializers.ModelSerializer):
    """Serializer for StoreTransaction model."""
    
    item_name = serializers.CharField(source='item.name', read_only=True)
    performed_by_name = serializers.CharField(
        source='performed_by.get_full_name', read_only=True
    )

    class Meta:
        model = StoreTransaction
        fields = [
            'id', 'item', 'item_name', 'transaction_type', 'quantity',
            'reference', 'notes', 'performed_by', 'performed_by_name',
            'transaction_date'
        ]
        read_only_fields = ['id', 'transaction_date']
