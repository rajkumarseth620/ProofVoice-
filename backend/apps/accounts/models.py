import os
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

def profile_image_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
        ext = '.jpg'
    user_id = instance.id or 'temp'
    return f"profile_photos/{user_id}/{uuid.uuid4().hex}{ext}"

class UserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email).lower()
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.PLATFORM_SUPERADMIN)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for ProofVoice.
    Supports email-based authentication and strict role-based access control.
    """
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        INSTITUTION_ADMIN = 'INSTITUTION_ADMIN', 'Institution Administrator'
        PLATFORM_SUPERADMIN = 'PLATFORM_SUPERADMIN', 'Platform Superadmin'

    email = models.EmailField(unique=True, db_index=True, max_length=255)
    full_name = models.CharField(max_length=200)
    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.STUDENT,
        db_index=True
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(
        default=False,
        help_text='Indicates if identity or institutional membership is confirmed.'
    )
    profile_image = models.ImageField(
        upload_to=profile_image_upload_path,
        null=True,
        blank=True,
        max_length=500,
        help_text='User profile photograph (JPG, PNG, WebP up to 5MB)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    @property
    def profile_image_url(self):
        if self.profile_image and hasattr(self.profile_image, 'url'):
            return self.profile_image.url
        return None

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_institution_admin(self):
        return self.role == self.Role.INSTITUTION_ADMIN

    @property
    def is_platform_superadmin(self):
        return self.role == self.Role.PLATFORM_SUPERADMIN


class StudentProfile(models.Model):
    """
    Extended profile for Students.
    Stores verified enrollment details, academic program, and institutional affiliation.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    student_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='Institutional roll or enrollment number (e.g. AJU/22/0451)'
    )
    institution = models.ForeignKey(
        'institutions.Institution',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    department = models.CharField(max_length=150, blank=True)
    course = models.CharField(max_length=150, blank=True)
    semester = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True, help_text='Correspondence / Hostel address')
    phone = models.CharField(max_length=25, blank=True)
    is_profile_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'

    def __str__(self):
        return f"Student: {self.user.full_name} ({self.student_id or 'No ID'})"

    def check_completeness(self):
        """Checks if all required fields are filled for formal letter generation."""
        is_complete = bool(
            self.student_id and
            self.institution and
            self.department and
            self.course and
            self.semester
        )
        if self.is_profile_complete != is_complete:
            self.is_profile_complete = is_complete
            self.save(update_fields=['is_profile_complete', 'updated_at'])
        return is_complete


class AdministratorProfile(models.Model):
    """
    Extended profile for Institution Administrators.
    Requires verified approval by Platform Superadmin or designated Authority.
    """
    class ApprovalStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        SUSPENDED = 'SUSPENDED', 'Suspended'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='admin_profile'
    )
    institution = models.ForeignKey(
        'institutions.Institution',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='administrators'
    )
    designation = models.CharField(
        max_length=150,
        default='Dean of Student Welfare'
    )
    department_name = models.CharField(max_length=150, blank=True)
    requested_role = models.CharField(max_length=50, default='INSTITUTION_ADMIN')
    approval_status = models.CharField(
        max_length=30,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        db_index=True
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_admin_profiles'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Administrator Profile'
        verbose_name_plural = 'Administrator Profiles'

    def __str__(self):
        inst_name = self.institution.name if self.institution else 'No Institution'
        return f"Admin: {self.user.full_name} - {inst_name} ({self.approval_status})"

    @property
    def is_approved(self):
        return self.approval_status == self.ApprovalStatus.APPROVED
