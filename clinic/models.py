# clinic/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.base import ContentFile
import datetime

# --- Departments / clinic users remain similar ---
class Department(models.Model):
    name = models.CharField(max_length=128)
    def __str__(self): return self.name

class ClinicUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ROLE_CHOICES = [
        ('admin','Admin'),
        ('doctor','Doctor'),
        ('cashier','Cashier'),
        ('reception','Reception'),
        ('pharmacy','Pharmacy'),
        ('inventory','Inventory'),
        ('finance','Finance'),
    ]
    role = models.CharField(max_length=32, choices=ROLE_CHOICES)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    def __str__(self): return f"{self.user.username} ({self.role})"

# --- Patient (extended demographics + insurance + membership number + age property) ---
INSURERS = [
    ('RSSB', 'RSSB'),
    ('RAMA', 'RAMA'),
    ('MMI', 'MMI'),
    ('SANLAM', 'SANLAM'),
    ('BRITAM', 'BRITAM'),
    ('OLDMUTUAL', 'OLDMUTUAL'),
    ('PRIME', 'PRIME'),
    ('RADIANT', 'RADIANT'),
    ('MISUR', 'MIS/UR'),
    ('EDENCARE', 'EDENCARE'),
    ('OTHER', 'Other'),
]

class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    national_id = models.CharField(max_length=64, blank=True, null=True)
    parent_name = models.CharField(max_length=256, blank=True, null=True)
    nationality = models.CharField(max_length=128, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    province = models.CharField(max_length=128, blank=True, null=True)
    district = models.CharField(max_length=128, blank=True, null=True)
    sector = models.CharField(max_length=128, blank=True, null=True)
    cell = models.CharField(max_length=128, blank=True, null=True)
    village = models.CharField(max_length=128, blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    occupation = models.CharField(max_length=128, blank=True, null=True)
    affiliation = models.CharField(max_length=128, blank=True, null=True)
    religion = models.CharField(max_length=128, blank=True, null=True)

    is_insured = models.BooleanField(default=False)
    insurer = models.CharField(max_length=32, choices=INSURERS, blank=True, null=True)
    insurer_other = models.CharField(max_length=128, blank=True, null=True)  # when OTHER chosen
    membership_number = models.CharField(max_length=128, blank=True, null=True)
    insurance_coverage_pct = models.IntegerField(default=0)  # selected by receptionist from allowed list

    dob = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        if not self.dob:
            return None
        today = datetime.date.today()
        age = today.year - self.dob.year
        if (today.month, today.day) < (self.dob.month, self.dob.day):
            age -= 1
        return age

class PatientCard(models.Model):
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='card')
    card_number = models.CharField(max_length=32, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

# --- Appointment & Visit ---
class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    scheduled_by = models.ForeignKey(ClinicUser, null=True, blank=True, on_delete=models.SET_NULL)
    scheduled_at = models.DateTimeField()
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    doctor = models.ForeignKey(ClinicUser, null=True, blank=True, related_name='appointments', on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=32, choices=[('scheduled','Scheduled'),('checked_in','Checked-in'),('completed','Completed'),('cancelled','Cancelled')], default='scheduled')
    notes = models.TextField(blank=True, null=True)
    def __str__(self): return f"Appointment {self.id} - {self.patient}"

class Visit(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True)
    doctor = models.ForeignKey(ClinicUser, limit_choices_to={'role':'doctor'}, null=True, blank=True, on_delete=models.SET_NULL)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)  # requested
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=32, default='open')  # open, billed, closed
    def __str__(self): return f"Visit {self.id} - {self.patient}"

# --- Triage & WaitingQueueEntry ---
class Triage(models.Model):
    visit = models.OneToOneField(Visit, on_delete=models.CASCADE, related_name='triage')
    temperature_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    pulse = models.PositiveIntegerField(null=True, blank=True)
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True)
    blood_pressure = models.CharField(max_length=32, blank=True, null=True)
    symptoms = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(ClinicUser, null=True, blank=True, on_delete=models.SET_NULL)

class WaitingQueueEntry(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    checked_in_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('waiting','Waiting'),('in_consultation','In Consultation'),('finished','Finished')], default='waiting')
    desk = models.CharField(max_length=64, blank=True, null=True)
    receptionist = models.ForeignKey(ClinicUser, null=True, blank=True, on_delete=models.SET_NULL)
    class Meta:
        ordering = ['position', 'checked_in_at']

# --- Tariff and Billing ---
class TariffAct(models.Model):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=256)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    price_private = models.DecimalField(max_digits=10, decimal_places=2)
    price_insurance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    active = models.BooleanField(default=True)
    def __str__(self): return f"{self.code} - {self.name}"

class BillingItem(models.Model):
    visit = models.ForeignKey(Visit, related_name='billing_items', on_delete=models.CASCADE)
    tariff = models.ForeignKey(TariffAct, on_delete=models.PROTECT)
    qty = models.PositiveIntegerField(default=1)
    price_private_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    price_insurance_snapshot = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, null=True, help_text="Details to appear on the invoice.")

# --- Invoice + Payment ---
class Invoice(models.Model):
    VISIT_STATUS_CHOICES = [
        ('outpatient', 'Outpatient'),
        ('inpatient', 'Inpatient'),
    ]
    visit = models.OneToOneField(Visit, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_private = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_insurance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(ClinicUser, null=True, blank=True, on_delete=models.SET_NULL)
    pdf_file = models.FileField(upload_to='invoices/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=VISIT_STATUS_CHOICES, default='outpatient')
    receipt_number = models.CharField(max_length=64, blank=True, null=True)  # for QR / barcode
    def __str__(self):
        return f"Invoice #{self.id} - Visit {self.visit_id}"

class Payment(models.Model):
    METHOD_CASH = 'cash'
    METHOD_MOMO = 'momo'
    METHOD_CARD = 'card'
    METHOD_INSURANCE = 'insurance'

    METHOD_CHOICES = [
        (METHOD_CASH, 'Cash'),
        (METHOD_MOMO, 'Mobile Money'),
        (METHOD_CARD, 'ATM Card'),
        (METHOD_INSURANCE, 'Insurance'),
    ]

    INSTANT_METHODS = {METHOD_CASH, METHOD_MOMO, METHOD_CARD}

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=32, choices=METHOD_CHOICES)
    reference = models.CharField(max_length=64, blank=True, null=True)
    paid_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def clears_invoice_immediately(cls, method: str) -> bool:
        return method in cls.INSTANT_METHODS

class Refund(models.Model):
    REFUND_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='pending')
    requested_by = models.ForeignKey(ClinicUser, on_delete=models.SET_NULL, null=True, related_name='refunds_requested')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(ClinicUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='refunds_processed')
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Refund #{self.id} - Invoice {self.invoice_id} - {self.amount} RWF"

# --- Prescription / Pharmacy / Inventory ---
class Prescription(models.Model):
    PRESCRIPTION_TYPES = [
        ('written', 'Written Prescription'),
        ('clinic', 'Clinic Store Dispense'),
    ]

    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='prescriptions')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(
        ClinicUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'doctor'},
        related_name='issued_prescriptions'
    )
    prescription_type = models.CharField(max_length=20, choices=PRESCRIPTION_TYPES)
    instructions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_prescription_type_display()} - Visit {self.visit_id}"


class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, related_name='items', on_delete=models.CASCADE)
    inventory_item = models.ForeignKey('InventoryItem', null=True, blank=True, on_delete=models.SET_NULL)
    custom_name = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    dosage = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 250mg, 1 tablet")
    frequency = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 3 times daily")
    duration = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 7 days")
    instructions = models.TextField(blank=True, null=True, help_text="Additional instructions")
    dosage_instructions = models.TextField(blank=True, null=True)  # Keep for backward compatibility
    created_at = models.DateTimeField(auto_now_add=True)

    def display_name(self):
        if self.inventory_item:
            return self.inventory_item.name
        return self.custom_name or "Medicine"

    def __str__(self):
        return f"{self.display_name()} x {self.quantity}"

class InventoryItem(models.Model):
    CATEGORY_CHOICES = [
        ('medicine', 'Medicine'),
        ('equipment', 'Equipment'),
        ('consumable', 'Consumable'),
        ('other', 'Other'),
    ]
    name = models.CharField(max_length=256)
    sku = models.CharField(max_length=64, blank=True, null=True)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=32, blank=True, null=True, default='units')
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    def __str__(self):
        return self.name

class PharmacyStock(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='pharmacy_stocks')
    qty_available = models.IntegerField(default=0)
    expiry_date = models.DateField(null=True, blank=True)
    batch_number = models.CharField(max_length=64, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.item.name} - Stock: {self.qty_available}"

class PharmacyDispense(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    pharmacy_stock = models.ForeignKey(PharmacyStock, on_delete=models.CASCADE)
    qty = models.IntegerField()
    dispensed_at = models.DateTimeField(auto_now_add=True)

class StockMovement(models.Model):
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=32, choices=[('in','In'),('out','Out')])
    qty = models.IntegerField()
    movement_date = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(ClinicUser, null=True, blank=True, on_delete=models.SET_NULL)


class NotificationLog(models.Model):
    CHANNEL_SMS = 'sms'
    CHANNEL_CHOICES = [
        (CHANNEL_SMS, 'SMS'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SENT, 'Sent'),
        (STATUS_FAILED, 'Failed'),
    ]

    category = models.CharField(max_length=64, default='general')
    channel = models.CharField(max_length=16, choices=CHANNEL_CHOICES, default=CHANNEL_SMS)
    recipient = models.CharField(max_length=32)
    recipient_name = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error_message = models.TextField(blank=True, null=True)
    provider_message_id = models.CharField(max_length=128, blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    response_payload = models.JSONField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_channel_display()} to {self.recipient} ({self.status})"

# Import medical record models
from .models_medical_records import (
    MedicalRecord, 
    MedicalRecordAttachment, 
    MedicalCertificate, 
    PatientTransfer,
    HMISClassification
)

# Import financial models
from .models_financial import (
    Expense,
    Purchase,
    FixedAsset,
    ConsumableInventory,
    ConsumableUsage,
    FinancialPeriod,
    StockAlert
)
