# -*- coding: utf-8 -*-
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

test_cases = [
    # 1. User's exact query from screenshot:
    {
        'query': 'how to sign out ?',
        'lang': 'en-IN',
        'expected_topic': 'campus_sign_out'
    },
    {
        'query': 'साइन आउट कैसे करें',
        'lang': 'hi-IN',
        'expected_topic': 'campus_sign_out'
    },
    # 2. Registration and login questions:
    {
        'query': 'how to register in proofvoice',
        'lang': 'en-IN',
        'expected_topic': 'campus_registration'
    },
    {
        'query': 'cannot login to my student account',
        'lang': 'en-IN',
        'expected_topic': 'campus_login_troubleshooting'
    },
    # 3. Complaint creation, status, edit:
    {
        'query': 'how do i create a complaint',
        'lang': 'en-IN',
        'expected_topic': 'campus_create_complaint'
    },
    {
        'query': 'what does in progress status mean',
        'lang': 'en-IN',
        'expected_topic': 'campus_complaint_status'
    },
    {
        'query': 'how to delete my complaint',
        'lang': 'en-IN',
        'expected_topic': 'campus_edit_delete_complaint'
    },
    # 4. Profile image & details:
    {
        'query': 'i want to edit my image in my profile fow to do that ?',
        'lang': 'en-IN',
        'expected_topic': 'profile_photo_guidance'
    },
    # 5. General Knowledge / Live Web Search:
    {
        'query': 'what is Python programming language',
        'lang': 'en-IN',
        'expected_topic': None # Should answer informatively via web search / knowledge engine
    }
]

failures = 0
for tc in test_cases:
    res = AiChatService.get_response(tc['query'], user=None, preferred_language=tc['lang'])
    topic = res.get('topic')
    reply = res.get('reply', '')
    expected = tc['expected_topic']
    status = "PASS" if (expected is None or topic == expected) else "FAIL"
    if status == "FAIL":
        failures += 1
    clean_preview = reply.replace('\n', ' ')[:100]
    print(f"[{status}] Query: '{tc['query']}' -> Topic: {topic}")
    print(f"       Preview: {clean_preview}...\n")

if failures == 0:
    print("ALL TESTS PASSED SUCCESSFULLY!")
else:
    print(f"FAILED {failures} TESTS!")
    sys.exit(1)
