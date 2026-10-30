from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.institutions.models import Institution
from apps.complaints.models import Complaint

class Notification(models.Model):
    """
    In-app alerts notifying students and administrators of lifecycle events,
    status updates, remarks, assignments, and resolution.
    """
    class NotificationType(models.TextChoices):
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

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
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
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.STATUS_CHANGE
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.email}: {self.title}"

    @classmethod
    def create_for_event(cls, recipient, title, message, notification_type=NotificationType.STATUS_CHANGE, complaint=None, institution=None):
        """
        Creates a personalized notification respecting student preferences and preventing duplicates.
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
        return cls.objects.create(
            recipient=recipient,
            institution=inst,
            complaint=complaint,
            notification_type=notification_type,
            title=title,
            message=message
        )
