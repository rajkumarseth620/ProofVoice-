from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Complaint, ComplaintStatusHistory, ComplaintAttachment
from .serializers import (
    ComplaintCreateSerializer,
    ComplaintDetailSerializer,
    ComplaintListSerializer,
    ComplaintStatusHistorySerializer,
    ComplaintAttachmentSerializer
)
from .services import FormalApplicationGenerator
from apps.accounts.models import User
from apps.accounts.permissions import IsStudent, IsOwnerOrAdmin
from apps.institutions.models import Institution, ComplaintCategory
from apps.notifications.models import Notification

class ComplaintListCreateView(APIView):
    """
    List student complaints or create a new complaint.
    Strictly isolated: Students can only view their own complaints.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == User.Role.STUDENT:
            complaints = Complaint.objects.filter(student=user).order_by('-created_at')
        elif user.role == User.Role.INSTITUTION_ADMIN and hasattr(user, 'admin_profile'):
            inst = user.admin_profile.institution
            complaints = Complaint.objects.filter(institution=inst).exclude(status=Complaint.Status.DRAFT).order_by('-created_at')
        elif user.role == User.Role.PLATFORM_SUPERADMIN or user.is_superuser:
            complaints = Complaint.objects.all().order_by('-created_at')
        else:
            complaints = Complaint.objects.none()

        # Optional status filtering
        status_filter = request.query_params.get('status')
        if status_filter:
            complaints = complaints.filter(status=status_filter.upper())

        # Optional search
        q = request.query_params.get('search')
        if q:
            complaints = complaints.filter(title__icontains=q)

        serializer = ComplaintListSerializer(complaints, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if request.user.role != User.Role.STUDENT:
            return Response({'error': 'Only registered students can lodge complaints.'}, status=status.HTTP_403_FORBIDDEN)

        # Ensure student has an institution assigned
        profile = getattr(request.user, 'student_profile', None)
        if not profile or not profile.institution:
            return Response({
                'error': 'Institutional membership required. Please select your college/university in your profile before lodging a complaint.'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = ComplaintCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            complaint = serializer.save()
            return Response({
                'message': 'Complaint lodged successfully.',
                'complaint': ComplaintDetailSerializer(complaint, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ComplaintDetailView(APIView):
    """
    Retrieve or update a specific complaint by complaint_id or pk.
    Enforces student ownership and administrator institution boundaries.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_object(self, lookup):
        if str(lookup).isdigit():
            obj = get_object_or_404(Complaint, pk=int(lookup))
        else:
            obj = get_object_or_404(Complaint, complaint_id=lookup)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, pk):
        complaint = self.get_object(pk)
        serializer = ComplaintDetailSerializer(complaint, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        complaint = self.get_object(pk)

        # Student ownership check
        if request.user.role == User.Role.STUDENT:
            if complaint.student != request.user:
                return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
            if complaint.status in [Complaint.Status.RESOLVED, Complaint.Status.REJECTED]:
                return Response({'error': 'Closed or resolved complaints cannot be edited.'}, status=status.HTTP_400_BAD_REQUEST)

        was_submitted = (complaint.status != Complaint.Status.DRAFT)

        for field in ['title', 'original_description', 'final_submitted_application', 'campus', 'building', 'floor', 'room_number', 'full_issue_location', 'priority']:
            if field in request.data:
                setattr(complaint, field, request.data[field])

        # Also support description and location aliases
        if 'description' in request.data:
            complaint.original_description = request.data['description']
            if not complaint.final_submitted_application:
                complaint.final_submitted_application = request.data['description']
        if 'application' in request.data or 'formal_application' in request.data:
            complaint.final_submitted_application = request.data.get('application') or request.data.get('formal_application')
        if 'location' in request.data:
            complaint.full_issue_location = request.data['location']

        if 'category_id' in request.data:
            cat_id = request.data['category_id']
            if cat_id:
                complaint.category = ComplaintCategory.objects.filter(id=cat_id, institution=complaint.institution).first()
            else:
                complaint.category = None

        complaint.save()

        if was_submitted:
            ComplaintStatusHistory.objects.create(
                complaint=complaint,
                previous_status=complaint.status,
                new_status=complaint.status,
                changed_by=request.user,
                public_remark="Student updated formal application details."
            )

        return Response({
            'success': True,
            'message': 'Complaint application updated successfully.',
            'complaint': ComplaintDetailSerializer(complaint, context={'request': request}).data
        }, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        complaint = self.get_object(pk)
        if request.user.role == User.Role.STUDENT and complaint.student != request.user:
            return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        complaint_id = complaint.complaint_id
        complaint.delete()
        return Response({
            'success': True,
            'message': f'Complaint {complaint_id} deleted successfully.'
        }, status=status.HTTP_200_OK)


class ComplaintSubmitView(APIView):
    """
    Explicitly submits a drafted complaint to institutional administration.
    Moves status to SUBMITTED and creates timeline history.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if str(pk).isdigit():
            complaint = get_object_or_404(Complaint, pk=int(pk), student=request.user)
        else:
            complaint = get_object_or_404(Complaint, complaint_id=pk, student=request.user)

        if complaint.status != Complaint.Status.DRAFT:
            return Response({'error': 'This complaint has already been submitted.'}, status=status.HTTP_400_BAD_REQUEST)

        # Student can optionally provide final edited application text at submission time
        if 'final_application' in request.data and request.data['final_application'].strip():
            complaint.final_submitted_application = request.data['final_application'].strip()

        # If no formal application was stored yet, generate it now
        if not complaint.final_submitted_application:
            letter_data = FormalApplicationGenerator.generate_letter(
                student=request.user,
                institution=complaint.institution,
                title=complaint.title,
                description=complaint.original_description,
                category=complaint.category,
                location_details=complaint.full_issue_location
            )
            complaint.final_submitted_application = letter_data['application_text']

        complaint.status = Complaint.Status.SUBMITTED
        complaint.submission_timestamp = timezone.now()
        complaint.save()

        # Check if verified administrator exists for this institution
        admins = User.objects.filter(
            role=User.Role.INSTITUTION_ADMIN,
            admin_profile__institution=complaint.institution,
            is_active=True
        )
        has_verified_admin = admins.exists()

        public_remark = (
            'Formal complaint submitted to institutional administration.'
            if has_verified_admin
            else 'Formal complaint lodged. Awaiting institutional administrator onboarding for review and resolution.'
        )

        # Record timeline
        ComplaintStatusHistory.objects.create(
            complaint=complaint,
            previous_status=Complaint.Status.DRAFT,
            new_status=Complaint.Status.SUBMITTED,
            changed_by=request.user,
            public_remark=public_remark
        )

        # Notify submitting student
        Notification.create_for_event(
            recipient=request.user,
            institution=complaint.institution,
            complaint=complaint,
            notification_type=Notification.NotificationType.SUBMISSION,
            title=f"Complaint Submitted: {complaint.complaint_id}",
            message=f"Your complaint '{complaint.title}' has been successfully logged with tracking ID {complaint.complaint_id}."
        )

        # Notify institution administrators if present
        for admin_user in admins:
            Notification.create_for_event(
                recipient=admin_user,
                institution=complaint.institution,
                complaint=complaint,
                notification_type=Notification.NotificationType.STATUS_CHANGE,
                title=f"New Complaint Submitted: {complaint.complaint_id}",
                message=f"A new complaint '{complaint.title}' has been submitted by {request.user.full_name}."
            )

        submit_message = (
            'Complaint submitted successfully.'
            if has_verified_admin
            else 'Complaint submitted successfully. Your institution does not have a verified administrator yet; complaints are queued and will be reviewed once an administrator is onboarded.'
        )

        return Response({
            'message': submit_message,
            'complaint': ComplaintDetailSerializer(complaint, context={'request': request}).data
        }, status=status.HTTP_200_OK)


class ComplaintTimelineView(APIView):
    """
    Returns the status progression timeline for a complaint.
    Confidential internal admin notes are automatically omitted for students.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get(self, request, pk):
        if str(pk).isdigit():
            complaint = get_object_or_404(Complaint, pk=int(pk))
        else:
            complaint = get_object_or_404(Complaint, complaint_id=pk)

        # Permission check
        if request.user.role == User.Role.STUDENT and complaint.student != request.user:
            return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
        if request.user.role == User.Role.INSTITUTION_ADMIN:
            admin_inst = getattr(request.user.admin_profile, 'institution', None)
            if not admin_inst or admin_inst.id != complaint.institution_id:
                return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        history = complaint.status_history.all().order_by('timestamp')
        serializer = ComplaintStatusHistorySerializer(history, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class GenerateApplicationView(APIView):
    """
    Generates a formal letter draft addressed to The Dean or configured authority
    based on student profile and submitted complaint details.
    Does NOT save or submit the complaint automatically.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk=None):
        student = request.user
        profile = getattr(student, 'student_profile', None)

        if not profile or not profile.institution:
            return Response({
                'error': 'Institutional membership required. Please select your college/university in your profile.'
            }, status=status.HTTP_400_BAD_REQUEST)

        institution = profile.institution

        if pk:
            # Generate for existing complaint
            if str(pk).isdigit():
                complaint = get_object_or_404(Complaint, pk=int(pk), student=student)
            else:
                complaint = get_object_or_404(Complaint, complaint_id=pk, student=student)
            title = complaint.title
            description = complaint.original_description
            category = complaint.category
            location = complaint.full_issue_location
        else:
            title = request.data.get('title', '').strip()
            description = request.data.get('description', '').strip() or request.data.get('original_description', '').strip()
            cat_id = request.data.get('category_id') or request.data.get('category')
            category = ComplaintCategory.objects.filter(id=cat_id, institution=institution).first() if cat_id else None
            location = {
                'campus': request.data.get('campus', ''),
                'building': request.data.get('building', ''),
                'floor': request.data.get('floor', ''),
                'room_number': request.data.get('room_number', '')
            }

        if not title or not description:
            return Response({'error': 'Title and description are required to generate a formal letter.'}, status=status.HTTP_400_BAD_REQUEST)

        result = FormalApplicationGenerator.generate_letter(
            student=student,
            institution=institution,
            title=title,
            description=description,
            category=category,
            location_details=location
        )

        return Response(result, status=status.HTTP_200_OK)


class ComplaintReopenView(APIView):
    """
    Allows a student to request reopening a resolved complaint if the issue persists.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if str(pk).isdigit():
            complaint = get_object_or_404(Complaint, pk=int(pk), student=request.user)
        else:
            complaint = get_object_or_404(Complaint, complaint_id=pk, student=request.user)

        if complaint.status != Complaint.Status.RESOLVED and complaint.status != Complaint.Status.REJECTED:
            return Response({'error': 'Only resolved or rejected complaints can be reopened.'}, status=status.HTTP_400_BAD_REQUEST)

        reason = request.data.get('reason', 'Problem persists or was not satisfactorily resolved.')

        old_status = complaint.status
        complaint.status = Complaint.Status.REOPENED
        complaint.save()

        ComplaintStatusHistory.objects.create(
            complaint=complaint,
            previous_status=old_status,
            new_status=Complaint.Status.REOPENED,
            changed_by=request.user,
            public_remark=f"Student reopened complaint: {reason}"
        )

        # Notify student recipient
        Notification.create_for_event(
            recipient=request.user,
            institution=complaint.institution,
            complaint=complaint,
            notification_type=Notification.NotificationType.REOPENED,
            title=f"Complaint Reopened: {complaint.complaint_id}",
            message=f"Your complaint '{complaint.title}' has been successfully reopened for further administrative review."
        )

        # Notify institution administrators
        admins = User.objects.filter(
            role=User.Role.INSTITUTION_ADMIN,
            admin_profile__institution=complaint.institution,
            admin_profile__approval_status='APPROVED'
        )
        for admin_user in admins:
            Notification.create_for_event(
                recipient=admin_user,
                institution=complaint.institution,
                complaint=complaint,
                notification_type=Notification.NotificationType.REOPENED,
                title=f"Complaint Reopened: {complaint.complaint_id}",
                message=f"Student {request.user.full_name} has reopened complaint '{complaint.title}'."
            )

        return Response({
            'message': 'Complaint reopened successfully.',
            'complaint': ComplaintDetailSerializer(complaint, context={'request': request}).data
        }, status=status.HTTP_200_OK)


class ComplaintAttachmentUploadView(APIView):
    """
    Upload an attachment (image, pdf) for a complaint.
    Enforces ownership and maximum file size.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if str(pk).isdigit():
            complaint = get_object_or_404(Complaint, pk=int(pk))
        else:
            complaint = get_object_or_404(Complaint, complaint_id=pk)

        # Permission check
        if request.user.role == User.Role.STUDENT and complaint.student != request.user:
            return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
        if request.user.role == User.Role.INSTITUTION_ADMIN:
            admin_inst = getattr(request.user.admin_profile, 'institution', None)
            if not admin_inst or admin_inst.id != complaint.institution_id:
                return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        upload_file = request.FILES.get('file')
        if not upload_file:
            return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        # Max 5MB check
        if upload_file.size > 5 * 1024 * 1024:
            return Response({'error': 'File size exceeds maximum limit of 5MB.'}, status=status.HTTP_400_BAD_REQUEST)

        attachment = ComplaintAttachment.objects.create(
            complaint=complaint,
            file=upload_file,
            file_name=upload_file.name,
            file_size=upload_file.size,
            mime_type=upload_file.content_type or 'application/octet-stream',
            uploaded_by=request.user
        )

        return Response(ComplaintAttachmentSerializer(attachment).data, status=status.HTTP_201_CREATED)
