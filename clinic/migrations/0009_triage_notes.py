from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinic", "0008_triage_respiratory_rate"),
    ]

    operations = [
        migrations.AddField(
            model_name="triage",
            name="notes",
            field=models.TextField(blank=True, null=True),
        ),
    ]
