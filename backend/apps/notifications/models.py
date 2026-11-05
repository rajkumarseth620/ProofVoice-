from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.institutions.models import Institution
from apps.complaints.models import Complaint
import uuid
import logging

logger = logging.getLogger(__name__)


class Notification(models.Model):
    """
    In-app alerts notifying students, institutional administrators, and Platform Super-Admins
    of complaint updates, registration requests, onboarding inquiries, and administrative lifecycle actions.
    All notifications remain 100% internal to ProofVoice.
    """
    class NotificationType(models.TextChoices):
        # Platform Governance & Institutional Access
        INSTITUTION_REQUEST = 'INSTITUTION_REQUEST', 'New Institutional Access Request'
        STUDENT_ONBOARDING_REQUEST = 'STUDENT_ONBOARDING_REQUEST', 'New Student Institution Request'
        INSTITUTION_APPROVED = 'INSTITUTION_APPROVED', 'Institution Registration Approved'
        INSTITUTION_REJECTED = 'INSTITUTION_REJECTED', 'Institution Registration Rejected'
        INSTITUTION_SUSPENDED = 'INSTITUTION_SUSPENDED', 'Institution Workspace Suspended'
        INSTITUTION_RESUBMITTED = 'INSTITUTION_RESUBMITTED', 'Institution Registration Resubmitted'

        # Complaint Lifecycle
        SUBMISSION = 'SUBMISSION', 'Complaint Submitted'
        STATUS_CHANGE = 'STATUS_CHANGE', 'Status Update'
        ASSIGNMENT = 'ASSIGNMENT', 'Complaint Assignment'
        REMARK = 'REMARK', 'Administrator Remark'
        APPLICATION_READY = 'APPLICATION_READY', 'Application Ready for Review'
        INFO_REQUESTED = 'INFO_REQUESTED', 'Information Requested'
        RESOLUTION = 'RESOLUTION', 'Complaint Resolved'
        REOPENED = 'REOPENED', 'Complaint Reopened'
        ACCOUNT = 'ACCOUNT', 'Account & Security'
        SYSTEM = 'SYSTEM', 'System Alert'

    notification_id = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True
    )
    recipient_role = models.CharField(
        max_length=40,
        blank=True,
        default='',
        db_index=True
    )
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    related_request_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
        db_index=True
    )
    notification_type = models.CharField(
        max_length=40,
        choices=NotificationType.choices,
        default=NotificationType.STATUS_CHANGE,
        db_index=True
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    metadata = models.JSONField(
        default=dict,
        blank=True
    )
    is_read = models.BooleanField(
        default=False,
        db_index=True
    )
    is_archived = models.BooleanField(
        default=False,
        db_index=True
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] {self.recipient.email}: {self.title}"

    def save(self, *args, **kwargs):
        if not self.notification_id:
            date_str = timezone.now().strftime('%Y%m%d')
            rand_hex = uuid.uuid4().hex[:8].upper()
            self.notification_id = f"PV-NTF-{date_str}-{rand_hex}"
        if not self.recipient_role and self.recipient_id:
            self.recipient_role = getattr(self.recipient, 'role', '')
        super().save(*args, **kwargs)

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    @classmethod
    def notify_super_admins(cls, title, message, notification_type, related_request_id='', metadata=None):
        """
        Creates an internal in-app notification for all Platform Super-Admins.
        Prevents duplicate notifications for the same request and event within 5 minutes.
        Ensures zero-data-loss: catches errors to protect the calling transaction.
        """
        from apps.accounts.models import User
        super_admins = User.objects.filter(role=User.Role.PLATFORM_SUPERADMIN, is_active=True)
        if not super_admins.exists():
            super_admins = User.objects.filter(is_superuser=True, is_active=True)

        created_list = []
        five_mins_ago = timezone.now() - timezone.timedelta(minutes=5)

        for admin_user in super_admins:
            try:
                # Check for recent duplicate
                existing = cls.objects.filter(
                    recipient=admin_user,
                    notification_type=notification_type,
                    related_request_id=related_request_id,
                    created_at__gte=five_mins_ago
                ).first()

                if existing:
                    created_list.append(existing)
                    continue

                notif = cls.objects.create(
                    recipient=admin_user,
                    recipient_role=User.Role.PLATFORM_SUPERADMIN,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    related_request_id=related_request_id,
                    metadata=metadata or {}
                )
                created_list.append(notif)
            except Exception as exc:
                logger.error(f"Failed to create Super Admin notification: {exc}")

        return created_list

    @classmethod
    def create_for_event(cls, recipient, title, message, notification_type=NotificationType.STATUS_CHANGE, complaint=None, institution=None, related_request_id='', metadata=None):
        """
        Creates an internal in-app notification for students or institutional administrators.
        Respects student in-app preferences and avoids duplicate alerts.
        """
        if not recipient:
            return None

        # Check student in-app notification preference
        if hasattr(recipient, 'student_profile'):
            if not getattr(recipient.student_profile, 'notify_in_app', True):
                return None

        # Prevent duplicate notifications within 5 minutes for the exact same event
        five_mins_ago = timezone.now() - timezone.timedelta(minutes=5)
        existing = cls.objects.filter(
            recipient=recipient,
            complaint=complaint,
            title=title,
            created_at__gte=five_mins_ago
        ).first()
        if existing:
            return existing

        inst = institution or (complaint.institution if complaint else None)
        try:
            return cls.objects.create(
                recipient=recipient,
                institution=inst,
                complaint=complaint,
                notification_type=notification_type,
                related_request_id=related_request_id,
                title=title,
                message=message,
                metadata=metadata or {}
            )
        except Exception as exc:
            logger.error(f"Failed to create in-app notification: {exc}")
            return None
