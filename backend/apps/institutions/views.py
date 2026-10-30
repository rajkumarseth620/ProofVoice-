from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from .models import (
    Institution,
    InstitutionDepartment,
    ComplaintCategory,
    ComplaintRecipientConfiguration,
    InstitutionRegistrationRequest,
    AdminAccessRequest
)
from .serializers import (
    InstitutionSerializer,
    InstitutionDepartmentSerializer,
    ComplaintCategorySerializer,
    ComplaintRecipientConfigurationSerializer,
    InstitutionRegistrationRequestSerializer,
    AdminAccessRequestSerializer
)
from apps.accounts.models import User, AdministratorProfile
from apps.accounts.permissions import IsInstitutionAdmin, IsPlatformSuperAdmin, IsAdminOrSuperAdmin

def get_user_institution(user):
    """Helper to determine the authenticated user's institution."""
    if user.role == User.Role.STUDENT and hasattr(user, 'student_profile') and user.student_profile:
        return user.student_profile.institution
    elif user.role == User.Role.INSTITUTION_ADMIN and hasattr(user, 'admin_profile') and user.admin_profile:
        inst = getattr(user.admin_profile, 'institution', None)
        if inst:
            return inst
    from apps.institutions.models import Institution
    return Institution.objects.first()


class InstitutionListView(APIView):
    """
    Public / Authenticated list of active, verified institutions.
    Used for registration dropdowns, directory, and discovery.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Platform superadmins can see all institutions including pending/suspended
        if request.user.is_authenticated and (request.user.role == User.Role.PLATFORM_SUPERADMIN or request.user.is_superuser):
            institutions = Institution.objects.all().order_by('name')
        else:
            institutions = Institution.objects.filter(
                verification_status=Institution.VerificationStatus.VERIFIED,
                is_active=True
            ).order_by('name')

        serializer = InstitutionSerializer(institutions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InstitutionDetailView(APIView):
    """
    Retrieve details of a specific institution by ID or code.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            if str(pk).isdigit():
                institution = Institution.objects.get(pk=int(pk))
            else:
                institution = Institution.objects.get(code=pk)
        except Institution.DoesNotExist:
            return Response({'error': 'Institution not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = InstitutionSerializer(institution)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InstitutionMeView(APIView):
    """
    Returns the institution details associated with the current authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        institution = get_user_institution(request.user)
        if not institution:
            return Response({'error': 'No institution associated with this user.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = InstitutionSerializer(institution)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InstitutionSettingsView(APIView):
    """
    Allows authorized institution administrators to view and update their institution profile.
    """
    permission_classes = [IsInstitutionAdmin]

    def get(self, request, pk=None):
        institution = get_user_institution(request.user)
        if not institution:
            return Response({'error': 'No institution associated with this administrator.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = InstitutionSerializer(institution)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk=None):
        institution = get_user_institution(request.user)
        if not institution:
            return Response({'error': 'No institution associated with this administrator.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = InstitutionSerializer(institution, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Institution settings updated successfully.',
                'institution': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InstitutionDepartmentListView(APIView):
    """
    List and create departments for the authenticated user's institution.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        institution = get_user_institution(request.user)
        # Fallback to query param if superadmin
        if not institution and request.user.role == User.Role.PLATFORM_SUPERADMIN:
            inst_id = request.query_params.get('institution_id')
            if inst_id:
                institution = Institution.objects.filter(id=inst_id).first()

        if not institution:
            return Response({'error': 'Institution scope required.'}, status=status.HTTP_400_BAD_REQUEST)

        departments = InstitutionDepartment.objects.filter(institution=institution, is_active=True).order_by('name')
        serializer = InstitutionDepartmentSerializer(departments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not (request.user.role in [User.Role.INSTITUTION_ADMIN, User.Role.PLATFORM_SUPERADMIN]):
            return Response({'error': 'Only administrators can create departments.'}, status=status.HTTP_403_FORBIDDEN)

        institution = get_user_institution(request.user)
        if not institution and request.user.role == User.Role.PLATFORM_SUPERADMIN:
            inst_id = request.data.get('institution') or request.data.get('institution_id')
            institution = get_object_or_404(Institution, pk=inst_id)

        if not institution:
            return Response({'error': 'Institution scope required.'}, status=status.HTTP_400_BAD_REQUEST)

        name = request.data.get('name', '').strip()
        code = request.data.get('code', '').strip()
        contact_email = request.data.get('contact_email', '').strip()

        if not name:
            return Response({'error': 'Department name is required.'}, status=status.HTTP_400_BAD_REQUEST)

        department, created = InstitutionDepartment.objects.get_or_create(
            institution=institution,
            name=name,
            defaults={'code': code, 'contact_email': contact_email, 'is_active': True}
        )
        if not created:
            department.is_active = True
            if code:
                department.code = code
            if contact_email:
                department.contact_email = contact_email
            department.save()

        return Response(InstitutionDepartmentSerializer(department).data, status=status.HTTP_201_CREATED)


class InstitutionCategoryListView(APIView):
    """
    List and create complaint categories for the authenticated user's institution.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        institution = get_user_institution(request.user)
        if not institution and request.user.role == User.Role.PLATFORM_SUPERADMIN:
            inst_id = request.query_params.get('institution_id')
            if inst_id:
                institution = Institution.objects.filter(id=inst_id).first()

        if not institution:
            return Response({'error': 'Institution scope required.'}, status=status.HTTP_400_BAD_REQUEST)

        categories = ComplaintCategory.objects.filter(institution=institution, is_active=True).order_by('name')
        serializer = ComplaintCategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not (request.user.role in [User.Role.INSTITUTION_ADMIN, User.Role.PLATFORM_SUPERADMIN]):
            return Response({'error': 'Only administrators can create complaint categories.'}, status=status.HTTP_403_FORBIDDEN)

        institution = get_user_institution(request.user)
        if not institution and request.user.role == User.Role.PLATFORM_SUPERADMIN:
            inst_id = request.data.get('institution') or request.data.get('institution_id')
            institution = get_object_or_404(Institution, pk=inst_id)

        if not institution:
            return Response({'error': 'Institution scope required.'}, status=status.HTTP_400_BAD_REQUEST)

        name = request.data.get('name', '').strip()
        description = request.data.get('description', '').strip()
        dept_id = request.data.get('default_department') or request.data.get('default_department_id')

        if not name:
            return Response({'error': 'Category name is required.'}, status=status.HTTP_400_BAD_REQUEST)

        default_dept = None
        if dept_id:
            default_dept = InstitutionDepartment.objects.filter(id=dept_id, institution=institution).first()

        category, created = ComplaintCategory.objects.get_or_create(
            institution=institution,
            name=name,
            defaults={'description': description, 'default_department': default_dept, 'is_active': True}
        )
        if not created:
            category.is_active = True
            if description:
                category.description = description
            if default_dept:
                category.default_department = default_dept
            category.save()

        return Response(ComplaintCategorySerializer(category).data, status=status.HTTP_201_CREATED)


class InstitutionRegistrationRequestView(APIView):
    """
    Allows submitting and listing institution registration requests.
    Superadmins can see all requests; applicants see their own.
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def get(self, request):
        if request.user.role == User.Role.PLATFORM_SUPERADMIN or request.user.is_superuser:
            requests = InstitutionRegistrationRequest.objects.all().order_by('-created_at')
        else:
            requests = InstitutionRegistrationRequest.objects.filter(applicant_user=request.user).order_by('-created_at')

        serializer = InstitutionRegistrationRequestSerializer(requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        name = request.data.get('institution_name', '').strip()
        inst_type = request.data.get('institution_type', Institution.InstitutionType.UNIVERSITY)
        email = request.data.get('official_email', '').strip()
        address = request.data.get('official_address', '').strip()
        state_name = request.data.get('state', '').strip()
        city_name = request.data.get('city', '').strip()
        website = request.data.get('website', '').strip()
        designation = request.data.get('applicant_designation', 'Dean / Administrator').strip()

        if not name or not email or not address:
            return Response({'error': 'Institution name, official email, and address are required.'}, status=status.HTTP_400_BAD_REQUEST)

        req = InstitutionRegistrationRequest.objects.create(
            institution_name=name,
            institution_type=inst_type,
            official_email=email,
            official_address=address,
            state=state_name,
            city=city_name,
            website=website,
            applicant_user=request.user,
            applicant_designation=designation,
            status=InstitutionRegistrationRequest.Status.PENDING
        )
        return Response(InstitutionRegistrationRequestSerializer(req).data, status=status.HTTP_201_CREATED)


class InstitutionRegistrationApproveView(APIView):
    """
    Platform Superadmin endpoint to approve or reject an institution registration request.
    """
    permission_classes = [IsPlatformSuperAdmin]

    def post(self, request, pk):
        req = get_object_or_404(InstitutionRegistrationRequest, pk=pk)
        action = request.data.get('action', 'approve').lower()

        if action == 'approve':
            # Create the verified Institution
            slug = slugify(req.institution_name)[:90]
            # Ensure unique slug
            counter = 1
            unique_slug = slug
            while Institution.objects.filter(code=unique_slug).exists():
                unique_slug = f"{slug}-{counter}"
                counter += 1

            institution = Institution.objects.create(
                code=unique_slug,
                name=req.institution_name,
                institution_type=req.institution_type,
                official_email=req.official_email,
                official_address=req.official_address,
                state=req.state,
                city=req.city,
                website=req.website,
                verification_status=Institution.VerificationStatus.VERIFIED,
                is_active=True
            )

            # Seed default departments and categories
            default_depts = [
                ('Estate & Maintenance', 'EST'),
                ('Hostel Administration', 'HST'),
                ('Academic Affairs', 'ACD'),
                ('IT & Network Services', 'ITS'),
                ('Dean of Student Welfare', 'DSW')
            ]
            created_depts = {}
            for d_name, d_code in default_depts:
                created_depts[d_name] = InstitutionDepartment.objects.create(
                    institution=institution,
                    name=d_name,
                    code=d_code
                )

            default_categories = [
                ('Infrastructure & Maintenance', created_depts['Estate & Maintenance']),
                ('Hostel & Accommodation', created_depts['Hostel Administration']),
                ('Academic & Faculty', created_depts['Academic Affairs']),
                ('Sanitation & Hygiene', created_depts['Estate & Maintenance']),
                ('IT & Network Issues', created_depts['IT & Network Services']),
                ('General Administration', created_depts['Dean of Student Welfare'])
            ]
            for cat_name, dept_obj in default_categories:
                ComplaintCategory.objects.create(
                    institution=institution,
                    name=cat_name,
                    default_department=dept_obj
                )

            # Configure default recipient as 'The Dean'
            ComplaintRecipientConfiguration.objects.create(
                institution=institution,
                recipient_designation='The Dean',
                recipient_name='',
                recipient_address=f"Office of the Dean, {institution.name}\n{institution.official_address}"
            )

            # Update request
            req.status = InstitutionRegistrationRequest.Status.APPROVED
            req.created_institution = institution
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.save()

            # Assign and approve applicant admin profile
            admin_user = req.applicant_user
            admin_user.role = User.Role.INSTITUTION_ADMIN
            admin_user.is_verified = True
            admin_user.save()

            admin_profile, _ = AdministratorProfile.objects.get_or_create(user=admin_user)
            admin_profile.institution = institution
            admin_profile.designation = req.applicant_designation
            admin_profile.approval_status = AdministratorProfile.ApprovalStatus.APPROVED
            admin_profile.approved_by = request.user
            admin_profile.approved_at = timezone.now()
            admin_profile.save()

            return Response({
                'message': f'Institution "{institution.name}" has been approved and verified.',
                'institution': InstitutionSerializer(institution).data,
                'request': InstitutionRegistrationRequestSerializer(req).data
            }, status=status.HTTP_200_OK)

        elif action == 'reject':
            req.status = InstitutionRegistrationRequest.Status.REJECTED
            req.rejection_reason = request.data.get('reason', 'Institutional criteria not met.')
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.save()
            return Response({
                'message': 'Registration request rejected.',
                'request': InstitutionRegistrationRequestSerializer(req).data
            }, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid action. Must be approve or reject.'}, status=status.HTTP_400_BAD_REQUEST)


class AdminAccessRequestView(APIView):
    """
    Submit and list administrator access requests to join an existing institution.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role == User.Role.PLATFORM_SUPERADMIN or request.user.is_superuser:
            requests = AdminAccessRequest.objects.all().order_by('-created_at')
        elif request.user.role == User.Role.INSTITUTION_ADMIN:
            inst = get_user_institution(request.user)
            requests = AdminAccessRequest.objects.filter(institution=inst).order_by('-created_at')
        else:
            requests = AdminAccessRequest.objects.filter(user=request.user).order_by('-created_at')

        serializer = AdminAccessRequestSerializer(requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        inst_id = request.data.get('institution') or request.data.get('institution_id')
        designation = request.data.get('designation', 'Staff Administrator').strip()
        department_name = request.data.get('department_name', '').strip()

        institution = get_object_or_404(Institution, pk=inst_id)

        req = AdminAccessRequest.objects.create(
            user=request.user,
            institution=institution,
            designation=designation,
            department_name=department_name,
            status=AdminAccessRequest.Status.PENDING
        )
        return Response(AdminAccessRequestSerializer(req).data, status=status.HTTP_201_CREATED)


class AdminAccessRequestApproveView(APIView):
    """
    Approve or reject an administrator access request.
    Authorized institution admins (or platform superadmins) can approve requests for their institution.
    """
    permission_classes = [IsAdminOrSuperAdmin]

    def post(self, request, pk):
        access_req = get_object_or_404(AdminAccessRequest, pk=pk)

        # Enforce multi-tenant isolation
        if request.user.role == User.Role.INSTITUTION_ADMIN:
            admin_inst = get_user_institution(request.user)
            if admin_inst.id != access_req.institution_id:
                return Response({'error': 'Cannot manage access requests for another institution.'}, status=status.HTTP_403_FORBIDDEN)

        action = request.data.get('action', 'approve').lower()
        if action == 'approve':
            access_req.status = AdminAccessRequest.Status.APPROVED
            access_req.reviewed_by = request.user
            access_req.reviewed_at = timezone.now()
            access_req.save()

            target_user = access_req.user
            target_user.role = User.Role.INSTITUTION_ADMIN
            target_user.is_verified = True
            target_user.save()

            admin_profile, _ = AdministratorProfile.objects.get_or_create(user=target_user)
            admin_profile.institution = access_req.institution
            admin_profile.designation = access_req.designation
            admin_profile.department_name = access_req.department_name
            admin_profile.approval_status = AdministratorProfile.ApprovalStatus.APPROVED
            admin_profile.approved_by = request.user
            admin_profile.approved_at = timezone.now()
            admin_profile.save()

            return Response({
                'message': f'Administrator access for {target_user.full_name} approved.',
                'request': AdminAccessRequestSerializer(access_req).data
            }, status=status.HTTP_200_OK)

        elif action == 'reject':
            access_req.status = AdminAccessRequest.Status.REJECTED
            access_req.reviewed_by = request.user
            access_req.reviewed_at = timezone.now()
            access_req.save()
            return Response({
                'message': 'Administrator access request rejected.',
                'request': AdminAccessRequestSerializer(access_req).data
            }, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid action. Must be approve or reject.'}, status=status.HTTP_400_BAD_REQUEST)
