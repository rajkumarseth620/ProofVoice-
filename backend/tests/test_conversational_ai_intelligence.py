# -*- coding: utf-8 -*-
"""
Verification Test Suite: ProofVoice Real-Time Conversational AI Assistant.
Validates the 3 independent intents and the Absolute Priority Rule:
- GENERAL_KNOWLEDGE: Direct educational & general AI answers (never triggers complaints).
- WEBSITE_SUPPORT: Verified website procedures.
- CAMPUS_COMPLAINT: Activated only when reporting issues or tracking tickets.
"""

import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['USE_SQLITE_FOR_TESTS'] = '1'
sys.path.insert(0, 'backend')

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import django
django.setup()

from apps.integrations.ai_chat import AiChatService
from apps.integrations.ai_assistant_services.intent_classifier import IntentClassifier, AssistantIntent

TEST_CASES = [
    # --------------------------------------------------------------------------
    # MANDATORY TEST 1: "What is computer network?"
    # --------------------------------------------------------------------------
    {
        'id': 'TEST 1',
        'query': "What is computer network?",
        'lang': 'en-IN',
        'expected_intent': AssistantIntent.GENERAL_KNOWLEDGE,
        'must_contain': ['network', 'interconnected', 'devices', 'LAN', 'WAN', 'protocols'],
        'must_NOT_contain': ['Recommended Category', 'Assigned Department', 'Suggested Priority', 'Report an Issue'],
        'description': "Proper educational explanation of computer networks, NOT complaint diagnostics"
    },

    # --------------------------------------------------------------------------
    # MANDATORY TEST 2: "What is IT?"
    # --------------------------------------------------------------------------
    {
        'id': 'TEST 2',
        'query': "What is IT?",
        'lang': 'en-IN',
        'expected_intent': AssistantIntent.GENERAL_KNOWLEDGE,
        'must_contain': ['Information Technology', 'computers', 'software', 'electronic data'],
        'must_NOT_contain': ['Recommended Category', 'Assigned Department', 'Suggested Priority', 'Report an Issue'],
        'description': "Explain Information Technology educational concepts"
    },

    # --------------------------------------------------------------------------
    # MANDATORY TEST 3: "Explain Python programming."
    # --------------------------------------------------------------------------
    {
        'id': 'TEST 3',
        'query': "Explain Python programming.",
        'lang': 'en-IN',
        'expected_intent': AssistantIntent.GENERAL_KNOWLEDGE,
        'must_contain': ['Python', 'high-level', 'interpreted', 'readability'],
        'must_NOT_contain': ['Recommended Category', 'Assigned Department', 'Suggested Priority'],
        'description': "Proper educational explanation of Python programming"
    },

    # --------------------------------------------------------------------------
    # MANDATORY TEST 4: "How does Wi-Fi work?"
    # --------------------------------------------------------------------------
    {
        'id': 'TEST 4',
        'query': "How does Wi-Fi work?",
        'lang': 'en-IN',
        'expected_intent': AssistantIntent.GENERAL_KNOWLEDGE,
        'must_contain': ['radio', 'waves', 'frequency', 'router', '802.11'],
        'must_NOT_contain': ['Recommended Category', 'Assigned Department', 'Suggested Priority'],
        'description': "Explain wireless networking technology without triggering IT ticket"
    },

    # --------------------------------------------------------------------------
    # MANDATORY TEST 5: "How do I change my ProofVoice password?"
    # --------------------------------------------------------------------------
    {
        'id': 'TEST 5',
        'query': "How do I change my ProofVoice password?",
        'lang': 'en-IN',
        'expected_intent': AssistantIntent.WEBSITE_SUPPORT,
        'must_contain': ['Profile & Settings', 'Change Password', 'password'],
        'must_NOT_contain': ['Recommended Category', 'Assigned Department'],
        'description': "Actual website-specific password change instructions"
    },

    # --------------------------------------------------------------------------
    # MANDATORY TEST 6: "How can I check my active complaints?"
    # --------------------------------------------------------------------------
    {
        'id': 'TEST 6',
        'query': "How can I check my active complaints?",
        'lang': 'en-IN',
        'expected_intent': AssistantIntent.CAMPUS_COMPLAINT,
        'must_contain': ['My Complaints', 'status'],
        'must_NOT_contain': [],
        'description': "Explain actual complaint tracking and statuses"
    },

    # --------------------------------------------------------------------------
    # MANDATORY TEST 7: "My classroom projector is broken. I want to report it."
    # --------------------------------------------------------------------------
    {
        'id': 'TEST 7',
        'query': "My classroom projector is broken. I want to report it.",
        'lang': 'en-IN',
        'expected_intent': AssistantIntent.CAMPUS_COMPLAINT,
        'must_contain': ['Classroom and Laboratory', 'Campus IT Services', 'Create Complaint'],
        'must_NOT_contain': [],
        'description': "Activate campus complaint assistance workflow"
    },

    # --------------------------------------------------------------------------
    # MANDATORY TEST 8: "Hello, how are you?"
    # --------------------------------------------------------------------------
    {
        'id': 'TEST 8',
        'query': "Hello, how are you?",
        'lang': 'en-IN',
        'expected_intent': AssistantIntent.GENERAL_KNOWLEDGE,
        'must_contain': ['doing', 'ProofVoice AI'],
        'must_NOT_contain': ['Recommended Category', 'Assigned Department', 'Suggested Priority'],
        'description': "Natural conversational rapport"
    },

    # --------------------------------------------------------------------------
    # MANDATORY TEST 9: "मुझे कंप्यूटर नेटवर्क समझाओ।"
    # --------------------------------------------------------------------------
    {
        'id': 'TEST 9',
        'query': "मुझे कंप्यूटर नेटवर्क समझाओ।",
        'lang': 'hi-IN',
        'expected_intent': AssistantIntent.GENERAL_KNOWLEDGE,
        'must_contain': ['कंप्यूटर नेटवर्क', 'डेटा', 'LAN', 'WAN', 'राउटर'],
        'must_NOT_contain': ['अनुशंसित श्रेणी', 'संबंधित विभाग'],
        'description': "Explain computer networks in Hindi"
    },

    # --------------------------------------------------------------------------
    # MANDATORY TEST 10: "What is TCP? Explain it in simple words."
    # --------------------------------------------------------------------------
    {
        'id': 'TEST 10',
        'query': "What is TCP? Explain it in simple words.",
        'lang': 'en-IN',
        'expected_intent': AssistantIntent.GENERAL_KNOWLEDGE,
        'must_contain': ['Transmission Control Protocol', 'reliable', 'packets', 'handshake'],
        'must_NOT_contain': ['Recommended Category', 'Assigned Department'],
        'description': "Correct simple educational explanation of TCP"
    },

    # --------------------------------------------------------------------------
    # ADDITIONAL TEST 11: "What is artificial intelligence?"
    # --------------------------------------------------------------------------
    {
        'id': 'TEST 11',
        'query': "What is artificial intelligence?",
        'lang': 'en-IN',
        'expected_intent': AssistantIntent.GENERAL_KNOWLEDGE,
        'must_contain': ['Artificial Intelligence', 'Machine Learning', 'Computer Science'],
        'must_NOT_contain': ['Recommended Category', 'Assigned Department'],
        'description': "Educational explanation of AI"
    },

    # --------------------------------------------------------------------------
    # ADDITIONAL TEST 12: "Write a Python program to check prime numbers."
    # --------------------------------------------------------------------------
    {
        'id': 'TEST 12',
        'query': "Write a Python program to check prime numbers.",
        'lang': 'en-IN',
        'expected_intent': AssistantIntent.GENERAL_KNOWLEDGE,
        'must_contain': ['def is_prime', 'python', 'sqrt'],
        'must_NOT_contain': ['Recommended Category', 'Assigned Department'],
        'description': "Working Python program with explanation"
    },

    # --------------------------------------------------------------------------
    # ADDITIONAL TEST 13: "What is the capital of Japan?"
    # --------------------------------------------------------------------------
    {
        'id': 'TEST 13',
        'query': "What is the capital of Japan?",
        'lang': 'en-IN',
        'expected_intent': AssistantIntent.GENERAL_KNOWLEDGE,
        'must_contain': ['Tokyo'],
        'must_NOT_contain': ['Recommended Category', 'Assigned Department'],
        'description': "Correct factual answer (Tokyo)"
    },

    # --------------------------------------------------------------------------
    # ADDITIONAL TEST 14: "Explain the difference between TCP and UDP."
    # --------------------------------------------------------------------------
    {
        'id': 'TEST 14',
        'query': "Explain the difference between TCP and UDP.",
        'lang': 'en-IN',
        'expected_intent': AssistantIntent.GENERAL_KNOWLEDGE,
        'must_contain': ['TCP', 'UDP', 'Connection-Oriented', 'Connectionless'],
        'must_NOT_contain': ['Recommended Category', 'Assigned Department'],
        'description': "Proper technical comparison of TCP vs UDP"
    },

    # --------------------------------------------------------------------------
    # ADDITIONAL TEST 15: "What is laboratory equipment?"
    # --------------------------------------------------------------------------
    {
        'id': 'TEST 15',
        'query': "What is laboratory equipment?",
        'lang': 'en-IN',
        'expected_intent': AssistantIntent.GENERAL_KNOWLEDGE,
        'must_contain': ['scientific', 'experiments', 'measuring'],
        'must_NOT_contain': ['Recommended Category', 'Assigned Department', 'Suggested Priority'],
        'description': "Educational explanation of laboratory equipment (NOT a complaint)"
    },

    # --------------------------------------------------------------------------
    # ADDITIONAL TEST 16: "What is a projector?"
    # --------------------------------------------------------------------------
    {
        'id': 'TEST 16',
        'query': "What is a projector?",
        'lang': 'en-IN',
        'expected_intent': AssistantIntent.GENERAL_KNOWLEDGE,
        'must_contain': ['optical', 'output', 'image', 'screen'],
        'must_NOT_contain': ['Recommended Category', 'Assigned Department', 'Suggested Priority'],
        'description': "Educational explanation of a projector (NOT a complaint)"
    },

    # --------------------------------------------------------------------------
    # ADDITIONAL TEST 17: "how to sign out ?"
    # --------------------------------------------------------------------------
    {
        'id': 'TEST 17',
        'query': "how to sign out ?",
        'lang': 'en-IN',
        'expected_intent': AssistantIntent.WEBSITE_SUPPORT,
        'must_contain': ['Sign Out', 'sidebar'],
        'must_NOT_contain': ['Recommended Category', 'Assigned Department'],
        'description': "Verified website guidance for signing out"
    }
]


def run_tests():
    print("=" * 70)
    print("RUNNING PROOFVOICE CONVERSATIONAL AI INTELLIGENCE TEST SUITE")
    print("=" * 70)

    passed_count = 0
    total_count = len(TEST_CASES)

    for tc in TEST_CASES:
        query = tc['query']
        lang = tc['lang']
        expected_intent = tc['expected_intent']

        # 1. Test Intent Classification
        detected_intent = IntentClassifier.classify(query, lang)
        if detected_intent != expected_intent:
            print(f"[FAIL] {tc['id']}: Query: '{query}'")
            print(f"       Expected Intent: {expected_intent}, Got: {detected_intent}")
            continue

        # 2. Test Response Generation
        res = AiChatService.get_response(query, user=None, preferred_language=lang)
        reply = res.get('reply', '')

        # Check required keywords
        missing_kw = [kw for kw in tc['must_contain'] if kw.lower() not in reply.lower()]
        if missing_kw:
            print(f"[FAIL] {tc['id']}: Query: '{query}' missing required keywords: {missing_kw}")
            print(f"       Actual Reply Preview: {reply[:150]}...")
            continue

        # Check prohibited keywords
        forbidden_found = [kw for kw in tc['must_NOT_contain'] if kw.lower() in reply.lower()]
        if forbidden_found:
            print(f"[FAIL] {tc['id']}: Query: '{query}' triggered forbidden complaint keywords: {forbidden_found}")
            print(f"       Actual Reply Preview: {reply[:150]}...")
            continue

        print(f"[PASS] {tc['id']}: '{query}'")
        print(f"       Intent: {detected_intent.value} | Topic: {res.get('topic')}")
        preview = reply.replace('\n', ' ')[:90]
        print(f"       Preview: {preview}...\n")
        passed_count += 1

    print("=" * 70)
    print(f"RESULTS: {passed_count}/{total_count} TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

    if passed_count != total_count:
        sys.exit(1)


if __name__ == '__main__':
    run_tests()
