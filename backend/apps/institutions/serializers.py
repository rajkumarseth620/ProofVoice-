from rest_framework import serializers
from .models import (
    Institution,
    InstitutionDepartment,
    ComplaintCategory,
    ComplaintRecipientConfiguration,
    InstitutionRegistrationRequest,
    AdminAccessRequest
)

class InstitutionSerializer(serializers.ModelSerializer):
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
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'verification_status', 'created_at', 'updated_at']


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
            'institution_name',
            'institution_type',
            'official_email',
            'official_address',
            'state',
            'city',
            'website',
            'applicant_user',
            'applicant_email',
            'applicant_name',
            'applicant_designation',
            'status',
            'rejection_reason',
            'created_institution',
            'reviewed_by',
            'reviewed_at',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'applicant_user',
            'status',
            'rejection_reason',
            'created_institution',
            'reviewed_by',
            'reviewed_at',
            'created_at'
        ]


class AdminAccessRequestSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    institution_name = serializers.CharField(source='institution.name', read_only=True)

    class Meta:
        model = AdminAccessRequest
        fields = [
            'id',
            'user',
            'user_email',
            'user_name',
            'institution',
            'institution_name',
            'designation',
            'department_name',
            'status',
            'reviewed_by',
            'reviewed_at',
            'created_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'reviewed_by', 'reviewed_at', 'created_at']
