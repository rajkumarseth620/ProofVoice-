import random
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.institutions.models import Institution, InstitutionDepartment, ComplaintCategory

class Complaint(models.Model):
    """
    Core complaint model representing student grievances.
    Stores both the raw complaint and the generated/reviewed formal letter.
    """
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    class SourceType(models.TextChoices):
        TEXT = 'TEXT', 'Text Input'
        VOICE = 'VOICE', 'Voice / Speech-to-Text'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        AWAITING_STUDENT = 'AWAITING_STUDENT', 'Awaiting Student Response'
        RESOLVED = 'RESOLVED', 'Resolved'
        REJECTED = 'REJECTED', 'Rejected'
        REOPENED = 'REOPENED', 'Reopened'

    complaint_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Server-generated tracking identifier (e.g. PV-2026-1042)'
    )
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name='complaints',
        db_index=True
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='complaints',
        db_index=True
    )
    title = models.CharField(max_length=255)
    original_description = models.TextField(help_text='Raw student description as originally typed or spoken.')
    original_transcription = models.TextField(blank=True, help_text='Original AI voice transcription if voice input.')
    final_submitted_application = models.TextField(
        blank=True,
        help_text='The formal, Dean-addressed application letter reviewed/edited and submitted by the student.'
    )
    category = models.ForeignKey(
        ComplaintCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints'
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True
    )
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        default=SourceType.TEXT
    )

    # Location specifics
    campus = models.CharField(max_length=150, blank=True)
    building = models.CharField(max_length=150, blank=True)
    floor = models.CharField(max_length=50, blank=True)
    room_number = models.CharField(max_length=50, blank=True)
    full_issue_location = models.CharField(max_length=255, blank=True)

    # Administrative workflow
    assigned_department = models.ForeignKey(
        InstitutionDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints'
    )
    assigned_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints'
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True
    )
    submission_timestamp = models.DateTimeField(null=True, blank=True)
    resolution_timestamp = models.DateTimeField(null=True, blank=True)
    resolution_details = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Complaint'
        verbose_name_plural = 'Complaints'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.complaint_id}] {self.title} ({self.get_status_display()})"

    @classmethod
    def generate_unique_complaint_id(cls):
        """Generates a collision-resistant identifier formatted as PV-YYYY-XXXX."""
        year = timezone.now().year
        for _ in range(50):
            seq = random.randint(1000, 9999)
            cid = f"PV-{year}-{seq}"
            if not cls.objects.filter(complaint_id=cid).exists():
                return cid
        # Fallback to high-range random
        return f"PV-{year}-{random.randint(10000, 99999)}"

    def save(self, *args, **kwargs):
        if not self.complaint_id:
            self.complaint_id = self.generate_unique_complaint_id()
        if not self.full_issue_location:
            parts = [p for p in [self.building, self.floor, self.room_number, self.campus] if p]
            self.full_issue_location = ', '.join(parts) if parts else 'Main Campus'
        super().save(*args, **kwargs)

    @property
    def is_submitted(self):
        return self.status != self.Status.DRAFT


class ComplaintStatusHistory(models.Model):
    """
    Immutable audit trail for complaint status transitions, remarks, and administrative notes.
    Separates public remarks from confidential internal administrator notes.
    """
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    previous_status = models.CharField(max_length=30, blank=True)
    new_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaint_status_changes'
    )
    public_remark = models.TextField(
        blank=True,
        help_text='Visible to the complainant student in their timeline.'
    )
    internal_note = models.TextField(
        blank=True,
        help_text='Confidential administrative note; never exposed to students.'
    )
    assignment_change = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Complaint Status History'
        verbose_name_plural = 'Complaint Status Histories'
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.complaint.complaint_id}: {self.previous_status} -> {self.new_status} at {self.timestamp}"


class ComplaintAttachment(models.Model):
    """
    Secure file attachments (photos, PDFs, documents) associated with a complaint.
    """
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='complaints/attachments/%Y/%m/')
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text='File size in bytes')
    mime_type = models.CharField(max_length=100, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Complaint Attachment'
        verbose_name_plural = 'Complaint Attachments'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.file_name} ({self.complaint.complaint_id})"
