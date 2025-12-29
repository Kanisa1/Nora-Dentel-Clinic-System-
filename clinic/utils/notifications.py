from __future__ import annotations

from copy import deepcopy
from typing import Iterable, List, Optional, Tuple, Union

from django.utils import timezone

from ..models import NotificationLog, Patient, ClinicUser
from .sms import format_phone_number, send_sms


class NotificationCategory:
    GENERAL = 'general'
    APPOINTMENT_CONFIRMATION = 'appointment_confirmation'
    APPOINTMENT_REMINDER = 'appointment_reminder'
    BIRTHDAY = 'birthday_greeting'
    HOLIDAY = 'holiday_greeting'
    STAFF_ONBOARDING = 'staff_onboarding'


Recipient = Union[str, Tuple[str, Optional[str]]]


def _normalize_recipients(recipients: Iterable[Recipient]) -> List[Tuple[str, Optional[str]]]:
    normalized: List[Tuple[str, Optional[str]]] = []
    for entry in recipients:
        if isinstance(entry, tuple):
            phone, name = entry[0], entry[1] if len(entry) > 1 else None
        else:
            phone, name = entry, None
        if not phone:
            continue
        formatted = format_phone_number(str(phone))
        normalized.append((formatted, name))
    return normalized


def send_sms_notification(
    *,
    message: str,
    recipients: Iterable[Recipient],
    category: str = NotificationCategory.GENERAL,
    metadata: Optional[dict] = None,
) -> List[NotificationLog]:
    """Send an SMS message and create NotificationLog rows for auditing."""
    normalized = _normalize_recipients(recipients)
    if not normalized:
        return []

    metadata_copy = deepcopy(metadata) if metadata else None
    logs: List[NotificationLog] = []
    for phone, name in normalized:
        logs.append(
            NotificationLog.objects.create(
                category=category,
                recipient=phone,
                recipient_name=name,
                message=message.strip(),
                metadata=metadata_copy,
            )
        )

    try:
        response = send_sms(message, [phone for phone, _ in normalized])
    except Exception as exc:  # pragma: no cover - provider issues should not halt app
        for log in logs:
            log.status = NotificationLog.STATUS_FAILED
            log.error_message = str(exc)
            log.save(update_fields=['status', 'error_message'])
        return logs

    recipients_data = (
        response.get('SMSMessageData', {}).get('Recipients', [])
        if isinstance(response, dict)
        else []
    )
    response_by_number = {
        format_phone_number(str(item.get('number'))): item
        for item in recipients_data
        if item.get('number')
    }

    sent_at = timezone.now()
    for log in logs:
        response_item = response_by_number.get(log.recipient)
        log.status = NotificationLog.STATUS_SENT
        log.sent_at = sent_at
        if response_item:
            log.provider_message_id = response_item.get('messageId')
            log.response_payload = response_item
        else:
            log.response_payload = response
        log.save(update_fields=['status', 'sent_at', 'provider_message_id', 'response_payload'])

    return logs


def notify_patient(patient: Patient, *, message: str, category: str, metadata: Optional[dict] = None):
    if not patient or not patient.phone:
        return []
    full_name = f"{patient.first_name or ''} {patient.last_name or ''}".strip() or None
    merged_metadata = {**(metadata or {}), 'patient_id': patient.id}
    return send_sms_notification(
        message=message,
        recipients=[(patient.phone, full_name)],
        category=category,
        metadata=merged_metadata,
    )


def notify_staff(clinic_user: ClinicUser, *, message: str, category: str, metadata: Optional[dict] = None):
    if not clinic_user or not clinic_user.phone:
        return []
    name = clinic_user.user.get_full_name() if clinic_user.user else None
    merged_metadata = {**(metadata or {}), 'clinic_user_id': clinic_user.id}
    return send_sms_notification(
        message=message,
        recipients=[(clinic_user.phone, name)],
        category=category,
        metadata=merged_metadata,
    )


__all__ = [
    'NotificationCategory',
    'send_sms_notification',
    'notify_patient',
    'notify_staff',
]
