from django.urls import path
from .views import (
    StudentRegisterView,
    AdminRegisterView,
    LoginView,
    LogoutView,
    MeView,
    ProfileView,
    ProfilePhotoView
)

urlpatterns = [
    path('register/student/', StudentRegisterView.as_view(), name='register-student'),
    path('register/institution-admin/', AdminRegisterView.as_view(), name='register-admin'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('me/', MeView.as_view(), name='auth-me'),
    path('profile/', ProfileView.as_view(), name='auth-profile'),
    path('profile/photo/', ProfilePhotoView.as_view(), name='auth-profile-photo'),
    path('profile-photo/', ProfilePhotoView.as_view(), name='auth-profile-photo-alias'),
]
