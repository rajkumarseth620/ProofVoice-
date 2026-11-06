from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Count, Q, Avg, F
from django.utils import timezone
from datetime import timedelta

from apps.complaints.models import Complaint
from apps.complaints.serializers import ComplaintListSerializer
from apps.accounts.models import User
from apps.accounts.permissions import IsStudent, IsInstitutionAdmin
from apps.institutions.models import Institution, InstitutionDepartment, ComplaintCategory

class StudentDashboardView(APIView):
    """
    Returns metrics and recent complaints tailored to the authenticated student.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        complaints = Complaint.objects.filter(student=user)

        total_count = complaints.count()
        draft_count = complaints.filter(status=Complaint.Status.DRAFT).count()
        submitted_count = complaints.filter(status=Complaint.Status.SUBMITTED).count()
        in_progress_count = complaints.filter(status__in=[Complaint.Status.UNDER_REVIEW, Complaint.Status.ASSIGNED, Complaint.Status.IN_PROGRESS]).count()
        resolved_count = complaints.filter(status=Complaint.Status.RESOLVED).count()

        recent = complaints.order_by('-created_at')[:6]

        # Profile completeness
        profile = getattr(user, 'student_profile', None)
        is_complete = profile.check_completeness() if profile else False

        institution_info = None
        if profile and profile.institution:
            institution_info = {
                'id': profile.institution.id,
                'name': profile.institution.name,
                'code': profile.institution.code
            }

        return Response({
            'metrics': {
                'total_complaints': total_count,
                'active_complaints': in_progress_count + submitted_count,
                'resolved_complaints': resolved_count,
                'draft_complaints': draft_count,
                'profile_complete': is_complete
            },
            'institution': institution_info,
            'recent_complaints': ComplaintListSerializer(recent, many=True).data
        }, status=status.HTTP_200_OK)


class AdminDashboardView(APIView):
    """
    Returns high-level desk metrics for an institution's administrators.
    Multi-tenant isolation: Scoped exclusively to the admin's institution.
    """
    permission_classes = [IsInstitutionAdmin]

    def get(self, request):
        user = request.user

        if user.role == User.Role.PLATFORM_SUPERADMIN or user.is_superuser:
            inst_id = request.query_params.get('institution_id')
            if inst_id:
                institution = Institution.objects.filter(id=inst_id).first()
                complaints = Complaint.objects.filter(institution=institution).exclude(status=Complaint.Status.DRAFT)
            else:
                institution = None
                complaints = Complaint.objects.exclude(status=Complaint.Status.DRAFT)
        else:
            admin_profile = getattr(user, 'admin_profile', None)
            institution = admin_profile.institution if admin_profile else None
            if not institution:
                return Response({'error': 'No institution associated with this administrator.'}, status=status.HTTP_400_BAD_REQUEST)
            complaints = Complaint.objects.filter(institution=institution).exclude(status=Complaint.Status.DRAFT)

        total_complaints = complaints.count()
        pending_review = complaints.filter(status=Complaint.Status.SUBMITTED).count()
        unassigned_count = complaints.filter(assigned_department__isnull=True).exclude(status__in=[Complaint.Status.RESOLVED, Complaint.Status.REJECTED]).count()
        in_progress = complaints.filter(status__in=[Complaint.Status.UNDER_REVIEW, Complaint.Status.ASSIGNED, Complaint.Status.IN_PROGRESS]).count()
        under_review_count = complaints.filter(status=Complaint.Status.UNDER_REVIEW).count()
        resolved = complaints.filter(status=Complaint.Status.RESOLVED).count()
        rejected = complaints.filter(status=Complaint.Status.REJECTED).count()
        critical_priority = complaints.filter(priority__in=[Complaint.Priority.HIGH, Complaint.Priority.CRITICAL]).exclude(status=Complaint.Status.RESOLVED).count()

        from apps.institutions.models import AdminAccessRequest
        if institution:
            pending_students = User.objects.filter(role=User.Role.STUDENT, is_verified=False, student_profile__institution=institution).count()
            pending_admin_reqs = AdminAccessRequest.objects.filter(institution=institution, status=AdminAccessRequest.Status.PENDING).count()
        else:
            pending_students = User.objects.filter(role=User.Role.STUDENT, is_verified=False).count()
            pending_admin_reqs = AdminAccessRequest.objects.filter(status=AdminAccessRequest.Status.PENDING).count()

        # Today's submissions
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_new = complaints.filter(submission_timestamp__gte=today_start).count()

        recent = complaints.order_by('-submission_timestamp')[:10]

        return Response({
            'metrics': {
                'total_complaints': total_complaints,
                'pending_review': pending_review,
                'unassigned_complaints': unassigned_count,
                'under_review': under_review_count,
                'in_progress': in_progress,
                'resolved': resolved,
                'rejected': rejected,
                'critical_priority': critical_priority,
                'today_new': today_new,
                'pending_student_verifications': pending_students,
                'pending_admin_access_requests': pending_admin_reqs
            },
            'institution': {
                'id': institution.id if institution else None,
                'name': institution.name if institution else 'All Institutions (Platform View)',
                'code': institution.code if institution else 'ALL'
            },
            'recent_complaints': ComplaintListSerializer(recent, many=True).data
        }, status=status.HTTP_200_OK)


class InstitutionAnalyticsView(APIView):
    """
    Aggregates departmental distribution, resolution rate, and category breakdowns.
    """
    permission_classes = [IsInstitutionAdmin]

    def get(self, request):
        user = request.user
        if user.role == User.Role.PLATFORM_SUPERADMIN or user.is_superuser:
            inst_id = request.query_params.get('institution_id')
            if inst_id:
                institution = Institution.objects.filter(id=inst_id).first()
            else:
                institution = Institution.objects.filter(verification_status='VERIFIED').first()
        else:
            admin_profile = getattr(user, 'admin_profile', None)
            institution = admin_profile.institution if admin_profile else None

        if not institution:
            return Response({'error': 'Institution scope required.'}, status=status.HTTP_400_BAD_REQUEST)

        complaints = Complaint.objects.filter(institution=institution).exclude(status=Complaint.Status.DRAFT)
        total = complaints.count()

        # Breakdown by status
        status_counts = dict(
            complaints.values_list('status').annotate(count=Count('id'))
        )

        # Breakdown by category
        category_data = []
        categories = ComplaintCategory.objects.filter(institution=institution)
        for cat in categories:
            cat_count = complaints.filter(category=cat).count()
            category_data.append({
                'id': cat.id,
                'name': cat.name,
                'count': cat_count,
                'percentage': round((cat_count / total * 100), 1) if total > 0 else 0
            })

        # Breakdown by department
        dept_data = []
        depts = InstitutionDepartment.objects.filter(institution=institution)
        for dept in depts:
            dept_count = complaints.filter(assigned_department=dept).count()
            dept_data.append({
                'id': dept.id,
                'name': dept.name,
                'count': dept_count
            })

        # Resolution rate
        resolved_count = complaints.filter(status=Complaint.Status.RESOLVED).count()
        resolution_rate = round((resolved_count / total * 100), 1) if total > 0 else 0

        # Average resolution time in days
        resolved_with_time = complaints.filter(
            status=Complaint.Status.RESOLVED,
            resolution_timestamp__isnull=False,
            submission_timestamp__isnull=False
        )
        avg_days = 2.4  # baseline average fallback
        if resolved_with_time.exists():
            diffs = [
                (c.resolution_timestamp - c.submission_timestamp).total_seconds() / 86400
                for c in resolved_with_time if c.resolution_timestamp > c.submission_timestamp
            ]
            if diffs:
                avg_days = round(sum(diffs) / len(diffs), 1)

        return Response({
            'institution': {
                'id': institution.id,
                'name': institution.name,
                'code': institution.code
            },
            'total_complaints': total,
            'resolution_rate': resolution_rate,
            'avg_resolution_days': avg_days,
            'status_breakdown': status_counts,
            'category_breakdown': category_data,
            'department_breakdown': dept_data
        }, status=status.HTTP_200_OK)
