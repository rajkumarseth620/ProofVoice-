from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.accounts.models import User
from apps.integrations.gnani_service import GnaniAiService

class GnaniAiIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.student = User.objects.create_user(
            email='teststudent@proofvoice.edu',
            password='Password123',
            full_name='Test Student',
            role=User.Role.STUDENT,
            is_verified=True
        )

    def test_gnani_status_public(self):
        """Public status endpoint correctly reports configuration state."""
        response = self.client.get('/api/v1/ai/status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('gnani_ai_configured', response.data)
        self.assertIn('endpoints', response.data)

    def test_unauthenticated_speech_to_text_denied(self):
        """STT endpoint must reject unauthenticated requests."""
        response = self.client.post('/api/v1/ai/speech-to-text/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unconfigured_gnani_returns_honest_service_status(self):
        """When GNANI_API_KEY is empty, backend returns honest 503 instead of fake transcription."""
        self.client.force_authenticate(user=self.student)
        fake_audio = SimpleUploadedFile("complaint.wav", b"RIFF....WAVEfmt ....data....", content_type="audio/wav")

        response = self.client.post(
            '/api/v1/ai/speech-to-text/',
            {'audio': fake_audio},
            format='multipart'
        )
        if not GnaniAiService.is_configured():
            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            self.assertFalse(response.data['success'])
            self.assertIn('not configured', response.data['error'])
