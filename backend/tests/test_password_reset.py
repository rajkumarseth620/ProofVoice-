from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User, StudentProfile, AdministratorProfile
from apps.institutions.models import Institution, InstitutionRegistrationRequest

class PasswordResetTests(TestCase):
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

        # Setup Admin user
        self.admin_user = User.objects.create_user(
            email="rajkr@apex.edu",
            password="OldPassword@123",
            full_name="Raj Kumar",
            role=User.Role.INSTITUTION_ADMIN,
            is_active=True,
            is_verified=True
        )
        self.admin_profile = AdministratorProfile.objects.create(
            user=self.admin_user,
            institution=self.institution,
            designation="Campus Administrator",
            phone="+91 9876543210",
            initial_password="OldPassword@123",
            approval_status=AdministratorProfile.ApprovalStatus.APPROVED
        )

        # Setup Student user
        self.student_user = User.objects.create_user(
            email="student@apex.edu",
            password="StudentOld@123",
            full_name="Test Student",
            role=User.Role.STUDENT,
            is_active=True,
            is_verified=True
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            institution=self.institution,
            phone="+91 9876543211",
            initial_password="StudentOld@123"
        )

    def test_reset_password_with_invalid_phone(self):
        url = reverse('auth-password-reset')
        response = self.client.post(url, {
            'email': 'rajkr@apex.edu',
            'phone': '12345',
            'new_password': 'NewPassword@2026',
            'confirm_password': 'NewPassword@2026'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('valid 10-digit', response.data['error'])

    def test_reset_password_with_mismatched_phone(self):
        url = reverse('auth-password-reset')
        response = self.client.post(url, {
            'email': 'rajkr@apex.edu',
            'phone': '9999999999',
            'new_password': 'NewPassword@2026',
            'confirm_password': 'NewPassword@2026'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Verification failed', response.data['error'])

    def test_reset_password_success_admin(self):
        url = reverse('auth-password-reset')
        response = self.client.post(url, {
            'email': 'rajkr@apex.edu',
            'phone': '9876543210',
            'new_password': 'ArkaJain@2026',
            'confirm_password': 'ArkaJain@2026'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        # Verify password check
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.check_password('ArkaJain@2026'))

        # Verify initial_password updated
        self.admin_profile.refresh_from_db()
        self.assertEqual(self.admin_profile.initial_password, 'ArkaJain@2026')

    def test_reset_password_success_student(self):
        url = reverse('auth-password-reset')
        response = self.client.post(url, {
            'email': 'student@apex.edu',
            'phone': '9876543211',
            'new_password': 'StudentNew@2026',
            'confirm_password': 'StudentNew@2026'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        self.student_user.refresh_from_db()
        self.assertTrue(self.student_user.check_password('StudentNew@2026'))

        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.initial_password, 'StudentNew@2026')
