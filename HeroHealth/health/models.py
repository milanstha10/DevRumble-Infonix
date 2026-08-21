from django.db import models
from django.contrib.auth.models import User

class Consultation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consultations', blank=True, null=True)
    symptoms = models.TextField()
    image = models.ImageField(upload_to='health_queries/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    result_json = models.JSONField(blank=True, null=True)

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"Consultation by {user_str} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
