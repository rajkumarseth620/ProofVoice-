from django.urls import path
from .admin_views import (
    AdminComplaintListView,
    AdminComplaintAssignView,
    AdminComplaintStatusView,
    AdminComplaintRemarksView,
    AdminComplaintInternalNotesView,
    AdminComplaintResolutionView
)
from apps.institutions.views import (
    InstitutionDepartmentListView,
    InstitutionCategoryListView
)

urlpatterns = [
    # Administrator Complaint Management Desk
    path('complaints/', AdminComplaintListView.as_view(), name='admin-complaints-list'),
    path('complaints/<int:pk>/assign/', AdminComplaintAssignView.as_view(), name='admin-complaint-assign-id'),
    path('complaints/<str:pk>/assign/', AdminComplaintAssignView.as_view(), name='admin-complaint-assign-str'),
    path('complaints/<int:pk>/status/', AdminComplaintStatusView.as_view(), name='admin-complaint-status-id'),
    path('complaints/<str:pk>/status/', AdminComplaintStatusView.as_view(), name='admin-complaint-status-str'),
    path('complaints/<int:pk>/remarks/', AdminComplaintRemarksView.as_view(), name='admin-complaint-remarks-id'),
    path('complaints/<str:pk>/remarks/', AdminComplaintRemarksView.as_view(), name='admin-complaint-remarks-str'),
    path('complaints/<int:pk>/internal-notes/', AdminComplaintInternalNotesView.as_view(), name='admin-complaint-notes-id'),
    path('complaints/<str:pk>/internal-notes/', AdminComplaintInternalNotesView.as_view(), name='admin-complaint-notes-str'),
    path('complaints/<int:pk>/resolution/', AdminComplaintResolutionView.as_view(), name='admin-complaint-resolution-id'),
    path('complaints/<str:pk>/resolution/', AdminComplaintResolutionView.as_view(), name='admin-complaint-resolution-str'),

    # Administrative creation of categories and departments
    path('categories/', InstitutionCategoryListView.as_view(), name='admin-create-category'),
    path('departments/', InstitutionDepartmentListView.as_view(), name='admin-create-department'),
]
