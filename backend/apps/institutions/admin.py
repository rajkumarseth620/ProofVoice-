from django.contrib import admin
from .models import (
    Institution,
    InstitutionDepartment,
    ComplaintCategory,
    ComplaintRecipientConfiguration,
    InstitutionRegistrationRequest,
    AdminAccessRequest
)

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'institution_type', 'city', 'state', 'verification_status', 'is_active')
    list_filter = ('verification_status', 'institution_type', 'is_active', 'state')
    search_fields = ('name', 'code', 'official_email', 'city')
    prepopulated_fields = {'code': ('name',)}

@admin.register(InstitutionDepartment)
class InstitutionDepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'institution', 'contact_email', 'is_active')
    list_filter = ('institution', 'is_active')
    search_fields = ('name', 'code', 'institution__name')

@admin.register(ComplaintCategory)
class ComplaintCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution', 'default_department', 'is_active')
    list_filter = ('institution', 'is_active')
    search_fields = ('name', 'institution__name')

@admin.register(ComplaintRecipientConfiguration)
class ComplaintRecipientConfigurationAdmin(admin.ModelAdmin):
    list_display = ('institution', 'category', 'recipient_designation', 'recipient_name')
    list_filter = ('institution',)
    search_fields = ('institution__name', 'recipient_designation', 'recipient_name')

@admin.register(InstitutionRegistrationRequest)
class InstitutionRegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ('institution_name', 'applicant_user', 'status', 'reviewed_by', 'created_at')
    list_filter = ('status', 'institution_type')
    search_fields = ('institution_name', 'applicant_user__email', 'official_email')

@admin.register(AdminAccessRequest)
class AdminAccessRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution', 'designation', 'status', 'reviewed_by', 'created_at')
    list_filter = ('status', 'institution')
    search_fields = ('user__email', 'institution__name', 'designation')
