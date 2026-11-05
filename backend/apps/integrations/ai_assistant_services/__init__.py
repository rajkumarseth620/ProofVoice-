# -*- coding: utf-8 -*-
"""
ProofVoice Advanced Multimodal Multilingual AI Assistant Services.
"""
from .language_detection import SUPPORTED_LANGUAGES, detect_language, normalize_text
from .intent_classifier import IntentClassifier, AssistantIntent
from .campus_knowledge import match_campus_knowledge
from .general_knowledge import match_general_knowledge
from .web_search import WebSearchService
from .conversation_memory import ConversationMemory
from .user_context import UserContextService
from .ai_engine import AiEngineService

__all__ = [
    'SUPPORTED_LANGUAGES',
    'detect_language',
    'normalize_text',
    'IntentClassifier',
    'AssistantIntent',
    'match_campus_knowledge',
    'match_general_knowledge',
    'WebSearchService',
    'ConversationMemory',
    'UserContextService',
    'AiEngineService',
]
