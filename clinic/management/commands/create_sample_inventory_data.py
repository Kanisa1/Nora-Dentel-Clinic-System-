"""
Sample Data Script for Pharmacy & Inventory Dashboards
Run this with: python manage.py create_sample_inventory_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from clinic.models import (
    InventoryItem, PharmacyStock, Department, ClinicUser,
    Prescription, PrescriptionItem, PharmacyDispense, Patient, Visit
)
from clinic.models_financial import (
    FixedAsset, ConsumableInventory, ConsumableUsage, StockMovement
)


class Command(BaseCommand):
    help = 'Create sample data for pharmacy and inventory dashboards'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...\n')
        
        # Create sample inventory items
        medicines = [
            {'name': 'Paracetamol 500mg', 'unit': 'tablets', 'cost': 50},
            {'name': 'Amoxicillin 250mg', 'unit': 'capsules', 'cost': 150},
            {'name': 'Ibuprofen 400mg', 'unit': 'tablets', 'cost': 80},
            {'name': 'Metronidazole 400mg', 'unit': 'tablets', 'cost': 100},
            {'name': 'Ciprofloxacin 500mg', 'unit': 'tablets', 'cost': 200},
            {'name': 'Dental Anesthetic (Lidocaine)', 'unit': 'vials', 'cost': 500},
            {'name': 'Mouthwash (Chlorhexidine)', 'unit': 'bottles', 'cost': 300},
            {'name': 'Dental Cement', 'unit': 'tubes', 'cost': 800},
        ]
        
        self.stdout.write('Creating medicines...')
        for med in medicines:
            item, created = InventoryItem.objects.get_or_create(
                name=med['name'],
                defaults={
                    'unit': med['unit'],
                    'unit_cost': Decimal(str(med['cost']))
                }
            )
            if created:
                self.stdout.write(f'  ✓ {med["name"]}')
        
        # Create pharmacy stock with various levels
        self.stdout.write('\nCreating pharmacy stock...')
        items = InventoryItem.objects.all()
        today = timezone.now().date()
        
        for i, item in enumerate(items):
            # Mix of good stock, low stock, and expiring items
            if i % 3 == 0:
                qty = 5  # Low stock
                expiry = today + timedelta(days=20)  # Expiring soon
            elif i % 3 == 1:
                qty = 50  # Good stock
                expiry = today + timedelta(days=180)
            else:
                qty = 8  # Low stock
                expiry = today + timedelta(days=10)  # Expiring very soon
            
            stock, created = PharmacyStock.objects.get_or_create(
                item=item,
                defaults={
                    'qty_available': qty,
                    'expiry_date': expiry
                }
            )
            if created:
                self.stdout.write(f'  ✓ {item.name}: {qty} units, expires {expiry}')
        
        # Create fixed assets
        self.stdout.write('\nCreating fixed assets...')
        assets = [
            {
                'name': 'Dental Chair Unit',
                'type': 'machine',
                'code': 'DC-001',
                'cost': 5000000,
                'status': 'active',
                'location': 'Treatment Room 1'
            },
            {
                'name': 'X-Ray Machine',
                'type': 'machine',
                'code': 'XR-001',
                'cost': 8000000,
                'status': 'active',
                'location': 'Radiology'
            },
            {
                'name': 'Autoclave Sterilizer',
                'type': 'machine',
                'code': 'AS-001',
                'cost': 2000000,
                'status': 'maintenance',
                'location': 'Sterilization Room'
            },
            {
                'name': 'Reception Desk',
                'type': 'furniture',
                'code': 'FU-001',
                'cost': 500000,
                'status': 'active',
                'location': 'Reception'
            },
            {
                'name': 'Office Computer',
                'type': 'computer',
                'code': 'PC-001',
                'cost': 800000,
                'status': 'active',
                'location': 'Admin Office'
            },
        ]
        
        for asset_data in assets:
            asset, created = FixedAsset.objects.get_or_create(
                asset_code=asset_data['code'],
                defaults={
                    'asset_name': asset_data['name'],
                    'asset_type': asset_data['type'],
                    'purchase_date': today - timedelta(days=365),
                    'purchase_cost': Decimal(str(asset_data['cost'])),
                    'status': asset_data['status'],
                    'location': asset_data['location'],
                    'useful_life_years': 10,
                    'salvage_value': Decimal(str(asset_data['cost'] * 0.1))
                }
            )
            if created:
                self.stdout.write(f'  ✓ {asset_data["name"]} - {asset_data["cost"]} RWF')
        
        # Create consumable inventory
        self.stdout.write('\nCreating consumable inventory...')
        consumables = [
            {
                'name': 'Disposable Gloves',
                'category': 'ppe',
                'unit': 'boxes',
                'qty': 15,
                'min': 20,
                'cost': 5000,
                'expiry': today + timedelta(days=90)
            },
            {
                'name': 'Face Masks',
                'category': 'ppe',
                'unit': 'boxes',
                'qty': 8,
                'min': 15,
                'cost': 3000,
                'expiry': today + timedelta(days=60)
            },
            {
                'name': 'Cotton Rolls',
                'category': 'dental_supply',
                'unit': 'packs',
                'qty': 25,
                'min': 10,
                'cost': 2000,
                'expiry': None
            },
            {
                'name': 'Dental Burs',
                'category': 'dental_supply',
                'unit': 'sets',
                'qty': 5,
                'min': 8,
                'cost': 15000,
                'expiry': None
            },
            {
                'name': 'Disinfectant Solution',
                'category': 'cleaning',
                'unit': 'liters',
                'qty': 3,
                'min': 5,
                'cost': 8000,
                'expiry': today + timedelta(days=180)
            },
        ]
        
        for cons in consumables:
            item, created = ConsumableInventory.objects.get_or_create(
                item_name=cons['name'],
                defaults={
                    'category': cons['category'],
                    'unit': cons['unit'],
                    'quantity_in_stock': Decimal(str(cons['qty'])),
                    'minimum_stock_level': Decimal(str(cons['min'])),
                    'average_unit_cost': Decimal(str(cons['cost'])),
                    'expiry_date': cons['expiry'],
                    'last_entry_date': today
                }
            )
            if created:
                status = "LOW STOCK" if cons['qty'] <= cons['min'] else "OK"
                self.stdout.write(f'  ✓ {cons["name"]}: {cons["qty"]} {cons["unit"]} [{status}]')
        
        # Create some stock movements
        self.stdout.write('\nCreating stock movements...')
        inv_items = InventoryItem.objects.all()[:3]
        doctor = ClinicUser.objects.filter(role='doctor').first()
        
        if inv_items and doctor:
            for item in inv_items:
                # Stock in
                StockMovement.objects.create(
                    inventory_item=item,
                    movement_type='in',
                    qty=50,
                    performed_by=doctor
                )
                # Stock out
                StockMovement.objects.create(
                    inventory_item=item,
                    movement_type='out',
                    qty=10,
                    performed_by=doctor
                )
            self.stdout.write('  ✓ Created sample stock movements')
        
        # Create consumable usage for today
        self.stdout.write('\nCreating today\'s usage records...')
        consumable_items = ConsumableInventory.objects.all()[:3]
        if consumable_items and doctor:
            for cons in consumable_items:
                ConsumableUsage.objects.create(
                    consumable=cons,
                    quantity_used=Decimal('2'),
                    usage_date=today,
                    used_by=doctor
                )
            self.stdout.write('  ✓ Created usage records for today')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Sample data created successfully!'))
        self.stdout.write('\nYou can now view the dashboards at:')
        self.stdout.write('  • Pharmacy: http://127.0.0.1:8000/dashboard/pharmacy/dashboard/')
        self.stdout.write('  • Inventory: http://127.0.0.1:8000/dashboard/inventory/dashboard/')
