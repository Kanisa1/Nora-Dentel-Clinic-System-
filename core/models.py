from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class User(AbstractUser):
    """Custom user model with role-based access control."""
    
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        RECEPTIONIST = 'receptionist', 'Receptionist'
        DOCTOR = 'doctor', 'Doctor'
        CASHIER = 'cashier', 'Cashier'
        FINANCE = 'finance', 'Finance'
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.RECEPTIONIST
    )
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class InsuranceCompany(models.Model):
    """Insurance company model."""
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    contact_person = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Insurance Companies"
        ordering = ['name']

    def __str__(self):
        return self.name


class Patient(models.Model):
    """Patient model with insurance percentage."""
    
    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=Gender.choices)
    national_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    
    # Insurance information
    insurance_company = models.ForeignKey(
        InsuranceCompany,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patients'
    )
    insurance_number = models.CharField(max_length=100, blank=True)
    insurance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )
    
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def patient_pays_percentage(self):
        """Percentage patient needs to pay (100 - insurance_percentage)."""
        return Decimal('100') - self.insurance_percentage


class TariffCategory(models.Model):
    """Category for grouping tariffs."""
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Tariff Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Tariff(models.Model):
    """Tariff model - defines acts/procedures that doctors can select."""
    
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        TariffCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tariffs'
    )
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class MedicalRecord(models.Model):
    """Medical records for patients."""
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='medical_records'
    )
    doctor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='medical_records',
        limit_choices_to={'role': User.Role.DOCTOR}
    )
    visit_date = models.DateTimeField(auto_now_add=True)
    chief_complaint = models.TextField()
    history_of_present_illness = models.TextField(blank=True)
    past_medical_history = models.TextField(blank=True)
    physical_examination = models.TextField(blank=True)
    diagnosis = models.TextField()
    treatment_plan = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-visit_date']

    def __str__(self):
        return f"Record for {self.patient} on {self.visit_date.strftime('%Y-%m-%d')}"


class Invoice(models.Model):
    """Invoice model - auto-generated for cashier."""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PARTIAL = 'partial', 'Partially Paid'
        PAID = 'paid', 'Paid'
        CANCELLED = 'cancelled', 'Cancelled'
    
    invoice_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invoices'
    )
    
    # Financial breakdown
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    insurance_coverage = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    patient_responsibility = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    notes = models.TextField(blank=True)
    invoice_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.patient}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Auto-generate invoice number
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            last_invoice = Invoice.objects.filter(
                invoice_number__startswith=f'INV-{date_str}'
            ).order_by('-invoice_number').first()
            if last_invoice:
                last_num = int(last_invoice.invoice_number.split('-')[-1])
                self.invoice_number = f'INV-{date_str}-{last_num + 1:04d}'
            else:
                self.invoice_number = f'INV-{date_str}-0001'
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Calculate invoice totals based on items."""
        self.subtotal = sum(item.total_price for item in self.items.all())
        self.insurance_coverage = self.subtotal * (self.patient.insurance_percentage / 100)
        self.patient_responsibility = self.subtotal - self.insurance_coverage
        self.save()

    @property
    def balance_due(self):
        return self.patient_responsibility - self.amount_paid


class InvoiceItem(models.Model):
    """Individual items on an invoice."""
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    tariff = models.ForeignKey(
        Tariff,
        on_delete=models.SET_NULL,
        null=True,
        related_name='invoice_items'
    )
    description = models.CharField(max_length=500)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.description} x {self.quantity}"

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Payment records for invoices."""
    
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Cash'
        CARD = 'card', 'Card'
        INSURANCE = 'insurance', 'Insurance'
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        MOBILE_MONEY = 'mobile_money', 'Mobile Money'
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )
    reference_number = models.CharField(max_length=100, blank=True)
    received_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_payments'
    )
    payment_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment of {self.amount} for {self.invoice}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update invoice status
        invoice = self.invoice
        invoice.amount_paid = sum(p.amount for p in invoice.payments.all())
        if invoice.amount_paid >= invoice.patient_responsibility:
            invoice.status = Invoice.Status.PAID
        elif invoice.amount_paid > 0:
            invoice.status = Invoice.Status.PARTIAL
        invoice.save()


# Pharmacy Models
class DrugCategory(models.Model):
    """Category for drugs."""
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Drug Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Drug(models.Model):
    """Drug/medication model for pharmacy."""
    
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(
        DrugCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drugs'
    )
    dosage_form = models.CharField(max_length=100, blank=True)  # tablet, syrup, injection, etc.
    strength = models.CharField(max_length=100, blank=True)
    unit_of_measure = models.CharField(max_length=50, blank=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.strength})"

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.reorder_level


class Prescription(models.Model):
    """Prescription model linking medical records to drugs."""
    
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    drug = models.ForeignKey(
        Drug,
        on_delete=models.SET_NULL,
        null=True,
        related_name='prescriptions'
    )
    dosage = models.CharField(max_length=200)
    frequency = models.CharField(max_length=200)  # e.g., "3 times daily"
    duration = models.CharField(max_length=200)  # e.g., "7 days"
    quantity = models.PositiveIntegerField(default=1)
    instructions = models.TextField(blank=True)
    is_dispensed = models.BooleanField(default=False)
    dispensed_at = models.DateTimeField(null=True, blank=True)
    dispensed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispensed_prescriptions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.drug} for {self.medical_record.patient}"


# Store/Inventory Models
class StoreCategory(models.Model):
    """Category for store items."""
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Store Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class StoreItem(models.Model):
    """Store/inventory item model."""
    
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        StoreCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items'
    )
    description = models.TextField(blank=True)
    unit_of_measure = models.CharField(max_length=50)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.reorder_level


class StoreTransaction(models.Model):
    """Store transaction for tracking inventory movements."""
    
    class TransactionType(models.TextChoices):
        IN = 'in', 'Stock In'
        OUT = 'out', 'Stock Out'
        ADJUSTMENT = 'adjustment', 'Adjustment'
    
    item = models.ForeignKey(
        StoreItem,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices
    )
    quantity = models.IntegerField()
    reference = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='store_transactions'
    )
    transaction_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-transaction_date']

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.item} x {self.quantity}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update stock quantity
        item = self.item
        if self.transaction_type == self.TransactionType.IN:
            item.stock_quantity += self.quantity
        elif self.transaction_type == self.TransactionType.OUT:
            item.stock_quantity = max(0, item.stock_quantity - self.quantity)
        else:  # Adjustment
            item.stock_quantity = max(0, item.stock_quantity + self.quantity)
        item.save()
