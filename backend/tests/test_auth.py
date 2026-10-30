from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User, StudentProfile, AdministratorProfile
from apps.institutions.models import Institution

class AuthenticationAndProfileTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.institution = Institution.objects.create(
            code='test-univ',
            name='Test University',
            official_email='info@testuniv.edu',
            official_address='Test Campus, Delhi',
            verification_status=Institution.VerificationStatus.VERIFIED
        )

    def test_student_registration_success(self):
        """Test public student registration creates STUDENT role and profile."""
        payload = {
            'email': 'newstudent@testuniv.edu',
            'password': 'SecurePassword123',
            'full_name': 'Aarav Patel',
            'institution_id': self.institution.id,
            'student_id': 'TU/2026/001',
            'department': 'Mechanical Engineering',
            'course': 'B.Tech ME',
            'semester': '4th Semester'
        }
        response = self.client.post('/api/v1/auth/register/student/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['role'], User.Role.STUDENT)

        user = User.objects.get(email='newstudent@testuniv.edu')
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertTrue(user.is_verified)
        self.assertEqual(user.student_profile.student_id, 'TU/2026/001')
        self.assertTrue(user.student_profile.is_profile_complete)

    def test_admin_registration_requires_approval(self):
        """Test admin registration creates unverified account with PENDING approval."""
        payload = {
            'email': 'admincandidate@testuniv.edu',
            'password': 'AdminPassword123',
            'full_name': 'Dr. Sunita Rao',
            'institution_id': self.institution.id,
            'designation': 'Hostel Warden'
        }
        response = self.client.post('/api/v1/auth/register/institution-admin/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get('requires_approval'))

        user = User.objects.get(email='admincandidate@testuniv.edu')
        self.assertEqual(user.role, User.Role.INSTITUTION_ADMIN)
        self.assertFalse(user.is_verified)
        self.assertEqual(user.admin_profile.approval_status, AdministratorProfile.ApprovalStatus.PENDING)

    def test_login_invalid_credentials(self):
        """Test invalid credentials return 400 Bad Request."""
        payload = {
            'email': 'nonexistent@testuniv.edu',
            'password': 'WrongPassword123'
        }
        response = self.client.post('/api/v1/auth/login/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_valid_credentials(self):
        """Test login with valid student credentials."""
        user = User.objects.create_user(
            email='validstudent@testuniv.edu',
            password='ValidPassword123',
            full_name='Vikram Singh',
            role=User.Role.STUDENT
        )
        StudentProfile.objects.create(user=user, institution=self.institution)

        payload = {
            'email': 'validstudent@testuniv.edu',
            'password': 'ValidPassword123'
        }
        response = self.client.post('/api/v1/auth/login/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['role'], 'STUDENT')
        self.assertEqual(response.data['institution']['id'], self.institution.id)

    def test_profile_update(self):
        """Test updating student profile fields via authenticated PATCH."""
        user = User.objects.create_user(
            email='updateuser@testuniv.edu',
            password='Password123',
            full_name='Initial Name',
            role=User.Role.STUDENT
        )
        profile = StudentProfile.objects.create(user=user, institution=self.institution)
        self.client.force_authenticate(user=user)

        payload = {
            'full_name': 'Updated Name',
            'phone': '+91 9876543210',
            'semester': '7th Semester'
        }
        response = self.client.patch('/api/v1/auth/profile/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        profile.refresh_from_db()
        self.assertEqual(user.full_name, 'Updated Name')
        self.assertEqual(profile.phone, '+91 9876543210')
        self.assertEqual(profile.semester, '7th Semester')

    def test_institution_users_list_for_admin(self):
        """Test institution admin can view users of their institution at /api/v1/users/."""
        admin_user = User.objects.create_user(
            email='campusadmin@testuniv.edu',
            password='Password123',
            full_name='Dr. Campus Admin',
            role=User.Role.INSTITUTION_ADMIN
        )
        AdministratorProfile.objects.create(
            user=admin_user,
            institution=self.institution,
            approval_status=AdministratorProfile.ApprovalStatus.APPROVED
        )
        student_user = User.objects.create_user(
            email='enrolled@testuniv.edu',
            password='Password123',
            full_name='Enrolled Student',
            role=User.Role.STUDENT
        )
        StudentProfile.objects.create(
            user=student_user,
            institution=self.institution,
            student_id='ENR-001'
        )

        self.client.force_authenticate(user=admin_user)
        response = self.client.get('/api/v1/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = [u['email'] for u in response.data]
        self.assertIn('campusadmin@testuniv.edu', emails)
        self.assertIn('enrolled@testuniv.edu', emails)

    def test_student_cannot_login_as_admin(self):
        """Cross-role security: student cannot login via the admin portal."""
        user = User.objects.create_user(
            email='teststudent_role@testuniv.edu',
            password='ValidPassword123',
            full_name='Role Test Student',
            role=User.Role.STUDENT
        )
        StudentProfile.objects.create(user=user, institution=self.institution)

        payload = {
            'email': 'teststudent_role@testuniv.edu',
            'password': 'ValidPassword123',
            'role': 'admin'
        }
        response = self.client.post('/api/v1/auth/login/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_text = str(response.data)
        self.assertIn('Access denied. This account does not have administrator privileges.', error_text)

    def test_admin_cannot_login_as_student(self):
        """Cross-role security: admin cannot login via the student portal."""
        admin = User.objects.create_user(
            email='testadmin_role@testuniv.edu',
            password='ValidPassword123',
            full_name='Role Test Admin',
            role=User.Role.INSTITUTION_ADMIN
        )
        AdministratorProfile.objects.create(user=admin, institution=self.institution)

        payload = {
            'email': 'testadmin_role@testuniv.edu',
            'password': 'ValidPassword123',
            'role': 'student'
        }
        response = self.client.post('/api/v1/auth/login/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_text = str(response.data)
        self.assertIn('Access denied. Please sign in via the Administrator portal.', error_text)

    def test_duplicate_registration_rejected(self):
        """Duplicate email registration is strictly rejected."""
        User.objects.create_user(
            email='duplicate@testuniv.edu',
            password='ExistingPassword123',
            full_name='First Student',
            role=User.Role.STUDENT
        )
        payload = {
            'email': 'duplicate@testuniv.edu',
            'password': 'NewPassword123',
            'full_name': 'Duplicate Student',
            'institution_id': self.institution.id,
            'student_id': 'TU/2026/099'
        }
        response = self.client.post('/api/v1/auth/register/student/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('An account with this email already exists.', str(response.data))

    def test_empty_credentials_rejected(self):
        """Empty email or password returns 400 Bad Request."""
        response = self.client.post('/api/v1/auth/login/', {'email': '', 'password': ''}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_invalidates_token(self):
        """Logging out deletes auth token from database; subsequent requests with that token return 401."""
        user = User.objects.create_user(
            email='logouttest@testuniv.edu',
            password='ValidPassword123',
            full_name='Logout Tester',
            role=User.Role.STUDENT
        )
        StudentProfile.objects.create(user=user, institution=self.institution)

        login_res = self.client.post('/api/v1/auth/login/', {'email': 'logouttest@testuniv.edu', 'password': 'ValidPassword123'}, format='json')
        token = login_res.data['token']

        # Call authenticated me endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        me_res = self.client.get('/api/v1/auth/me/')
        self.assertEqual(me_res.status_code, status.HTTP_200_OK)

        # Call logout
        logout_res = self.client.post('/api/v1/auth/logout/')
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)

        # Attempt to access protected endpoint using the old token
        me_after_logout = self.client.get('/api/v1/auth/me/')
        self.assertEqual(me_after_logout.status_code, status.HTTP_401_UNAUTHORIZED)
