from django.urls import path
from .views import (
    ComplaintListCreateView,
    ComplaintDetailView,
    ComplaintSubmitView,
    ComplaintTimelineView,
    GenerateApplicationView,
    ComplaintReopenView,
    ComplaintAttachmentUploadView
)

urlpatterns = [
    # Complaint listing & creation
    path('', ComplaintListCreateView.as_view(), name='complaint-list-create'),

    # Application generator preview endpoints
    path('generate-application/', GenerateApplicationView.as_view(), name='complaint-generate-app-preview'),
    path('<int:pk>/generate-application/', GenerateApplicationView.as_view(), name='complaint-generate-app-existing'),
    path('<str:pk>/generate-application/', GenerateApplicationView.as_view(), name='complaint-generate-app-existing-str'),

    # Detail, update, and submission
    path('<int:pk>/', ComplaintDetailView.as_view(), name='complaint-detail-id'),
    path('<str:pk>/', ComplaintDetailView.as_view(), name='complaint-detail-str'),
    path('<int:pk>/submit/', ComplaintSubmitView.as_view(), name='complaint-submit-id'),
    path('<str:pk>/submit/', ComplaintSubmitView.as_view(), name='complaint-submit-str'),
    path('<int:pk>/timeline/', ComplaintTimelineView.as_view(), name='complaint-timeline-id'),
    path('<str:pk>/timeline/', ComplaintTimelineView.as_view(), name='complaint-timeline-str'),
    path('<int:pk>/reopen-request/', ComplaintReopenView.as_view(), name='complaint-reopen-id'),
    path('<str:pk>/reopen-request/', ComplaintReopenView.as_view(), name='complaint-reopen-str'),
    path('<int:pk>/reopen/', ComplaintReopenView.as_view(), name='complaint-reopen-alt-id'),
    path('<str:pk>/reopen/', ComplaintReopenView.as_view(), name='complaint-reopen-alt-str'),
    path('<int:pk>/attachments/', ComplaintAttachmentUploadView.as_view(), name='complaint-attachment-id'),
    path('<str:pk>/attachments/', ComplaintAttachmentUploadView.as_view(), name='complaint-attachment-str'),
]
