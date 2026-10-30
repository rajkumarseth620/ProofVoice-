from django.urls import path
from .views import (
    StudentDashboardView,
    AdminDashboardView,
    InstitutionAnalyticsView
)

urlpatterns = [
    path('dashboard/student/', StudentDashboardView.as_view(), name='dashboard-student'),
    path('dashboard/admin/', AdminDashboardView.as_view(), name='dashboard-admin'),
    path('analytics/institution/', InstitutionAnalyticsView.as_view(), name='analytics-institution'),
]
