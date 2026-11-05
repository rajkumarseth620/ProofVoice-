from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    """
    Returns in-app notifications for the authenticated user with unread counts and category filters.
    Strictly isolated: users only receive notifications where recipient == request.user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Notification.objects.filter(recipient=request.user)

        # Archive filter: exclude archived unless explicitly requested
        include_archived = request.query_params.get('include_archived', 'false').lower() in ('true', '1')
        if not include_archived:
            qs = qs.filter(is_archived=False)

        # Read/Unread filter
        is_read_param = request.query_params.get('is_read')
        if is_read_param is not None:
            qs = qs.filter(is_read=is_read_param.lower() in ('true', '1'))
        elif request.query_params.get('unread_only', 'false').lower() in ('true', '1'):
            qs = qs.filter(is_read=False)

        # Type filter
        notif_type = request.query_params.get('type')
        if notif_type:
            qs = qs.filter(notification_type=notif_type.upper())

        # Category shortcuts for Super Admin Dashboard
        category = request.query_params.get('category', '').lower()
        if category in ('institution', 'institution_requests', 'institutional'):
            qs = qs.filter(notification_type__in=[
                Notification.NotificationType.INSTITUTION_REQUEST,
                Notification.NotificationType.INSTITUTION_APPROVED,
                Notification.NotificationType.INSTITUTION_REJECTED,
                Notification.NotificationType.INSTITUTION_SUSPENDED,
                Notification.NotificationType.INSTITUTION_RESUBMITTED
            ])
        elif category in ('student', 'student_onboarding', 'student_requests'):
            qs = qs.filter(notification_type=Notification.NotificationType.STUDENT_ONBOARDING_REQUEST)

        # Unread counts calculation
        base_user_qs = Notification.objects.filter(recipient=request.user, is_archived=False)
        unread_count = base_user_qs.filter(is_read=False).count()
        unread_inst_count = base_user_qs.filter(
            is_read=False,
            notification_type__in=[
                Notification.NotificationType.INSTITUTION_REQUEST,
                Notification.NotificationType.INSTITUTION_RESUBMITTED
            ]
        ).count()
        unread_student_count = base_user_qs.filter(
            is_read=False,
            notification_type=Notification.NotificationType.STUDENT_ONBOARDING_REQUEST
        ).count()

        # Limit
        limit = min(int(request.query_params.get('limit', 50)), 100)
        notifications = qs.order_by('-created_at')[:limit]

        serializer = NotificationSerializer(notifications, many=True)
        return Response({
            'unread_count': unread_count,
            'unread_institution_requests': unread_inst_count,
            'unread_student_requests': unread_student_count,
            'total_count': qs.count(),
            'notifications': serializer.data
        }, status=status.HTTP_200_OK)


class NotificationMarkReadView(APIView):
    """
    Marks a single notification as read and records read_at timestamp.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.mark_as_read()
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False, is_archived=False).count()
        return Response({
            'message': 'Notification marked as read.',
            'unread_count': unread_count,
            'notification': NotificationSerializer(notification).data
        }, status=status.HTTP_200_OK)


class NotificationMarkAllReadView(APIView):
    """
    Marks all notifications for the authenticated user as read.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        qs = Notification.objects.filter(recipient=request.user, is_read=False)
        category = request.data.get('category') or request.query_params.get('category')
        if category == 'institution':
            qs = qs.filter(notification_type__in=[
                Notification.NotificationType.INSTITUTION_REQUEST,
                Notification.NotificationType.INSTITUTION_APPROVED,
                Notification.NotificationType.INSTITUTION_REJECTED,
                Notification.NotificationType.INSTITUTION_SUSPENDED,
                Notification.NotificationType.INSTITUTION_RESUBMITTED
            ])
        elif category == 'student':
            qs = qs.filter(notification_type=Notification.NotificationType.STUDENT_ONBOARDING_REQUEST)

        updated_count = qs.update(is_read=True, read_at=timezone.now())
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False, is_archived=False).count()
        return Response({
            'message': f'{updated_count} notification(s) marked as read.',
            'updated_count': updated_count,
            'unread_count': unread_count
        }, status=status.HTTP_200_OK)


class NotificationArchiveReadView(APIView):
    """
    Archives read notifications for the authenticated user so they no longer clutter the active list.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        archived_count = Notification.objects.filter(
            recipient=request.user,
            is_read=True,
            is_archived=False
        ).update(is_archived=True)
        return Response({
            'message': f'{archived_count} read notification(s) archived.',
            'archived_count': archived_count
        }, status=status.HTTP_200_OK)


class NotificationDeleteView(APIView):
    """
    Deletes or archives a single notification owned by the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.delete()
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False, is_archived=False).count()
        return Response({
            'message': 'Notification deleted successfully.',
            'unread_count': unread_count
        }, status=status.HTTP_200_OK)

    def post(self, request, pk):
        action = request.data.get('action', 'delete').lower()
        if action == 'archive':
            notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
            notification.is_archived = True
            notification.save(update_fields=['is_archived'])
            return Response({'message': 'Notification archived.'}, status=status.HTTP_200_OK)
        return self.delete(request, pk)


class NotificationClearAllView(APIView):
    """
    Clears all notifications for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        count, _ = Notification.objects.filter(recipient=request.user).delete()
        return Response({'message': f'{count} notifications cleared.', 'unread_count': 0}, status=status.HTTP_200_OK)

    def post(self, request):
        return self.delete(request)
