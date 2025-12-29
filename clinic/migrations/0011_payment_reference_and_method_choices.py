from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0010_update_prescription_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='reference',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='method',
            field=models.CharField(choices=[
                ('cash', 'Cash'),
                ('momo', 'Mobile Money'),
                ('card', 'ATM Card'),
                ('insurance', 'Insurance'),
            ], max_length=32),
        ),
    ]
