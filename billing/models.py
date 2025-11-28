from django.db import models


class Tariff(models.Model):
    """Model representing a tariff/act with pricing for dental services."""

    DEPARTMENT_CHOICES = [
        ('general', 'General Dentistry'),
        ('orthodontics', 'Orthodontics'),
        ('periodontics', 'Periodontics'),
        ('endodontics', 'Endodontics'),
        ('oral_surgery', 'Oral Surgery'),
        ('pediatric', 'Pediatric Dentistry'),
    ]

    act_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='general')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.act_name} - {self.price}"

    class Meta:
        ordering = ['department', 'act_name']
        verbose_name_plural = 'Tariffs'
