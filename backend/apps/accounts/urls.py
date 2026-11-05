from django.urls import path
from .views import (
    StudentRegisterView,
    AdminRegisterView,
    LoginView,
    LogoutView,
    MeView,
    ProfileView,
    ProfilePhotoView,
    ChangePasswordView,
    PasswordResetView
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
    path('password/change/', ChangePasswordView.as_view(), name='auth-change-password'),
    path('change-password/', ChangePasswordView.as_view(), name='auth-change-password-alias'),
    path('password/reset/', PasswordResetView.as_view(), name='auth-password-reset'),
    path('password-reset/', PasswordResetView.as_view(), name='auth-password-reset-alias'),
]
