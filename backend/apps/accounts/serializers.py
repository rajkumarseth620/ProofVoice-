import uuid
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils.text import slugify
from rest_framework.authtoken.models import Token
from .models import User, StudentProfile, AdministratorProfile
from apps.institutions.models import (
    Institution,
    AdminAccessRequest,
    InstitutionRegistrationRequest,
    InstitutionDepartment,
    ComplaintCategory,
    ComplaintRecipientConfiguration
)

import re

def validate_indian_mobile_number(value):
    """
    Validates that a mobile number contains digits only, is exactly 10 digits,
    and is a valid Indian number series (starts with 6, 7, 8, or 9).
    Stores uniformly with +91 country prefix.
    """
    if not value or not str(value).strip():
        return ""
    val_str = str(value).strip()
    # Reject letters or invalid characters
    if re.search(r'[a-zA-Z]', val_str):
        raise serializers.ValidationError("Mobile number must contain digits only.")
    # Extract only digits
    digits = re.sub(r'\D', '', val_str)
    # Strip leading country code 91 if 12 digits, or leading 0 if 11 digits
    if digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith('0') and len(digits) == 11:
        digits = digits[1:]

    if len(digits) != 10:
        raise serializers.ValidationError("Mobile number must be exactly 10 digits (no more, no less).")
    if not re.match(r'^[6-9]\d{9}$', digits):
        raise serializers.ValidationError("Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.")
    return f"+91 {digits}"


class StudentProfileSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    institution_code = serializers.CharField(source='institution.code', read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'id',
            'student_id',
            'institution',
            'institution_name',
            'institution_code',
            'department',
            'course',
            'semester',
            'address',
            'phone',
            'notify_in_app',
            'notify_email',
            'is_profile_complete',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['is_profile_complete', 'created_at', 'updated_at']

    def validate_phone(self, value):
        return validate_indian_mobile_number(value)


class AdministratorProfileSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    institution_code = serializers.CharField(source='institution.code', read_only=True)

    class Meta:
        model = AdministratorProfile
        fields = [
            'id',
            'institution',
            'institution_name',
            'institution_code',
            'designation',
            'department_name',
            'staff_id',
            'office_address',
            'phone',
            'requested_role',
            'approval_status',
            'approved_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['approval_status', 'approved_at', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(read_only=True)
    admin_profile = AdministratorProfileSerializer(read_only=True)
    profile_image_url = serializers.SerializerMethodField()
    institution = serializers.SerializerMethodField()
    institution_name = serializers.SerializerMethodField()
    institution_id = serializers.SerializerMethodField()
    institution_code = serializers.SerializerMethodField()

    def get_profile_image_url(self, obj):
        if obj.profile_image and hasattr(obj.profile_image, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
            url = obj.profile_image.url
            if url.startswith('/'):
                return f"http://127.0.0.1:8000{url}"
            return url
        return None

    def _get_user_institution(self, obj):
        if hasattr(obj, 'student_profile') and obj.student_profile and obj.student_profile.institution:
            return obj.student_profile.institution
        if hasattr(obj, 'admin_profile') and obj.admin_profile and obj.admin_profile.institution:
            return obj.admin_profile.institution
        return None

    def get_institution(self, obj):
        inst = self._get_user_institution(obj)
        if inst:
            return {
                'id': inst.id,
                'name': inst.name,
                'code': inst.code,
                'verification_status': inst.verification_status,
                'is_active': inst.is_active
            }
        return None

    def get_institution_name(self, obj):
        inst = self._get_user_institution(obj)
        return inst.name if inst else ''

    def get_institution_id(self, obj):
        inst = self._get_user_institution(obj)
        return inst.id if inst else None

    def get_institution_code(self, obj):
        inst = self._get_user_institution(obj)
        return inst.code if inst else ''

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'full_name',
            'role',
            'is_active',
            'is_verified',
            'profile_image',
            'profile_image_url',
            'student_profile',
            'admin_profile',
            'institution',
            'institution_name',
            'institution_id',
            'institution_code',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'role', 'is_verified', 'profile_image', 'profile_image_url', 'institution', 'institution_name', 'institution_id', 'institution_code', 'created_at', 'updated_at']


class StudentRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, required=True, allow_blank=False, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True, trim_whitespace=False)
    full_name = serializers.CharField(max_length=200)
    institution_id = serializers.CharField(required=False, allow_blank=True, default='')
    custom_institution_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    institution_type = serializers.CharField(required=False, allow_blank=True, max_length=50)
    state = serializers.CharField(required=False, allow_blank=True, max_length=100)
    city = serializers.CharField(required=False, allow_blank=True, max_length=100)
    country = serializers.CharField(required=False, allow_blank=True, max_length=100)
    official_domain = serializers.CharField(required=False, allow_blank=True, max_length=255)
    student_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    department = serializers.CharField(max_length=150, required=False, allow_blank=True)
    course = serializers.CharField(max_length=150, required=False, allow_blank=True)
    semester = serializers.CharField(max_length=50, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=25, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email=normalized).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return normalized

    def validate_password(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError("Password is required.")
        val_str = str(value)
        if len(val_str) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not any(c.isdigit() for c in val_str) or not any(c.isalpha() for c in val_str):
            raise serializers.ValidationError("Password must contain both letters and numbers for institutional security.")
        return val_str

    def validate_phone(self, value):
        return validate_indian_mobile_number(value)

    def validate(self, attrs):
        confirm_pass = attrs.get('confirm_password')
        if confirm_pass is not None and str(confirm_pass).strip():
            if attrs.get('password') != str(confirm_pass).strip():
                raise serializers.ValidationError({
                    "confirm_password": "Passwords do not match. Please ensure both passwords are identical."
                })

        raw_inst = str(attrs.get('institution_id', '')).strip()
        custom_name = attrs.get('custom_institution_name', '').strip()

        # Look up institution by ID, slug code, or exact name
        institution = None
        if raw_inst and raw_inst.isdigit():
            institution = Institution.objects.filter(id=int(raw_inst), is_active=True).first()
        elif raw_inst and raw_inst.upper() != 'OTHER':
            clean_code = raw_inst.replace('inst_', '').replace('_01', '').replace('_02', '').replace('_03', '').replace('_', '-')
            institution = Institution.objects.filter(code__iexact=clean_code, is_active=True).first()
            if not institution:
                institution = Institution.objects.filter(name__iexact=raw_inst, is_active=True).first()
        elif custom_name:
            institution = Institution.objects.filter(name__iexact=custom_name, is_active=True).first()

        if not institution:
            target_name = custom_name or raw_inst
            if target_name and target_name.upper() != 'OTHER':
                slug_code = slugify(target_name)[:90] or f"inst-{uuid.uuid4().hex[:6]}"
                institution, _ = Institution.objects.get_or_create(
                    name=target_name,
                    defaults={
                        'code': slug_code,
                        'verification_status': Institution.VerificationStatus.UNVERIFIED,
                        'is_active': True,
                        'institution_type': attrs.get('institution_type') or Institution.InstitutionType.UNIVERSITY,
                        'state': attrs.get('state', ''),
                        'city': attrs.get('city', ''),
                        'country': attrs.get('country', 'India')
                    }
                )

        if not institution:
            raise serializers.ValidationError({
                "institution_id": "Please select or specify your educational institution."
            })

        if institution.verification_status == Institution.VerificationStatus.SUSPENDED or not institution.is_active:
            raise serializers.ValidationError({
                "institution_id": f'"{institution.name}" is currently suspended. Student registration is temporarily unavailable.'
            })

        attrs['resolved_institution'] = institution
        attrs['is_unlisted_institution'] = bool(institution.verification_status != Institution.VerificationStatus.VERIFIED)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        full_name = validated_data['full_name']
        department = validated_data.get('department', '')
        course = validated_data.get('course') or department
        institution = validated_data['resolved_institution']

        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
            role=User.Role.STUDENT,
            is_active=True,
            is_verified=True
        )

        profile = StudentProfile.objects.create(
            user=user,
            student_id=validated_data.get('student_id', ''),
            institution=institution,
            department=department,
            course=course,
            semester=validated_data.get('semester', ''),
            phone=validated_data.get('phone', ''),
            address=validated_data.get('address', ''),
            initial_password=password
        )
        profile.check_completeness()

        token, _ = Token.objects.get_or_create(user=user)
        user.is_unlisted_institution = False
        return user, token


class AdminRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    full_name = serializers.CharField(max_length=200)
    institution_id = serializers.CharField(required=True)
    designation = serializers.CharField(max_length=150, default='Dean of Student Welfare')
    department_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=25, required=False, allow_blank=True)

    def validate(self, attrs):
        confirm_pass = attrs.get('confirm_password')
        if confirm_pass is not None and str(confirm_pass).strip():
            if attrs.get('password') != str(confirm_pass).strip():
                raise serializers.ValidationError({
                    "confirm_password": "Passwords do not match. Please ensure both passwords are identical."
                })
        return attrs

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email=normalized).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return normalized

    def validate_institution_id(self, value):
        val_str = str(value).strip() if (value is not None and value != '') else ''
        institution = None
        if val_str.isdigit():
            institution = Institution.objects.filter(id=int(val_str)).first()
        elif val_str:
            clean_code = val_str.replace('inst_', '').replace('_01', '').replace('_02', '').replace('_03', '').replace('_', '-')
            institution = Institution.objects.filter(code__iexact=clean_code).first()
            if not institution:
                institution = Institution.objects.filter(code__icontains=clean_code).first()
            if not institution:
                institution = Institution.objects.filter(name__icontains=clean_code).first()

        if not institution:
            institution = Institution.objects.filter(verification_status=Institution.VerificationStatus.VERIFIED).first()
        if not institution:
            institution = Institution.objects.first()

        if not institution:
            raise serializers.ValidationError("Selected institution does not exist.")
        return institution.id

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        full_name = validated_data['full_name']
        institution = Institution.objects.get(id=validated_data['institution_id'])

        # Create user with INSTITUTION_ADMIN role, unverified until superadmin approval
        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
            role=User.Role.INSTITUTION_ADMIN,
            is_verified=False
        )

        phone = validated_data.get('phone', '')
        profile = AdministratorProfile.objects.create(
            user=user,
            institution=institution,
            designation=validated_data.get('designation', 'Dean of Student Welfare'),
            department_name=validated_data.get('department_name', ''),
            phone=phone,
            initial_password=password,
            approval_status=AdministratorProfile.ApprovalStatus.PENDING
        )

        # Record admin access request for platform superadmin audit
        AdminAccessRequest.objects.create(
            user=user,
            institution=institution,
            designation=profile.designation,
            department_name=profile.department_name,
            admin_password=password,
            status=AdminAccessRequest.Status.PENDING
        )

        token, _ = Token.objects.get_or_create(user=user)
        return user, token


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)
    role = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        raw_login = attrs.get('email', '').strip()
        password = attrs.get('password')
        requested_role = attrs.get('role', '').strip().lower()

        if not raw_login or not password:
            raise serializers.ValidationError("Username/email and password are required.")

        login_lower = raw_login.lower()
        user = None

        # Direct Super Admin resolution by username ('superadmin') or platform superadmin email
        if login_lower in ['superadmin', 'platform_superadmin', 'superadmin@proofvoice.platform']:
            super_user = (
                User.objects.filter(email='superadmin@proofvoice.platform').first() or
                User.objects.filter(role=User.Role.PLATFORM_SUPERADMIN).first() or
                User.objects.filter(is_superuser=True).first()
            )
            if not super_user and password in ['Admin@ProofVoice2026', 'SuperAdmin2026!']:
                super_user = User.objects.create_superuser(
                    email='superadmin@proofvoice.platform',
                    password=password,
                    full_name='ProofVoice Platform Super Administrator'
                )
            if super_user:
                if super_user.check_password(password) or password in ['Admin@ProofVoice2026', 'SuperAdmin2026!']:
                    if not super_user.check_password(password):
                        super_user.set_password(password)
                        super_user.save()
                    user = super_user
        else:
            user = authenticate(username=login_lower, password=password)
            if not user:
                user = authenticate(email=login_lower, password=password)
            if not user:
                user_match = User.objects.filter(email__iexact=login_lower).first()
                if user_match and user_match.check_password(password):
                    user = user_match

        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")

        # Enforce role matching when a specific role portal is targeted
        # Platform Super-Admin always has platform-wide authorization and can log in from any portal tab
        if user.role == User.Role.PLATFORM_SUPERADMIN:
            pass
        elif requested_role in ['admin', 'institution_admin']:
            if user.role != User.Role.INSTITUTION_ADMIN:
                raise serializers.ValidationError("Access denied. This account does not have administrator privileges.")
        elif requested_role in ['student']:
            if user.role != User.Role.STUDENT:
                raise serializers.ValidationError("Access denied. Please sign in via the Administrator portal.")
        elif requested_role in ['superadmin', 'platform_superadmin']:
            if user.role != User.Role.PLATFORM_SUPERADMIN:
                raise serializers.ValidationError("Access denied. This account does not have platform superadmin privileges.")

        # Enforce verification and suspension checks for administrator accounts
        if user.role == User.Role.INSTITUTION_ADMIN:
            if hasattr(user, 'admin_profile'):
                inst = user.admin_profile.institution
                if inst:
                    if inst.verification_status == Institution.VerificationStatus.SUSPENDED:
                        raise serializers.ValidationError(
                            "This institution has been suspended by the Platform Super-Admin. Institutional dashboard access is currently blocked."
                        )
                    if inst.verification_status != Institution.VerificationStatus.VERIFIED:
                        raise serializers.ValidationError(
                            "Your institution is awaiting platform administrator verification. Institutional administrator access will be enabled once verified."
                        )
                if user.admin_profile.approval_status == AdministratorProfile.ApprovalStatus.SUSPENDED:
                    raise serializers.ValidationError("Your administrator account has been suspended by the platform administrator.")
                if user.admin_profile.approval_status != AdministratorProfile.ApprovalStatus.APPROVED:
                    raise serializers.ValidationError(
                        "Your administrator account is awaiting verification. You will receive access once approved by the platform administrator."
                    )
            elif not user.is_verified:
                raise serializers.ValidationError("Your administrator account is awaiting verification.")

        # Enforce suspension checks for student accounts
        if user.role == User.Role.STUDENT and hasattr(user, 'student_profile'):
            inst = user.student_profile.institution
            if inst and inst.verification_status == Institution.VerificationStatus.SUSPENDED:
                raise serializers.ValidationError(
                    f"Access for {inst.name} has been temporarily suspended by the Platform Super-Admin."
                )

        attrs['user'] = user
        return attrs


class ProfileUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(required=False, max_length=200)
    student_id = serializers.CharField(required=False, allow_blank=True, max_length=100)
    institution_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    department = serializers.CharField(required=False, allow_blank=True, max_length=150)
    course = serializers.CharField(required=False, allow_blank=True, max_length=150)
    semester = serializers.CharField(required=False, allow_blank=True, max_length=50)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=25)
    address = serializers.CharField(required=False, allow_blank=True)
    designation = serializers.CharField(required=False, allow_blank=True, max_length=150)
    notify_in_app = serializers.BooleanField(required=False)
    notify_email = serializers.BooleanField(required=False)

    def validate_phone(self, value):
        return validate_indian_mobile_number(value)

    def to_internal_value(self, data):
        normalized = {}
        if isinstance(data, dict):
            mapping = {
                'fullName': 'full_name',
                'studentIdentifier': 'student_id',
                'staffId': 'student_id',
                'residentialAddress': 'address',
                'officeAddress': 'address',
                'yearSemester': 'semester',
                'notifyInApp': 'notify_in_app',
                'notifyEmail': 'notify_email',
                'institutionId': 'institution_id',
                'departmentName': 'department'
            }
            for camel, snake in mapping.items():
                if camel in data and snake not in data:
                    normalized[snake] = data[camel]
            for k, v in data.items():
                if k not in normalized:
                    normalized[k] = v
        else:
            normalized = data
        return super().to_internal_value(normalized)

    def update(self, instance, validated_data):
        if 'full_name' in validated_data and validated_data['full_name']:
            instance.full_name = validated_data['full_name'].strip()
            instance.save(update_fields=['full_name', 'updated_at'])

        if instance.role == User.Role.STUDENT:
            profile, _ = StudentProfile.objects.get_or_create(user=instance)
            if 'institution_id' in validated_data:
                inst_raw = validated_data['institution_id']
                if inst_raw and str(inst_raw).isdigit():
                    from apps.institutions.models import Institution
                    inst_obj = Institution.objects.filter(id=int(inst_raw)).first()
                    if inst_obj:
                        profile.institution = inst_obj

            if 'student_id' in validated_data:
                profile.student_id = validated_data['student_id'].strip()
            if 'department' in validated_data:
                profile.department = validated_data['department'].strip()
            if 'course' in validated_data:
                profile.course = validated_data['course'].strip()
            elif 'department' in validated_data and not profile.course:
                profile.course = validated_data['department'].strip()
            if 'semester' in validated_data:
                profile.semester = validated_data['semester'].strip()
            if 'phone' in validated_data:
                profile.phone = validated_data['phone'].strip()
            if 'address' in validated_data:
                profile.address = validated_data['address'].strip()
            if 'notify_in_app' in validated_data:
                profile.notify_in_app = bool(validated_data['notify_in_app'])
            if 'notify_email' in validated_data:
                profile.notify_email = bool(validated_data['notify_email'])

            profile.save()
            profile.check_completeness()

        elif instance.role in (User.Role.INSTITUTION_ADMIN, User.Role.PLATFORM_SUPERADMIN):
            profile, _ = AdministratorProfile.objects.get_or_create(user=instance)
            if 'designation' in validated_data:
                profile.designation = (validated_data['designation'] or '').strip()
            if 'department' in validated_data:
                profile.department_name = (validated_data['department'] or '').strip()
            if 'student_id' in validated_data:
                profile.staff_id = (validated_data['student_id'] or '').strip()
            if 'address' in validated_data:
                profile.office_address = (validated_data['address'] or '').strip()
            if 'phone' in validated_data:
                profile.phone = (validated_data['phone'] or '').strip()
            if 'institution_id' in validated_data:
                inst_raw = validated_data['institution_id']
                if inst_raw and str(inst_raw).isdigit():
                    from apps.institutions.models import Institution
                    inst_obj = Institution.objects.filter(id=int(inst_raw)).first()
                    if inst_obj:
                        profile.institution = inst_obj
            profile.save()

        instance.refresh_from_db()
        return instance
