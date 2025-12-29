from datetime import timedelta

from django.conf import settings
from django.utils.timezone import now

from .models import Appointment, Patient
from .utils.notifications import NotificationCategory, notify_patient, send_sms_notification

# 1️⃣ Appointment Reminder (24 hours before)
def appointment_reminder():
    tomorrow = now() + timedelta(days=1)
    start = tomorrow.replace(hour=0, minute=0)
    end = tomorrow.replace(hour=23, minute=59)

    appointments = Appointment.objects.filter(
        scheduled_at__range=(start, end),
        status="scheduled"
    )

    clinic_name = settings.CLINIC_INFO.get('name', 'Norha Dental Clinic')

    tzinfo = now().tzinfo

    for appt in appointments.select_related('patient'):
        if not appt.patient.phone:
            continue
        local_time = appt.scheduled_at.astimezone(tzinfo) if tzinfo else appt.scheduled_at
        msg = (
            f"Reminder: {clinic_name} appointment tomorrow at {local_time.strftime('%H:%M')}.")
        notify_patient(
            appt.patient,
            message=msg,
            category=NotificationCategory.APPOINTMENT_REMINDER,
            metadata={'appointment_id': appt.id, 'scheduled_at': appt.scheduled_at.isoformat()},
        )

# 2️⃣ Birthday Wishes
def birthday_wishes():
    today = now().date()
    patients = Patient.objects.filter(dob__month=today.month, dob__day=today.day)

    clinic_name = settings.CLINIC_INFO.get('name', 'Norha Dental Clinic')

    for p in patients:
        if not p.phone:
            continue
        msg = f"Happy Birthday {p.first_name or ''}! {clinic_name} wishes you good health!"
        notify_patient(
            p,
            message=msg,
            category=NotificationCategory.BIRTHDAY,
            metadata={'patient_id': p.id, 'dob': p.dob.isoformat() if p.dob else None},
        )

# 3️⃣ Holiday Wishes
def holiday_wishes():
    today = now().strftime("%m-%d")

    holidays = {
        "12-25": "Merry Christmas 🎄!",
        "01-01": "Happy New Year 🎉!",
        "07-04": "Happy Liberation Day Rwanda 🇷🇼!",
        # Add more holidays if you want
    }

    if today in holidays:
        message = holidays[today]
        patients = Patient.objects.exclude(phone__isnull=True).exclude(phone__exact='')

        send_sms_notification(
            message=message,
            recipients=[(p.phone, f"{p.first_name} {p.last_name}".strip()) for p in patients],
            category=NotificationCategory.HOLIDAY,
            metadata={'holiday': today},
        )
