from rest_framework import serializers
from .models import (
    Institution,
    InstitutionDepartment,
    ComplaintCategory,
    ComplaintRecipientConfiguration,
    InstitutionRegistrationRequest,
    AdminAccessRequest,
    StudentOnboardingRequest,
    EmailNotificationLog
)

class InstitutionSerializer(serializers.ModelSerializer):
    can_onboard_students = serializers.BooleanField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    is_suspended = serializers.BooleanField(read_only=True)

    class Meta:
        model = Institution
        fields = [
            'id',
            'code',
            'name',
            'institution_type',
            'official_email',
            'official_address',
            'country',
            'state',
            'city',
            'website',
            'logo',
            'verification_status',
            'is_active',
            'is_verified',
            'is_suspended',
            'can_onboard_students',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'verification_status', 'created_at', 'updated_at', 'can_onboard_students', 'is_verified', 'is_suspended']


class InstitutionDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionDepartment
        fields = [
            'id',
            'institution',
            'name',
            'code',
            'contact_email',
            'is_active',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ComplaintCategorySerializer(serializers.ModelSerializer):
    default_department_name = serializers.CharField(source='default_department.name', read_only=True)

    class Meta:
        model = ComplaintCategory
        fields = [
            'id',
            'institution',
            'name',
            'description',
            'default_department',
            'default_department_name',
            'is_active',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ComplaintRecipientConfigurationSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = ComplaintRecipientConfiguration
        fields = [
            'id',
            'institution',
            'category',
            'category_name',
            'recipient_designation',
            'recipient_name',
            'recipient_address',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InstitutionRegistrationRequestSerializer(serializers.ModelSerializer):
    applicant_email = serializers.CharField(source='applicant_user.email', read_only=True)
    applicant_name = serializers.CharField(source='applicant_user.full_name', read_only=True)

    class Meta:
        model = InstitutionRegistrationRequest
        fields = [
            'id',
            'request_id',
            'institution_name',
            'institution_type',
            'official_email',
            'official_address',
            'state',
            'city',
            'website',
            'contact_person_name',
            'applicant_designation',
            'contact_number',
            'admin_password',
            'verification_document',
            'additional_information',
            'applicant_user',
            'applicant_email',
            'applicant_name',
            'status',
            'rejection_reason',
            'internal_remarks',
            'created_institution',
            'reviewed_by',
            'reviewed_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'request_id',
            'admin_password',
            'applicant_user',
            'status',
            'rejection_reason',
            'created_institution',
            'reviewed_by',
            'reviewed_at',
            'created_at',
            'updated_at'
        ]


class StudentOnboardingRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentOnboardingRequest
        fields = [
            'id',
            'request_id',
            'student_name',
            'student_email',
            'student_user',
            'institution_name',
            'institution_location',
            'institution_website',
            'message',
            'status',
            'admin_notes',
            'reviewed_by',
            'reviewed_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'request_id',
            'student_user',
            'status',
            'reviewed_by',
            'reviewed_at',
            'created_at',
            'updated_at'
        ]


class EmailNotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailNotificationLog
        fields = [
            'id',
            'recipient',
            'subject',
            'email_type',
            'status',
            'error_message',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AdminAccessRequestSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_phone = serializers.SerializerMethodField(read_only=True)
    institution_name = serializers.CharField(source='institution.name', read_only=True)

    def get_user_phone(self, obj):
        if hasattr(obj.user, 'admin_profile') and obj.user.admin_profile and obj.user.admin_profile.phone:
            return obj.user.admin_profile.phone
        return ''

    class Meta:
        model = AdminAccessRequest
        fields = [
            'id',
            'user',
            'user_email',
            'user_name',
            'user_phone',
            'institution',
            'institution_name',
            'designation',
            'department_name',
            'admin_password',
            'status',
            'reviewed_by',
            'reviewed_at',
            'created_at'
        ]
        read_only_fields = ['id', 'user', 'user_phone', 'admin_password', 'status', 'reviewed_by', 'reviewed_at', 'created_at']
