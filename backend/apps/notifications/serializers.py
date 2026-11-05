from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    complaint_id = serializers.CharField(source='complaint.complaint_id', read_only=True)
    complaint_identifier = serializers.CharField(source='complaint.complaint_id', read_only=True)
    recipient_id = serializers.IntegerField(source='recipient.id', read_only=True)
    recipient_email = serializers.CharField(source='recipient.email', read_only=True)
    institution_id = serializers.SerializerMethodField()
    action_url = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_id',
            'recipient_id',
            'recipient_email',
            'recipient_role',
            'institution_id',
            'complaint',
            'complaint_id',
            'complaint_identifier',
            'related_request_id',
            'notification_type',
            'title',
            'message',
            'metadata',
            'is_read',
            'is_archived',
            'action_url',
            'read_at',
            'created_at'
        ]
        read_only_fields = ['id', 'notification_id', 'created_at']

    def get_action_url(self, obj):
        # Platform Super-Admin institutional actions
        if obj.notification_type in [
            Notification.NotificationType.INSTITUTION_REQUEST,
            Notification.NotificationType.INSTITUTION_APPROVED,
            Notification.NotificationType.INSTITUTION_REJECTED,
            Notification.NotificationType.INSTITUTION_SUSPENDED,
            Notification.NotificationType.INSTITUTION_RESUBMITTED
        ]:
            if obj.related_request_id:
                return f"super-admin.html?tab=institutions&reqId={obj.related_request_id}"
            return "super-admin.html?tab=institutions"

        # Platform Super-Admin student onboarding inquiries
        if obj.notification_type == Notification.NotificationType.STUDENT_ONBOARDING_REQUEST:
            if obj.related_request_id:
                return f"super-admin.html?tab=student-onboarding&reqId={obj.related_request_id}"
            return "super-admin.html?tab=student-onboarding"

        # Student / Admin complaint detail
        if obj.complaint and obj.complaint.complaint_id:
            return f"complaint-details.html?id={obj.complaint.complaint_id}"

        return None

    def get_institution_id(self, obj):
        if obj.institution:
            return obj.institution.id
        if obj.complaint and obj.complaint.institution:
            return obj.complaint.institution.id
        return None
