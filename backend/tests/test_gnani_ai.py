from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from apps.accounts.models import User
from apps.integrations.gnani_service import GnaniAiService, pcm_to_wav, validate_pcm_wav

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
        fake_audio = SimpleUploadedFile("complaint.wav", pcm_to_wav(b'\x00\x00' * 8000), content_type="audio/wav")

        with patch.object(GnaniAiService, 'is_configured', return_value=False):
            response = self.client.post(
                '/api/v1/ai/speech-to-text/',
                {'audio': fake_audio},
                format='multipart'
            )
            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            self.assertFalse(response.data['success'])
            self.assertIn('not configured', response.data['error'])

    @patch('requests.post')
    def test_speech_to_text_sends_prisma_v3_model(self, mock_post):
        """Verifies that speech_to_text includes model='prisma-v3.0' and X-API-Key-ID."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'success': True,
            'request_id': 'req-test-12345',
            'model': 'prisma-v3.0',
            'transcript': 'Please fix the classroom fan.'
        }
        mock_post.return_value = mock_resp

        self.client.force_authenticate(user=self.student)
        # Create authentic 16kHz mono 16-bit linear PCM WAV
        wav_data = pcm_to_wav(b'\x00\x00' * 16000, sample_rate=16000, num_channels=1, sampwidth=2)
        audio_file = SimpleUploadedFile("recording.wav", wav_data, content_type="audio/wav")

        with patch.object(GnaniAiService, 'is_configured', return_value=True):
            response = self.client.post(
                '/api/v1/ai/speech-to-text/',
                {'audio': audio_file, 'language_code': 'en-IN'},
                format='multipart'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
            self.assertEqual(response.data['transcript'], 'Please fix the classroom fan.')
            self.assertEqual(response.data['model'], 'prisma-v3.0')
            self.assertEqual(response.data['request_id'], 'req-test-12345')

            # Check mock call arguments
            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            self.assertIn('X-API-Key-ID', kwargs['headers'])
            self.assertEqual(kwargs['data']['model'], 'prisma-v3.0')
            self.assertEqual(kwargs['data']['language_code'], 'en-IN')
            self.assertEqual(kwargs['data']['format'], 'transcribe')

    def test_speech_to_text_rejects_webm_audio(self):
        """WebM audio must be strictly rejected before sending to Gnani AI."""
        self.client.force_authenticate(user=self.student)
        webm_data = b'\x1a\x45\xdf\xa3' + b'\x00' * 100
        audio_file = SimpleUploadedFile("recording.wav", webm_data, content_type="audio/wav")

        with patch.object(GnaniAiService, 'is_configured', return_value=True):
            response = self.client.post(
                '/api/v1/ai/speech-to-text/',
                {'audio': audio_file},
                format='multipart'
            )
            self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
            self.assertFalse(response.data['success'])
            self.assertIn('WebM', response.data['error'])

    def test_speech_to_text_rejects_non_16khz(self):
        """WAV audio with non-16kHz sample rate must be rejected."""
        self.client.force_authenticate(user=self.student)
        wav_44k = pcm_to_wav(b'\x00\x00' * 44100, sample_rate=44100, num_channels=1, sampwidth=2)
        audio_file = SimpleUploadedFile("recording.wav", wav_44k, content_type="audio/wav")

        with patch.object(GnaniAiService, 'is_configured', return_value=True):
            response = self.client.post(
                '/api/v1/ai/speech-to-text/',
                {'audio': audio_file},
                format='multipart'
            )
            self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
            self.assertIn('16000 Hz', response.data['error'])

    def test_speech_to_text_rejects_stereo_audio(self):
        """WAV audio with stereo channels must be rejected."""
        self.client.force_authenticate(user=self.student)
        wav_stereo = pcm_to_wav(b'\x00\x00' * 32000, sample_rate=16000, num_channels=2, sampwidth=2)
        audio_file = SimpleUploadedFile("recording.wav", wav_stereo, content_type="audio/wav")

        with patch.object(GnaniAiService, 'is_configured', return_value=True):
            response = self.client.post(
                '/api/v1/ai/speech-to-text/',
                {'audio': audio_file},
                format='multipart'
            )
            self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
            self.assertIn('mono', response.data['error'])

    def test_pcm_to_wav_wrapper(self):
        """Verifies raw PCM bytes are converted into valid RIFF WAV with 44-byte header."""
        raw_pcm = b'\x00\x00' * 8000  # 0.5s of silence at 16kHz
        wav_output = pcm_to_wav(raw_pcm, sample_rate=16000, num_channels=1, sampwidth=2)
        self.assertTrue(wav_output.startswith(b'RIFF'))
        self.assertIn(b'WAVE', wav_output[:16])
        self.assertEqual(len(wav_output), 44 + len(raw_pcm))

        is_valid, err = validate_pcm_wav(wav_output)
        self.assertTrue(is_valid)
        self.assertEqual(err, "")
