from django.db import models


class Patient(models.Model):
    """Model representing a patient in the dental clinic."""

    DEPARTMENT_CHOICES = [
        ('general', 'General Dentistry'),
        ('orthodontics', 'Orthodontics'),
        ('periodontics', 'Periodontics'),
        ('endodontics', 'Endodontics'),
        ('oral_surgery', 'Oral Surgery'),
        ('pediatric', 'Pediatric Dentistry'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    insurance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='general')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ['-created_at']
