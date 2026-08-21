from django.contrib import admin
from .models import Consultation

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'get_severity']
    search_fields = ['symptoms']
    list_filter = ['created_at']

    def get_severity(self, obj):
        if obj.result_json:
            return obj.result_json.get('severity', 'N/A')
        return 'N/A'
    get_severity.short_description = 'Severity'
