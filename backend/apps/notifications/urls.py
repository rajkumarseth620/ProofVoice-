from django.urls import path
from .views import (
    NotificationListView,
    NotificationMarkReadView,
    NotificationMarkAllReadView,
    NotificationArchiveReadView,
    NotificationDeleteView,
    NotificationClearAllView
)

urlpatterns = [
    # List notifications with unread counts and category filters
    path('', NotificationListView.as_view(), name='notification-list'),

    # Mark single or all notifications as read
    path('<int:pk>/read/', NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('read-all/', NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),

    # Archive read notifications
    path('archive-read/', NotificationArchiveReadView.as_view(), name='notification-archive-read'),

    # Delete or clear
    path('<int:pk>/delete/', NotificationDeleteView.as_view(), name='notification-delete'),
    path('<int:pk>/', NotificationDeleteView.as_view(), name='notification-delete-rest'),
    path('clear-all/', NotificationClearAllView.as_view(), name='notification-clear-all'),
]
