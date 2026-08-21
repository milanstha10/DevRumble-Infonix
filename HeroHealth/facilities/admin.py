from django.contrib import admin
from .models import HealthcareFacility

@admin.register(HealthcareFacility)
class HealthcareFacilityAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'address', 'phone', 'status']
    search_fields = ['name', 'address', 'specializations_raw']
    list_filter = ['type', 'status']
