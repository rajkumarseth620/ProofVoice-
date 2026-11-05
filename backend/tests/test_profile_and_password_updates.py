from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from apps.accounts.models import User, StudentProfile, AdministratorProfile
from apps.institutions.models import Institution

class ProfileAndPasswordUpdatesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.institution = Institution.objects.create(
            name="Arka Jain University",
            code="arka-jain-university",
            institution_type=Institution.InstitutionType.UNIVERSITY,
            official_email="info@arkajainuniversity.ac.in",
            verification_status=Institution.VerificationStatus.VERIFIED,
            is_active=True
        )

        # 1. Admin setup
        self.admin_user = User.objects.create_user(
            email="rajkr@apex.edu",
            password="CurrentAdmin@2026",
            full_name="Raj Kumar",
            role=User.Role.INSTITUTION_ADMIN,
            is_active=True,
            is_verified=True
        )
        self.admin_profile = AdministratorProfile.objects.create(
            user=self.admin_user,
            institution=self.institution,
            designation="Campus Administrator",
            department_name="General Administration",
            staff_id="ADM-001",
            office_address="Room 101, Main Block",
            phone="+91 9876543210",
            initial_password="CurrentAdmin@2026",
            approval_status=AdministratorProfile.ApprovalStatus.APPROVED
        )
        self.admin_token = Token.objects.create(user=self.admin_user)

        # 2. Student setup
        self.student_user = User.objects.create_user(
            email="student@apex.edu",
            password="CurrentStudent@2026",
            full_name="Aarav Sharma",
            role=User.Role.STUDENT,
            is_active=True,
            is_verified=True
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            institution=self.institution,
            student_id="STU-2026-001",
            department="Computer Science",
            course="B.Tech CSE",
            semester="Semester 4",
            address="Hostel B, Room 204",
            phone="+91 9876543211",
            initial_password="CurrentStudent@2026"
        )
        self.student_token = Token.objects.create(user=self.student_user)

    def test_admin_profile_update(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        url = reverse('auth-profile')
        payload = {
            'fullName': 'Dr. Raj Kumar',
            'studentIdentifier': 'ADM-999',
            'department': 'Dean of Student Affairs',
            'designation': 'Chief Administrative Dean',
            'residentialAddress': 'Admin Tower, Suite 405',
            'phone': '9876543210'
        }
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.admin_user.refresh_from_db()
        self.admin_profile.refresh_from_db()

        self.assertEqual(self.admin_user.full_name, 'Dr. Raj Kumar')
        self.assertEqual(self.admin_profile.designation, 'Chief Administrative Dean')
        self.assertEqual(self.admin_profile.department_name, 'Dean of Student Affairs')
        self.assertEqual(self.admin_profile.staff_id, 'ADM-999')
        self.assertEqual(self.admin_profile.office_address, 'Admin Tower, Suite 405')
        self.assertEqual(self.admin_profile.phone, '+91 9876543210')

    def test_student_profile_update(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.student_token.key}')
        url = reverse('auth-profile')
        payload = {
            'fullName': 'Aarav K. Sharma',
            'studentIdentifier': 'STU-999',
            'department': 'Information Technology',
            'yearSemester': 'Semester 5',
            'residentialAddress': 'Campus Wing 3',
            'phone': '9876543211'
        }
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.student_user.refresh_from_db()
        self.student_profile.refresh_from_db()

        self.assertEqual(self.student_user.full_name, 'Aarav K. Sharma')
        self.assertEqual(self.student_profile.student_id, 'STU-999')
        self.assertEqual(self.student_profile.department, 'Information Technology')
        self.assertEqual(self.student_profile.semester, 'Semester 5')
        self.assertEqual(self.student_profile.address, 'Campus Wing 3')

    def test_admin_change_password_invalid_current(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        url = reverse('auth-change-password')
        res = self.client.post(url, {
            'current_password': 'WrongPassword@123',
            'new_password': 'NewAdminPass@2026',
            'confirm_password': 'NewAdminPass@2026'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Incorrect current password', res.data['error'])

    def test_admin_change_password_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        url = reverse('auth-change-password')
        res = self.client.post(url, {
            'current_password': 'CurrentAdmin@2026',
            'new_password': 'NewAdminPass@2026',
            'confirm_password': 'NewAdminPass@2026'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertIn('token', res.data)

        # Verify new password in MySQL
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.check_password('NewAdminPass@2026'))
        self.assertFalse(self.admin_user.check_password('CurrentAdmin@2026'))

        # Verify initial_password sync
        self.admin_profile.refresh_from_db()
        self.assertEqual(self.admin_profile.initial_password, 'NewAdminPass@2026')

    def test_student_change_password_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.student_token.key}')
        url = reverse('auth-change-password')
        res = self.client.post(url, {
            'current_password': 'CurrentStudent@2026',
            'new_password': 'NewStudentPass@2026',
            'confirm_password': 'NewStudentPass@2026'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])

        self.student_user.refresh_from_db()
        self.assertTrue(self.student_user.check_password('NewStudentPass@2026'))
        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.initial_password, 'NewStudentPass@2026')
