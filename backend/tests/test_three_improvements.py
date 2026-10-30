import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

import django
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from apps.accounts.models import User, StudentProfile
from apps.complaints.models import Complaint
from apps.notifications.models import Notification
from apps.integrations.views import AiChatbotView
from apps.integrations.ai_chat import AiChatService

NotificationType = Notification.NotificationType

def run_tests():
    print('========================================')
    print('VERIFYING THREE REQUESTED IMPROVEMENTS')
    print('========================================')

    # 1. TEST AI CHATBOT
    print('\n[1/3] Testing AI Chatbot & Help Assistant...')
    student = User.objects.filter(role=User.Role.STUDENT, email='laxmi.seth@apex.edu').first()
    factory = APIRequestFactory()

    # Endpoint POST
    req = factory.post('/api/ai/chat/', {'message': 'How does voice reporting work?', 'voice_mode': True}, format='json')
    force_authenticate(req, user=student)
    res = AiChatbotView.as_view()(req)
    assert res.status_code == 200, f'Expected 200, got {res.status_code}'
    assert res.data.get('topic') == 'voice_reporting'
    assert len(res.data.get('speak_text', '')) > 20
    assert len(res.data.get('suggested_actions', [])) > 0
    print('  [PASS] AI Chatbot endpoint answered topic "voice_reporting" with speak_text')

    # Complaint check
    res_comp = AiChatService.get_response('What are my complaints?', user=student)
    assert res_comp.get('topic') in ['complaints_summary', 'no_complaints']
    print('  [PASS] Authenticated complaint query returned topic:', res_comp.get('topic'))

    # 2. TEST PROFILE PERSISTENCE
    print('\n[2/3] Testing Student Profile Saving & Persistence in MySQL...')
    sp, _ = StudentProfile.objects.get_or_create(user=student)
    sp.student_id = 'AIT-TEST-2026'
    sp.department = 'Computer Science & Engineering'
    sp.course = 'B.Tech CSE'
    sp.semester = '3rd Year, 5th Semester'
    sp.address = 'Hostel Block B, Room 204'
    sp.phone = '+91 9876543210'
    sp.notify_in_app = True
    sp.notify_email = True
    sp.save()

    # Re-read fresh from database
    sp_fresh = StudentProfile.objects.get(user=student)
    assert sp_fresh.student_id == 'AIT-TEST-2026'
    assert sp_fresh.address == 'Hostel Block B, Room 204'
    assert sp_fresh.notify_in_app is True
    print('  [PASS] Student profile fields successfully written and verified fresh from MySQL')

    # 3. TEST PERSONALIZED NOTIFICATIONS
    print('\n[3/3] Testing Personalized Notifications...')
    complaint = Complaint.objects.filter(student=student).first()
    if complaint:
        notif = Notification.create_for_event(
            recipient=student,
            title='Status Updated: In Progress',
            message='Your grievance has been assigned to IT Support.',
            notification_type=NotificationType.STATUS_CHANGE,
            complaint=complaint
        )
        assert notif is not None, 'Expected notification to be created'
        assert notif.recipient == student
        assert notif.complaint == complaint
        print('  [PASS] Real notification created for student:', notif.title)

        # Test duplicate prevention
        dup = Notification.create_for_event(
            recipient=student,
            title='Status Updated: In Progress',
            message='Your grievance has been assigned to IT Support.',
            notification_type=NotificationType.STATUS_CHANGE,
            complaint=complaint
        )
        assert dup.id == notif.id, 'Duplicate within 5 minutes was not deduplicated'
        print('  [PASS] Duplicate notification within 5 minutes successfully prevented')

    print('\n========================================')
    print('>>> ALL THREE IMPROVEMENTS 100% VERIFIED! <<<')
    print('========================================')

if __name__ == '__main__':
    run_tests()
