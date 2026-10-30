import io
from PIL import Image
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User, StudentProfile, AdministratorProfile
from apps.institutions.models import Institution


def create_test_image(format='PNG', size=(100, 100), color=(79, 70, 229)):
    """Creates a real in-memory image buffer valid for Pillow verification."""
    file = io.BytesIO()
    image = Image.new('RGB', size, color)
    image.save(file, format=format)
    file.seek(0)
    return file.getvalue()


class ProfilePhotoTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.institution = Institution.objects.create(
            name="Apex Institute of Technology",
            code="AIT-TEST",
            official_address="Test Address, City"
        )
        self.student = User.objects.create_user(
            email="student_test@apex.edu",
            password="StrongPassword123!",
            role=User.Role.STUDENT,
            full_name="Laxmi Kumari"
        )
        StudentProfile.objects.create(
            user=self.student,
            institution=self.institution,
            student_id="AIT/22/0101",
            department="Computer Science"
        )
        self.admin_user = User.objects.create_user(
            email="admin_test@apex.edu",
            password="AdminPassword123!",
            role=User.Role.INSTITUTION_ADMIN,
            full_name="Dr. Arvind Sharma"
        )
        AdministratorProfile.objects.create(
            user=self.admin_user,
            institution=self.institution,
            designation="Dean"
        )

    def test_unauthenticated_upload_rejected(self):
        response = self.client.post('/api/v1/auth/profile/photo/', {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_upload_valid_png_photo(self):
        self.client.force_authenticate(user=self.student)
        png_bytes = create_test_image('PNG')
        upload_file = SimpleUploadedFile("avatar.png", png_bytes, content_type="image/png")

        response = self.client.post('/api/v1/auth/profile/photo/', {'photo': upload_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profile_image_url', response.data)
        self.assertIsNotNone(response.data['profile_image_url'])

        # Verify database record updated
        self.student.refresh_from_db()
        self.assertTrue(bool(self.student.profile_image))
        self.assertTrue(self.student.profile_image.name.endswith('.png'))

    def test_student_upload_valid_jpeg_and_webp(self):
        self.client.force_authenticate(user=self.student)

        # JPEG
        jpeg_bytes = create_test_image('JPEG')
        jpeg_file = SimpleUploadedFile("avatar.jpg", jpeg_bytes, content_type="image/jpeg")
        resp_jpeg = self.client.post('/api/v1/auth/profile/photo/', {'photo': jpeg_file}, format='multipart')
        self.assertEqual(resp_jpeg.status_code, status.HTTP_200_OK)

        # WebP
        webp_bytes = create_test_image('WEBP')
        webp_file = SimpleUploadedFile("avatar.webp", webp_bytes, content_type="image/webp")
        resp_webp = self.client.put('/api/v1/auth/profile/photo/', {'photo': webp_file}, format='multipart')
        self.assertEqual(resp_webp.status_code, status.HTTP_200_OK)

    def test_reject_corrupted_or_fake_image(self):
        self.client.force_authenticate(user=self.student)
        fake_bytes = b"This is a text string pretending to be a PNG image."
        fake_file = SimpleUploadedFile("fake.png", fake_bytes, content_type="image/png")

        response = self.client.post('/api/v1/auth/profile/photo/', {'photo': fake_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('corrupted', response.data['error'])

    def test_reject_unsupported_extension(self):
        self.client.force_authenticate(user=self.student)
        dummy_file = SimpleUploadedFile("document.pdf", b"%PDF-1.4...", content_type="application/pdf")

        response = self.client.post('/api/v1/auth/profile/photo/', {'photo': dummy_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Unsupported image file extension', response.data['error'])

    def test_reject_oversized_file(self):
        self.client.force_authenticate(user=self.student)
        # Create a mock file with reported size > 5 MB
        oversized_bytes = b"x" * (6 * 1024 * 1024)
        large_file = SimpleUploadedFile("large.png", oversized_bytes, content_type="image/png")

        response = self.client.post('/api/v1/auth/profile/photo/', {'photo': large_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('exceeds maximum allowed size of 5 MB', response.data['error'])

    def test_remove_profile_photo(self):
        self.client.force_authenticate(user=self.student)
        png_bytes = create_test_image('PNG')
        upload_file = SimpleUploadedFile("avatar.png", png_bytes, content_type="image/png")
        self.client.post('/api/v1/auth/profile/photo/', {'photo': upload_file}, format='multipart')

        self.student.refresh_from_db()
        self.assertTrue(bool(self.student.profile_image))

        # Delete photo
        delete_resp = self.client.delete('/api/v1/auth/profile/photo/')
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(delete_resp.data['profile_image_url'])

        self.student.refresh_from_db()
        self.assertFalse(bool(self.student.profile_image))

    def test_admin_upload_and_delete_photo(self):
        self.client.force_authenticate(user=self.admin_user)
        png_bytes = create_test_image('PNG', color=(30, 41, 59))
        upload_file = SimpleUploadedFile("admin_avatar.png", png_bytes, content_type="image/png")

        response = self.client.post('/api/v1/auth/profile/photo/', {'photo': upload_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.admin_user.refresh_from_db()
        self.assertTrue(bool(self.admin_user.profile_image))

        del_resp = self.client.delete('/api/v1/auth/profile/photo/')
        self.assertEqual(del_resp.status_code, status.HTTP_200_OK)
        self.admin_user.refresh_from_db()
        self.assertFalse(bool(self.admin_user.profile_image))
