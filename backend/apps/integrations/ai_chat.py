"""
ProofVoice Intelligent AI Campus Redressal & Help Assistant Service.
Delegates to AiEngineService for unified, context-aware conversational AI.
Supported Languages: English ('en-IN') and Hindi ('hi-IN') only.
"""

import logging
from apps.integrations.gnani_service import GnaniAiService
from apps.integrations.ai_assistant_services.ai_engine import AiEngineService
from apps.integrations.ai_assistant_services.language_detection import SUPPORTED_LANGUAGES, normalize_lang_code, detect_language

logger = logging.getLogger(__name__)


class AiChatService:
    """
    Intelligent chatbot engine for ProofVoice Help & Support.
    Operates strictly in English ('en-IN') and Hindi ('hi-IN').
    Handles text questions, student account status checks, and voice generation.
    """

    @classmethod
    def get_response(cls, message, user=None, history=None, voice_mode=False, preferred_language='en-IN'):
        """
        Processes a user query and returns a structured AI response in English or Hindi.
        Enforces authenticated student privacy for account/complaint queries.
        """
        try:
            res = AiEngineService.generate_response(
                query=message,
                user=user,
                history=history,
                preferred_language=preferred_language
            )
            # Ensure strictly supported language tag
            lang = res.get('language', 'en-IN')
            if lang != 'hi-IN':
                lang = 'en-IN'
            res['language'] = lang
            return res
        except Exception as e:
            logger.exception("AiEngineService error in AiChatService.get_response: %s", str(e))
            is_hindi = (preferred_language == 'hi-IN' or 'hi' in str(preferred_language).lower())
            if is_hindi:
                return {
                    'reply': "क्षमा करें, इस समय सेवा में तकनीकी समस्या आ रही है। कृपया थोड़ी देर बाद पुनः प्रयास करें या 'My Complaints' में जाकर अपने टिकट देखें।",
                    'speak_text': "क्षमा करें, इस समय सेवा में तकनीकी समस्या आ रही है।",
                    'topic': 'system_error_fallback',
                    'language': 'hi-IN',
                    'suggested_actions': ["मेरी शिकायतें देखें", "शिकायत दर्ज करें", "पेज रिफ्रेश करें"]
                }
            return {
                'reply': "I apologize, but I am experiencing a temporary connection issue. Please try again in a moment or visit **My Complaints** to manage your tickets directly.",
                'speak_text': "I apologize, but I am experiencing a temporary connection issue. Please try again in a moment.",
                'topic': 'system_error_fallback',
                'language': 'en-IN',
                'suggested_actions': ["View My Complaints", "Create Complaint", "Refresh Page"]
            }
