import os
import django
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from apps.accounts.models import User, AdministratorProfile, StudentProfile
from apps.institutions.models import Institution, InstitutionDepartment, ComplaintCategory
from apps.complaints.models import Complaint
from apps.notifications.models import Notification


class NotificationsAndUserInspectTests(APITestCase):
    def setUp(self):
        # Create test institution
        self.inst = Institution.objects.create(
            name='Test Institute of Technology',
            code='tit-tech',
            verification_status=Institution.VerificationStatus.VERIFIED,
            is_active=True
        )
        self.dept = InstitutionDepartment.objects.create(
            institution=self.inst,
            name='Computer Science'
        )
        self.cat = ComplaintCategory.objects.create(
            institution=self.inst,
            name='Lab Equipment',
            default_department=self.dept
        )

        # Create Institution Admin
        self.admin = User.objects.create_user(
            email='testadmin@tit.edu',
            password='AdminPassword@2026',
            full_name='Dr. Test Admin',
            role=User.Role.INSTITUTION_ADMIN,
            is_verified=True
        )
        self.admin_profile = AdministratorProfile.objects.create(
            user=self.admin,
            institution=self.inst,
            designation='Dean',
            department_name='Computer Science',
            staff_id='ADM-001',
            office_address='Room 101, Main Block',
            phone='+91 9876543210',
            approval_status=AdministratorProfile.ApprovalStatus.APPROVED
        )

        # Create Student
        self.student = User.objects.create_user(
            email='teststudent@tit.edu',
            password='StudentPassword@2026',
            full_name='Test Student',
            role=User.Role.STUDENT,
            is_verified=False
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student,
            institution=self.inst,
            student_id='STU-2026-001',
            department='Computer Science',
            course='B.Tech CS',
            semester='3rd Semester',
            phone='+91 9123456780',
            address='Campus Hostel 1'
        )

    def test_student_complaint_notifies_institution_admin(self):
        """When a student submits a complaint, the institution admin receives an internal in-app notification."""
        self.client.force_authenticate(user=self.student)
        payload = {
            'title': 'Projector bulb broken in Room 302',
            'original_description': 'The lab projector lamp is dead and cannot be turned on.',
            'category_id': self.cat.id,
            'submit_now': True
        }
        res = self.client.post('/api/v1/complaints/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        complaint_id = res.data['complaint']['complaint_id']

        # Verify admin received notification
        admin_notifs = Notification.objects.filter(recipient=self.admin)
        self.assertTrue(admin_notifs.exists())
        latest = admin_notifs.latest('created_at')
        self.assertIn(complaint_id, latest.title)
        self.assertIn(self.student.full_name, latest.message)

    def test_admin_inspect_and_verify_student(self):
        """Institution admin can inspect and update is_verified for students in their institution."""
        self.client.force_authenticate(user=self.admin)
        
        # 1. Fetch user profile
        res_get = self.client.get(f'/api/v1/users/{self.student.id}/profile/')
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(res_get.data['id'], self.student.id)
        self.assertFalse(res_get.data['is_verified'])

        # 2. Verify student
        res_patch = self.client.patch(f'/api/v1/users/{self.student.id}/profile/', {'is_verified': True}, format='json')
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        self.assertTrue(res_patch.data['user']['is_verified'])

        self.student.refresh_from_db()
        self.assertTrue(self.student.is_verified)

        # 3. Verify notification created for student
        student_notif = Notification.objects.filter(recipient=self.student).latest('created_at')
        self.assertIn('verified', student_notif.message.lower())

    def test_admin_profile_persistence_update(self):
        """Admin can update phone, office address, staff id, and details with MySQL persistence."""
        self.client.force_authenticate(user=self.admin)
        payload = {
            'fullName': 'Dr. Updated Admin Name',
            'phone': '9988776655',
            'address': 'New Admin Wing Room 204',
            'studentIdentifier': 'STAFF-NEW-888',
            'department': 'Information Technology',
            'designation': 'Senior Dean'
        }
        res = self.client.patch('/api/v1/auth/profile/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.admin.refresh_from_db()
        self.admin_profile.refresh_from_db()

        self.assertEqual(self.admin.full_name, 'Dr. Updated Admin Name')
        self.assertEqual(self.admin_profile.phone, '+91 9988776655')
        self.assertEqual(self.admin_profile.office_address, 'New Admin Wing Room 204')
        self.assertEqual(self.admin_profile.staff_id, 'STAFF-NEW-888')
        self.assertEqual(self.admin_profile.department_name, 'Information Technology')
        self.assertEqual(self.admin_profile.designation, 'Senior Dean')
