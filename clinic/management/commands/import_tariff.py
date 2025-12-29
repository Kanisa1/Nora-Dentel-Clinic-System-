from django.core.management.base import BaseCommand
import pandas as pd
from clinic.models import TariffAct, Department

class Command(BaseCommand):
    help = 'Import tariff from xlsx'

    def add_arguments(self, parser):
        parser.add_argument('xlsx_path', type=str)

    def handle(self, *args, **options):
        path = options['xlsx_path']
        df = pd.read_excel(path)
        # normalize columns
        cols = {c.lower().strip(): c for c in df.columns}
        def get(colnames, row):
            for c in colnames:
                key = c.lower().strip()
                if key in cols:
                    return row[cols[key]]
            return None
        for _, row in df.iterrows():
            code = get(['code','code ' ,'act code'], row) or ''
            name = get(['name','act','description'], row) or ''
            price_private = get(['price_private','amount','price','price private'], row) or 0
            price_insurance = get(['price_insurance','insurance price','price insurance'], row) or 0
            dept_name = get(['department','dept'], row) or 'General'
            if not code or not name:
                continue
            dept, _ = Department.objects.get_or_create(name=str(dept_name))
            TariffAct.objects.update_or_create(code=str(code).strip(), defaults={
                'name': str(name).strip(),
                'department': dept,
                'price_private': price_private,
                'price_insurance': price_insurance or 0,
                'active': True
            })
        self.stdout.write(self.style.SUCCESS(f'Imported tariffs from {path}'))
