from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from .utils import generate_invoice_pdf
from decimal import Decimal

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().order_by('-created_at')
    serializer_class = PatientSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        patient = serializer.save()
        import uuid
        card_number = f"CLINIC-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        PatientCard.objects.create(patient=patient, card_number=card_number)

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all().order_by('-scheduled_at')
    serializer_class = AppointmentSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        scheduled_by = None
        request = getattr(self, 'request', None)
        if request and request.user.is_authenticated and hasattr(request.user, 'clinicuser'):
            scheduled_by = request.user.clinicuser
        serializer.save(scheduled_by=scheduled_by)

@api_view(['POST'])
@permission_classes([AllowAny])
def check_in_patient(request):
    patient_id = request.data.get('patient_id')
    appointment_id = request.data.get('appointment_id')
    department_id = request.data.get('department_id')
    try:
        clinicuser = request.user.clinicuser
    except Exception:
        clinicuser = None
    with transaction.atomic():
        patient = get_object_or_404(Patient, pk=patient_id)
        if appointment_id:
            appt = Appointment.objects.select_for_update().get(pk=appointment_id)
            appt.status = 'checked_in'
            appt.save()
            visit = Visit.objects.create(patient=patient, department=appt.department, doctor=appt.doctor)
        else:
            visit = Visit.objects.create(patient=patient, department_id=department_id)
        last = WaitingQueueEntry.objects.select_for_update().filter(visit__department_id=visit.department_id, status='waiting').order_by('-position').first()
        next_pos = last.position + 1 if last else 1
        entry = WaitingQueueEntry.objects.create(visit=visit, position=next_pos, receptionist=clinicuser)
    return Response(QueueEntrySerializer(entry).data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_queue(request):
    department_id = request.query_params.get('department_id')
    qs = WaitingQueueEntry.objects.filter(status='waiting')
    if department_id:
        qs = qs.filter(visit__department_id=department_id)
    serializer = QueueEntrySerializer(qs.order_by('position'), many=True)
    return Response(serializer.data)

class TariffViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TariffAct.objects.filter(active=True)
    serializer_class = TariffActSerializer
    permission_classes = [AllowAny]

@api_view(['POST'])
@permission_classes([AllowAny])
def add_billing_item(request, visit_id):
    visit = get_object_or_404(Visit, pk=visit_id)
    tariff_id = request.data.get('tariff_id')
    qty = int(request.data.get('qty', 1))
    tariff = get_object_or_404(TariffAct, pk=tariff_id)
    item = BillingItem.objects.create(
        visit=visit,
        tariff=tariff,
        qty=qty,
        price_private_snapshot=tariff.price_private,
        price_insurance_snapshot=tariff.price_insurance or Decimal('0.00')
    )
    return Response({'item_id': item.id})

@api_view(['POST'])
@permission_classes([AllowAny])
def finalize_invoice(request, visit_id):
    visit = get_object_or_404(Visit, pk=visit_id)
    patient = visit.patient
    items = visit.billing_items.all()
    total_ins = Decimal('0.00')
    total_priv = Decimal('0.00')
    for it in items:
        line_total = it.qty * it.price_private_snapshot
        ins_share = (line_total * Decimal(patient.insurance_coverage_pct)) / Decimal(100)
        priv_share = line_total - ins_share
        total_ins += ins_share
        total_priv += priv_share
    invoice, created = Invoice.objects.get_or_create(visit=visit, defaults={
        'total_private': total_priv,
        'total_insurance': total_ins,
        'created_by': request.user.clinicuser if hasattr(request.user, 'clinicuser') else None
    })
    if not created:
        invoice.total_private = total_priv
        invoice.total_insurance = total_ins
        invoice.save()
    pdf_url = generate_invoice_pdf(invoice)
    return Response({'invoice_id': invoice.id, 'pdf_url': pdf_url})

@api_view(['POST'])
@permission_classes([AllowAny])
def pay_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    amount = Decimal(request.data.get('amount'))
    raw_method = request.data.get('method', Payment.METHOD_CASH)
    method = raw_method.strip() if isinstance(raw_method, str) else Payment.METHOD_CASH
    raw_reference = request.data.get('reference', '')
    reference = raw_reference.strip() if isinstance(raw_reference, str) else ''

    valid_methods = dict(Payment.METHOD_CHOICES)
    if method not in valid_methods:
        method = Payment.METHOD_CASH

    Payment.objects.create(
        invoice=invoice,
        amount=amount,
        method=method,
        reference=reference or None,
    )

    if Payment.clears_invoice_immediately(method):
        invoice.paid = True
        invoice.paid_at = timezone.now()
        status_value = 'paid'
    else:
        invoice.paid = False
        invoice.paid_at = None
        status_value = 'pending'

    invoice.save(update_fields=['paid', 'paid_at'])
    return Response({'status': status_value})
