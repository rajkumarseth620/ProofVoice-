from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from apps.accounts.models import User, StudentProfile, AdministratorProfile
from apps.institutions.models import Institution, InstitutionDepartment, AdminAccessRequest
from apps.complaints.models import Complaint, ComplaintStatusHistory
from apps.notifications.models import Notification

class Phase2ManagementTests(APITestCase):
    def setUp(self):
        # Create two institutions
        self.inst_a = Institution.objects.create(
            name="Institution Alpha",
            code="ALPHA",
            verification_status=Institution.VerificationStatus.VERIFIED
        )
        self.inst_b = Institution.objects.create(
            name="Institution Beta",
            code="BETA",
            verification_status=Institution.VerificationStatus.VERIFIED
        )

        # Departments for Institution A
        self.dept_a1 = InstitutionDepartment.objects.create(
            institution=self.inst_a,
            name="Alpha IT Services",
            code="AIT"
        )
        self.dept_a2 = InstitutionDepartment.objects.create(
            institution=self.inst_a,
            name="Alpha Maintenance",
            code="AMAINT"
        )

        # Departments for Institution B
        self.dept_b1 = InstitutionDepartment.objects.create(
            institution=self.inst_b,
            name="Beta IT Services",
            code="BIT"
        )

        # Platform Super Admin
        self.superadmin = User.objects.create_superuser(
            email="superadmin@proofvoice.io",
            password="SuperPassword123!",
            full_name="Super Admin User",
            role=User.Role.PLATFORM_SUPERADMIN
        )

        # Institution A Admin
        self.admin_a = User.objects.create_user(
            email="admin@alpha.edu",
            password="AdminPassword123!",
            full_name="Admin Alpha",
            role=User.Role.INSTITUTION_ADMIN
        )
        AdministratorProfile.objects.create(
            user=self.admin_a,
            institution=self.inst_a,
            approval_status=AdministratorProfile.ApprovalStatus.APPROVED,
            designation="Dean of Campus"
        )

        # Institution B Admin
        self.admin_b = User.objects.create_user(
            email="admin@beta.edu",
            password="AdminPassword123!",
            full_name="Admin Beta",
            role=User.Role.INSTITUTION_ADMIN
        )
        AdministratorProfile.objects.create(
            user=self.admin_b,
            institution=self.inst_b,
            approval_status=AdministratorProfile.ApprovalStatus.APPROVED,
            designation="Campus Registrar"
        )

        # Student A
        self.student_a = User.objects.create_user(
            email="student@alpha.edu",
            password="StudentPassword123!",
            full_name="Student Alpha",
            role=User.Role.STUDENT,
            is_verified=False
        )
        StudentProfile.objects.create(
            user=self.student_a,
            institution=self.inst_a,
            student_id="A-STU-001",
            department="Computer Science"
        )

        # Student B
        self.student_b = User.objects.create_user(
            email="student@beta.edu",
            password="StudentPassword123!",
            full_name="Student Beta",
            role=User.Role.STUDENT,
            is_verified=True
        )
        StudentProfile.objects.create(
            user=self.student_b,
            institution=self.inst_b,
            student_id="B-STU-001",
            department="Electrical"
        )

        # Complaints for Inst A
        self.complaint_a1 = Complaint.objects.create(
            complaint_id="PV-2026-1001",
            student=self.student_a,
            institution=self.inst_a,
            title="Broken projector in Lab 1",
            original_description="Broken projector in Lab 1",
            final_submitted_application="Formal grievance about broken projector in Lab 1.",
            priority=Complaint.Priority.HIGH,
            status=Complaint.Status.SUBMITTED
        )

        # Complaints for Inst B
        self.complaint_b1 = Complaint.objects.create(
            complaint_id="PV-2026-2001",
            student=self.student_b,
            institution=self.inst_b,
            title="Water leakage in Hostel B",
            original_description="Water leakage in Hostel B",
            final_submitted_application="Formal grievance about water leakage.",
            priority=Complaint.Priority.MEDIUM,
            status=Complaint.Status.SUBMITTED
        )

    # TEST A: Multi-Tenancy & Institution Isolation
    def test_institution_isolation_complaints_and_users(self):
        # Admin A should only see Inst A complaints
        self.client.force_authenticate(user=self.admin_a)
        res = self.client.get('/api/v1/admin/complaints/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        c_ids = [c['complaint_id'] for c in res.data]
        self.assertIn("PV-2026-1001", c_ids)
        self.assertNotIn("PV-2026-2001", c_ids)

        # Admin B should only see Inst B complaints
        self.client.force_authenticate(user=self.admin_b)
        res_b = self.client.get('/api/v1/admin/complaints/')
        self.assertEqual(res_b.status_code, status.HTTP_200_OK)
        c_ids_b = [c['complaint_id'] for c in res_b.data]
        self.assertIn("PV-2026-2001", c_ids_b)
        self.assertNotIn("PV-2026-1001", c_ids_b)

        # Admin A should only see Inst A users
        self.client.force_authenticate(user=self.admin_a)
        res_users = self.client.get('/api/v1/users/')
        self.assertEqual(res_users.status_code, status.HTTP_200_OK)
        emails = [u['email'] for u in res_users.data]
        self.assertIn(self.student_a.email, emails)
        self.assertNotIn(self.student_b.email, emails)

    # TEST B: Complaints Workflow & Department Assignment & Status History Audit
    def test_complaints_workflow_and_status_history(self):
        self.client.force_authenticate(user=self.admin_a)

        # Assign department
        res_assign = self.client.post(f'/api/v1/admin/complaints/{self.complaint_a1.complaint_id}/assign/', {
            'department': self.dept_a1.name,
            'public_remark': 'Assigned to IT Team'
        })
        self.assertEqual(res_assign.status_code, status.HTTP_200_OK)
        self.complaint_a1.refresh_from_db()
        self.assertEqual(self.complaint_a1.assigned_department, self.dept_a1)

        # Status transition: UNDER_REVIEW -> IN_PROGRESS -> RESOLVED
        res_status = self.client.post(f'/api/v1/admin/complaints/{self.complaint_a1.complaint_id}/status/', {
            'status': 'IN_PROGRESS',
            'public_remark': 'Technicians are repairing the projector.',
            'internal_note': 'Parts requisitioned from vendor.'
        })
        self.assertEqual(res_status.status_code, status.HTTP_200_OK)
        self.complaint_a1.refresh_from_db()
        self.assertEqual(self.complaint_a1.status, Complaint.Status.IN_PROGRESS)

        # Verify audit history
        history = ComplaintStatusHistory.objects.filter(complaint=self.complaint_a1).order_by('-timestamp')
        self.assertTrue(history.exists())
        latest = history.first()
        self.assertEqual(latest.new_status, 'IN_PROGRESS')
        self.assertEqual(latest.changed_by, self.admin_a)
        self.assertEqual(latest.internal_note, 'Parts requisitioned from vendor.')

        # Verify notification generated for student
        notifs = Notification.objects.filter(recipient=self.student_a, complaint=self.complaint_a1)
        self.assertTrue(notifs.exists())

    # TEST C: Student Verification (Approve / Reject)
    def test_student_verification_approve_and_reject(self):
        self.client.force_authenticate(user=self.admin_a)

        # Approve student
        res_approve = self.client.patch(f'/api/v1/users/{self.student_a.id}/profile/', {
            'is_verified': True,
            'action': 'approve'
        }, format='json')
        self.assertEqual(res_approve.status_code, status.HTTP_200_OK)
        self.student_a.refresh_from_db()
        self.assertTrue(self.student_a.is_verified)
        self.assertTrue(self.student_a.is_active)

        # Reject student
        res_reject = self.client.patch(f'/api/v1/users/{self.student_a.id}/profile/', {
            'is_verified': False,
            'is_active': False,
            'action': 'reject',
            'reason': 'ID card unreadable'
        }, format='json')
        self.assertEqual(res_reject.status_code, status.HTTP_200_OK)
        self.student_a.refresh_from_db()
        self.assertFalse(self.student_a.is_verified)
        self.assertFalse(self.student_a.is_active)

    # TEST D: Staff & Admin Access Requests
    def test_admin_access_requests_management(self):
        # Create applicant user for Inst A
        applicant = User.objects.create_user(
            email="staff.applicant@alpha.edu",
            password="StaffPassword123!",
            full_name="Staff Applicant",
            role=User.Role.STUDENT
        )
        req = AdminAccessRequest.objects.create(
            user=applicant,
            institution=self.inst_a,
            designation="Lab In-Charge",
            department_name="Alpha IT Services",
            status=AdminAccessRequest.Status.PENDING
        )

        # Admin B cannot approve Inst A request (IDOR prevention)
        self.client.force_authenticate(user=self.admin_b)
        res_forbidden = self.client.post(f'/api/v1/institutions/admin-access-requests/{req.id}/approve/', {
            'action': 'approve'
        })
        self.assertEqual(res_forbidden.status_code, status.HTTP_403_FORBIDDEN)

        # Admin A can approve Inst A request
        self.client.force_authenticate(user=self.admin_a)
        res_approve = self.client.post(f'/api/v1/institutions/admin-access-requests/{req.id}/approve/', {
            'action': 'approve'
        })
        self.assertEqual(res_approve.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.status, AdminAccessRequest.Status.APPROVED)
        applicant.refresh_from_db()
        self.assertEqual(applicant.role, User.Role.INSTITUTION_ADMIN)
        self.assertTrue(hasattr(applicant, 'admin_profile'))
        self.assertEqual(applicant.admin_profile.approval_status, AdministratorProfile.ApprovalStatus.APPROVED)

    # TEST E: Super Admin Global Visibility & Institution Filtering
    def test_super_admin_global_visibility(self):
        self.client.force_authenticate(user=self.superadmin)

        # Super Admin sees all complaints
        res_all = self.client.get('/api/v1/admin/complaints/')
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        c_ids = [c['complaint_id'] for c in res_all.data]
        self.assertIn("PV-2026-1001", c_ids)
        self.assertIn("PV-2026-2001", c_ids)

        # Super Admin filters by Inst A
        res_filter_a = self.client.get(f'/api/v1/admin/complaints/?institution_id={self.inst_a.id}')
        self.assertEqual(res_filter_a.status_code, status.HTTP_200_OK)
        filtered_ids = [c['complaint_id'] for c in res_filter_a.data]
        self.assertIn("PV-2026-1001", filtered_ids)
        self.assertNotIn("PV-2026-2001", filtered_ids)

        # Super Admin overview metrics
        res_overview = self.client.get('/api/v1/institutions/super-admin/overview/')
        self.assertEqual(res_overview.status_code, status.HTTP_200_OK)
        self.assertIn('total_institutions', res_overview.data)
        self.assertIn('total_complaints', res_overview.data)

    # TEST F: Cross-Institution IDOR Prevention
    def test_cross_institution_idor_blocked(self):
        # Admin A cannot modify Inst B complaint status
        self.client.force_authenticate(user=self.admin_a)
        res_cross_status = self.client.post(f'/api/v1/admin/complaints/{self.complaint_b1.complaint_id}/status/', {
            'status': 'RESOLVED'
        })
        self.assertEqual(res_cross_status.status_code, status.HTTP_403_FORBIDDEN)

        # Admin A cannot modify Inst B student profile
        res_cross_user = self.client.patch(f'/api/v1/users/{self.student_b.id}/profile/', {
            'is_verified': True
        })
        self.assertEqual(res_cross_user.status_code, status.HTTP_403_FORBIDDEN)

    # TEST G: Student Complaint Regression
    def test_student_complaint_ownership(self):
        # Student A sees their own complaint
        self.client.force_authenticate(user=self.student_a)
        res = self.client.get('/api/v1/complaints/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [c['complaint_id'] for c in res.data]
        self.assertIn("PV-2026-1001", ids)
        self.assertNotIn("PV-2026-2001", ids)
