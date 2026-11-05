"""
Gnani AI Service Integration.
Official Documentation Reference: https://docs.gnani.ai/
Integrates:
1. Prisma Speech-to-Text (/stt/v3)
2. Timbre Text-to-Speech (/api/v1/tts/inference)
"""

import io
import wave
import base64
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 16000, num_channels: int = 1, sampwidth: int = 2) -> bytes:
    """
    Wraps raw 16-bit linear PCM audio in a compliant RIFF WAV container
    so HTML5 browsers and media players can decode and play it seamlessly.
    """
    if not pcm_bytes:
        return b''
    if pcm_bytes.startswith(b'RIFF'):
        return pcm_bytes
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(sampwidth)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)
    return wav_io.getvalue()


class GnaniAiService:
    """
    Server-side client for Gnani AI APIs.
    Never exposes API credentials to frontend clients.
    """

    # Verified live voices supported by Gnani AI Timbre v3.0
    GNANI_SUPPORTED_VOICES = {
        'Avinash', 'Shivani', 'Lakshmi', 'Kalpana', 'Shubham',
        'Prakash', 'Devansh', 'Yashraj', 'Chetana', 'Vasudha',
        'Harshad', 'Riyaa', 'Tarika'
    }

    # High quality regional language voice mappings
    LANGUAGE_VOICE_MAP = {
        'hi-IN': 'Shivani',
        'en-IN': 'Shivani'
    }

    @classmethod
    def is_configured(cls):
        """Checks if live Gnani AI API credentials are configured in environment."""
        key = getattr(settings, 'GNANI_API_KEY', '')
        return bool(key and key.strip() and key != 'your_gnani_api_key_here')

    @classmethod
    def speech_to_text(cls, audio_file, language_code='en-IN'):
        """
        Transcribes speech audio using Gnani AI Prisma STT.
        Official Endpoint: https://api.vachana.ai/stt/v3
        Header: X-API-Key-ID: <key>
        """
        if not cls.is_configured():
            return {
                'success': False,
                'is_configured': False,
                'error': 'Gnani AI API key is not configured. Set GNANI_API_KEY in backend/.env to activate live Prisma STT.'
            }

        endpoint = getattr(settings, 'GNANI_STT_ENDPOINT', 'https://api.vachana.ai/stt/v3')
        api_key = settings.GNANI_API_KEY.strip()

        headers = {
            'X-API-Key-ID': api_key
        }

        # Format validation
        allowed_extensions = ['.wav', '.mp3', '.ogg', '.webm', '.m4a', '.flac']
        file_name = getattr(audio_file, 'name', 'audio.wav').lower()
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            return {
                'success': False,
                'is_configured': True,
                'error': f'Unsupported audio format. Allowed: {", ".join(allowed_extensions)}'
            }

        # Size check (max 10MB)
        if audio_file.size > 10 * 1024 * 1024:
            return {
                'success': False,
                'is_configured': True,
                'error': 'Audio file exceeds 10MB limit.'
            }

        try:
            audio_file.seek(0)
            files = {
                'audio_file': (audio_file.name, audio_file.read(), audio_file.content_type or 'audio/wav')
            }
            data = {
                'language_code': language_code,
                'format': 'transcribe',
                'itn_native_numerals': 'true'
            }

            response = requests.post(
                endpoint,
                headers=headers,
                files=files,
                data=data,
                timeout=25
            )

            if response.status_code == 200:
                result = response.json()
                transcript = result.get('transcript') or result.get('text') or result.get('data', {}).get('transcript', '')
                return {
                    'success': True,
                    'is_configured': True,
                    'transcript': transcript,
                    'language': language_code,
                    'raw_response': result
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'is_configured': True,
                    'error': 'Gnani AI authentication failed. Please verify GNANI_API_KEY in backend/.env.'
                }
            elif response.status_code == 429:
                return {
                    'success': False,
                    'is_configured': True,
                    'error': 'Gnani AI rate limit reached. Please wait before attempting again.'
                }
            else:
                return {
                    'success': False,
                    'is_configured': True,
                    'error': f'Gnani AI STT error (HTTP {response.status_code}): {response.text[:200]}'
                }

        except requests.Timeout:
            return {
                'success': False,
                'is_configured': True,
                'error': 'Gnani AI STT service timed out.'
            }
        except Exception as e:
            logger.exception("Gnani AI STT exception: %s", str(e))
            return {
                'success': False,
                'is_configured': True,
                'error': f'Connection error contacting Gnani AI: {str(e)}'
            }

    @classmethod
    def text_to_speech(cls, text, language='en-IN', voice=None):
        """
        Converts text to spoken audio using Gnani AI Timbre TTS.
        Official Endpoint: https://api.vachana.ai/api/v1/tts/inference
        Header: X-API-Key-ID: <key>
        """
        if not cls.is_configured():
            return {
                'success': False,
                'is_configured': False,
                'error': 'Gnani AI API key is not configured. Set GNANI_API_KEY in backend/.env to activate live Timbre TTS.'
            }

        endpoint = getattr(settings, 'GNANI_TTS_ENDPOINT', 'https://api.vachana.ai/api/v1/tts/inference')
        api_key = settings.GNANI_API_KEY.strip()

        # Select verified voice
        target_voice = voice if (voice and voice in cls.GNANI_SUPPORTED_VOICES) else cls.LANGUAGE_VOICE_MAP.get(language, 'Shivani')

        headers = {
            'X-API-Key-ID': api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            'text': text[:2000],  # Limit chunk size
            'voice': target_voice,
            'model': 'timbre-v3.0',
            'language': language,
            'speed': 1.0,
            'sampling_rate': 16000
        }

        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                # Timbre TTS returns binary 16-bit linear PCM audio
                content_type = response.headers.get('Content-Type', '')
                if 'audio' in content_type or 'octet-stream' in content_type or len(response.content) > 100:
                    wav_bytes = pcm_to_wav(response.content, sample_rate=16000)
                    b64 = base64.b64encode(wav_bytes).decode('utf-8')
                    return {
                        'success': True,
                        'is_configured': True,
                        'audio_bytes': wav_bytes,
                        'audio_base64': b64,
                        'content_type': 'audio/wav',
                        'voice': target_voice
                    }
                else:
                    result = response.json()
                    b64_str = result.get('audio_base64') or result.get('audio_content') or ''
                    if b64_str:
                        raw_bytes = base64.b64decode(b64_str)
                        wav_bytes = pcm_to_wav(raw_bytes, sample_rate=16000)
                        b64_str = base64.b64encode(wav_bytes).decode('utf-8')
                    return {
                        'success': True,
                        'is_configured': True,
                        'audio_url': result.get('audio_url'),
                        'audio_base64': b64_str,
                        'content_type': 'audio/wav',
                        'voice': target_voice
                    }
            else:
                return {
                    'success': False,
                    'is_configured': True,
                    'error': f'Gnani AI TTS error (HTTP {response.status_code}): {response.text[:200]}'
                }

        except requests.Timeout:
            return {
                'success': False,
                'is_configured': True,
                'error': 'Gnani AI TTS service timed out.'
            }
        except Exception as e:
            logger.exception("Gnani AI TTS exception: %s", str(e))
            return {
                'success': False,
                'is_configured': True,
                'error': f'Connection error contacting Gnani AI TTS: {str(e)}'
            }
