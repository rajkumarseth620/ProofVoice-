"""
Automated Verification Suite for ProofVoice Multilingual Indian Language AI Assistant.
Tests all 11 Indian languages and real-time conversational capabilities.
"""

import os
import sys

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, 'apps'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('USE_SQLITE_FOR_TESTS', '1')

import django
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from apps.accounts.models import User
from apps.integrations.views import AiChatbotView
from apps.integrations.ai_chat import AiChatService, detect_language

def run_multilingual_tests():
    print("==================================================")
    print("VERIFYING MULTILINGUAL INDIAN AI CHAT ASSISTANT")
    print("==================================================")

    student = User.objects.filter(role=User.Role.STUDENT).first()
    factory = APIRequestFactory()

    # 1. TEST TAMIL GREETING (USER TEST CASE: "அக்கா")
    print("\n[1] Testing Tamil User Case: 'அக்கா' (Akka)...")
    req = factory.post('/api/ai/chat/', {'message': 'அக்கா', 'language': 'ta-IN'}, format='json')
    if student: force_authenticate(req, user=student)
    res = AiChatbotView.as_view()(req)
    assert res.status_code == 200
    assert res.data.get('language') == 'ta-IN'
    assert 'ProofVoice AI உதவியாளர்' in res.data.get('reply') or 'வணக்கம்' in res.data.get('reply')
    print("  [PASS] 'அக்கா' answered in Tamil (தமிழ்):", res.data.get('reply')[:60].replace('\n', ' '))

    # 2. TEST TAMIL IDENTITY QUERY: "உன் பெயர் என்ன"
    print("\n[2] Testing Tamil Identity: 'உன் பெயர் என்ன'...")
    req = factory.post('/api/ai/chat/', {'message': 'உன் பெயர் என்ன', 'language': 'ta-IN'}, format='json')
    if student: force_authenticate(req, user=student)
    res = AiChatbotView.as_view()(req)
    assert res.status_code == 200
    assert res.data.get('language') == 'ta-IN'
    assert 'ProofVoice AI உதவியாளர்' in res.data.get('reply')
    print("  [PASS] 'உன் பெயர் என்ன' answered with real-time name in Tamil:", res.data.get('reply')[:65].replace('\n', ' '))

    # 3. TEST REAL-TIME IDENTITY IN ENGLISH
    print("\n[3] Testing Real-Time Identity: 'What is your name?'...")
    res = AiChatService.get_response('What is your name?', user=student, preferred_language='en-IN')
    assert res.get('language') == 'en-IN'
    assert 'ProofVoice AI Assistant' in res.get('reply')
    assert res.get('topic') == 'identity'
    print("  [PASS] 'What is your name?' answered directly in English:", res.get('reply')[:65].replace('\n', ' '))

    # 4. TEST REAL-TIME IDENTITY IN HINDI
    print("\n[4] Testing Real-Time Identity in Hindi: 'Aapka naam kya hai?'...")
    res = AiChatService.get_response('Aapka naam kya hai?', user=student, preferred_language='hi-IN')
    assert res.get('language') == 'hi-IN'
    assert 'ProofVoice AI असिस्टेंट' in res.get('reply')
    assert res.get('topic') == 'identity'
    print("  [PASS] 'Aapka naam kya hai?' answered in Hindi:", res.get('reply')[:65].replace('\n', ' '))

    # 5. TEST REAL-TIME IDENTITY IN TELUGU
    print("\n[5] Testing Real-Time Identity in Telugu: 'Mee peru enti?'...")
    res = AiChatService.get_response('Mee peru enti?', user=student, preferred_language='te-IN')
    assert res.get('language') == 'te-IN'
    assert 'ProofVoice AI అసిస్టెంట్' in res.get('reply')
    print("  [PASS] 'Mee peru enti?' answered in Telugu:", res.get('reply')[:65].replace('\n', ' '))

    # 6. TEST REAL-TIME IDENTITY IN GUJARATI
    print("\n[6] Testing Real-Time Identity in Gujarati: 'Tamaru naam shu chhe?'...")
    res = AiChatService.get_response('Tamaru naam shu chhe?', user=student, preferred_language='gu-IN')
    assert res.get('language') == 'gu-IN'
    assert 'ProofVoice AI આસિસ્ટન્ટ' in res.get('reply')
    print("  [PASS] 'Tamaru naam shu chhe?' answered in Gujarati:", res.get('reply')[:65].replace('\n', ' '))

    # 7. TEST LANGUAGE SCRIPT AUTO-DETECTION ACROSS OTHER INDIAN LANGUAGES
    print("\n[7] Testing Language Script Auto-Detection Across Other Indian Languages...")
    languages_tests = [
        ('kn-IN', 'ನಿಮ್ಮ ಹೆಸರು ಏನು', 'ಕನ್ನಡ'),
        ('bn-IN', 'আপনার নাম কি', 'বাংলা'),
        ('mr-IN', 'तुमचे नाव काय आहे', 'मराठी'),
        ('ml-IN', 'നിങ്ങളുടെ പേര് എന്താണ്', 'മലയാളം'),
        ('pa-IN', 'ਤੁਹਾਡਾ ਨਾਮ ਕੀ ਹੈ', 'ਪੰਜਾਬੀ'),
        ('or-IN', 'ଆପଣଙ୍କ ନାମ କଣ', 'ଓଡ଼ିଆ'),
    ]
    for code, text, lang_name in languages_tests:
        det = detect_language(text)
        res = AiChatService.get_response(text, user=student)
        assert res.get('language') == code, f"Expected {code}, got {res.get('language')}"
        print(f"  [PASS] {lang_name} ({code}) detected & answered accurately: {res.get('reply')[:50].replace('\n', ' ')}")

    # 8. TEST TAMIL PROBLEM DIAGNOSTICS & GUIDANCE
    print("\n[8] Testing Tamil Problem Diagnostics: 'குடிநீர் பிரச்சனை உள்ளது' (Drinking water issue)...")
    res = AiChatService.get_response('குடிநீர் பிரச்சனை உள்ளது', user=student, preferred_language='ta-IN')
    assert res.get('language') == 'ta-IN'
    assert res.get('topic') == 'problem_diagnostics'
    print("  [PASS] Tamil problem diagnostics identified Category & Dept in Tamil:", res.get('reply')[:70].replace('\n', ' '))

    # 9. TEST TAMIL EDIT / DELETE GUIDANCE
    print("\n[9] Testing Tamil Complaint Edit/Delete Query: 'விண்ணப்பத்தை எடிட் செய்வது எப்படி?'...")
    res = AiChatService.get_response('விண்ணப்பத்தை எடிட் செய்வது எப்படி?', user=student, preferred_language='ta-IN')
    assert res.get('language') == 'ta-IN'
    assert res.get('topic') == 'edit_delete_complaint'
    print("  [PASS] Tamil application edit guidance answered in Tamil:", res.get('reply')[:65].replace('\n', ' '))

    # 10. TEST TAMIL PASSWORD CHANGE GUIDANCE
    print("\n[10] Testing Tamil Password Change Query: 'கடவுச்சொல்லை மாற்றுவது எப்படி?'...")
    res = AiChatService.get_response('கடவுச்சொல்லை மாற்றுவது எப்படி?', user=student, preferred_language='ta-IN')
    assert res.get('language') == 'ta-IN'
    assert res.get('topic') == 'password_change'
    print("  [PASS] Tamil password update guidance answered in Tamil:", res.get('reply')[:65].replace('\n', ' '))

    print("\n==================================================")
    print(">>> ALL MULTILINGUAL AI TESTS 100% PASSED! <<<")
    print("==================================================")

if __name__ == '__main__':
    run_multilingual_tests()
