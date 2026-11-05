from django.urls import path
from .views import (
    InstitutionListView,
    InstitutionDetailView,
    InstitutionMeView,
    InstitutionSettingsView,
    InstitutionDepartmentListView,
    InstitutionCategoryListView,
    InstitutionRegistrationRequestView,
    InstitutionRegistrationApproveView,
    AdminAccessRequestView,
    AdminAccessRequestApproveView,
    StudentOnboardingRequestView,
    StudentOnboardingRequestDetailView,
    SuperAdminOverviewView,
    InstitutionSuspendView
)

urlpatterns = [
    # Institution directory & scoped details
    path('', InstitutionListView.as_view(), name='institution-list'),
    path('me/', InstitutionMeView.as_view(), name='institution-me'),
    path('me/settings/', InstitutionSettingsView.as_view(), name='institution-settings'),
    path('me/departments/', InstitutionDepartmentListView.as_view(), name='institution-departments'),
    path('me/categories/', InstitutionCategoryListView.as_view(), name='institution-categories'),

    # Platform Super-Admin Console
    path('super-admin/overview/', SuperAdminOverviewView.as_view(), name='super-admin-overview'),

    # Student Onboarding Requests (unlisted institutions)
    path('student-onboarding-requests/', StudentOnboardingRequestView.as_view(), name='student-onboarding-requests'),
    path('student-onboarding-requests/<int:pk>/', StudentOnboardingRequestDetailView.as_view(), name='student-onboarding-request-detail'),

    # Registration requests (new institution onboarding)
    path('registration-requests/', InstitutionRegistrationRequestView.as_view(), name='institution-reg-requests'),
    path('registration-requests/me/', InstitutionRegistrationRequestView.as_view(), name='institution-reg-requests-me'),
    path('registration-requests/<int:pk>/approve/', InstitutionRegistrationApproveView.as_view(), name='institution-reg-approve'),

    # Admin access requests (joining existing institution)
    path('admin-access-requests/', AdminAccessRequestView.as_view(), name='institution-admin-access-requests'),
    path('admin-access-requests/me/', AdminAccessRequestView.as_view(), name='institution-admin-access-requests-me'),
    path('admin-access-requests/<str:pk>/approve/', AdminAccessRequestApproveView.as_view(), name='institution-admin-access-approve'),

    # Institution suspension & reactivation by Super-Admin
    path('<int:pk>/suspend/', InstitutionSuspendView.as_view(), name='institution-suspend'),

    # Institution detail by ID or Slug (Must be at the end to avoid capturing fixed slug-like endpoints)
    path('<int:pk>/', InstitutionDetailView.as_view(), name='institution-detail-by-id'),
    path('<str:pk>/', InstitutionDetailView.as_view(), name='institution-detail-by-slug'),
]
