from django.urls import path
from .views import (
    GnaniStatusView,
    SpeechToTextView,
    TextToSpeechView,
    AiProcessGrievanceView,
    AiSummarizeView,
    AiRefineView,
    AiCategorizeView,
    AiChatbotView
)

urlpatterns = [
    # Intelligent AI Support Assistant
    path('chat/', AiChatbotView.as_view(), name='ai-chat'),

    # Gnani AI Gateway
    path('status/', GnaniStatusView.as_view(), name='gnani-status'),
    path('speech-to-text/', SpeechToTextView.as_view(), name='gnani-stt'),
    path('text-to-speech/', TextToSpeechView.as_view(), name='gnani-tts'),

    # ProofVoice AI Processing & Structuring Suite
    path('process/', AiProcessGrievanceView.as_view(), name='ai-process'),
    path('assist/', AiProcessGrievanceView.as_view(), name='ai-assist-alias'),
    path('summarize/', AiSummarizeView.as_view(), name='ai-summarize'),
    path('refine/', AiRefineView.as_view(), name='ai-refine'),
    path('categorize/', AiCategorizeView.as_view(), name='ai-categorize'),
]
