from rest_framework import serializers
from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework.authtoken.models import Token
from .models import User, StudentProfile, AdministratorProfile
from apps.institutions.models import Institution, AdminAccessRequest

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
    institution_id = serializers.CharField(required=True)
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

    def validate_institution_id(self, value):
        val_str = str(value).strip()
        institution = None
        if val_str.isdigit():
            institution = Institution.objects.filter(
                id=int(val_str),
                is_active=True,
                verification_status=Institution.VerificationStatus.VERIFIED
            ).first()
        else:
            clean_code = val_str.replace('inst_', '').replace('_01', '').replace('_02', '').replace('_03', '').replace('_', '-')
            institution = Institution.objects.filter(
                code__icontains=clean_code,
                is_active=True,
                verification_status=Institution.VerificationStatus.VERIFIED
            ).first()
            if not institution:
                institution = Institution.objects.filter(
                    name__icontains=clean_code,
                    is_active=True,
                    verification_status=Institution.VerificationStatus.VERIFIED
                ).first()

        if not institution:
            raise serializers.ValidationError("Please select a verified, active institution.")
        return institution.id

    def validate_password(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError("This field is required.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        full_name = validated_data['full_name']
        institution = Institution.objects.get(id=validated_data['institution_id'])
        department = validated_data.get('department', '')
        course = validated_data.get('course') or department

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

        token, _ = Token.objects.get_or_create(user=user)
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

    def validate(self, attrs):
        email = attrs.get('email', '').strip().lower()
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError("Email and password are required.")

        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")

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
