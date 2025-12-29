# clinic/models_financial.py
"""
Financial Models for Comprehensive Finance Management
Includes: Expenses, Purchases, Fixed Assets, Consumables, Financial Tracking
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal


class Expense(models.Model):
    """Track all clinic expenses"""
    CATEGORY_CHOICES = [
        ('salary', 'Salary'),
        ('utilities', 'Utilities (Water, Electricity, Internet)'),
        ('rent', 'Rent'),
        ('maintenance', 'Maintenance'),
        ('supplies', 'Supplies'),
        ('marketing', 'Marketing'),
        ('insurance', 'Insurance'),
        ('equipment', 'Equipment'),
        ('transport', 'Transport'),
        ('miscellaneous', 'Miscellaneous'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ]
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Approval workflow
    requested_by = models.ForeignKey(
        'ClinicUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='expenses_requested'
    )
    approved_by = models.ForeignKey(
        'ClinicUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='expenses_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Payment tracking
    paid_at = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=128, blank=True, null=True)
    
    # Department allocation (optional)
    department = models.ForeignKey(
        'Department', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Attachments (receipts, invoices)
    receipt_file = models.FileField(upload_to='expenses/receipts/', null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-expense_date', '-created_at']
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.amount} RWF - {self.expense_date}"


class Purchase(models.Model):
    """Track purchases of inventory items"""
    PURCHASE_TYPE_CHOICES = [
        ('consumable', 'Consumable'),
        ('fixed_asset', 'Fixed Asset'),
        ('equipment', 'Equipment'),
        ('medicine', 'Medicine'),
        ('supplies', 'Dental Supplies'),
    ]
    
    purchase_type = models.CharField(max_length=30, choices=PURCHASE_TYPE_CHOICES)
    item_name = models.CharField(max_length=255)
    supplier_name = models.CharField(max_length=255)
    supplier_contact = models.CharField(max_length=100, blank=True, null=True)
    
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50, help_text="e.g., pieces, boxes, kg, liters")
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    
    purchase_date = models.DateField()
    entry_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True, help_text="For consumables and medicines")
    
    # Tracking
    entered_by = models.ForeignKey(
        'ClinicUser', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='purchases_entered'
    )
    department = models.ForeignKey(
        'Department', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Link to inventory if applicable
    inventory_item = models.ForeignKey(
        'InventoryItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchases'
    )
    
    # Link to fixed asset if applicable
    fixed_asset = models.ForeignKey(
        'FixedAsset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchases'
    )
    
    invoice_number = models.CharField(max_length=128, blank=True, null=True)
    invoice_file = models.FileField(upload_to='purchases/invoices/', null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-purchase_date', '-entry_date']
    
    def __str__(self):
        return f"{self.item_name} - {self.quantity} {self.unit} - {self.total_cost} RWF"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total cost
        self.total_cost = self.quantity * self.price_per_unit
        super().save(*args, **kwargs)


class FixedAsset(models.Model):
    """Track fixed assets (machines, furniture, etc.)"""
    ASSET_TYPE_CHOICES = [
        ('machine', 'Machine/Equipment'),
        ('furniture', 'Furniture'),
        ('vehicle', 'Vehicle'),
        ('computer', 'Computer/IT Equipment'),
        ('building', 'Building/Property'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('retired', 'Retired'),
        ('sold', 'Sold'),
        ('damaged', 'Damaged'),
    ]
    
    asset_type = models.CharField(max_length=30, choices=ASSET_TYPE_CHOICES)
    asset_name = models.CharField(max_length=255)
    asset_code = models.CharField(max_length=50, unique=True, help_text="Unique asset ID/code")
    description = models.TextField(blank=True, null=True)
    
    # Purchase details
    purchase_date = models.DateField()
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2)
    supplier = models.CharField(max_length=255, blank=True, null=True)
    
    # Depreciation
    useful_life_years = models.IntegerField(
        default=5, 
        help_text="Expected useful life in years for depreciation"
    )
    salvage_value = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Expected value at end of useful life"
    )
    
    # Current status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    location = models.CharField(max_length=255, blank=True, null=True)
    department = models.ForeignKey(
        'Department', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Maintenance tracking
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    
    # Documentation
    serial_number = models.CharField(max_length=128, blank=True, null=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    invoice_file = models.FileField(upload_to='assets/invoices/', null=True, blank=True)
    photo = models.ImageField(upload_to='assets/photos/', null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['asset_name']
    
    def __str__(self):
        return f"{self.asset_code} - {self.asset_name}"
    
    def current_value(self):
        """Calculate current depreciated value using straight-line method"""
        if self.useful_life_years == 0:
            return self.purchase_cost
        
        days_elapsed = (timezone.now().date() - self.purchase_date).days
        years_elapsed = Decimal(str(days_elapsed)) / Decimal('365.25')
        annual_depreciation = (self.purchase_cost - self.salvage_value) / self.useful_life_years
        total_depreciation = annual_depreciation * min(years_elapsed, Decimal(str(self.useful_life_years)))
        
        current_value = self.purchase_cost - total_depreciation
        return max(current_value, self.salvage_value)


class ConsumableInventory(models.Model):
    """Enhanced consumable inventory tracking with expiry and usage"""
    item_name = models.CharField(max_length=255)
    item_code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    category = models.CharField(
        max_length=50, 
        choices=[
            ('medicine', 'Medicine'),
            ('dental_supply', 'Dental Supply'),
            ('office_supply', 'Office Supply'),
            ('cleaning', 'Cleaning Supply'),
            ('ppe', 'Personal Protective Equipment'),
            ('other', 'Other'),
        ]
    )
    
    unit = models.CharField(max_length=50, help_text="e.g., pieces, boxes, kg, liters")
    
    # Current stock
    quantity_in_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_stock_level = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Alert when stock falls below this level"
    )
    
    # Tracking
    last_entry_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    department = models.ForeignKey(
        'Department', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Costing (for inventory valuation)
    average_unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['item_name']
        verbose_name_plural = 'Consumable Inventories'
    
    def __str__(self):
        return f"{self.item_name} - {self.quantity_in_stock} {self.unit}"
    
    def is_low_stock(self):
        """Check if stock is below minimum level"""
        return self.quantity_in_stock <= self.minimum_stock_level
    
    def is_expired(self):
        """Check if item has expired"""
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False
    
    def total_value(self):
        """Calculate total inventory value"""
        return self.quantity_in_stock * self.average_unit_cost


class ConsumableUsage(models.Model):
    """Track usage of consumable items"""
    consumable = models.ForeignKey(
        ConsumableInventory, 
        on_delete=models.CASCADE,
        related_name='usage_records'
    )
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2)
    usage_date = models.DateField()
    
    # Who used it and where
    used_by = models.ForeignKey(
        'ClinicUser', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='consumable_usage'
    )
    department = models.ForeignKey(
        'Department', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Optional: link to patient visit if used in treatment
    visit = models.ForeignKey(
        'Visit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consumables_used'
    )
    
    purpose = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-usage_date', '-created_at']
    
    def __str__(self):
        return f"{self.consumable.item_name} - {self.quantity_used} {self.consumable.unit} - {self.usage_date}"


class FinancialPeriod(models.Model):
    """Track financial reporting periods"""
    PERIOD_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    ]
    
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Calculated totals (cached for performance)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        'ClinicUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='periods_closed'
    )
    
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
        unique_together = ['period_type', 'start_date', 'end_date']
    
    def __str__(self):
        return f"{self.get_period_type_display()} - {self.start_date} to {self.end_date}"
    
    def calculate_totals(self):
        """Recalculate period totals"""
        from django.db.models import Sum
        from .models import Invoice
        
        # Revenue from invoices
        invoices = Invoice.objects.filter(
            created_at__date__gte=self.start_date,
            created_at__date__lte=self.end_date
        ).aggregate(
            insurance=Sum('total_insurance'),
            private=Sum('total_private')
        )
        
        self.total_revenue = (invoices['insurance'] or 0) + (invoices['private'] or 0)
        
        # Expenses
        expenses = Expense.objects.filter(
            expense_date__gte=self.start_date,
            expense_date__lte=self.end_date,
            status='paid'
        ).aggregate(total=Sum('amount'))
        
        self.total_expenses = expenses['total'] or 0
        
        # Net profit/loss
        self.net_profit = self.total_revenue - self.total_expenses
        
        self.save()
        return {
            'revenue': self.total_revenue,
            'expenses': self.total_expenses,
            'profit': self.net_profit
        }


class StockAlert(models.Model):
    """Track stock alerts for low inventory and expiring items"""
    ALERT_TYPE_CHOICES = [
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
    ]
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Can be for consumable or fixed asset
    consumable = models.ForeignKey(
        ConsumableInventory,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )
    
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        'ClinicUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts_acknowledged'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.created_at.date()}"
