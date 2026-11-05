# -*- coding: utf-8 -*-
"""
Automated regression tests for ProofVoice Multilingual AI Assistant.
Validates profile photo editing queries, conversational questions, and Indian language support.
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['USE_SQLITE_FOR_TESTS'] = '1'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import django
django.setup()

from apps.integrations.ai_chat import AiChatService

test_cases = [
    # 1. Profile photo query from user screenshot:
    {
        'query': 'i want to edit my image in my profile fow to do that ?',
        'lang': 'en-IN',
        'expected_topic': 'profile_photo_guidance'
    },
    {
        'query': 'how do i change my profile picture',
        'lang': 'en-IN',
        'expected_topic': 'profile_photo_guidance'
    },
    {
        'query': 'अपनी प्रोफाइल फोटो कैसे बदलें',
        'lang': 'hi-IN',
        'expected_topic': 'profile_photo_guidance'
    },
    {
        'query': 'என் சுயவிவரப் படத்தை எப்படி மாற்றுவது',
        'lang': 'ta-IN',
        'expected_topic': 'profile_photo_guidance'
    },
    {
        'query': 'ప్రొఫైల్ ఫోటో ఎలా మార్చాలి',
        'lang': 'te-IN',
        'expected_topic': 'profile_photo_guidance'
    },
    {
        'query': 'আমার প্রোফাইল ছবি কিভাবে পরিবর্তন করব',
        'lang': 'bn-IN',
        'expected_topic': 'profile_photo_guidance'
    },
    # 2. Conversational queries:
    {
        'query': 'what are you doing',
        'lang': 'en-IN',
        'expected_topic': 'what_are_you_doing'
    },
    {
        'query': 'kya kar rahe ho',
        'lang': 'hi-IN',
        'expected_topic': 'what_are_you_doing'
    },
    {
        'query': 'how was your day',
        'lang': 'en-IN',
        'expected_topic': 'how_was_your_day'
    },
    {
        'query': 'tell me a joke',
        'lang': 'en-IN',
        'expected_topic': 'humor_joke'
    },
    {
        'query': 'who made you',
        'lang': 'en-IN',
        'expected_topic': 'creator_info'
    },
    {
        'query': 'what can you help me with',
        'lang': 'en-IN',
        'expected_topic': 'capabilities_help'
    },
    # 3. Profile details:
    {
        'query': 'how do i update my name and student id in profile',
        'lang': 'en-IN',
        'expected_topic': 'profile_details_guidance'
    },
    # 4. Notifications:
    {
        'query': 'how can i delete my notifications',
        'lang': 'en-IN',
        'expected_topic': 'notifications_guidance'
    }
]

def run_tests():
    failures = 0
    for tc in test_cases:
        res = AiChatService.get_response(tc['query'], user=None, preferred_language=tc['lang'])
        actual_topic = res.get('topic')
        status = "PASS" if actual_topic == tc['expected_topic'] else "FAIL"
        if status == "FAIL":
            failures += 1
        reply_preview = res.get('reply', '').replace('\n', ' ')[:90]
        print(f"[{status}] Query: '{tc['query']}' ({tc['lang']}) -> Topic: {actual_topic}")
        print(f"       Preview: {reply_preview}...\n")

    if failures == 0:
        print("=========================================")
        print("ALL 14 MULTILINGUAL TEST CASES PASSED!!")
        print("=========================================")
        return True
    else:
        print(f"FAILED {failures} test cases.")
        return False

if __name__ == '__main__':
    ok = run_tests()
    if not ok:
        sys.exit(1)
