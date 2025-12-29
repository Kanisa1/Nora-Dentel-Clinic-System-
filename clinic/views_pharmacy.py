# clinic/views_pharmacy.py
"""Pharmacy management dashboard"""

from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required


@require_http_methods(["GET", "POST"])
def pharmacy_login(request):
    """Custom login page for pharmacy staff"""
    if request.user.is_authenticated:
        # Check if already logged in as pharmacy
        if hasattr(request.user, 'clinicuser') and request.user.clinicuser.role == 'pharmacy':
            return redirect('pharmacy_dashboard')
    
    if request.method == 'POST':
        # Logout any existing user
        if request.user.is_authenticated:
            logout(request)
        
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user has pharmacy role
            if hasattr(user, 'clinicuser'):
                if user.clinicuser.role == 'pharmacy':
                    login(request, user)
                    return redirect('pharmacy_dashboard')
                else:
                    return render(request, 'pharmacy/login.html', {
                        'error': 'You do not have pharmacy privileges. Please contact your administrator.'
                    })
            else:
                return render(request, 'pharmacy/login.html', {
                    'error': 'You do not have pharmacy privileges. Please contact your administrator.'
                })
        else:
            return render(request, 'pharmacy/login.html', {
                'error': 'Invalid username or password. Please try again.'
            })
    
    return render(request, 'pharmacy/login.html')


@require_http_methods(["GET", "POST"])
def pharmacy_logout(request):
    """Logout pharmacy user"""
    logout(request)
    return redirect('pharmacy_login')


@login_required
def pharmacy_dashboard(request):
    """Pharmacy dashboard overview"""
    from clinic.models import InventoryItem, PharmacyStock, Prescription
    from django.utils import timezone
    from datetime import timedelta
    
    # Get all medicines from pharmacy stock
    all_medicines = PharmacyStock.objects.select_related('item').all()
    
    # Low stock medicines (less than 10)
    low_stock_medicines = all_medicines.filter(qty_available__lt=10)
    
    # Expiring soon (within 30 days)
    today = timezone.now().date()
    expiry_threshold = today + timedelta(days=30)
    expiring_medicines = all_medicines.filter(
        expiry_date__lte=expiry_threshold,
        expiry_date__isnull=False
    )
    
    # Get pending prescriptions
    pending_prescriptions = Prescription.objects.filter(
        prescription_type='clinic'
    ).select_related('patient', 'doctor', 'visit')[:10]
    
    context = {
        'total_medicines': all_medicines.count(),
        'low_stock_count': low_stock_medicines.count(),
        'expired_count': expiring_medicines.count(),
        'today_dispensed': 0,  # TODO: Implement dispensing tracking
        'low_stock_medications': low_stock_medicines[:5],
        'recent_prescriptions': pending_prescriptions,
        'pending_prescriptions': pending_prescriptions,
    }
    
    return render(request, 'pharmacy/dashboard.html', context)


@login_required
def pharmacy_medications(request):
    """Manage medications"""
    
    context = {
        'medications': [],
    }
    
    return render(request, 'pharmacy/medications.html', context)


@login_required
def pharmacy_prescriptions(request):
    """View prescriptions"""
    from clinic.models import Prescription
    
    # Get all prescriptions
    all_prescriptions = Prescription.objects.select_related(
        'patient', 'doctor', 'doctor__user', 'visit'
    ).prefetch_related('items__inventory_item').order_by('-created_at')
    
    # Filter by status
    pending_prescriptions = all_prescriptions.filter(prescription_type='clinic')
    completed_prescriptions = all_prescriptions.filter(prescription_type='written')
    
    # Count statistics
    total_count = all_prescriptions.count()
    pending_count = pending_prescriptions.count()
    completed_count = completed_prescriptions.count()
    
    context = {
        'all_prescriptions': all_prescriptions,
        'pending_prescriptions': pending_prescriptions,
        'completed_prescriptions': completed_prescriptions,
        'total_count': total_count,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'prescriptions': all_prescriptions,  # For backward compatibility
    }
    
    return render(request, 'pharmacy/prescriptions.html', context)


@login_required
def pharmacy_medicines_view(request):
    """View and manage medicines"""
    from clinic.models import InventoryItem, PharmacyStock
    
    # Get all medicines from inventory with pharmacy stock
    medicine_items = InventoryItem.objects.filter(category='medicine').prefetch_related('pharmacy_stocks')
    
    # Build medicines list with stock information
    medicines_data = []
    for item in medicine_items:
        # Get the most recent pharmacy stock for this item
        stock = item.pharmacy_stocks.first()
        if stock:
            medicines_data.append(stock)
        else:
            # Create a default stock entry if none exists
            stock = PharmacyStock.objects.create(
                item=item,
                qty_available=0,
                unit_price=item.unit_cost
            )
            medicines_data.append(stock)
    
    context = {
        'medicines': medicines_data,
        'total_count': len(medicines_data),
    }
    
    return render(request, 'pharmacy/medicines.html', context)


@login_required
def pharmacy_stock_view(request):
    """View and manage stock"""
    from clinic.models import PharmacyStock
    from django.utils import timezone
    from datetime import timedelta
    
    # Get all pharmacy stock items
    all_stock = PharmacyStock.objects.select_related('item').all().order_by('item__name')
    
    # Filter low stock items (≤10 units)
    low_stock_items = all_stock.filter(qty_available__lte=10)
    
    # Filter critical stock (≤5 units)
    critical_stock = all_stock.filter(qty_available__lte=5)
    
    # Filter out of stock
    out_of_stock = all_stock.filter(qty_available=0)
    
    # Filter expiring items (next 30 days)
    today = timezone.now().date()
    expiring_date = today + timedelta(days=30)
    expiring_items = all_stock.filter(
        expiry_date__isnull=False,
        expiry_date__lte=expiring_date,
        expiry_date__gte=today
    )
    
    # Calculate statistics
    total_items = all_stock.count()
    low_stock_count = low_stock_items.count()
    critical_count = critical_stock.count()
    out_of_stock_count = out_of_stock.count()
    expiring_count = expiring_items.count()
    in_stock_count = all_stock.filter(qty_available__gt=10).count()
    
    # Calculate total stock value
    total_value = sum(item.qty_available * item.unit_price for item in all_stock)
    
    context = {
        'all_stock': all_stock,
        'low_stock_items': low_stock_items,
        'critical_stock': critical_stock,
        'out_of_stock': out_of_stock,
        'expiring_items': expiring_items,
        'total_items': total_items,
        'low_stock_count': low_stock_count,
        'critical_count': critical_count,
        'out_of_stock_count': out_of_stock_count,
        'expiring_count': expiring_count,
        'in_stock_count': in_stock_count,
        'total_value': total_value,
    }
    
    return render(request, 'pharmacy/stock.html', context)


@login_required
def pharmacy_dispensing_view(request):
    """Dispensing interface"""
    return render(request, 'pharmacy/dispensing.html', {})


@login_required
def pharmacy_prescriptions_view(request):
    """View prescriptions"""
    from clinic.models import Prescription
    from django.utils import timezone
    from datetime import timedelta
    
    # Get all prescriptions
    all_prescriptions = Prescription.objects.select_related(
        'patient', 'doctor', 'doctor__user', 'visit'
    ).prefetch_related('items__inventory_item').order_by('-created_at')
    
    # Filter by status
    pending_prescriptions = all_prescriptions.filter(prescription_type='clinic')
    completed_prescriptions = all_prescriptions.filter(prescription_type='written')
    
    # Get today's prescriptions (last 24 hours)
    today_start = timezone.now() - timedelta(hours=24)
    today_prescriptions = all_prescriptions.filter(created_at__gte=today_start)
    
    # Count statistics
    total_count = all_prescriptions.count()
    pending_count = pending_prescriptions.count()
    completed_count = completed_prescriptions.count()
    today_count = today_prescriptions.count()
    
    context = {
        'all_prescriptions': all_prescriptions,
        'pending_prescriptions': pending_prescriptions,
        'completed_prescriptions': completed_prescriptions,
        'total_count': total_count,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'today_count': today_count,
    }
    
    return render(request, 'pharmacy/prescriptions.html', context)


@login_required
def pharmacy_reports_view(request):
    """Pharmacy reports"""
    return render(request, 'pharmacy/reports.html', {})


@login_required
def pharmacy_alerts_view(request):
    """View pharmacy alerts"""
    return render(request, 'pharmacy/alerts.html', {})


@login_required
def pharmacy_prescription_detail(request, prescription_id):
    """View prescription details in JSON format for AJAX requests"""
    from clinic.models import Prescription
    from django.http import JsonResponse
    
    try:
        prescription = Prescription.objects.select_related(
            'patient', 'doctor', 'doctor__user', 'visit'
        ).prefetch_related('items__inventory_item').get(id=prescription_id)
        
        # Build prescription data
        items = []
        for item in prescription.items.all():
            items.append({
                'name': item.inventory_item.name,
                'dosage': item.dosage or 'N/A',
                'frequency': item.frequency or 'N/A',
                'duration': item.duration or 'N/A',
                'quantity': item.quantity,
                'instructions': item.instructions or 'N/A'
            })
        
        data = {
            'success': True,
            'prescription': {
                'id': prescription.id,
                'prescription_id': f"#{prescription.id:05d}",
                'patient_name': f"{prescription.patient.first_name} {prescription.patient.last_name}",
                'patient_id': prescription.patient.patient_id,
                'doctor_name': prescription.doctor.user.get_full_name(),
                'date': prescription.created_at.strftime('%B %d, %Y'),
                'time': prescription.created_at.strftime('%I:%M %p'),
                'type': prescription.prescription_type.title(),
                'items': items,
                'notes': prescription.notes or 'No additional notes'
            }
        }
        return JsonResponse(data)
    except Prescription.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Prescription not found'}, status=404)


@login_required
def pharmacy_print_prescription(request, prescription_id):
    """Print prescription"""
    from clinic.models import Prescription
    from django.shortcuts import get_object_or_404
    
    prescription = get_object_or_404(
        Prescription.objects.select_related(
            'patient', 'doctor', 'doctor__user', 'visit'
        ).prefetch_related('items__inventory_item'),
        id=prescription_id
    )
    
    context = {
        'prescription': prescription,
    }
    
    return render(request, 'pharmacy/prescription_print.html', context)


@login_required
def pharmacy_dispense_prescription(request, prescription_id):
    """Dispense a prescription"""
    from clinic.models import Prescription, PharmacyStock, Dispense
    from django.http import JsonResponse
    from django.db import transaction
    from django.utils import timezone
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)
    
    try:
        with transaction.atomic():
            prescription = Prescription.objects.select_related('patient').prefetch_related(
                'items__inventory_item'
            ).get(id=prescription_id)
            
            # Check if already dispensed
            if prescription.prescription_type != 'clinic':
                return JsonResponse({
                    'success': False,
                    'error': 'This prescription has already been dispensed'
                }, status=400)
            
            # Dispense each item
            dispensed_items = []
            insufficient_stock = []
            
            for item in prescription.items.all():
                # Find available stock
                stock = PharmacyStock.objects.filter(
                    item=item.inventory_item,
                    qty_available__gte=item.quantity
                ).first()
                
                if not stock:
                    insufficient_stock.append(item.inventory_item.name)
                    continue
                
                # Create dispense record
                dispense = Dispense.objects.create(
                    prescription=prescription,
                    pharmacy_stock=stock,
                    quantity_dispensed=item.quantity,
                    dispensed_by=request.user,
                    dispensed_at=timezone.now()
                )
                
                # Update stock
                stock.qty_available -= item.quantity
                stock.save()
                
                dispensed_items.append(item.inventory_item.name)
            
            if insufficient_stock:
                return JsonResponse({
                    'success': False,
                    'error': f'Insufficient stock for: {", ".join(insufficient_stock)}'
                }, status=400)
            
            # Update prescription type to mark as dispensed
            prescription.prescription_type = 'written'
            prescription.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully dispensed {len(dispensed_items)} item(s)',
                'dispensed_items': dispensed_items
            })
            
    except Prescription.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Prescription not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
