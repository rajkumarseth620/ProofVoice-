# -*- coding: utf-8 -*-
"""
ProofVoice Language Capabilities Matrix for 22 Indian Official Languages + English.
Maintains separate capability indicators for:
- Text Input
- Text Output
- Speech-to-Text (STT) via Gnani AI Prisma
- Text-to-Speech (TTS) via Gnani AI Timbre

Enforces honest disclosure: clearly distinguishes between native voice support
and text-only with browser speech synthesis fallback.
"""

# Complete 22 8th Schedule Indian Languages + English Capability Matrix
LANGUAGE_CAPABILITIES_MATRIX = {
    'en-IN': {
        'name': 'English (India)',
        'native': 'English',
        'script': 'Latin',
        'bcp47': 'en-IN',
        'text_input': True,
        'text_output': True,
        'speech_to_text': True,
        'text_to_speech': True,
        'stt_provider': 'Gnani AI Prisma',
        'tts_provider': 'Gnani AI Timbre',
        'default_voice': 'Shivani',
        'voice_gender': 'Female'
    },
    'hi-IN': {
        'name': 'Hindi',
        'native': 'हिन्दी',
        'script': 'Devanagari',
        'bcp47': 'hi-IN',
        'text_input': True,
        'text_output': True,
        'speech_to_text': True,
        'text_to_speech': True,
        'stt_provider': 'Gnani AI Prisma',
        'tts_provider': 'Gnani AI Timbre',
        'default_voice': 'Shivani',
        'voice_gender': 'Female'
    }
}


class LanguageCapabilitiesService:
    @classmethod
    def get_capabilities(cls, lang_code: str = None) -> dict:
        """Returns the full capabilities matrix or details for a specific language."""
        if lang_code:
            c = lang_code.strip().lower()
            for key, val in LANGUAGE_CAPABILITIES_MATRIX.items():
                if key.lower() == c or key.split('-')[0].lower() == c:
                    return val
            return LANGUAGE_CAPABILITIES_MATRIX.get('en-IN')
        return LANGUAGE_CAPABILITIES_MATRIX

    @classmethod
    def is_stt_supported(cls, lang_code: str) -> bool:
        cap = cls.get_capabilities(lang_code)
        return bool(cap and cap.get('speech_to_text'))

    @classmethod
    def is_tts_supported(cls, lang_code: str) -> bool:
        cap = cls.get_capabilities(lang_code)
        return bool(cap and cap.get('text_to_speech'))

    @classmethod
    def get_tts_voice(cls, lang_code: str) -> str:
        cap = cls.get_capabilities(lang_code)
        return cap.get('default_voice') or 'Paul'
