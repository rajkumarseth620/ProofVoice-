"""
Main URL Configuration for ProofVoice Backend.
Prefixes all REST APIs under /api/v1/
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

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

# Safe production serving for public UI media assets from the Railway persistent volume.
# Strictly limited to public directories: profile photos and institution logos.
# Sensitive complaint attachments and verification documents are deliberately omitted here
# and remain strictly protected behind authenticated, role-authorized REST endpoints.
urlpatterns += [
    re_path(r'^media/profile_photos/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT / 'profile_photos',
    }),
    re_path(r'^media/institutions/logos/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT / 'institutions' / 'logos',
    }),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
