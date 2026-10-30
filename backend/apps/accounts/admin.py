from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StudentProfile, AdministratorProfile

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Student Profile'
    fk_name = 'user'

class AdministratorProfileInline(admin.StackedInline):
    model = AdministratorProfile
    can_delete = False
    verbose_name_plural = 'Administrator Profile'
    fk_name = 'user'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'role', 'is_active', 'is_verified', 'created_at')
    list_filter = ('role', 'is_active', 'is_verified', 'created_at')
    search_fields = ('email', 'full_name')
    ordering = ('-created_at',)
    inlines = (StudentProfileInline, AdministratorProfileInline)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name',)}),
        ('Permissions & Role', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'is_verified')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at', 'last_login')

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'institution', 'department', 'course', 'is_profile_complete')
    list_filter = ('institution', 'department', 'is_profile_complete')
    search_fields = ('user__email', 'user__full_name', 'student_id')

@admin.register(AdministratorProfile)
class AdministratorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution', 'designation', 'approval_status', 'approved_by', 'approved_at')
    list_filter = ('approval_status', 'institution')
    search_fields = ('user__email', 'user__full_name', 'designation')
    actions = ['approve_selected_administrators']

    def approve_selected_administrators(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            approval_status=AdministratorProfile.ApprovalStatus.APPROVED,
            approved_by=request.user,
            approved_at=timezone.now()
        )
    approve_selected_administrators.short_description = "Approve selected administrator accounts"
