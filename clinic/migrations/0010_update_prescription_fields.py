from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def set_prescription_defaults(apps, schema_editor):
    Prescription = apps.get_model("clinic", "Prescription")
    for prescription in Prescription.objects.select_related("visit"):
        visit = prescription.visit
        prescription.patient = getattr(visit, "patient", None)
        prescription.doctor = getattr(visit, "doctor", None)
        if not prescription.prescription_type:
            prescription.prescription_type = "written"
        if not prescription.created_at:
            prescription.created_at = visit.created_at
        if not prescription.updated_at:
            prescription.updated_at = visit.created_at
        prescription.save(update_fields=[
            "patient",
            "doctor",
            "prescription_type",
            "created_at",
            "updated_at",
        ])


class Migration(migrations.Migration):

    dependencies = [
        ("clinic", "0009_triage_notes"),
    ]

    operations = [
        migrations.AddField(
            model_name="prescription",
            name="patient",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="prescriptions",
                to="clinic.patient",
            ),
        ),
        migrations.AddField(
            model_name="prescription",
            name="doctor",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"role": "doctor"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="issued_prescriptions",
                to="clinic.clinicuser",
            ),
        ),
        migrations.AddField(
            model_name="prescription",
            name="prescription_type",
            field=models.CharField(
                choices=[("written", "Written Prescription"), ("clinic", "Clinic Store Dispense")],
                default="written",
                max_length=20,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="prescription",
            name="instructions",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="prescription",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="prescription",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.RunPython(set_prescription_defaults, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="prescription",
            name="patient",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="prescriptions",
                to="clinic.patient",
            ),
        ),
    ]
