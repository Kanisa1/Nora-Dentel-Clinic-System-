from django.core.management.base import BaseCommand

from clinic import cron


class Command(BaseCommand):
    help = 'Send appointment reminders, birthday wishes, and holiday greetings via SMS'

    def handle(self, *args, **options):
        tasks = [
            ('appointment reminders', cron.appointment_reminder),
            ('birthday wishes', cron.birthday_wishes),
            ('holiday wishes', cron.holiday_wishes),
        ]

        summary = []
        for label, func in tasks:
            try:
                func()
                summary.append(f"{label}: OK")
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"{label}: {exc}"))
                summary.append(f"{label}: FAILED")

        self.stdout.write(" | ".join(summary))
