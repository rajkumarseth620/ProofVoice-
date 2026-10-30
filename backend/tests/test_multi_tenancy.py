from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from apps.accounts.models import User, StudentProfile, AdministratorProfile
from apps.institutions.models import Institution, InstitutionDepartment, ComplaintCategory
from apps.complaints.models import Complaint, ComplaintStatusHistory

class MultiTenantSecurityTests(TestCase):
    """
    CRITICAL MULTI-INSTITUTION SECURITY TESTS
    Verifies strict isolation between institutions, student complaint privacy,
    and administrator access controls.
    """
    def setUp(self):
        self.client = APIClient()

        # Institution A
        self.inst_a = Institution.objects.create(
            code='alpha-tech',
            name='Alpha Institute of Technology',
            official_email='info@alphatech.edu',
            official_address='Alpha Campus, Pune',
            verification_status=Institution.VerificationStatus.VERIFIED
        )
        self.dept_a = InstitutionDepartment.objects.create(
            institution=self.inst_a,
            name='Alpha Estate & Maintenance',
            code='A-EST'
        )

        # Institution B
        self.inst_b = Institution.objects.create(
            code='beta-univ',
            name='Beta State University',
            official_email='info@betauniv.edu',
            official_address='Beta Campus, Jaipur',
            verification_status=Institution.VerificationStatus.VERIFIED
        )
        self.dept_b = InstitutionDepartment.objects.create(
            institution=self.inst_b,
            name='Beta Hostel Directorate',
            code='B-HST'
        )

        # Admin A (Institution A)
        self.admin_a = User.objects.create_user(
            email='admin@alpha.edu',
            password='AdminPassword123',
            full_name='Admin Alpha',
            role=User.Role.INSTITUTION_ADMIN,
            is_verified=True
        )
        AdministratorProfile.objects.create(
            user=self.admin_a,
            institution=self.inst_a,
            approval_status=AdministratorProfile.ApprovalStatus.APPROVED
        )

        # Admin B (Institution B)
        self.admin_b = User.objects.create_user(
            email='admin@beta.edu',
            password='AdminPassword123',
            full_name='Admin Beta',
            role=User.Role.INSTITUTION_ADMIN,
            is_verified=True
        )
        AdministratorProfile.objects.create(
            user=self.admin_b,
            institution=self.inst_b,
            approval_status=AdministratorProfile.ApprovalStatus.APPROVED
        )

        # Student A (Institution A)
        self.student_a = User.objects.create_user(
            email='student@alpha.edu',
            password='StudentPassword123',
            full_name='Student Alpha',
            role=User.Role.STUDENT,
            is_verified=True
        )
        StudentProfile.objects.create(
            user=self.student_a,
            institution=self.inst_a,
            student_id='ALPHA/22/01',
            department='Computer Science',
            course='B.Tech CSE',
            semester='6th Semester',
            is_profile_complete=True
        )

        # Student B (Institution B)
        self.student_b = User.objects.create_user(
            email='student@beta.edu',
            password='StudentPassword123',
            full_name='Student Beta',
            role=User.Role.STUDENT,
            is_verified=True
        )
        StudentProfile.objects.create(
            user=self.student_b,
            institution=self.inst_b,
            student_id='BETA/23/02',
            department='Physics',
            course='B.Sc Physics',
            semester='4th Semester',
            is_profile_complete=True
        )

        # Complaint belonging to Institution A (Student A)
        self.complaint_a = Complaint.objects.create(
            complaint_id='PV-2026-0001',
            institution=self.inst_a,
            student=self.student_a,
            title='Alpha Campus Wi-Fi Failure',
            original_description='Library Wi-Fi router is offline.',
            final_submitted_application='Formal letter text for Alpha.',
            status=Complaint.Status.SUBMITTED,
            submission_timestamp=timezone.now()
        )
        ComplaintStatusHistory.objects.create(
            complaint=self.complaint_a,
            previous_status=Complaint.Status.DRAFT,
            new_status=Complaint.Status.SUBMITTED,
            changed_by=self.student_a,
            public_remark='Submitted by student.',
            internal_note='Confidential IT diagnostic note for Alpha Admin only.'
        )

        # Complaint belonging to Institution B (Student B)
        self.complaint_b = Complaint.objects.create(
            complaint_id='PV-2026-0002',
            institution=self.inst_b,
            student=self.student_b,
            title='Beta Hostel Hot Water Geyser Damaged',
            original_description='Hot water supply unavailable in Wing C.',
            final_submitted_application='Formal letter text for Beta.',
            status=Complaint.Status.SUBMITTED,
            submission_timestamp=timezone.now()
        )

    def test_admin_a_cannot_view_admin_b_complaints(self):
        """Admin A should only see Institution A complaints in desk listing."""
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.get('/api/v1/admin/complaints/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        complaint_ids = [c['complaint_id'] for c in response.data]
        self.assertIn('PV-2026-0001', complaint_ids)
        self.assertNotIn('PV-2026-0002', complaint_ids)

    def test_admin_a_cannot_modify_institution_b_complaint(self):
        """Admin A cannot modify status or assign Institution B complaint."""
        self.client.force_authenticate(user=self.admin_a)

        # Attempt to change status of Complaint B
        response = self.client.post(
            f'/api/v1/admin/complaints/{self.complaint_b.complaint_id}/status/',
            {'status': 'IN_PROGRESS', 'public_remark': 'Unauthorized attempt'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Attempt to assign Complaint B
        response_assign = self.client.post(
            f'/api/v1/admin/complaints/{self.complaint_b.complaint_id}/assign/',
            {'department_id': self.dept_a.id},
            format='json'
        )
        self.assertEqual(response_assign.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_view_other_student_complaint(self):
        """Student A cannot access Complaint B by direct URL or complaint ID."""
        self.client.force_authenticate(user=self.student_a)

        # Accessing own complaint succeeds
        resp_own = self.client.get(f'/api/v1/complaints/{self.complaint_a.complaint_id}/')
        self.assertEqual(resp_own.status_code, status.HTTP_200_OK)

        # Accessing other student's complaint is blocked
        resp_other = self.client.get(f'/api/v1/complaints/{self.complaint_b.complaint_id}/')
        self.assertEqual(resp_other.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_timeline_masks_internal_notes(self):
        """Student viewing complaint timeline must not see internal admin notes."""
        self.client.force_authenticate(user=self.student_a)
        response = self.client.get(f'/api/v1/complaints/{self.complaint_a.complaint_id}/timeline/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for event in response.data:
            self.assertNotIn('internal_note', event, "Internal note was leaked to student!")

        # Administrator viewing timeline DOES see internal notes
        self.client.force_authenticate(user=self.admin_a)
        response_admin = self.client.get(f'/api/v1/complaints/{self.complaint_a.complaint_id}/timeline/')
        self.assertEqual(response_admin.status_code, status.HTTP_200_OK)
        has_internal = any('internal_note' in event and event['internal_note'] for event in response_admin.data)
        self.assertTrue(has_internal)
