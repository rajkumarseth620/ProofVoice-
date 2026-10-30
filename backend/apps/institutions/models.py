from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Institution(models.Model):
    """
    Multi-tenant Institution entity (University, College, Institute, Polytechnic).
    Each institution isolates its complaints, departments, categories, and staff.
    """
    class InstitutionType(models.TextChoices):
        UNIVERSITY = 'UNIVERSITY', 'University'
        COLLEGE = 'COLLEGE', 'College'
        POLYTECHNIC = 'POLYTECHNIC', 'Polytechnic'
        INSTITUTE = 'INSTITUTE', 'Technical Institute'

    class VerificationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Verification'
        VERIFIED = 'VERIFIED', 'Verified & Active'
        REJECTED = 'REJECTED', 'Rejected'
        SUSPENDED = 'SUSPENDED', 'Suspended'

    code = models.SlugField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    institution_type = models.CharField(
        max_length=50,
        choices=InstitutionType.choices,
        default=InstitutionType.UNIVERSITY
    )
    official_email = models.EmailField(max_length=255)
    official_address = models.TextField()
    country = models.CharField(max_length=100, default='India')
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    website = models.URLField(max_length=255, blank=True)
    logo = models.ImageField(upload_to='institutions/logos/', null=True, blank=True)
    
    verification_status = models.CharField(
        max_length=30,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Institution'
        verbose_name_plural = 'Institutions'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} [{self.get_verification_status_display()}]"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)[:90]
        super().save(*args, **kwargs)

    @property
    def is_verified(self):
        return self.verification_status == self.VerificationStatus.VERIFIED


class InstitutionDepartment(models.Model):
    """
    Institution-specific departments (e.g. Estate & Maintenance, Hostel Administration, Dean Office).
    """
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name='departments'
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True)
    contact_email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Institution Department'
        verbose_name_plural = 'Institution Departments'
        unique_together = ('institution', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.institution.name}"


class ComplaintCategory(models.Model):
    """
    Institution-specific complaint categories mapped to default resolving departments.
    """
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name='complaint_categories'
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    default_department = models.ForeignKey(
        InstitutionDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categories'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Complaint Category'
        verbose_name_plural = 'Complaint Categories'
        unique_together = ('institution', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.institution.name})"


class ComplaintRecipientConfiguration(models.Model):
    """
    Configures formal letter recipient authorities per institution and category.
    Defaults to 'The Dean' if no category-specific configuration is established.
    """
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name='recipient_configurations'
    )
    category = models.ForeignKey(
        ComplaintCategory,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='recipient_configs',
        help_text='If empty, this configuration acts as the default recipient for the institution.'
    )
    recipient_designation = models.CharField(
        max_length=200,
        default='The Dean',
        help_text='e.g., The Dean of Student Welfare, The Chief Warden, The Registrar'
    )
    recipient_name = models.CharField(
        max_length=200,
        blank=True,
        help_text='e.g., Dr. Arvind Sharma (optional)'
    )
    recipient_address = models.TextField(
        blank=True,
        help_text='Office address block to appear on formal letter'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Complaint Recipient Configuration'
        verbose_name_plural = 'Complaint Recipient Configurations'
        unique_together = ('institution', 'category')

    def __str__(self):
        cat_name = self.category.name if self.category else 'Default (All Categories)'
        return f"{self.recipient_designation} - {self.institution.name} [{cat_name}]"


class InstitutionRegistrationRequest(models.Model):
    """
    Tracks new institution registration applications awaiting Platform Superadmin approval.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    institution_name = models.CharField(max_length=255)
    institution_type = models.CharField(
        max_length=50,
        choices=Institution.InstitutionType.choices,
        default=Institution.InstitutionType.UNIVERSITY
    )
    official_email = models.EmailField(max_length=255)
    official_address = models.TextField()
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    website = models.URLField(max_length=255, blank=True)
    applicant_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='institution_registration_requests'
    )
    applicant_designation = models.CharField(max_length=150)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    rejection_reason = models.TextField(blank=True)
    created_institution = models.ForeignKey(
        Institution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='originating_request'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_institution_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Institution Registration Request'
        verbose_name_plural = 'Institution Registration Requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.institution_name} by {self.applicant_user.email} ({self.status})"


class AdminAccessRequest(models.Model):
    """
    Tracks staff/administrator requests to join an existing institution.
    Must be reviewed and approved by an authorized Institution Admin or Platform Superadmin.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admin_access_requests'
    )
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name='admin_access_requests'
    )
    designation = models.CharField(max_length=150)
    department_name = models.CharField(max_length=150, blank=True)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_admin_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Admin Access Request'
        verbose_name_plural = 'Admin Access Requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"Access Request: {self.user.email} -> {self.institution.name} ({self.status})"
