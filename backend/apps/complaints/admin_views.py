from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Complaint, ComplaintStatusHistory
from .serializers import ComplaintDetailSerializer, ComplaintListSerializer
from apps.accounts.models import User
from apps.accounts.permissions import IsInstitutionAdmin
from apps.institutions.models import InstitutionDepartment
from apps.notifications.models import Notification

class AdminComplaintListView(APIView):
    """
    Administrator complaints desk.
    Returns all non-draft complaints scoped exclusively to the administrator's institution.
    """
    permission_classes = [IsInstitutionAdmin]

    def get(self, request):
        user = request.user
        if user.role == User.Role.PLATFORM_SUPERADMIN or user.is_superuser:
            complaints = Complaint.objects.exclude(status=Complaint.Status.DRAFT)
            inst_param = request.query_params.get('institution_id')
            if inst_param:
                complaints = complaints.filter(institution_id=inst_param)
        else:
            admin_prof = getattr(user, 'admin_profile', None)
            admin_inst = getattr(admin_prof, 'institution', None) if admin_prof else None
            if not admin_inst:
                return Response([], status=status.HTTP_200_OK)
            complaints = Complaint.objects.filter(institution=admin_inst).exclude(status=Complaint.Status.DRAFT)

        # Filters
        st = request.query_params.get('status')
        if st:
            complaints = complaints.filter(status=st.upper())

        pr = request.query_params.get('priority')
        if pr:
            complaints = complaints.filter(priority=pr.upper())

        dept = request.query_params.get('department_id')
        if dept:
            complaints = complaints.filter(assigned_department_id=dept)

        search = request.query_params.get('search')
        if search:
            complaints = complaints.filter(title__icontains=search)

        serializer = ComplaintListSerializer(complaints.order_by('-created_at'), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminComplaintAssignView(APIView):
    """
    Assigns a complaint to a department and/or responsible staff member.
    """
    permission_classes = [IsInstitutionAdmin]

    def post(self, request, pk):
        if str(pk).isdigit():
            complaint = get_object_or_404(Complaint, pk=int(pk))
        else:
            complaint = get_object_or_404(Complaint, complaint_id=pk)

        # Verify institution boundary
        if request.user.role != User.Role.PLATFORM_SUPERADMIN and not request.user.is_superuser:
            if complaint.institution_id != request.user.admin_profile.institution_id:
                return Response({'error': 'Permission denied. Cannot modify complaints from another institution.'}, status=status.HTTP_403_FORBIDDEN)

        dept_id = request.data.get('department_id') or request.data.get('department')
        admin_id = request.data.get('assigned_admin_id') or request.data.get('admin_id')
        internal_note = request.data.get('internal_note', '').strip()
        public_remark = request.data.get('public_remark', '').strip()

        dept = None
        if dept_id:
            dept = get_object_or_404(InstitutionDepartment, pk=dept_id, institution=complaint.institution)
            complaint.assigned_department = dept

        assigned_user = None
        if admin_id:
            assigned_user = get_object_or_404(User, pk=admin_id)
            complaint.assigned_admin = assigned_user

        old_status = complaint.status
        if complaint.status in [Complaint.Status.SUBMITTED, Complaint.Status.UNDER_REVIEW]:
            complaint.status = Complaint.Status.ASSIGNED

        complaint.save()

        # Build assignment summary
        parts = []
        if dept:
            parts.append(f"Department: {dept.name}")
        if assigned_user:
            parts.append(f"Staff: {assigned_user.full_name}")
        assign_desc = ", ".join(parts) or "Department / Admin updated"

        ComplaintStatusHistory.objects.create(
            complaint=complaint,
            previous_status=old_status,
            new_status=complaint.status,
            changed_by=request.user,
            assignment_change=assign_desc,
            public_remark=public_remark or f"Complaint assigned to {dept.name if dept else 'designated department'}.",
            internal_note=internal_note
        )

        # Notify student
        Notification.create_for_event(
            recipient=complaint.student,
            institution=complaint.institution,
            complaint=complaint,
            notification_type=Notification.NotificationType.ASSIGNMENT,
            title=f"Complaint Assigned: {complaint.complaint_id}",
            message=f"Your complaint '{complaint.title}' has been assigned to {dept.name if dept else 'the concerned department'}."
        )

        return Response({
            'message': 'Complaint assigned successfully.',
            'complaint': ComplaintDetailSerializer(complaint, context={'request': request}).data
        }, status=status.HTTP_200_OK)


class AdminComplaintStatusView(APIView):
    """
    Updates the status of a complaint (e.g. UNDER_REVIEW, IN_PROGRESS, AWAITING_STUDENT).
    """
    permission_classes = [IsInstitutionAdmin]

    def post(self, request, pk):
        if str(pk).isdigit():
            complaint = get_object_or_404(Complaint, pk=int(pk))
        else:
            complaint = get_object_or_404(Complaint, complaint_id=pk)

        # Verify institution boundary
        if request.user.role != User.Role.PLATFORM_SUPERADMIN and not request.user.is_superuser:
            admin_prof = getattr(request.user, 'admin_profile', None)
            if admin_prof and admin_prof.institution_id and complaint.institution_id:
                if complaint.institution_id != admin_prof.institution_id:
                    return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status', '').upper()
        if new_status not in Complaint.Status.values:
            return Response({'error': f'Invalid status. Valid choices are: {Complaint.Status.values}'}, status=status.HTTP_400_BAD_REQUEST)

        public_remark = request.data.get('public_remark', '').strip()
        internal_note = request.data.get('internal_note', '').strip()
        dept_val = request.data.get('department')
        assigned_to_val = request.data.get('assigned_to')

        old_status = complaint.status
        complaint.status = new_status

        assignment_desc = ''
        if dept_val:
            dept = None
            if str(dept_val).isdigit():
                dept = InstitutionDepartment.objects.filter(id=int(dept_val), institution=complaint.institution).first()
            else:
                dept = InstitutionDepartment.objects.filter(name__iexact=str(dept_val).strip(), institution=complaint.institution).first()
            if dept:
                complaint.assigned_department = dept
                assignment_desc = f"Assigned to {dept.name}"

        if new_status == Complaint.Status.RESOLVED and not complaint.resolution_timestamp:
            complaint.resolution_timestamp = timezone.now()
            if public_remark:
                complaint.resolution_details = public_remark

        complaint.save()

        ComplaintStatusHistory.objects.create(
            complaint=complaint,
            previous_status=old_status,
            new_status=new_status,
            changed_by=request.user,
            assignment_change=assignment_desc,
            public_remark=public_remark or f"Status changed to {complaint.get_status_display()}.",
            internal_note=internal_note
        )

        # Notify student with contextual alert
        notif_type = Notification.NotificationType.STATUS_CHANGE
        if new_status == Complaint.Status.AWAITING_STUDENT:
            notif_type = Notification.NotificationType.INFO_REQUESTED
            notif_title = f"Information Requested: {complaint.complaint_id}"
            notif_msg = f"Administrative action requires clarification on your complaint '{complaint.title}'. Remark: {public_remark or 'Please inspect your complaint details.'}"
        elif new_status == Complaint.Status.UNDER_REVIEW:
            notif_title = f"Under Review: {complaint.complaint_id}"
            notif_msg = f"Your complaint '{complaint.title}' is now actively under administrative review."
        elif new_status == Complaint.Status.IN_PROGRESS:
            notif_title = f"In Progress: {complaint.complaint_id}"
            notif_msg = f"Work has begun on your complaint '{complaint.title}'."
        else:
            notif_title = f"Status Update: {complaint.complaint_id}"
            notif_msg = f"Your complaint '{complaint.title}' status is now {complaint.get_status_display()}."

        Notification.create_for_event(
            recipient=complaint.student,
            institution=complaint.institution,
            complaint=complaint,
            notification_type=notif_type,
            title=notif_title,
            message=notif_msg
        )

        return Response({
            'message': f'Status updated to {complaint.get_status_display()}.',
            'complaint': ComplaintDetailSerializer(complaint, context={'request': request}).data
        }, status=status.HTTP_200_OK)


class AdminComplaintRemarksView(APIView):
    """
    Adds a public remark to the complaint timeline visible to the student.
    """
    permission_classes = [IsInstitutionAdmin]

    def post(self, request, pk):
        if str(pk).isdigit():
            complaint = get_object_or_404(Complaint, pk=int(pk))
        else:
            complaint = get_object_or_404(Complaint, complaint_id=pk)

        if request.user.role != User.Role.PLATFORM_SUPERADMIN and not request.user.is_superuser:
            if complaint.institution_id != request.user.admin_profile.institution_id:
                return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        remark = request.data.get('remark', '').strip()
        if not remark:
            return Response({'error': 'Remark text is required.'}, status=status.HTTP_400_BAD_REQUEST)

        ComplaintStatusHistory.objects.create(
            complaint=complaint,
            previous_status=complaint.status,
            new_status=complaint.status,
            changed_by=request.user,
            public_remark=remark
        )

        # Notify student
        Notification.create_for_event(
            recipient=complaint.student,
            institution=complaint.institution,
            complaint=complaint,
            notification_type=Notification.NotificationType.REMARK,
            title=f"New Remark on {complaint.complaint_id}",
            message=f"Administrator remarked: {remark}"
        )

        return Response({'message': 'Public remark added.'}, status=status.HTTP_200_OK)


class AdminComplaintInternalNotesView(APIView):
    """
    Adds a confidential internal note to the complaint (never visible to student).
    """
    permission_classes = [IsInstitutionAdmin]

    def post(self, request, pk):
        if str(pk).isdigit():
            complaint = get_object_or_404(Complaint, pk=int(pk))
        else:
            complaint = get_object_or_404(Complaint, complaint_id=pk)

        if request.user.role != User.Role.PLATFORM_SUPERADMIN and not request.user.is_superuser:
            if complaint.institution_id != request.user.admin_profile.institution_id:
                return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        note = request.data.get('internal_note', '').strip()
        if not note:
            return Response({'error': 'Internal note text is required.'}, status=status.HTTP_400_BAD_REQUEST)

        ComplaintStatusHistory.objects.create(
            complaint=complaint,
            previous_status=complaint.status,
            new_status=complaint.status,
            changed_by=request.user,
            internal_note=note
        )

        return Response({'message': 'Internal note recorded.'}, status=status.HTTP_200_OK)


class AdminComplaintResolutionView(APIView):
    """
    Formally records resolution details and closes the complaint as RESOLVED.
    """
    permission_classes = [IsInstitutionAdmin]

    def post(self, request, pk):
        if str(pk).isdigit():
            complaint = get_object_or_404(Complaint, pk=int(pk))
        else:
            complaint = get_object_or_404(Complaint, complaint_id=pk)

        if request.user.role != User.Role.PLATFORM_SUPERADMIN and not request.user.is_superuser:
            if complaint.institution_id != request.user.admin_profile.institution_id:
                return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        resolution_details = request.data.get('resolution_details', '').strip()
        internal_note = request.data.get('internal_note', '').strip()

        if not resolution_details:
            return Response({'error': 'Resolution details are required.'}, status=status.HTTP_400_BAD_REQUEST)

        old_status = complaint.status
        complaint.status = Complaint.Status.RESOLVED
        complaint.resolution_details = resolution_details
        complaint.resolution_timestamp = timezone.now()
        complaint.save()

        ComplaintStatusHistory.objects.create(
            complaint=complaint,
            previous_status=old_status,
            new_status=Complaint.Status.RESOLVED,
            changed_by=request.user,
            public_remark=f"Resolution: {resolution_details}",
            internal_note=internal_note
        )

        # Notify student
        Notification.create_for_event(
            recipient=complaint.student,
            institution=complaint.institution,
            complaint=complaint,
            notification_type=Notification.NotificationType.RESOLUTION,
            title=f"Complaint Resolved: {complaint.complaint_id}",
            message=f"Your complaint '{complaint.title}' has been marked as resolved: {resolution_details}"
        )

        return Response({
            'message': 'Complaint marked as resolved.',
            'complaint': ComplaintDetailSerializer(complaint, context={'request': request}).data
        }, status=status.HTTP_200_OK)
