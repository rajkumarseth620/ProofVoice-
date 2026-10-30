from django.contrib import admin
from .models import Complaint, ComplaintStatusHistory, ComplaintAttachment

class ComplaintStatusHistoryInline(admin.TabularInline):
    model = ComplaintStatusHistory
    extra = 0
    readonly_fields = ('previous_status', 'new_status', 'changed_by', 'timestamp')

class ComplaintAttachmentInline(admin.TabularInline):
    model = ComplaintAttachment
    extra = 0
    readonly_fields = ('file_name', 'file_size', 'mime_type', 'uploaded_by', 'created_at')

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        'complaint_id',
        'title',
        'institution',
        'student',
        'status',
        'priority',
        'category',
        'assigned_department',
        'created_at'
    )
    list_filter = ('status', 'priority', 'institution', 'category', 'assigned_department')
    search_fields = ('complaint_id', 'title', 'student__email', 'student__full_name', 'original_description')
    readonly_fields = ('complaint_id', 'created_at', 'last_updated_at')
    inlines = [ComplaintStatusHistoryInline, ComplaintAttachmentInline]

@admin.register(ComplaintStatusHistory)
class ComplaintStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'previous_status', 'new_status', 'changed_by', 'timestamp')
    list_filter = ('new_status', 'complaint__institution')
    search_fields = ('complaint__complaint_id', 'changed_by__email')

@admin.register(ComplaintAttachment)
class ComplaintAttachmentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'complaint', 'file_size', 'uploaded_by', 'created_at')
    search_fields = ('file_name', 'complaint__complaint_id')
