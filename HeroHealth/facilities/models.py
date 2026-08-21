from django.db import models

class HealthcareFacility(models.Model):
    TYPE_CHOICES = [
        ('Hospital', 'Hospital'),
        ('Clinic', 'Clinic'),
        ('Health Post', 'Health Post'),
        ('Pharmacy', 'Pharmacy'),
    ]
    
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Busy', 'Busy'),
        ('Emergency Only', 'Emergency Only'),
    ]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True, null=True)
    website = models.URLField(max_length=200, blank=True, null=True)
    specializations_raw = models.TextField(help_text="Comma-separated specializations or doctor services")
    latitude = models.FloatField()
    longitude = models.FloatField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Available')

    @property
    def specializations_list(self):
        if not self.specializations_raw:
            return []
        return [s.strip() for s in self.specializations_raw.split(',') if s.strip()]

    def __str__(self):
        return f"{self.name} ({self.type})"
