# clinic/models_medical_records.py
from django.db import models
from .models import Visit, Patient, ClinicUser, Department

class MedicalRecord(models.Model):
    """Comprehensive medical record for each visit"""
    visit = models.OneToOneField(Visit, on_delete=models.CASCADE, related_name='medical_record')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 1. Chief Complaint
    chief_complaint = models.TextField(blank=True, null=True, help_text="Main reason for visit")
    
    # 2. History of Presenting Illness
    history_presenting_illness = models.TextField(blank=True, null=True, 
        help_text="Detailed history of current condition")
    
    # 3. Past Medical and Dental History
    past_medical_history = models.TextField(blank=True, null=True,
        help_text="Previous medical conditions, surgeries, hospitalizations")
    past_dental_history = models.TextField(blank=True, null=True,
        help_text="Previous dental treatments, procedures")
    current_medications = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    
    # 4. Social and Family History
    social_history = models.TextField(blank=True, null=True,
        help_text="Smoking, alcohol, occupation, lifestyle")
    family_history = models.TextField(blank=True, null=True,
        help_text="Family medical/dental conditions")
    
    # 5. Review of Systems
    review_of_systems = models.TextField(blank=True, null=True,
        help_text="Systematic review of body systems")
    
    # 6. General Medical and Dental Examination
    general_examination = models.TextField(blank=True, null=True,
        help_text="General appearance, vital signs, overall health")
    oral_examination = models.TextField(blank=True, null=True,
        help_text="Oral cavity examination findings")
    
    # 7. Dental and Medical Specialty Examination
    specialty_examination = models.TextField(blank=True, null=True,
        help_text="Detailed specialty-specific findings")
    
    # 8. Investigations
    investigations = models.TextField(blank=True, null=True,
        help_text="Lab results, radiograph findings")
    
    # 9. Diagnosis
    diagnosis = models.TextField(blank=True, null=True,
        help_text="Clinical diagnosis")
    
    # 10. Treatment Plan
    treatment_plan = models.TextField(blank=True, null=True,
        help_text="Proposed treatment and management")
    
    # 11. HMIS/IDSR Classification
    hmis_classification = models.CharField(max_length=10, blank=True, null=True,
        help_text="HMIS disease code")
    idsr_disease = models.CharField(max_length=100, blank=True, null=True,
        choices=[
            ('AFP', 'Acute Flaccid Paralysis'),
            ('MEASLES', 'Measles'),
            ('NEONATAL_TETANUS', 'Neonatal Tetanus'),
            ('YELLOW_FEVER', 'Yellow Fever'),
            ('VIRAL_HEMORRHAGIC', 'Viral Hemorrhagic Fever'),
            ('CHOLERA', 'Cholera'),
            ('MENINGITIS', 'Meningitis'),
            ('RABIES', 'Rabies'),
            ('ANTHRAX', 'Anthrax'),
            ('PLAGUE', 'Plague'),
            ('TYPHOID', 'Typhoid Fever'),
            ('MALARIA', 'Malaria'),
            ('HIV', 'HIV/AIDS'),
            ('TB', 'Tuberculosis'),
            ('COVID19', 'COVID-19'),
            ('MPOX', 'Mpox'),
            ('OTHER', 'Other'),
        ]
    )
    
    def __str__(self):
        return f"Medical Record - Visit {self.visit.id} - {self.visit.patient}"


class MedicalRecordAttachment(models.Model):
    """Attachments for medical records (photos, documents)"""
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, 
        related_name='attachments')
    file = models.FileField(upload_to='medical_records/%Y/%m/')
    file_type = models.CharField(max_length=50, choices=[
        ('photo', 'Photo'),
        ('xray', 'X-Ray'),
        ('lab_result', 'Lab Result'),
        ('document', 'Document'),
        ('other', 'Other'),
    ])
    description = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(ClinicUser, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.file_type} - {self.medical_record.visit.patient}"


class MedicalCertificate(models.Model):
    """Medical certificates issued by doctors"""
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='certificates')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(ClinicUser, on_delete=models.SET_NULL, null=True,
        limit_choices_to={'role': 'doctor'})
    
    certificate_type = models.CharField(max_length=50, choices=[
        ('fitness', 'Certificate of Fitness'),
        ('sick_leave', 'Sick Leave'),
        ('medical_report', 'Medical Report'),
        ('referral', 'Referral Letter'),
        ('other', 'Other'),
    ])
    
    diagnosis = models.TextField()
    recommendations = models.TextField(blank=True, null=True)
    duration_days = models.IntegerField(blank=True, null=True,
        help_text="Duration for sick leave")
    
    issue_date = models.DateField(auto_now_add=True)
    valid_until = models.DateField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    printed = models.BooleanField(default=False)
    printed_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.certificate_type} - {self.patient} - {self.issue_date}"


class PatientTransfer(models.Model):
    """Transfer patient to another doctor or department"""
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='transfers')
    from_doctor = models.ForeignKey(ClinicUser, on_delete=models.SET_NULL, null=True,
        related_name='transfers_from', limit_choices_to={'role': 'doctor'})
    to_doctor = models.ForeignKey(ClinicUser, on_delete=models.SET_NULL, null=True,
        related_name='transfers_to', limit_choices_to={'role': 'doctor'})
    from_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True,
        related_name='transfers_from')
    to_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True,
        related_name='transfers_to')
    
    reason = models.TextField()
    notes = models.TextField(blank=True, null=True)
    transferred_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Transfer - {self.visit.patient} from {self.from_doctor} to {self.to_doctor}"


# HMIS Classifications
class HMISClassification(models.Model):
    """HMIS Disease Classification codes"""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
