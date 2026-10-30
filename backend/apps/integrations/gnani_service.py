"""
Gnani AI Service Integration.
Official Documentation Reference: https://docs.gnani.ai/
Integrates:
1. Prisma Speech-to-Text (/stt/v3)
2. Timbre Text-to-Speech (/api/v1/tts/inference)
"""

import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class GnaniAiService:
    """
    Server-side client for Gnani AI APIs.
    Never exposes API credentials to frontend clients.
    """

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
                # Gnani AI Prisma STT typically returns { "transcript": "...", "confidence": ... }
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
                    'error': f'Gnani AI provider error (HTTP {response.status_code}): {response.text[:200]}'
                }

        except requests.Timeout:
            return {
                'success': False,
                'is_configured': True,
                'error': 'Gnani AI service timed out. Please try again or type your complaint.'
            }
        except Exception as e:
            logger.exception("Gnani AI STT exception: %s", str(e))
            return {
                'success': False,
                'is_configured': True,
                'error': f'Connection error contacting Gnani AI: {str(e)}'
            }

    @classmethod
    def text_to_speech(cls, text, language='en-IN', voice='Nalini'):
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

        headers = {
            'X-API-Key-ID': api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            'text': text[:2000],  # Limit chunk size
            'voice': voice,
            'model': 'timbre-v3.0',
            'language': language,
            'speed': 1.0
        }

        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                # Timbre TTS returns binary audio (audio/wav or audio/mpeg) or JSON with audio base64
                content_type = response.headers.get('Content-Type', '')
                if 'audio' in content_type:
                    return {
                        'success': True,
                        'is_configured': True,
                        'audio_bytes': response.content,
                        'content_type': content_type
                    }
                else:
                    result = response.json()
                    return {
                        'success': True,
                        'is_configured': True,
                        'audio_url': result.get('audio_url'),
                        'audio_base64': result.get('audio_base64') or result.get('audio_content')
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
