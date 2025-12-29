from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.crypto import get_random_string

from .models import Appointment, BillingItem, ClinicUser, Invoice, Payment, Visit, InventoryItem, PharmacyStock
from .utils import generate_invoice_pdf
from .utils.notifications import NotificationCategory, notify_patient, notify_staff


ROLE_LABELS = dict(ClinicUser.ROLE_CHOICES)


def _role_label(value: str) -> str:
    return ROLE_LABELS.get(value, value)


@receiver(post_save, sender=Appointment)
def send_appointment_confirmation(sender, instance, created, **kwargs):
    if not created or not instance.patient.phone:
        return

    clinic_name = settings.CLINIC_INFO.get('name', 'Norha Dental Clinic')
    local_time = instance.scheduled_at.astimezone(timezone.get_current_timezone())
    message = (
        f"Hello {instance.patient.first_name}, your appointment at {clinic_name} "
        f"is confirmed for {local_time.strftime('%Y-%m-%d %H:%M')}"
    )

    notify_patient(
        instance.patient,
        message=message,
        category=NotificationCategory.APPOINTMENT_CONFIRMATION,
        metadata={'appointment_id': instance.id},
    )


@receiver(pre_save, sender=ClinicUser)
def cache_previous_role(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_role = None
        return

    try:
        instance._previous_role = sender.objects.only('role').get(pk=instance.pk).role
    except sender.DoesNotExist:
        instance._previous_role = None


@receiver(post_save, sender=ClinicUser)
def send_staff_onboarding_sms(sender, instance, created, **kwargs):
    if not instance.phone:
        return

    clinic_name = settings.CLINIC_INFO.get('name', 'Norha Dental Clinic')
    role_label = _role_label(instance.role)
    metadata = {'role': instance.role}

    if created:
        username = instance.user.username if instance.user else ''
        message = (
            f"Welcome to {clinic_name}! Your account ({username}) is set up "
            f"with the {role_label} role."
        )
        notify_staff(
            instance,
            message=message,
            category=NotificationCategory.STAFF_ONBOARDING,
            metadata=metadata,
        )
        return

    previous_role = getattr(instance, '_previous_role', None)
    if previous_role and previous_role != instance.role:
        previous_label = _role_label(previous_role)
        message = (
            f"Heads up! Your {clinic_name} role changed from {previous_label} to {role_label}."
        )
        notify_staff(
            instance,
            message=message,
            category=NotificationCategory.STAFF_ONBOARDING,
            metadata={**metadata, 'previous_role': previous_role},
        )


@receiver(post_save, sender=Payment)
def generate_pdf_after_payment(sender, instance, created, **kwargs):
    if not created:
        return  # Only trigger when payment is NEW

    invoice = instance.invoice

    total = sum(
        (item.qty or 0) * float(item.price_private_snapshot or 0)
        for item in invoice.visit.billing_items.all()
    )

    invoice.total_private = total
    invoice.paid = True
    invoice.save()

    pdf_content = generate_invoice_pdf(invoice)
    filename = f"invoice_{invoice.id}.pdf"
    invoice.pdf_file.save(filename, ContentFile(pdf_content))
    invoice.save()


@receiver(post_save, sender=BillingItem)
def maybe_create_invoice_on_billing(sender, instance, created, **kwargs):
    visit = instance.visit
    invoice, _ = Invoice.objects.get_or_create(
        visit=visit,
        defaults={'receipt_number': get_random_string(12)}
    )

    total_private = 0
    total_insurance = 0
    for it in visit.billing_items.all():
        total_private += (it.price_private_snapshot or 0) * it.qty
        total_insurance += (it.price_insurance_snapshot or 0) * it.qty
    invoice.total_private = total_private
    invoice.total_insurance = total_insurance
    invoice.save()


@receiver(post_save, sender=Invoice)
def generate_pdf_on_invoice_update(sender, instance, created, **kwargs):
    # PDF generation disabled - requires GTK libraries on Windows
    # Will be generated manually when needed
    pass


@receiver(post_save, sender=InventoryItem)
def create_pharmacy_stock_for_medicine(sender, instance, created, **kwargs):
    """
    Automatically create PharmacyStock entry when a medicine is added to inventory
    """
    if instance.category == 'medicine':
        # Check if PharmacyStock already exists for this item
        if not PharmacyStock.objects.filter(item=instance).exists():
            PharmacyStock.objects.create(
                item=instance,
                qty_available=0,
                unit_price=instance.unit_cost
            )
