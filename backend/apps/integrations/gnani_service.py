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


def validate_pcm_wav(audio_bytes: bytes) -> tuple[bool, str]:
    """
    Strictly verifies that audio_bytes is an uncompressed, 16kHz, mono, 16-bit linear PCM WAV.
    Explicitly rejects WebM, compressed formats, and invalid configurations before contacting Gnani AI.
    """
    if not audio_bytes or len(audio_bytes) < 44:
        return False, "Audio data is empty or too short to be a valid WAV file."

    if audio_bytes.startswith(b'\x1a\x45\xdf\xa3'):
        return False, "WebM audio format cannot be sent to Gnani AI. A 16kHz mono linear PCM WAV file is required."

    if not (audio_bytes.startswith(b'RIFF') and audio_bytes[8:12] == b'WAVE'):
        return False, "Audio file is not in valid RIFF WAVE format."

    try:
        with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            comptype = wf.getcomptype()

            if comptype != 'NONE':
                return False, f"Compressed WAV ({comptype}) is unsupported. Uncompressed linear PCM is required."
            if channels != 1:
                return False, f"Audio must be mono (1 channel). Received {channels} channels."
            if sample_width != 2:
                return False, f"Audio must be 16-bit (2 bytes per sample). Received {sample_width * 8}-bit."
            if framerate != 16000:
                return False, f"Audio sample rate must be exactly 16000 Hz. Received {framerate} Hz."
    except Exception as e:
        return False, f"Invalid or unreadable WAV structure: {str(e)}"

    return True, ""


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
        stt_model = getattr(settings, 'GNANI_STT_MODEL', 'prisma-v3.0')

        headers = {
            'X-API-Key-ID': api_key
        }

        # Format validation: Gnani AI Prisma STT only accepts linear PCM .wav files
        allowed_extensions = ['.wav']
        file_name = getattr(audio_file, 'name', 'audio.wav').lower()
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            return {
                'success': False,
                'is_configured': True,
                'error': f'Unsupported audio format. Gnani AI Prisma STT requires a 16kHz linear PCM .wav file. Allowed: {", ".join(allowed_extensions)}'
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
            raw_audio_bytes = audio_file.read()
            audio_size = len(raw_audio_bytes)

            # Strict 16kHz mono 16-bit linear PCM WAV verification
            is_valid_wav, val_err = validate_pcm_wav(raw_audio_bytes)
            if not is_valid_wav:
                logger.warning(
                    "[Gnani STT] Audio validation failed: %s (file: %s, size: %d bytes)",
                    val_err, file_name, audio_size
                )
                return {
                    'success': False,
                    'is_configured': True,
                    'error': f'Invalid audio format: {val_err}'
                }

            logger.info(
                "[Gnani STT] Audio verified: 16kHz mono 16-bit linear PCM WAV (%d bytes, file: %s)",
                audio_size, file_name
            )

            files = {
                'audio_file': ('recording.wav', raw_audio_bytes, 'audio/wav')
            }
            data = {
                'model': stt_model,
                'language_code': language_code,
                'format': 'transcribe',
                'itn_native_numerals': 'true'
            }

            logger.info(
                "[Gnani STT] Initiating request to %s (model=%s, lang=%s, size=%d bytes)",
                endpoint, stt_model, language_code, audio_size
            )

            response = requests.post(
                endpoint,
                headers=headers,
                files=files,
                data=data,
                timeout=25
            )

            logger.info("[Gnani STT] Upstream response HTTP %s received", response.status_code)

            if response.status_code == 200:
                result = response.json()
                req_id = result.get('request_id', 'N/A')
                resp_model = result.get('model', stt_model)
                transcript = result.get('transcript') or result.get('text') or result.get('data', {}).get('transcript', '')
                logger.info(
                    "[Gnani STT] Request succeeded! (request_id=%s, model=%s, transcript_len=%d)",
                    req_id, resp_model, len(transcript)
                )
                return {
                    'success': True,
                    'is_configured': True,
                    'transcript': transcript,
                    'language': language_code,
                    'request_id': req_id,
                    'model': resp_model,
                    'raw_response': result
                }
            elif response.status_code == 401:
                logger.warning("[Gnani STT] Authentication failed (HTTP 401). Verify GNANI_API_KEY in environment.")
                return {
                    'success': False,
                    'is_configured': True,
                    'error': 'Gnani AI authentication failed. Please verify GNANI_API_KEY in backend/.env.'
                }
            elif response.status_code == 429:
                logger.warning("[Gnani STT] Rate limit reached (HTTP 429).")
                return {
                    'success': False,
                    'is_configured': True,
                    'error': 'Gnani AI rate limit reached. Please wait before attempting again.'
                }
            else:
                logger.warning(
                    "[Gnani STT] Upstream API returned error HTTP %s: %s",
                    response.status_code, response.text[:300]
                )
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
    def _prepare_tts_text(cls, text: str) -> str:
        """
        Normalizes formal letter and complaint text for neural TTS playback:
        - Collapses consecutive newlines and whitespace that generate unnatural pauses
        - Strips markdown formatting (*, _, #, `, ~, etc.)
        - Normalizes repeated punctuation and divider lines
        - Preserves natural sentence punctuation (. , ? !) for authentic Hindi/English prosody
        """
        if not text:
            return ""
        import re
        # Remove markdown formatting characters
        cleaned = re.sub(r'[*_`#~]', '', text)
        # Collapse multiple horizontal whitespace
        cleaned = re.sub(r'[ 	]+', ' ', cleaned)
        # Collapse 3 or more newlines into double newline (paragraph pause)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        # Collapse repeated dashes or equal signs used as section dividers
        cleaned = re.sub(r'[-_=]{3,}', ' ', cleaned)
        return cleaned.strip()

    @classmethod
    def text_to_speech(cls, text, language='en-IN', voice=None, speed=None):
        """
        Converts text to spoken audio using Gnani AI Timbre TTS.
        Official Endpoint: https://api.vachana.ai/api/v1/tts/inference
        Header: X-API-Key-ID: <key>
        Strictly specifies audio_config with 16kHz linear PCM in WAV container
        to ensure zero sample-rate mismatch and eliminate slow-playback distortion.
        """
        if not cls.is_configured():
            return {
                'success': False,
                'is_configured': False,
                'error': 'Gnani AI API key is not configured. Set GNANI_API_KEY in backend/.env to activate live Timbre TTS.'
            }

        endpoint = getattr(settings, 'GNANI_TTS_ENDPOINT', 'https://api.vachana.ai/api/v1/tts/inference')
        api_key = settings.GNANI_API_KEY.strip()
        tts_model = getattr(settings, 'GNANI_TTS_MODEL', 'timbre-v3.0')

        # Select verified voice (defaulting to Shivani for natural Indian English / Hindi articulation)
        target_voice = voice if (voice and voice in cls.GNANI_SUPPORTED_VOICES) else cls.LANGUAGE_VOICE_MAP.get(language, 'Shivani')

        # Speaking speed multiplier: Gnani supported range is 0.85 to 1.15 (1.0 = normal natural speed)
        raw_speed = speed if speed is not None else getattr(settings, 'GNANI_TTS_SPEED', 1.0)
        try:
            speed_val = float(raw_speed)
            speed_val = max(0.85, min(1.15, speed_val))
        except (ValueError, TypeError):
            speed_val = 1.0

        headers = {
            'X-API-Key-ID': api_key,
            'Content-Type': 'application/json'
        }

        clean_text = cls._prepare_tts_text(text)

        payload = {
            'text': clean_text[:2000],  # Limit chunk size
            'voice': target_voice,
            'model': tts_model,
            'language': language,
            'speed': speed_val,
            'audio_config': {
                'encoding': 'linear_pcm',
                'container': 'wav',
                'sample_rate': 16000,
                'num_channels': 1,
                'sample_width': 2
            }
        }

        logger.info(
            "[Gnani TTS] Initiating TTS request to %s (model=%s, voice=%s, lang=%s, speed=%.2f, text_len=%d)",
            endpoint, tts_model, target_voice, language, speed_val, len(payload['text'])
        )

        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )

            logger.info("[Gnani TTS] Upstream response HTTP %s received", response.status_code)

            if response.status_code == 200:
                logger.info("[Gnani TTS] Speech synthesis succeeded (bytes: %d)", len(response.content))
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
