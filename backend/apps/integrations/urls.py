from django.urls import path
from .views import (
    GnaniStatusView,
    SpeechToTextView,
    TextToSpeechView,
    AiProcessGrievanceView,
    AiSummarizeView,
    AiRefineView,
    AiCategorizeView,
    AiChatbotView,
    ConversationListView,
    ConversationDetailView,
    LanguageCapabilitiesView
)

urlpatterns = [
    # Intelligent AI Support Assistant
    path('chat/', AiChatbotView.as_view(), name='ai-chat'),
    path('conversations/', ConversationListView.as_view(), name='ai-conversations-list'),
    path('conversations/<uuid:conversation_id>/', ConversationDetailView.as_view(), name='ai-conversations-detail'),
    path('languages/', LanguageCapabilitiesView.as_view(), name='ai-languages'),

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
