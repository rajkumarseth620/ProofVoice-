from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.http import HttpResponse

from .gnani_service import GnaniAiService
from .ai_assistant import AiAssistantService
from apps.complaints.models import Complaint

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
        result = GnaniAiService.speech_to_text(audio_file, language_code=language)

        if not result['success']:
            # If Gnani is unconfigured, provide a transparent response
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
        voice = request.data.get('voice', 'Nalini')

        result = GnaniAiService.text_to_speech(text, language=language, voice=voice)

        if not result['success']:
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

