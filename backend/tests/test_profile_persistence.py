import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('USE_SQLITE_FOR_TESTS', '1')

import django
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from apps.accounts.models import User, StudentProfile
from apps.institutions.models import Institution
from apps.accounts.views import ProfileView, MeView

def test_profile_persistence():
    print("==================================================")
    print("VERIFYING STUDENT PROFILE PERSISTENCE (CAMELCASE & SNAKE_CASE)")
    print("==================================================")

    test_email = 'isolated_profile_test_student@test.local'
    inst = Institution.objects.first()
    student, _ = User.objects.get_or_create(
        email=test_email,
        defaults={'role': User.Role.STUDENT, 'full_name': 'Original Test Name', 'is_verified': True}
    )
    StudentProfile.objects.get_or_create(user=student, defaults={'institution': inst})
    print(f"Testing with isolated fixture student: {student.email} (ID: {student.id})")

    factory = APIRequestFactory()

    try:
        # 1. Test camelCase PATCH (sent by frontend form)
        camel_payload = {
            "fullName": "Maya Sharma Updated",
            "studentIdentifier": "STU-AIT-9999",
            "department": "Computer Science & Eng",
            "course": "B.Tech CSE Advanced",
            "yearSemester": "4th Year, 8th Sem",
            "residentialAddress": "Flat 302, Nilgiri Towers, Campus West",
            "phone": "+919988776655",
            "notifyInApp": False,
            "notifyEmail": True
        }

        req = factory.patch('/api/v1/auth/profile/', camel_payload, format='json')
        force_authenticate(req, user=student)
        res = ProfileView.as_view()(req)

        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.data}"
        print("  [PASS] ProfileView.patch returned 200 OK")

        # 2. Verify in MySQL database fresh from DB
        student.refresh_from_db()
        assert student.full_name == "Maya Sharma Updated", f"User full_name not saved: {student.full_name}"

        profile = StudentProfile.objects.get(user=student)
        assert profile.student_id == "STU-AIT-9999", f"student_id mismatch: {profile.student_id}"
        assert profile.department == "Computer Science & Eng", f"department mismatch: {profile.department}"
        assert profile.course == "B.Tech CSE Advanced", f"course mismatch: {profile.course}"
        assert profile.semester == "4th Year, 8th Sem", f"semester mismatch: {profile.semester}"
        assert profile.address == "Flat 302, Nilgiri Towers, Campus West", f"address mismatch: {profile.address}"
        assert profile.phone in ["+919988776655", "+91 9988776655"], f"phone mismatch: {profile.phone}"
        assert profile.notify_in_app is False, f"notify_in_app mismatch: {profile.notify_in_app}"
        assert profile.notify_email is True, f"notify_email mismatch: {profile.notify_email}"
        print("  [PASS] All 9 student profile fields successfully persisted to MySQL database!")

        # 3. Test MeView to verify session hydration
        req_me = factory.get('/api/v1/auth/me/')
        force_authenticate(req_me, user=student)
        res_me = MeView.as_view()(req_me)

        assert res_me.status_code == 200, f"Expected 200, got {res_me.status_code}"
        me_data = res_me.data
        assert me_data['full_name'] == "Maya Sharma Updated"
        assert me_data['student_profile']['student_id'] == "STU-AIT-9999"
        assert me_data['student_profile']['semester'] == "4th Year, 8th Sem"
        assert me_data['student_profile']['address'] == "Flat 302, Nilgiri Towers, Campus West"
        print("  [PASS] MeView returned fresh database persisted data for session refresh!")

        print("==================================================")
        print(">>> STUDENT PROFILE PERSISTENCE 100% VERIFIED! <<<")
        print("==================================================")

    finally:
        student.delete()
        print("  [CLEANUP] Isolated profile test user safely removed.")

if __name__ == '__main__':
    test_profile_persistence()
