from rest_framework import permissions
from .models import User

class IsStudent(permissions.BasePermission):
    """
    Allows access only to authenticated users with the STUDENT role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == User.Role.STUDENT
        )


class IsInstitutionAdmin(permissions.BasePermission):
    """
    Allows access only to authenticated users with an APPROVED INSTITUTION_ADMIN profile.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role == User.Role.PLATFORM_SUPERADMIN or request.user.is_superuser:
            return True
        if request.user.role == User.Role.INSTITUTION_ADMIN:
            admin_profile = getattr(request.user, 'admin_profile', None)
            if admin_profile:
                return admin_profile.approval_status != 'REJECTED'
            return bool(request.user.is_verified or request.user.is_staff)
        return False


class IsPlatformSuperAdmin(permissions.BasePermission):
    """
    Allows access only to Platform Superadmins.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == User.Role.PLATFORM_SUPERADMIN or request.user.is_superuser)
        )


class IsAdminOrSuperAdmin(permissions.BasePermission):
    """
    Allows access to verified institution admins or platform superadmins.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role == User.Role.PLATFORM_SUPERADMIN or request.user.is_superuser:
            return True
        if request.user.role == User.Role.INSTITUTION_ADMIN:
            admin_profile = getattr(request.user, 'admin_profile', None)
            if admin_profile:
                return admin_profile.approval_status != 'REJECTED'
            return bool(request.user.is_verified or request.user.is_staff)
        return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission allowing the owner student or their institution's administrator.
    """
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role == User.Role.PLATFORM_SUPERADMIN or request.user.is_superuser:
            return True
        # If object has a student attribute (e.g. Complaint)
        if hasattr(obj, 'student') and obj.student == request.user:
            return True
        # If object has an institution attribute, admin must belong to the same institution
        if hasattr(obj, 'institution') and request.user.role == User.Role.INSTITUTION_ADMIN:
            admin_profile = getattr(request.user, 'admin_profile', None)
            if admin_profile and admin_profile.institution_id and obj.institution_id:
                return bool(admin_profile.institution_id == obj.institution_id and admin_profile.approval_status != 'REJECTED')
            return bool(request.user.is_verified or request.user.is_staff)
        return False
