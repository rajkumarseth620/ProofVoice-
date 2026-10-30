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
            'is_profile_complete',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['is_profile_complete', 'created_at', 'updated_at']


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
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'role', 'is_verified', 'profile_image', 'profile_image_url', 'created_at', 'updated_at']


class StudentRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, required=True, allow_blank=False, trim_whitespace=False)
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
            raise serializers.ValidationError("This field is required.")
        return value

    def validate(self, attrs):
        raw_inst = str(attrs.get('institution_id', '')).strip()
        custom_name = attrs.get('custom_institution_name', '').strip()
        is_other = (raw_inst.upper() == 'OTHER' or not raw_inst or custom_name)

        if is_other:
            if not custom_name:
                raise serializers.ValidationError({
                    "custom_institution_name": "Please enter your institution name."
                })
            # Check for existing institution by case-insensitive name to prevent duplicates
            existing = Institution.objects.filter(name__iexact=custom_name).first()
            if existing:
                attrs['resolved_institution'] = existing
                attrs['is_unlisted_institution'] = (existing.verification_status != Institution.VerificationStatus.VERIFIED)
            else:
                attrs['resolved_institution'] = None
                attrs['is_unlisted_institution'] = True
        else:
            # Look up verified institution
            institution = None
            if raw_inst.isdigit():
                institution = Institution.objects.filter(
                    id=int(raw_inst),
                    is_active=True
                ).first()
            else:
                clean_code = raw_inst.replace('inst_', '').replace('_01', '').replace('_02', '').replace('_03', '').replace('_', '-')
                institution = Institution.objects.filter(
                    code__icontains=clean_code,
                    is_active=True
                ).first()
                if not institution:
                    institution = Institution.objects.filter(
                        name__icontains=clean_code,
                        is_active=True
                    ).first()

            if not institution:
                raise serializers.ValidationError({
                    "institution_id": "Please select an institution or choose '+ My Institution Is Not Listed'."
                })
            attrs['resolved_institution'] = institution
            attrs['is_unlisted_institution'] = False

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        full_name = validated_data['full_name']
        department = validated_data.get('department', '')
        course = validated_data.get('course') or department
        is_unlisted_institution = validated_data.get('is_unlisted_institution', False)
        institution = validated_data.get('resolved_institution')

        if not institution:
            # Create a new Institution record with UNVERIFIED status
            custom_name = validated_data.get('custom_institution_name', '').strip()
            inst_type_raw = (validated_data.get('institution_type') or 'College').strip().upper()
            valid_types = dict(Institution.InstitutionType.choices)
            inst_type = inst_type_raw if inst_type_raw in valid_types else Institution.InstitutionType.COLLEGE

            base_code = slugify(custom_name)[:80] or 'inst'
            code = base_code
            counter = 1
            while Institution.objects.filter(code=code).exists():
                code = f"{base_code}-{counter}"
                counter += 1

            institution = Institution.objects.create(
                name=custom_name,
                code=code,
                institution_type=inst_type,
                official_email=validated_data.get('official_domain', '').strip() or email,
                official_address=f"{validated_data.get('city', '')}, {validated_data.get('state', '')}, {validated_data.get('country', '')}".strip(', '),
                state=validated_data.get('state', '').strip(),
                city=validated_data.get('city', '').strip(),
                country=validated_data.get('country', '').strip() or 'India',
                website=validated_data.get('official_domain', '').strip(),
                verification_status=Institution.VerificationStatus.UNVERIFIED,
                is_active=True
            )

            # Seed default departments and categories so students can immediately lodge grievances
            default_depts = [
                ('Estate & Maintenance', 'EST'),
                ('Hostel Administration', 'HST'),
                ('Academic Affairs', 'ACD'),
                ('IT & Network Services', 'ITS'),
                ('Dean of Student Welfare', 'DSW')
            ]
            created_depts = {}
            for d_name, d_code in default_depts:
                created_depts[d_name] = InstitutionDepartment.objects.create(
                    institution=institution,
                    name=d_name,
                    code=d_code
                )

            default_categories = [
                ('Infrastructure & Maintenance', created_depts['Estate & Maintenance']),
                ('Hostel & Accommodation', created_depts['Hostel Administration']),
                ('Academic & Faculty', created_depts['Academic Affairs']),
                ('Sanitation & Hygiene', created_depts['Estate & Maintenance']),
                ('IT & Network Issues', created_depts['IT & Network Services']),
                ('General Administration', created_depts['Dean of Student Welfare'])
            ]
            for cat_name, dept_obj in default_categories:
                ComplaintCategory.objects.create(
                    institution=institution,
                    name=cat_name,
                    default_department=dept_obj
                )

            ComplaintRecipientConfiguration.objects.create(
                institution=institution,
                recipient_designation='The Dean',
                recipient_name='',
                recipient_address=f"Office of the Dean, {institution.name}\n{institution.official_address}"
            )

        # Allow immediate student account activation and login
        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
            role=User.Role.STUDENT,
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
            address=validated_data.get('address', '')
        )
        profile.check_completeness()

        # Audit record for Platform Superadmin review
        if is_unlisted_institution:
            InstitutionRegistrationRequest.objects.get_or_create(
                created_institution=institution,
                defaults={
                    'institution_name': institution.name,
                    'institution_type': institution.institution_type,
                    'official_email': validated_data.get('official_domain', '').strip() or email,
                    'official_address': institution.official_address or f"{institution.city}, {institution.state}".strip(', '),
                    'state': institution.state,
                    'city': institution.city,
                    'website': institution.website,
                    'applicant_user': user,
                    'applicant_designation': 'Student Registrant',
                    'status': InstitutionRegistrationRequest.Status.PENDING
                }
            )

        token, _ = Token.objects.get_or_create(user=user)
        user.is_unlisted_institution = is_unlisted_institution
        return user, token


class AdminRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=200)
    institution_id = serializers.CharField(required=True)
    designation = serializers.CharField(max_length=150, default='Dean of Student Welfare')
    department_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email=normalized).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return normalized

    def validate_institution_id(self, value):
        val_str = str(value).strip()
        institution = None
        if val_str.isdigit():
            institution = Institution.objects.filter(id=int(val_str)).first()
        else:
            clean_code = val_str.replace('inst_', '').replace('_01', '').replace('_02', '').replace('_03', '').replace('_', '-')
            institution = Institution.objects.filter(code__icontains=clean_code).first()
            if not institution:
                institution = Institution.objects.filter(name__icontains=clean_code).first()

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

        profile = AdministratorProfile.objects.create(
            user=user,
            institution=institution,
            designation=validated_data.get('designation', 'Dean of Student Welfare'),
            department_name=validated_data.get('department_name', ''),
            approval_status=AdministratorProfile.ApprovalStatus.PENDING
        )

        # Record admin access request for platform superadmin audit
        AdminAccessRequest.objects.create(
            user=user,
            institution=institution,
            designation=profile.designation,
            department_name=profile.department_name,
            status=AdminAccessRequest.Status.PENDING
        )

        token, _ = Token.objects.get_or_create(user=user)
        return user, token


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        email = attrs.get('email', '').strip().lower()
        password = attrs.get('password')
        requested_role = attrs.get('role', '').strip().lower()

        if not email or not password:
            raise serializers.ValidationError("Email and password are required.")

        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")

        # Enforce role matching when a specific role portal is targeted
        if requested_role in ['admin', 'institution_admin']:
            if user.role not in [User.Role.INSTITUTION_ADMIN, User.Role.PLATFORM_SUPERADMIN]:
                raise serializers.ValidationError("Access denied. This account does not have administrator privileges.")
        elif requested_role in ['student']:
            if user.role != User.Role.STUDENT:
                raise serializers.ValidationError("Access denied. Please sign in via the Administrator portal.")
        elif requested_role in ['superadmin', 'platform_superadmin']:
            if user.role != User.Role.PLATFORM_SUPERADMIN:
                raise serializers.ValidationError("Access denied. This account does not have platform superadmin privileges.")

        # Enforce verification for administrator accounts
        if user.role == User.Role.INSTITUTION_ADMIN:
            if hasattr(user, 'admin_profile'):
                inst = user.admin_profile.institution
                if inst and inst.verification_status != Institution.VerificationStatus.VERIFIED:
                    raise serializers.ValidationError(
                        "Your institution is awaiting platform administrator verification. Institutional administrator access will be enabled once verified."
                    )
                if user.admin_profile.approval_status != AdministratorProfile.ApprovalStatus.APPROVED:
                    raise serializers.ValidationError(
                        "Your administrator account is awaiting verification. You will receive access once approved by the platform administrator."
                    )
            elif not user.is_verified:
                raise serializers.ValidationError("Your administrator account is awaiting verification.")

        attrs['user'] = user
        return attrs


class ProfileUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(required=False, max_length=200)
    student_id = serializers.CharField(required=False, allow_blank=True, max_length=100)
    institution_id = serializers.IntegerField(required=False, allow_null=True)
    department = serializers.CharField(required=False, allow_blank=True, max_length=150)
    course = serializers.CharField(required=False, allow_blank=True, max_length=150)
    semester = serializers.CharField(required=False, allow_blank=True, max_length=50)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=25)
    address = serializers.CharField(required=False, allow_blank=True)
    designation = serializers.CharField(required=False, allow_blank=True, max_length=150)

    def update(self, instance, validated_data):
        if 'full_name' in validated_data:
            instance.full_name = validated_data['full_name']
            instance.save(update_fields=['full_name', 'updated_at'])

        if instance.role == User.Role.STUDENT and hasattr(instance, 'student_profile'):
            profile = instance.student_profile
            if 'institution_id' in validated_data:
                inst_id = validated_data['institution_id']
                if inst_id:
                    profile.institution = Institution.objects.filter(id=inst_id).first()
                else:
                    profile.institution = None
            if 'student_id' in validated_data:
                profile.student_id = validated_data['student_id']
            if 'department' in validated_data:
                profile.department = validated_data['department']
            if 'course' in validated_data:
                profile.course = validated_data['course']
            if 'semester' in validated_data:
                profile.semester = validated_data['semester']
            if 'phone' in validated_data:
                profile.phone = validated_data['phone']
            if 'address' in validated_data:
                profile.address = validated_data['address']
            profile.save()
            profile.check_completeness()

        elif instance.role == User.Role.INSTITUTION_ADMIN and hasattr(instance, 'admin_profile'):
            profile = instance.admin_profile
            if 'designation' in validated_data:
                profile.designation = validated_data['designation']
            profile.save()

        return instance
