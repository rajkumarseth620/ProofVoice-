from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.http import HttpResponse
import base64
import re
import uuid
import logging

from .gnani_service import GnaniAiService
from .ai_assistant import AiAssistantService
from .ai_chat import AiChatService
from apps.complaints.models import Complaint

logger = logging.getLogger(__name__)

class GnaniStatusView(APIView):
    """
    Returns whether Gnani AI voice services are live or pending API credentials.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        configured = GnaniAiService.is_configured()
        return Response({
            'gnani_ai_configured': configured,
            'prisma_stt': 'Active' if configured else 'Pending GNANI_API_KEY',
            'timbre_tts': 'Active' if configured else 'Pending GNANI_API_KEY',
            'endpoints': {
                'stt': 'https://api.vachana.ai/stt/v3',
                'tts': 'https://api.vachana.ai/api/v1/tts/inference'
            }
        }, status=status.HTTP_200_OK)


class SpeechToTextView(APIView):
    """
    Authenticated endpoint for voice complaint recording.
    Transcribes audio using Gnani AI Prisma STT.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        audio_file = request.FILES.get('audio') or request.FILES.get('audio_file')
        if not audio_file:
            return Response({'error': 'No audio file provided in request.'}, status=status.HTTP_400_BAD_REQUEST)

        language = request.data.get('language_code', 'en-IN')
        logger.info(
            "[STT View] Incoming voice transcription request: user=%s, file=%s, size=%s bytes, lang=%s",
            request.user.id, getattr(audio_file, 'name', 'unknown'), getattr(audio_file, 'size', 'unknown'), language
        )
        result = GnaniAiService.speech_to_text(audio_file, language_code=language)

        if not result['success']:
            logger.warning("[STT View] Transcription failed: %s", result.get('error'))
            return Response(result, status=status.HTTP_503_SERVICE_UNAVAILABLE if not result.get('is_configured') else status.HTTP_502_BAD_GATEWAY)

        return Response(result, status=status.HTTP_200_OK)


class TextToSpeechView(APIView):
    """
    Authenticated endpoint for text-to-speech accessibility.
    Reads aloud formal applications using Gnani AI Timbre TTS.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        text = request.data.get('text', '').strip()
        complaint_id = request.data.get('complaint_id')

        # If complaint_id is provided, verify user has access to that complaint
        if complaint_id:
            if str(complaint_id).isdigit():
                complaint = Complaint.objects.filter(pk=int(complaint_id)).first()
            else:
                complaint = Complaint.objects.filter(complaint_id=complaint_id).first()

            if complaint:
                if request.user.role == 'STUDENT' and complaint.student != request.user:
                    return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
                if not text:
                    text = complaint.final_submitted_application or complaint.original_description

        if not text:
            return Response({'error': 'No text provided for speech synthesis.'}, status=status.HTTP_400_BAD_REQUEST)

        language = request.data.get('language', 'en-IN')
        voice = request.data.get('voice', 'Shivani')

        logger.info(
            "[TTS View] Incoming text-to-speech synthesis request: user=%s, text_len=%d, voice=%s, lang=%s",
            request.user.id, len(text), voice, language
        )

        result = GnaniAiService.text_to_speech(text, language=language, voice=voice)

        if not result['success']:
            logger.warning("[TTS View] Speech synthesis failed: %s", result.get('error'))
            return Response(result, status=status.HTTP_503_SERVICE_UNAVAILABLE if not result.get('is_configured') else status.HTTP_502_BAD_GATEWAY)

        if 'audio_bytes' in result:
            response = HttpResponse(result['audio_bytes'], content_type=result.get('content_type', 'audio/wav'))
            response['Content-Disposition'] = 'inline; filename="complaint_audio.wav"'
            return response

        return Response(result, status=status.HTTP_200_OK)


class AiProcessGrievanceView(APIView):
    """
    Intelligent endpoint for grievance structuring.
    Analyzes raw text or voice transcript and returns structured title, category,
    suggested department, summary, and polished grammar.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        text = request.data.get('text') or request.data.get('description') or ''
        if not text.strip():
            return Response({'error': 'No grievance text provided for AI processing.'}, status=status.HTTP_400_BAD_REQUEST)

        processed = AiAssistantService.process_complete_grievance(
            text=text,
            user=request.user,
            institution=getattr(request.user, 'institution', None)
        )
        return Response({
            'success': True,
            'data': processed
        }, status=status.HTTP_200_OK)


class AiSummarizeView(APIView):
    """
    Summarizes lengthy complaints into concise executive summaries.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        text = request.data.get('text') or request.data.get('description') or ''
        if not text.strip():
            return Response({'error': 'No text provided to summarize.'}, status=status.HTTP_400_BAD_REQUEST)

        summary = AiAssistantService.summarize(text)
        return Response({
            'success': True,
            'summary': summary
        }, status=status.HTTP_200_OK)


class AiRefineView(APIView):
    """
    Refines grammar and formal tone while preserving authentic student meaning.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        text = request.data.get('text') or request.data.get('description') or ''
        if not text.strip():
            return Response({'error': 'No text provided for refinement.'}, status=status.HTTP_400_BAD_REQUEST)

        refined = AiAssistantService.refine_grammar(text)
        return Response({
            'success': True,
            'refined_text': refined
        }, status=status.HTTP_200_OK)


class AiCategorizeView(APIView):
    """
    Suggests category, department routing, and priority based on grievance content.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        text = request.data.get('text') or request.data.get('description') or ''
        if not text.strip():
            return Response({'error': 'No text provided for categorization.'}, status=status.HTTP_400_BAD_REQUEST)

        routing = AiAssistantService.categorize_and_route(text)
        title = AiAssistantService.generate_title(text, category=routing['category'])
        return Response({
            'success': True,
            'category': routing['category'],
            'department': routing['department'],
            'priority': routing['priority'],
            'suggested_title': title,
            'confidence': routing['confidence']
        }, status=status.HTTP_200_OK)


def strip_markdown_for_speech(text):
    if not text:
        return ""
    clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    clean = re.sub(r'`([^`]+)`', r'\1', clean)
    clean = re.sub(r'[*#_~`•✓⏳]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


class AiChatbotView(APIView):
    """
    Intelligent AI Support Assistant endpoint for FAQ & Help / Student Support.
    Accepts text or audio queries, enforces strict multi-tenant student privacy,
    persists multi-turn conversations in MySQL, and returns contextual advice
    with optional text-to-speech audio.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = request.user if (request.user and request.user.is_authenticated) else None
        conversation_id = request.data.get('conversation_id')
        session_key = (request.session.session_key if hasattr(request, 'session') and request.session else '') or ''
        message = (request.data.get('message') or '').strip()
        history = request.data.get('history', [])
        voice_mode = bool(request.data.get('voice_mode', False))
        language = (request.data.get('language') or 'en-IN').strip()

        # Check if an audio voice message was uploaded directly
        audio_file = request.FILES.get('audio') or request.FILES.get('audio_file')
        recognized_text = ""
        if audio_file:
            stt_res = GnaniAiService.speech_to_text(audio_file, language_code=language)
            if stt_res.get('success'):
                recognized_text = stt_res.get('transcript', '')
                message = recognized_text
            else:
                if not message:
                    return Response({
                        'success': False,
                        'error': stt_res.get('error', 'Audio transcription failed.')
                    }, status=status.HTTP_400_BAD_REQUEST)

        # Get or create persistent conversation session
        conversation = None
        try:
            from .ai_assistant_services.conversation_manager import ConversationManager
            conversation = ConversationManager.get_or_create_conversation(
                conversation_id=conversation_id,
                user=user,
                session_key=session_key,
                language=language
            )
            # If client didn't supply history, fetch from DB
            if not history and conversation:
                history = ConversationManager.get_conversation_history(conversation)
            # Persist incoming user message
            if message and conversation:
                ConversationManager.save_message(
                    conversation=conversation,
                    role='user',
                    content=message,
                    language=language
                )
        except Exception as e:
            logger.warning(f"ConversationManager error during incoming message: {e}")

        # Get AI Chat response
        result = AiChatService.get_response(
            message=message,
            user=user,
            history=history,
            voice_mode=voice_mode,
            preferred_language=language
        )

        reply_text = result.get('reply', '')
        speak_text = result.get('speak_text') or strip_markdown_for_speech(reply_text)

        response_data = {
            'success': True,
            'conversation_id': str(conversation.id) if conversation else None,
            'message': message,
            'recognized_text': recognized_text,
            'reply': reply_text,
            'speak_text': speak_text,
            'language': result.get('language', 'en-IN'),
            'topic': result.get('topic', 'general'),
            'intent': result.get('intent', 'GENERAL_KNOWLEDGE'),
            'suggested_actions': result.get('suggested_actions', []),
            'complaint_id': result.get('complaint_id')
        }

        # If voice_mode requested and Gnani TTS is configured, try generating server-side audio
        if voice_mode and GnaniAiService.is_configured():
            target_lang = result.get('language') or language or 'en-IN'
            from .ai_assistant_services.language_capabilities import LanguageCapabilitiesService
            voice_name = LanguageCapabilitiesService.get_tts_voice(target_lang)
            tts_res = GnaniAiService.text_to_speech(speak_text[:500], language=target_lang, voice=voice_name)
            if tts_res.get('success'):
                if 'audio_bytes' in tts_res:
                    response_data['audio_base64'] = base64.b64encode(tts_res['audio_bytes']).decode('utf-8')
                    response_data['audio_content_type'] = tts_res.get('content_type', 'audio/wav')
                elif tts_res.get('audio_base64'):
                    response_data['audio_base64'] = tts_res['audio_base64']
                    response_data['audio_content_type'] = tts_res.get('content_type', 'audio/wav')
                elif tts_res.get('audio_url'):
                    response_data['audio_url'] = tts_res['audio_url']

        # Persist assistant response message
        if conversation and reply_text:
            try:
                from .ai_assistant_services.conversation_manager import ConversationManager
                ConversationManager.save_message(
                    conversation=conversation,
                    role='assistant',
                    content=reply_text,
                    speak_text=speak_text,
                    topic=result.get('topic', 'general'),
                    language=result.get('language', language),
                    intent=result.get('intent', 'GENERAL_KNOWLEDGE'),
                    audio_base64=response_data.get('audio_base64', ''),
                    audio_url=response_data.get('audio_url', '')
                )
            except Exception as e:
                logger.warning(f"ConversationManager error saving assistant response: {e}")

        return Response(response_data, status=status.HTTP_200_OK)


class ConversationListView(APIView):
    """
    List user conversation sessions or create a fresh conversation.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user = request.user if (request.user and request.user.is_authenticated) else None
        session_key = (request.session.session_key if hasattr(request, 'session') and request.session else '') or ''
        try:
            from .ai_assistant_services.conversation_manager import ConversationManager
            conversations = ConversationManager.list_user_conversations(user=user, session_key=session_key)
            return Response({'success': True, 'conversations': conversations}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        user = request.user if (request.user and request.user.is_authenticated) else None
        session_key = (request.session.session_key if hasattr(request, 'session') and request.session else '') or ''
        title = (request.data.get('title') or 'New Chat').strip()
        language = (request.data.get('language') or 'en-IN').strip()
        try:
            from .ai_assistant_services.conversation_manager import ConversationManager
            conv = ConversationManager.get_or_create_conversation(
                conversation_id=None,
                user=user,
                session_key=session_key,
                title=title,
                language=language
            )
            return Response({
                'success': True,
                'conversation': {
                    'id': str(conv.id),
                    'title': conv.title,
                    'language': conv.language,
                    'intent_mode': conv.intent_mode,
                    'created_at': conv.created_at.strftime('%b %d, %Y, %I:%M %p') if conv.created_at else ''
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConversationDetailView(APIView):
    """
    Retrieve message history or delete a conversation session with strict ownership check.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, conversation_id):
        user = request.user if (request.user and request.user.is_authenticated) else None
        session_key = (request.session.session_key if hasattr(request, 'session') and request.session else '') or ''
        try:
            from apps.integrations.models import ChatConversation
            conv_uuid = uuid.UUID(str(conversation_id))
            conv = ChatConversation.objects.filter(id=conv_uuid).first()
            if not conv:
                return Response({'success': False, 'error': 'Conversation not found.'}, status=status.HTTP_404_NOT_FOUND)

            # Security verification
            if user and getattr(user, 'is_authenticated', False):
                if conv.user and conv.user != user:
                    return Response({'success': False, 'error': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
            elif session_key:
                if conv.session_key != session_key:
                    return Response({'success': False, 'error': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

            messages = [
                {
                    'id': str(m.id),
                    'role': m.role,
                    'content': m.content,
                    'speak_text': m.speak_text,
                    'topic': m.topic,
                    'language': m.language,
                    'intent': m.intent,
                    'audio_base64': m.audio_base64,
                    'audio_url': m.audio_url,
                    'created_at': m.created_at.strftime('%I:%M %p') if m.created_at else ''
                }
                for m in conv.messages.order_by('created_at')
            ]

            return Response({
                'success': True,
                'conversation': {
                    'id': str(conv.id),
                    'title': conv.title,
                    'language': conv.language,
                    'intent_mode': conv.intent_mode,
                    'messages': messages
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching conversation {conversation_id}: {e}")
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, conversation_id):
        user = request.user if (request.user and request.user.is_authenticated) else None
        session_key = (request.session.session_key if hasattr(request, 'session') and request.session else '') or ''
        try:
            from .ai_assistant_services.conversation_manager import ConversationManager
            deleted = ConversationManager.delete_conversation(conversation_id, user=user, session_key=session_key)
            if deleted:
                return Response({'success': True, 'message': 'Conversation deleted successfully.'}, status=status.HTTP_200_OK)
            return Response({'success': False, 'error': 'Conversation not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LanguageCapabilitiesView(APIView):
    """
    Returns the 22 Indian language + English capability matrix.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            from .ai_assistant_services.language_capabilities import LanguageCapabilitiesService
            lang = request.query_params.get('language')
            caps = LanguageCapabilitiesService.get_capabilities(lang)
            return Response({'success': True, 'capabilities': caps}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching language capabilities: {e}")
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


