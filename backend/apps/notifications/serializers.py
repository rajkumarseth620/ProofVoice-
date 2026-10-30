from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    complaint_id = serializers.CharField(source='complaint.complaint_id', read_only=True)
    complaint_identifier = serializers.CharField(source='complaint.complaint_id', read_only=True)
    action_url = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'complaint',
            'complaint_id',
            'complaint_identifier',
            'notification_type',
            'title',
            'message',
            'is_read',
            'action_url',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_action_url(self, obj):
        if obj.complaint and obj.complaint.complaint_id:
            return f"complaint-details.html?id={obj.complaint.complaint_id}"
        return None
