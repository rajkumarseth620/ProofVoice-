import os
import django
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.accounts.models import StudentProfile
from apps.institutions.models import Institution

User = get_user_model()

class StudentRegistrationAndLoginTests(APITestCase):
    def setUp(self):
        # Create a verified test institution
        self.institution = Institution.objects.create(
            name="Apex Institute of Technology",
            code="AIT-TEST",
            verification_status=Institution.VerificationStatus.VERIFIED,
            is_active=True,
            state="Jharkhand",
            city="Jamshedpur"
        )

    def test_student_registration_creates_user_and_profile_in_db(self):
        payload = {
            "fullName": "Priya Sharma",
            "email": "priya.sharma.test@apextech.edu",
            "password": "SecurePassword123!",
            "institution_id": str(self.institution.id),
            "student_id": "AIT-2026-CSE-099",
            "department": "Computer Science & Engineering",
            "course": "B.Tech CSE",
            "semester": "5th Semester",
            "residentialAddress": "Room 204, Ganga Hostel, Campus Greens",
            "phone": "+91 9876543210"
        }

        # Match payload sent by frontend api-client.js
        backend_payload = {
            "full_name": payload["fullName"],
            "email": payload["email"],
            "password": payload["password"],
            "institution_id": payload["institution_id"],
            "student_id": payload["student_id"],
            "department": payload["department"],
            "course": payload["course"],
            "semester": payload["semester"],
            "address": payload["residentialAddress"],
            "phone": payload["phone"]
        }

        response = self.client.post("/api/v1/auth/register/student/", backend_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertIn("token", response.data)

        # Verify User in Database
        user = User.objects.filter(email="priya.sharma.test@apextech.edu").first()
        self.assertIsNotNone(user, "User record must exist in database")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_verified)
        self.assertEqual(user.full_name, "Priya Sharma")

        # Verify StudentProfile in Database
        profile = StudentProfile.objects.filter(user=user).first()
        self.assertIsNotNone(profile, "StudentProfile record must exist in database")
        self.assertEqual(profile.student_id, "AIT-2026-CSE-099")
        self.assertEqual(profile.institution, self.institution)
        self.assertEqual(profile.department, "Computer Science & Engineering")
        self.assertEqual(profile.course, "B.Tech CSE")
        self.assertEqual(profile.semester, "5th Semester")
        self.assertEqual(profile.address, "Room 204, Ganga Hostel, Campus Greens")
        self.assertEqual(profile.phone, "+91 9876543210")
        self.assertTrue(profile.is_profile_complete)

    def test_student_login_with_registered_credentials(self):
        # First register student
        register_payload = {
            "full_name": "Arun Kumar",
            "email": "arun.kumar.test@apextech.edu",
            "password": "Password2026!",
            "institution_id": str(self.institution.id),
            "student_id": "AIT-2026-ME-045",
            "department": "Mechanical Engineering",
            "course": "B.Tech ME",
            "semester": "3rd Semester",
            "address": "Block C, Hostels",
            "phone": "+91 9123456780"
        }
        reg_res = self.client.post("/api/v1/auth/register/student/", register_payload, format="json")
        self.assertEqual(reg_res.status_code, status.HTTP_201_CREATED)

        # Now test login on /api/v1/auth/login/
        login_payload = {
            "email": "arun.kumar.test@apextech.edu",
            "password": "Password2026!",
            "role": "student"
        }
        login_res = self.client.post("/api/v1/auth/login/", login_payload, format="json")
        self.assertEqual(login_res.status_code, status.HTTP_200_OK, login_res.data)
        self.assertIn("token", login_res.data)
        self.assertEqual(login_res.data["user"]["email"], "arun.kumar.test@apextech.edu")
        self.assertEqual(login_res.data["user"]["role"], User.Role.STUDENT)
        self.assertEqual(login_res.data["user"]["student_profile"]["student_id"], "AIT-2026-ME-045")
        self.assertEqual(login_res.data["user"]["student_profile"]["institution_name"], "Apex Institute of Technology")

    def test_student_login_wrong_password_fails(self):
        # Create student user
        User.objects.create_user(
            email="test.student@apextech.edu",
            password="CorrectPassword123!",
            full_name="Test Student",
            role=User.Role.STUDENT,
            is_active=True,
            is_verified=True
        )

        login_res = self.client.post("/api/v1/auth/login/", {
            "email": "test.student@apextech.edu",
            "password": "WrongPassword123!",
            "role": "student"
        }, format="json")
        self.assertEqual(login_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid email or password", str(login_res.data))

    def test_student_cannot_login_via_admin_portal(self):
        User.objects.create_user(
            email="regular.student@apextech.edu",
            password="CorrectPassword123!",
            full_name="Regular Student",
            role=User.Role.STUDENT,
            is_active=True,
            is_verified=True
        )

        login_res = self.client.post("/api/v1/auth/login/", {
            "email": "regular.student@apextech.edu",
            "password": "CorrectPassword123!",
            "role": "admin"
        }, format="json")
        self.assertEqual(login_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Access denied", str(login_res.data))

    def test_student_registration_mismatched_password_fails(self):
        payload = {
            "full_name": "Test Mismatch",
            "email": "mismatch@apextech.edu",
            "password": "Password123!",
            "confirm_password": "DifferentPassword456!",
            "institution_id": str(self.institution.id),
            "student_id": "AIT-2026-MISMATCH",
            "department": "Computer Science",
            "course": "B.Tech",
            "semester": "1st Semester"
        }
        res = self.client.post("/api/v1/auth/register/student/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirm_password", res.data)
        self.assertIn("Passwords do not match", str(res.data["confirm_password"]))

    def test_change_password_requires_correct_current_and_matching_confirmation(self):
        from rest_framework.authtoken.models import Token
        user = User.objects.create_user(
            email="pwchange.student@apextech.edu",
            password="OriginalPassword123!",
            full_name="Password Test Student",
            role=User.Role.STUDENT,
            is_active=True,
            is_verified=True
        )
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        # 1. Mismatched new password and confirm password should fail with 400
        res1 = self.client.post("/api/v1/auth/password/change/", {
            "current_password": "OriginalPassword123!",
            "new_password": "NewSecretPassword2026!",
            "confirm_password": "WrongConfirm2026!"
        }, format="json")
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("match", str(res1.data))

        # 2. Incorrect current password should fail with 400
        res2 = self.client.post("/api/v1/auth/password/change/", {
            "current_password": "IncorrectOldPassword!",
            "new_password": "NewSecretPassword2026!",
            "confirm_password": "NewSecretPassword2026!"
        }, format="json")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("current password", str(res2.data).lower())

        # 3. Matching new passwords and correct current password should succeed with 200
        res3 = self.client.post("/api/v1/auth/password/change/", {
            "current_password": "OriginalPassword123!",
            "new_password": "NewSecretPassword2026!",
            "confirm_password": "NewSecretPassword2026!"
        }, format="json")
        self.assertEqual(res3.status_code, status.HTTP_200_OK)
        self.assertTrue(res3.data.get("success"))

        # 4. Verify user can now log in with the new password
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewSecretPassword2026!"))
