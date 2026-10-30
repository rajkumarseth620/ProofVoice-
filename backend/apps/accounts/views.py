import os
from PIL import Image
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.authtoken.models import Token
from django.contrib.auth import login as django_login, logout as django_logout

from .models import User, StudentProfile, AdministratorProfile
from .serializers import (
    UserSerializer,
    StudentRegistrationSerializer,
    AdminRegistrationSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    StudentProfileSerializer,
    AdministratorProfileSerializer
)

class StudentRegisterView(APIView):
    """
    Public registration endpoint for students.
    Enforces STUDENT role and sets up initial StudentProfile.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user, token = serializer.save()
            if getattr(user, 'is_unlisted_pending', False):
                return Response({
                    'message': 'Your institution is not yet verified. Your registration request has been submitted and is awaiting platform administrator approval.',
                    'requires_approval': True,
                    'institution_status': 'PENDING',
                    'user': UserSerializer(user).data
                }, status=status.HTTP_201_CREATED)

            return Response({
                'message': 'Student account registered successfully.',
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminRegisterView(APIView):
    """
    Public registration request endpoint for institution administrators.
    Sets status to PENDING until approved by platform superadmin.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AdminRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user, token = serializer.save()
            return Response({
                'message': 'Administrator registration request submitted. Access is pending institutional verification.',
                'token': token.key,
                'user': UserSerializer(user).data,
                'requires_approval': True
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    Authenticates a user via email and password.
    Returns auth token, user profile, and institutional scope.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, _ = Token.objects.get_or_create(user=user)
            
            # Determine institutional affiliation and approval status
            institution_data = None
            is_approved = True

            if user.role == User.Role.STUDENT and hasattr(user, 'student_profile') and user.student_profile.institution:
                inst = user.student_profile.institution
                institution_data = {
                    'id': inst.id,
                    'name': inst.name,
                    'code': inst.code
                }
            elif user.role == User.Role.INSTITUTION_ADMIN and hasattr(user, 'admin_profile'):
                admin_prof = user.admin_profile
                is_approved = admin_prof.is_approved
                if admin_prof.institution:
                    institution_data = {
                        'id': admin_prof.institution.id,
                        'name': admin_prof.institution.name,
                        'code': admin_prof.institution.code
                    }

            return Response({
                'token': token.key,
                'user': UserSerializer(user, context={'request': request}).data,
                'role': user.role,
                'institution': institution_data,
                'is_approved': is_approved,
                'message': 'Login successful.'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    Deletes the active authentication token.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)


class MeView(APIView):
    """
    Returns the currently authenticated user's profile and institutional scope.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileView(APIView):
    """
    Allows the authenticated user to view or update their profile.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(UserSerializer(user, context={'request': request}).data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(request.user, serializer.validated_data)
            return Response({
                'message': 'Profile updated successfully.',
                'user': UserSerializer(request.user, context={'request': request}).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfilePhotoView(APIView):
    """
    Dedicated, authenticated endpoint for profile photo management.
    Allows students and administrators to upload, change, and remove their own profile photo.
    Enforces server-side validation: formats (JPG, JPEG, PNG, WebP), max 5MB, PIL byte verification.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        return self._handle_upload(request)

    def put(self, request):
        return self._handle_upload(request)

    def _handle_upload(self, request):
        image_file = request.FILES.get('photo') or request.FILES.get('image') or request.FILES.get('profile_image')
        if not image_file:
            return Response({'error': 'No image file was provided in the request.'}, status=status.HTTP_400_BAD_REQUEST)

        # File size check (max 5 MB)
        max_size = 5 * 1024 * 1024
        if image_file.size > max_size:
            return Response({'error': f'Image file exceeds maximum allowed size of 5 MB (received {round(image_file.size / (1024*1024), 2)} MB).'}, status=status.HTTP_400_BAD_REQUEST)

        # File extension validation
        ext = os.path.splitext(image_file.name)[1].lower()
        allowed_exts = ['.jpg', '.jpeg', '.png', '.webp']
        if ext not in allowed_exts:
            return Response({'error': f'Unsupported image file extension ({ext}). Allowed formats are JPG, JPEG, PNG, and WebP.'}, status=status.HTTP_400_BAD_REQUEST)

        # Deep image content inspection via Pillow
        try:
            image_file.seek(0)
            img = Image.open(image_file)
            img.verify()

            # Format verification
            if img.format.upper() not in ['JPEG', 'PNG', 'WEBP']:
                return Response({'error': f'Invalid image format ({img.format}). Allowed formats are JPEG, PNG, and WebP.'}, status=status.HTTP_400_BAD_REQUEST)

            image_file.seek(0)
        except Exception as e:
            return Response({'error': f'Uploaded file is corrupted or not a valid image: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # Safely remove old profile image file if exists
        old_image = user.profile_image
        if old_image:
            try:
                old_image.delete(save=False)
            except Exception:
                pass

        user.profile_image = image_file
        user.save(update_fields=['profile_image', 'updated_at'])

        photo_url = request.build_absolute_uri(user.profile_image.url) if hasattr(user.profile_image, 'url') else None
        return Response({
            'message': 'Profile photo updated successfully.',
            'profile_image_url': photo_url,
            'user': UserSerializer(user, context={'request': request}).data
        }, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user
        if user.profile_image:
            try:
                user.profile_image.delete(save=False)
            except Exception:
                pass
            user.profile_image = None
            user.save(update_fields=['profile_image', 'updated_at'])

        return Response({
            'message': 'Profile photo removed successfully.',
            'profile_image_url': None,
            'user': UserSerializer(user, context={'request': request}).data
        }, status=status.HTTP_200_OK)


class UserProfileDetailView(APIView):
    """
    Returns profile information for a specified user ID (accessible to authorized staff).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            target_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Ensure object-level privacy
        if request.user.id != target_user.id and request.user.role not in [User.Role.INSTITUTION_ADMIN, User.Role.PLATFORM_SUPERADMIN]:
            return Response({'error': 'You do not have permission to view this profile.'}, status=status.HTTP_403_FORBIDDEN)

        return Response(UserSerializer(target_user).data, status=status.HTTP_200_OK)


class InstitutionUserListView(APIView):
    """
    Returns users (students and administrators) associated with the current user's institution.
    Accessible to institution admins and platform superadmins.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role not in [User.Role.INSTITUTION_ADMIN, User.Role.PLATFORM_SUPERADMIN] and not user.is_superuser:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        institution = None
        if user.role == User.Role.PLATFORM_SUPERADMIN or user.is_superuser:
            inst_id = request.query_params.get('institution_id')
            if inst_id:
                from apps.institutions.models import Institution
                institution = Institution.objects.filter(id=inst_id).first()
        else:
            admin_prof = getattr(user, 'admin_profile', None)
            institution = getattr(admin_prof, 'institution', None) if admin_prof else None

        from django.db.models import Q
        if institution:
            users_qs = User.objects.filter(
                Q(student_profile__institution=institution) |
                Q(admin_profile__institution=institution)
            ).distinct().select_related('student_profile', 'admin_profile')
        else:
            users_qs = User.objects.all().select_related('student_profile', 'admin_profile')

        role_filter = request.query_params.get('role')
        if role_filter and role_filter != 'All':
            r = role_filter.upper()
            if r in ['STUDENT', 'INSTITUTION_ADMIN', 'PLATFORM_SUPERADMIN']:
                users_qs = users_qs.filter(role=r)

        search = request.query_params.get('search')
        if search:
            s = search.strip()
            users_qs = users_qs.filter(
                Q(full_name__icontains=s) |
                Q(email__icontains=s) |
                Q(student_profile__student_id__icontains=s)
            )

        data = []
        for u in users_qs.order_by('-created_at'):
            photo_url = request.build_absolute_uri(u.profile_image.url) if u.profile_image and hasattr(u.profile_image, 'url') else None
            user_dict = {
                'id': u.id,
                'email': u.email,
                'fullName': u.full_name,
                'full_name': u.full_name,
                'role': 'admin' if u.role == User.Role.INSTITUTION_ADMIN else ('superadmin' if u.role == User.Role.PLATFORM_SUPERADMIN else 'student'),
                'backendRole': u.role,
                'isActive': u.is_active,
                'isVerified': u.is_verified,
                'profileImage': photo_url,
                'profile_image_url': photo_url,
                'dateJoined': u.created_at.isoformat() if u.created_at else None
            }
            if hasattr(u, 'student_profile') and u.student_profile:
                sp = u.student_profile
                user_dict.update({
                    'studentId': sp.student_id or 'AIT-STU',
                    'identifier': sp.student_id or 'AIT-STU',
                    'department': sp.department or sp.course or 'General Campus',
                    'course': sp.course or '',
                    'yearSemester': sp.semester or '',
                    'phone': sp.phone or '',
                    'institutionId': sp.institution_id,
                    'institutionName': sp.institution.name if sp.institution else '',
                    'profileComplete': bool(sp.student_id and sp.address)
                })
            elif hasattr(u, 'admin_profile') and u.admin_profile:
                ap = u.admin_profile
                user_dict.update({
                    'studentId': 'STAFF-AUTH',
                    'identifier': 'STAFF-AUTH',
                    'department': ap.department_name or ap.designation or 'Academic Administration',
                    'designation': ap.designation or 'Administrator',
                    'institutionId': ap.institution_id,
                    'institutionName': ap.institution.name if ap.institution else '',
                    'profileComplete': True
                })
            data.append(user_dict)

        return Response(data, status=status.HTTP_200_OK)
