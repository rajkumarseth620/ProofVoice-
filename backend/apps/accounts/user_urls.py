from django.urls import path
from .views import UserProfileDetailView, InstitutionUserListView

urlpatterns = [
    path('', InstitutionUserListView.as_view(), name='institution-user-list'),
    path('<int:pk>/profile/', UserProfileDetailView.as_view(), name='user-profile-detail-int'),
    path('<str:pk>/profile/', UserProfileDetailView.as_view(), name='user-profile-detail'),
    path('<int:pk>/status/', UserProfileDetailView.as_view(), name='user-profile-status-int'),
    path('<str:pk>/status/', UserProfileDetailView.as_view(), name='user-profile-status'),
    path('<int:pk>/', UserProfileDetailView.as_view(), name='user-profile-root-int'),
    path('<str:pk>/', UserProfileDetailView.as_view(), name='user-profile-root'),
]
