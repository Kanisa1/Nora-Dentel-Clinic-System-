from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinic", "0007_refund"),
    ]

    operations = [
        migrations.AddField(
            model_name="triage",
            name="respiratory_rate",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
