import csv
from decimal import Decimal
from django.core.management.base import BaseCommand
from clinic.models import TariffAct, BillingItem

CSV_PATH = 'assets/new - NEW TALLIF RAMA & PRIVATE INSURANCE.csv'

class Command(BaseCommand):
    help = 'Replace all TariffAct entries with those from the new CSV tariff.'

    def handle(self, *args, **options):
        self.stdout.write('Deleting all BillingItem records...')
        BillingItem.objects.all().delete()
        self.stdout.write('Deleting all existing TariffAct entries...')
        TariffAct.objects.all().delete()
        self.stdout.write('Importing new tariff acts from CSV...')
        with open(CSV_PATH, encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            # Skip header rows
            for _ in range(2):
                next(reader)
            for row in reader:
                if len(row) < 4:
                    continue
                code = row[0].strip()
                name = row[1].strip()
                price_ins = row[2].replace(',', '').replace('"', '').strip()
                price_priv = row[3].replace(',', '').replace('"', '').strip()
                # Skip rows with no code or name
                if not code or not name:
                    continue
                # Handle missing/invalid prices
                try:
                    price_ins_val = Decimal(price_ins) if price_ins and price_ins != '-' else None
                except Exception:
                    price_ins_val = None
                try:
                    price_priv_val = Decimal(price_priv) if price_priv and price_priv != '-' else None
                except Exception:
                    price_priv_val = None
                TariffAct.objects.create(
                    code=code,
                    name=name,
                    price_insurance=price_ins_val or 0,
                    price_private=price_priv_val or 0,
                    department=None,
                    active=True
                )
        self.stdout.write(self.style.SUCCESS('Tariff acts replaced successfully!'))
