# clinic/views_inventory.py
"""Inventory management dashboard"""

from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count, F, Value, DecimalField
from django.db.models.functions import Coalesce
from clinic.models import (
    ClinicUser, InventoryItem, FixedAsset, ConsumableInventory, 
    StockMovement, ConsumableUsage
)


@require_http_methods(["GET", "POST"])
def inventory_login(request):
    """Custom login page for inventory staff"""
    if request.user.is_authenticated:
        # Check if already logged in as inventory
        if hasattr(request.user, 'clinicuser') and request.user.clinicuser.role == 'inventory':
            return redirect('inventory_dashboard')
    
    if request.method == 'POST':
        # Logout any existing user
        if request.user.is_authenticated:
            logout(request)
        
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user has inventory role
            if hasattr(user, 'clinicuser'):
                if user.clinicuser.role == 'inventory':
                    login(request, user)
                    return redirect('inventory_dashboard')
                else:
                    return render(request, 'inventory/login.html', {
                        'error': 'You do not have inventory privileges. Please contact your administrator.'
                    })
            else:
                return render(request, 'inventory/login.html', {
                    'error': 'You do not have inventory privileges. Please contact your administrator.'
                })
        else:
            return render(request, 'inventory/login.html', {
                'error': 'Invalid username or password.'
            })
    
    # For GET request, log out any existing user and show login form
    if request.user.is_authenticated:
        logout(request)
    
    return render(request, 'inventory/login.html')


@login_required(login_url='/dashboard/inventory/login/')
def inventory_logout(request):
    """Logout inventory user"""
    logout(request)
    return redirect('inventory_login')


def inventory_dashboard(request):
    """Inventory dashboard overview"""
    
    # This is a placeholder - inventory models need to be created
    # For now showing the structure
    
    context = {
        'low_stock_items': [],
        'recent_transactions': [],
        'total_items': 0,
    }
    
    return render(request, 'inventory/dashboard.html', context)


def inventory_items(request):
    """Manage inventory items"""
    
    context = {
        'items': [],
    }
    
    return render(request, 'inventory/items.html', context)


def inventory_by_department(request, dept_id=None):
    """Track inventory usage by department"""
    
    context = {
        'department': None,
        'items': [],
    }
    
    return render(request, 'inventory/by_department.html', context)


@login_required(login_url='/dashboard/inventory/login/')
def inventory_items_view(request):
    """View all inventory items"""
    
    # Get all inventory items
    all_items = InventoryItem.objects.all().order_by('name')
    
    # Get consumable inventory
    consumables = ConsumableInventory.objects.all().order_by('item_name')
    
    # Get fixed assets
    assets = FixedAsset.objects.order_by('-purchase_date')
    
    total_items = all_items.count()
    total_consumables = consumables.count()
    total_assets = assets.count()
    
    context = {
        'all_items': all_items,
        'consumables': consumables,
        'assets': assets,
        'total_items': total_items,
        'total_consumables': total_consumables,
        'total_assets': total_assets,
    }
    
    return render(request, 'inventory/items.html', context)


@login_required(login_url='/dashboard/inventory/login/')
def inventory_stock_view(request):
    """Manage inventory stock levels"""
    today = timezone.now().date()
    
    # Low stock consumables
    low_stock_items = ConsumableInventory.objects.filter(
        quantity_in_stock__lte=F('minimum_stock_level')
    ).order_by('quantity_in_stock')
    
    # Expiring soon (within 30 days)
    expiry_threshold = today + timedelta(days=30)
    expiring_items = ConsumableInventory.objects.filter(
        expiry_date__lte=expiry_threshold,
        expiry_date__isnull=False
    ).order_by('expiry_date')
    
    # All consumable stock
    all_stock = ConsumableInventory.objects.all().order_by('-quantity_in_stock')
    
    # Recent stock movements
    recent_movements = StockMovement.objects.select_related(
        'inventory_item', 'performed_by'
    ).order_by('-movement_date')[:20]
    
    context = {
        'low_stock_items': low_stock_items,
        'expiring_items': expiring_items,
        'all_stock': all_stock,
        'recent_movements': recent_movements,
        'low_stock_count': low_stock_items.count(),
        'expiring_count': expiring_items.count(),
    }
    
    return render(request, 'inventory/stock.html', context)


@login_required(login_url='/dashboard/inventory/login/')
def inventory_equipment_view(request):
    """Manage equipment and fixed assets"""
    
    # All equipment
    all_equipment = FixedAsset.objects.all().order_by('-purchase_date')
    
    # Active equipment
    active_equipment = all_equipment.filter(status='active')
    
    # Maintenance equipment
    maintenance_equipment = all_equipment.filter(status='maintenance')
    
    # Damaged equipment
    damaged_equipment = all_equipment.filter(status='damaged')
    
    # Disposed equipment
    disposed_equipment = all_equipment.filter(status='disposed')
    
    # Equipment by type
    equipment_by_type = FixedAsset.objects.values('asset_type').annotate(
        count=Count('id'),
        total_value=Sum('purchase_cost')
    ).order_by('-count')
    
    # Calculate total value
    total_value = active_equipment.aggregate(
        total=Coalesce(Sum('purchase_cost'), Value(0, output_field=DecimalField()))
    )['total'] or 0
    
    context = {
        'all_equipment': all_equipment,
        'active_equipment': active_equipment,
        'maintenance_equipment': maintenance_equipment,
        'damaged_equipment': damaged_equipment,
        'disposed_equipment': disposed_equipment,
        'equipment_by_type': equipment_by_type,
        'total_equipment': all_equipment.count(),
        'active_count': active_equipment.count(),
        'maintenance_count': maintenance_equipment.count(),
        'damaged_count': damaged_equipment.count(),
        'total_value': total_value,
    }
    
    return render(request, 'inventory/equipment.html', context)


@login_required(login_url='/dashboard/inventory/login/')
def inventory_maintenance_view(request):
    """Track equipment maintenance"""
    today = timezone.now().date()
    
    # Equipment in maintenance
    in_maintenance = FixedAsset.objects.filter(status='maintenance').order_by('asset_code')
    
    # Equipment due for maintenance (last maintenance > 90 days ago or never maintained)
    maintenance_due = FixedAsset.objects.filter(
        status='active'
    ).exclude(
        last_maintenance_date__gte=today - timedelta(days=90)
    ).order_by('last_maintenance_date')
    
    # Recently maintained equipment
    recently_maintained = FixedAsset.objects.filter(
        last_maintenance_date__gte=today - timedelta(days=30)
    ).order_by('-last_maintenance_date')
    
    context = {
        'in_maintenance': in_maintenance,
        'maintenance_due': maintenance_due,
        'recently_maintained': recently_maintained,
        'in_maintenance_count': in_maintenance.count(),
        'maintenance_due_count': maintenance_due.count(),
    }
    
    return render(request, 'inventory/maintenance.html', context)


@login_required(login_url='/dashboard/inventory/login/')
def inventory_consumables_view(request):
    """Manage consumable inventory"""
    today = timezone.now().date()
    
    # All consumables
    all_consumables = ConsumableInventory.objects.all().order_by('item_name')
    
    # Low stock consumables
    low_stock = all_consumables.filter(
        quantity_in_stock__lte=F('minimum_stock_level')
    )
    
    # Today's usage
    today_usage = ConsumableUsage.objects.filter(
        usage_date=today
    ).select_related('consumable', 'used_by', 'department')
    
    # Calculate total value
    total_value = all_consumables.aggregate(
        total=Coalesce(
            Sum(F('quantity_in_stock') * F('average_unit_cost')),
            Value(0, output_field=DecimalField())
        )
    )['total'] or 0
    
    # Usage statistics
    today_usage_count = today_usage.aggregate(
        total=Coalesce(Sum('quantity_used'), Value(0, output_field=DecimalField()))
    )['total'] or 0
    
    context = {
        'all_consumables': all_consumables,
        'low_stock': low_stock,
        'today_usage': today_usage[:10],
        'total_consumables': all_consumables.count(),
        'low_stock_count': low_stock.count(),
        'today_usage_count': today_usage_count,
        'total_value': total_value,
    }
    
    return render(request, 'inventory/consumables.html', context)


@login_required(login_url='/dashboard/inventory/login/')
def inventory_reports_view(request):
    """View inventory reports and analytics"""
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # Stock movement statistics
    recent_movements = StockMovement.objects.filter(
        movement_date__gte=last_30_days
    )
    
    movements_in = recent_movements.filter(movement_type='in').aggregate(
        total=Sum('qty')
    )['total'] or 0
    
    movements_out = recent_movements.filter(movement_type='out').aggregate(
        total=Sum('qty')
    )['total'] or 0
    
    # Consumable usage statistics
    usage_stats = ConsumableUsage.objects.filter(
        usage_date__gte=last_30_days
    ).values('consumable__item_name').annotate(
        total_used=Sum('quantity_used')
    ).order_by('-total_used')[:10]
    
    # Equipment statistics
    total_equipment = FixedAsset.objects.count()
    active_equipment = FixedAsset.objects.filter(status='active').count()
    
    # Total inventory value
    consumable_value = ConsumableInventory.objects.aggregate(
        total=Coalesce(
            Sum(F('quantity_in_stock') * F('average_unit_cost')),
            Value(0, output_field=DecimalField())
        )
    )['total'] or 0
    
    asset_value = FixedAsset.objects.filter(
        status__in=['active', 'maintenance']
    ).aggregate(
        total=Coalesce(Sum('purchase_cost'), Value(0, output_field=DecimalField()))
    )['total'] or 0
    
    total_value = consumable_value + asset_value
    
    context = {
        'movements_in': movements_in,
        'movements_out': movements_out,
        'usage_stats': usage_stats,
        'total_equipment': total_equipment,
        'active_equipment': active_equipment,
        'consumable_value': consumable_value,
        'asset_value': asset_value,
        'total_value': total_value,
        'date_range': f"{last_30_days.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}",
    }
    
    return render(request, 'inventory/reports.html', context)


@login_required(login_url='/dashboard/inventory/login/')
def inventory_add_item_view(request):
    """Add new inventory item (consumable)"""
    if request.method == 'POST':
        try:
            item_name = request.POST.get('item_name')
            category = request.POST.get('category', 'other')
            unit = request.POST.get('unit', 'pieces')
            description = request.POST.get('description', '')
            quantity = float(request.POST.get('quantity', 0))
            min_stock = float(request.POST.get('min_stock', 0))
            unit_cost = float(request.POST.get('unit_cost', 0))
            expiry_date = request.POST.get('expiry_date') or None
            
            # Create or update InventoryItem entry
            inventory_item, item_created = InventoryItem.objects.get_or_create(
                name=item_name,
                defaults={
                    'category': category,
                    'unit': unit,
                    'description': description,
                    'unit_cost': unit_cost,
                }
            )
            
            # Update if exists
            if not item_created:
                inventory_item.category = category
                inventory_item.unit = unit
                inventory_item.description = description
                inventory_item.unit_cost = unit_cost
                inventory_item.save()
            
            # Create consumable inventory entry
            ConsumableInventory.objects.create(
                item_name=item_name,
                category=category,
                unit=unit,
                notes=description,
                quantity_in_stock=quantity,
                minimum_stock_level=min_stock,
                average_unit_cost=unit_cost,
                expiry_date=expiry_date,
            )
            
            # If it's a medicine, update PharmacyStock
            if category == 'medicine':
                from clinic.models import PharmacyStock
                pharmacy_stock, _ = PharmacyStock.objects.get_or_create(
                    item=inventory_item,
                    defaults={
                        'qty_available': int(quantity),
                        'unit_price': unit_cost,
                        'expiry_date': expiry_date,
                    }
                )
                # If already exists, update the quantity
                if _:
                    pharmacy_stock.qty_available = int(quantity)
                    pharmacy_stock.unit_price = unit_cost
                    if expiry_date:
                        pharmacy_stock.expiry_date = expiry_date
                    pharmacy_stock.save()
            
            messages.success(request, f'Item "{item_name}" added successfully!')
            return redirect('inventory_items')
        except Exception as e:
            messages.error(request, f'Error adding item: {str(e)}')
    
    context = {}
    return render(request, 'inventory/add_item.html', context)


@login_required(login_url='/dashboard/inventory/login/')
def inventory_add_equipment_view(request):
    """Add new equipment/fixed asset"""
    if request.method == 'POST':
        try:
            from clinic.models_financial import FixedAsset
            from decimal import Decimal
            
            # Get form data
            asset_code = request.POST.get('asset_code')
            asset_name = request.POST.get('asset_name')
            asset_type = request.POST.get('asset_type')
            description = request.POST.get('description', '')
            purchase_date = request.POST.get('purchase_date')
            purchase_cost = Decimal(request.POST.get('purchase_cost', 0))
            supplier = request.POST.get('supplier', '')
            serial_number = request.POST.get('serial_number', '')
            warranty_expiry = request.POST.get('warranty_expiry') or None
            location = request.POST.get('location', '')
            useful_life = int(request.POST.get('useful_life', 5))
            status = request.POST.get('status', 'active')
            
            # Create fixed asset
            FixedAsset.objects.create(
                asset_code=asset_code,
                asset_name=asset_name,
                asset_type=asset_type,
                description=description,
                purchase_date=purchase_date,
                purchase_cost=purchase_cost,
                supplier=supplier,
                serial_number=serial_number,
                warranty_expiry=warranty_expiry,
                location=location,
                useful_life_years=useful_life,
                status=status,
            )
            
            messages.success(request, f'Equipment "{asset_name}" (Code: {asset_code}) added successfully!')
            return redirect('inventory_equipment')
        except Exception as e:
            messages.error(request, f'Error adding equipment: {str(e)}')
    
    context = {}
    return render(request, 'inventory/add_equipment.html', context)


@login_required(login_url='/dashboard/inventory/login/')
def inventory_stock_take_view(request):
    """Perform stock take/inventory count"""
    
    # Get all consumable items for stock take
    all_consumables = ConsumableInventory.objects.all().order_by('item_name')
    
    if request.method == 'POST':
        try:
            updated_count = 0
            # Process each item's physical count
            for consumable in all_consumables:
                physical_count_key = f'physical_count_{consumable.id}'
                notes_key = f'notes_{consumable.id}'
                
                if physical_count_key in request.POST and request.POST[physical_count_key]:
                    physical_count = float(request.POST[physical_count_key])
                    notes = request.POST.get(notes_key, '')
                    
                    # Calculate difference
                    difference = physical_count - consumable.quantity_in_stock
                    
                    # Update stock quantity
                    consumable.quantity_in_stock = physical_count
                    consumable.save()
                    
                    # Record stock movement if there's a difference
                    if difference != 0:
                        StockMovement.objects.create(
                            consumable=consumable,
                            movement_type='adjustment',
                            quantity=abs(difference),
                            notes=f'Stock take adjustment: {notes}' if notes else 'Stock take adjustment',
                            performed_by=request.user
                        )
                        updated_count += 1
            
            messages.success(request, f'Stock take completed! {updated_count} items updated.')
            return redirect('inventory_stock')
        except Exception as e:
            messages.error(request, f'Error completing stock take: {str(e)}')
    
    context = {
        'all_consumables': all_consumables,
    }
    return render(request, 'inventory/stock_take.html', context)


@login_required(login_url='/dashboard/inventory/login/')
def inventory_maintenance_log_view(request):
    """View and add maintenance log entries"""
    
    # Get all equipment
    all_equipment = FixedAsset.objects.all().order_by('-last_maintenance_date')
    
    if request.method == 'POST':
        try:
            from datetime import datetime
            
            equipment_id = request.POST.get('equipment_id')
            maintenance_date = request.POST.get('maintenance_date')
            maintenance_type = request.POST.get('maintenance_type', 'routine')
            description = request.POST.get('description')
            performed_by = request.POST.get('performed_by', '')
            cost = request.POST.get('cost', 0)
            
            # Get the equipment
            equipment = FixedAsset.objects.get(id=equipment_id)
            
            # Update last maintenance date
            equipment.last_maintenance_date = maintenance_date
            equipment.save()
            
            # Create a note in the equipment notes field
            maintenance_note = f"\n[{maintenance_date}] {maintenance_type.title()}: {description}"
            if performed_by:
                maintenance_note += f" (by {performed_by})"
            if cost and float(cost) > 0:
                maintenance_note += f" - Cost: {cost} RWF"
            
            if equipment.notes:
                equipment.notes += maintenance_note
            else:
                equipment.notes = maintenance_note.strip()
            equipment.save()
            
            messages.success(request, f'Maintenance record added for {equipment.asset_name}!')
            return redirect('inventory_maintenance')
        except Exception as e:
            messages.error(request, f'Error adding maintenance log: {str(e)}')
    
    context = {
        'all_equipment': all_equipment,
    }
    return render(request, 'inventory/maintenance_log.html', context)
