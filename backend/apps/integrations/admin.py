from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'actor', 'institution', 'target_model', 'target_id', 'timestamp')
    list_filter = ('action', 'institution', 'timestamp')
    search_fields = ('action', 'actor__email', 'target_id')
    readonly_fields = ('action', 'actor', 'institution', 'target_model', 'target_id', 'details', 'ip_address', 'timestamp')
