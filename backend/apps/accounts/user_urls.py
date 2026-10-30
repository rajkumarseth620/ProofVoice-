from django.urls import path
from .views import UserProfileDetailView, InstitutionUserListView

urlpatterns = [
    path('', InstitutionUserListView.as_view(), name='institution-user-list'),
    path('<int:pk>/profile/', UserProfileDetailView.as_view(), name='user-profile-detail'),
]
