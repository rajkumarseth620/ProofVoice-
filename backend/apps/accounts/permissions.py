from rest_framework import permissions
from .models import User, AdministratorProfile

class IsStudent(permissions.BasePermission):
    """
    Allows access only to authenticated users with the STUDENT role
    whose institution is not suspended.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.role == User.Role.STUDENT):
            return False
        student_profile = getattr(request.user, 'student_profile', None)
        if student_profile and student_profile.institution:
            if student_profile.institution.verification_status == 'SUSPENDED':
                return False
        return True


class IsInstitutionAdmin(permissions.BasePermission):
    """
    Allows access only to authenticated users with an APPROVED INSTITUTION_ADMIN profile
    whose institution is VERIFIED and not suspended.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role == User.Role.PLATFORM_SUPERADMIN or request.user.is_superuser:
            return True
        if request.user.role == User.Role.INSTITUTION_ADMIN:
            admin_profile = getattr(request.user, 'admin_profile', None)
            if not admin_profile:
                return False
            if admin_profile.approval_status != AdministratorProfile.ApprovalStatus.APPROVED:
                return False
            inst = admin_profile.institution
            if not inst or inst.verification_status != 'VERIFIED' or not inst.is_active or inst.verification_status == 'SUSPENDED':
                return False
            return True
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
    Allows access to verified institution admins (with approved institution) or platform superadmins.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role == User.Role.PLATFORM_SUPERADMIN or request.user.is_superuser:
            return True
        if request.user.role == User.Role.INSTITUTION_ADMIN:
            admin_profile = getattr(request.user, 'admin_profile', None)
            if not admin_profile:
                return False
            if admin_profile.approval_status != AdministratorProfile.ApprovalStatus.APPROVED:
                return False
            inst = admin_profile.institution
            if not inst or inst.verification_status != 'VERIFIED' or not inst.is_active or inst.verification_status == 'SUSPENDED':
                return False
            return True
        return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission allowing the owner student or their institution's administrator.
    Strict multi-tenant boundary check: an institution administrator can NEVER access another institution's objects.
    """
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role == User.Role.PLATFORM_SUPERADMIN or request.user.is_superuser:
            return True
        # If object has a student attribute (e.g. Complaint)
        if hasattr(obj, 'student') and obj.student == request.user:
            return True
        # If object has an institution attribute, admin must belong to the exact same verified institution
        if hasattr(obj, 'institution') and request.user.role == User.Role.INSTITUTION_ADMIN:
            admin_profile = getattr(request.user, 'admin_profile', None)
            if admin_profile and admin_profile.institution_id and obj.institution_id:
                if admin_profile.approval_status == AdministratorProfile.ApprovalStatus.APPROVED:
                    return bool(admin_profile.institution_id == obj.institution_id)
            return False
        return False
