# -*- coding: utf-8 -*-
"""
Test Suite for Conversation Endpoints and Persistence.
Tests:
1. POST /api/ai/conversations/ creates session
2. GET /api/ai/conversations/ lists user conversations
3. POST /api/ai/chat/ with conversation_id saves user message and AI reply in MySQL/SQLite
4. GET /api/ai/conversations/<id>/ returns saved message turns
5. Intent classification and educational guards in multi-turn chat
6. GET /api/ai/languages/ returns 22-language capabilities matrix
7. DELETE /api/ai/conversations/<id>/ removes conversation
"""

import os
import sys
import json
import django

# Setup Django test environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ['USE_SQLITE_FOR_TESTS'] = '1'
django.setup()

from django.test import RequestFactory
from apps.accounts.models import User
from apps.integrations.models import ChatConversation, ChatMessage
from apps.integrations.views import (
    AiChatbotView,
    ConversationListView,
    ConversationDetailView,
    LanguageCapabilitiesView
)
from rest_framework.test import APIRequestFactory

def run_tests():
    print("=" * 60)
    print("RUNNING CONVERSATION PERSISTENCE & API TEST SUITE")
    print("=" * 60)

    factory = APIRequestFactory()

    # Create test user
    user, _ = User.objects.get_or_create(
        email='student_persist_test@apex.edu',
        defaults={'role': 'STUDENT', 'full_name': 'Persistence Tester'}
    )

    # Clean prior test conversations
    ChatConversation.objects.filter(user=user).delete()

    # 1. Test POST /api/ai/conversations/
    view_list = ConversationListView.as_view()
    req = factory.post('/api/ai/conversations/', {'title': 'Study Session', 'language': 'en-IN'}, format='json')
    req.user = user
    res = view_list(req)
    assert res.status_code == 201, f"Expected 201, got {res.status_code}"
    conv_data = res.data.get('conversation')
    conv_id = conv_data['id']
    print(f"[PASS] Test 1: Created conversation {conv_id} with title '{conv_data['title']}'")

    # 2. Test GET /api/ai/conversations/
    req = factory.get('/api/ai/conversations/')
    req.user = user
    res = view_list(req)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert len(res.data.get('conversations', [])) >= 1, "Expected at least 1 conversation"
    print(f"[PASS] Test 2: Listed user conversations count = {len(res.data['conversations'])}")

    # 3. Test POST /api/ai/chat/ with conversation_id
    chat_view = AiChatbotView.as_view()
    req = factory.post('/api/ai/chat/', {
        'message': 'What is computer network?',
        'conversation_id': conv_id,
        'language': 'en-IN'
    }, format='json')
    req.user = user
    res = chat_view(req)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert res.data.get('conversation_id') == conv_id, "conversation_id mismatch"
    assert res.data.get('topic') != 'IT & Laboratory Equipment', f"Forbidden complaint topic: {res.data.get('topic')}"
    print(f"[PASS] Test 3: Chatbot replied to 'What is computer network?' with topic '{res.data.get('topic')}'")

    # Verify database persistence in ChatMessage
    messages = ChatMessage.objects.filter(conversation_id=conv_id).order_by('created_at')
    assert messages.count() == 2, f"Expected 2 messages (1 user, 1 assistant), got {messages.count()}"
    user_msg = messages[0]
    bot_msg = messages[1]
    assert user_msg.role == 'user' and user_msg.content == 'What is computer network?'
    assert bot_msg.role == 'assistant' and 'computer network' in bot_msg.content.lower()
    print(f"[PASS] Test 4: Database persistence verified (1 user message, 1 assistant message in DB)")

    # 4. Test GET /api/ai/conversations/<conv_id>/
    detail_view = ConversationDetailView.as_view()
    req = factory.get(f'/api/ai/conversations/{conv_id}/')
    req.user = user
    res = detail_view(req, conversation_id=conv_id)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    detail_conv = res.data.get('conversation')
    assert len(detail_conv.get('messages', [])) == 2, f"Expected 2 messages returned in detail, got {len(detail_conv.get('messages', []))}"
    print(f"[PASS] Test 5: Retrieved conversation detail with {len(detail_conv['messages'])} persisted messages")

    # 5. Multi-turn chat persistence test (Second question in same conversation)
    req = factory.post('/api/ai/chat/', {
        'message': 'Write a Python program to check prime numbers.',
        'conversation_id': conv_id,
        'language': 'en-IN'
    }, format='json')
    req.user = user
    res = chat_view(req)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    messages = ChatMessage.objects.filter(conversation_id=conv_id)
    assert messages.count() == 4, f"Expected 4 messages after turn 2, got {messages.count()}"
    print(f"[PASS] Test 6: Multi-turn turn 2 persisted (Total messages in conversation: {messages.count()})")

    # 6. Test GET /api/ai/languages/
    lang_view = LanguageCapabilitiesView.as_view()
    req = factory.get('/api/ai/languages/')
    res = lang_view(req)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    caps = res.data.get('capabilities', {})
    assert 'hi-IN' in caps and 'ta-IN' in caps and 'en-IN' in caps and 'te-IN' in caps
    assert len(caps) >= 23, f"Expected at least 23 languages (22 Indian + English), got {len(caps)}"
    print(f"[PASS] Test 7: Language capabilities API returned {len(caps)} official Indian languages + English")

    # Specific language query: ?language=ta-IN
    req = factory.get('/api/ai/languages/?language=ta-IN')
    res = lang_view(req)
    assert res.status_code == 200
    ta_caps = res.data.get('capabilities')
    assert ta_caps['name'] == 'Tamil' and ta_caps['speech_to_text'] is True
    print(f"[PASS] Test 8: Specific language query for Tamil returned valid capabilities (STT={ta_caps['speech_to_text']}, TTS={ta_caps['text_to_speech']})")

    # 7. Test DELETE /api/ai/conversations/<conv_id>/
    req = factory.delete(f'/api/ai/conversations/{conv_id}/')
    req.user = user
    res = detail_view(req, conversation_id=conv_id)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert not ChatConversation.objects.filter(id=conv_id).exists(), "Conversation should be deleted"
    print(f"[PASS] Test 9: Deleted conversation {conv_id} safely with cascade on messages")

    # Clean up
    user.delete()
    print("=" * 60)
    print("ALL 9 CONVERSATION & PERSISTENCE API TESTS PASSED!")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
