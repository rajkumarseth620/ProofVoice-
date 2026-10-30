"""
Main URL Configuration for ProofVoice Backend.
Prefixes all REST APIs under /api/v1/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication & User Profiles
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/users/', include('apps.accounts.user_urls')),

    # Multi-Tenant Institutions & Settings
    path('api/v1/institutions/', include('apps.institutions.urls')),

    # Complaints Workflow & Application Generation
    path('api/v1/complaints/', include('apps.complaints.urls')),

    # Administrator Management Desk
    path('api/v1/admin/', include('apps.complaints.admin_urls')),

    # Notifications System
    path('api/v1/notifications/', include('apps.notifications.urls')),

    # Gnani AI Gateway (Prisma STT & Timbre TTS)
    path('api/v1/ai/', include('apps.integrations.urls')),

    # Dashboards & Analytics
    path('api/v1/', include('apps.analytics.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
