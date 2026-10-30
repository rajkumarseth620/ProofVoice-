"""
Verification script for ProofVoice live Django + MySQL endpoints.
Tests every key endpoint against the actual configured MySQL database (proofvoice_db).
Ensures passwords and secrets are never printed.
Cleans up only fictional test records created during the test run.
"""

import os
import sys

# Ensure backend root is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.db import connection
from rest_framework.test import APIClient
from apps.accounts.models import User, StudentProfile, AdministratorProfile
from apps.institutions.models import Institution, InstitutionDepartment, ComplaintCategory
from apps.complaints.models import Complaint, ComplaintStatusHistory
from apps.notifications.models import Notification

def run_verification():
    print("=" * 60)
    print("PROOFVOICE LIVE MYSQL ENDPOINT & INTEGRATION VERIFICATION")
    print("=" * 60)

    # 1. Database Engine and Name Check
    db_settings = connection.settings_dict
    engine = db_settings.get('ENGINE')
    db_name = db_settings.get('NAME')
    print(f"Database Engine: {engine}")
    print(f"Database Name: {db_name}")
    is_real_mysql = 'mysql' in engine.lower() and db_name == 'proofvoice_db'
    print(f"Using Real MySQL proofvoice_db? {is_real_mysql}")
    if not is_real_mysql:
        print("ERROR: Not connected to proofvoice_db via MySQL!")
        return False

    client = APIClient()
    results = []

    # 2. Public Institution List
    res = client.get('/api/v1/institutions/')
    status_ok = res.status_code == 200 and len(res.data) > 0
    results.append(('GET', '/api/v1/institutions/', 'Public', 200, res.status_code, status_ok, 'Reads MySQL'))
    print(f"1. GET /api/v1/institutions/ -> {res.status_code} (Count: {len(res.data)})")

    # 3. Public Institution Detail
    apex_inst = Institution.objects.filter(code='apex-tech').first()
    if apex_inst:
        res = client.get(f'/api/v1/institutions/{apex_inst.id}/')
        status_ok = res.status_code == 200 and res.data.get('code') == 'apex-tech'
        results.append(('GET', f'/api/v1/institutions/{apex_inst.id}/', 'Public', 200, res.status_code, status_ok, 'Reads MySQL'))
        print(f"2. GET /api/v1/institutions/{apex_inst.id}/ -> {res.status_code} ({res.data.get('name')})")

    # 4. Student Registration
    test_email = 'audit.fictional.student@apextech.edu'
    # Clean up prior test user if exists
    User.objects.filter(email=test_email).delete()

    reg_payload = {
        'email': test_email,
        'password': 'StrongPassword123!',
        'full_name': 'Audit Verification Student',
        'institution_id': apex_inst.id if apex_inst else 1,
        'student_id': 'AIT-VERIFY-99',
        'department': 'Information Technology',
        'course': 'B.Tech IT',
        'semester': '6th Semester',
        'phone': '9876543210',
        'address': 'Campus Hostel B-402'
    }
    res = client.post('/api/v1/auth/register/student/', reg_payload, format='json')
    status_ok = res.status_code == 201 and 'token' in res.data
    results.append(('POST', '/api/v1/auth/register/student/', 'Public', 201, res.status_code, status_ok, 'Writes MySQL'))
    print(f"3. POST /api/v1/auth/register/student/ -> {res.status_code} (User ID: {res.data.get('user', {}).get('id') if status_ok else 'N/A'})")

    # Verify student persisted in MySQL
    created_student = User.objects.filter(email=test_email).first()
    student_persisted = bool(created_student and created_student.student_profile and created_student.student_profile.student_id == 'AIT-VERIFY-99')
    print(f"   -> Persisted in MySQL proofvoice_db? {student_persisted}")

    # 5. Student Login
    login_payload = {
        'email': test_email,
        'password': 'StrongPassword123!'
    }
    res = client.post('/api/v1/auth/login/', login_payload, format='json')
    status_ok = res.status_code == 200 and 'token' in res.data
    student_token = res.data.get('token') if status_ok else None
    results.append(('POST', '/api/v1/auth/login/', 'Public', 200, res.status_code, status_ok, 'Reads MySQL'))
    print(f"4. POST /api/v1/auth/login/ (Student) -> {res.status_code} (Token Generated: {bool(student_token)})")

    # 6. Authenticated User Profile (Me)
    client.credentials(HTTP_AUTHORIZATION='Token ' + student_token)
    res = client.get('/api/v1/auth/me/')
    status_ok = res.status_code == 200 and res.data.get('email') == test_email
    results.append(('GET', '/api/v1/auth/me/', 'Student Token', 200, res.status_code, status_ok, 'Reads MySQL'))
    print(f"5. GET /api/v1/auth/me/ -> {res.status_code} (Email: {res.data.get('email')})")

    # 7. Student Complaint Creation
    complaint_payload = {
        'title': 'Audit Test: Network Switch Power Interruption',
        'original_description': 'The network switch on 3rd floor Computer Lab trips intermittently during afternoon practicals.',
        'final_submitted_application': 'Formal Grievance Application\nTo: The Dean\nSubject: Network Switch\nDetails: Power tripping...',
        'category': 'IT & Network Issues',
        'priority': 'HIGH',
        'source_type': 'TEXT',
        'full_issue_location': 'Academic Block B, 3rd Floor, Lab 304',
        'submit_now': True
    }
    res = client.post('/api/v1/complaints/', complaint_payload, format='json')
    status_ok = res.status_code == 201 and 'complaint' in res.data
    complaint_data = res.data.get('complaint', {}) if status_ok else {}
    test_complaint_id = complaint_data.get('complaint_id')
    results.append(('POST', '/api/v1/complaints/', 'Student Token', 201, res.status_code, status_ok, 'Writes MySQL'))
    print(f"6. POST /api/v1/complaints/ -> {res.status_code} (Generated ID: {test_complaint_id})")

    # Verify complaint persisted in MySQL
    db_complaint = Complaint.objects.filter(complaint_id=test_complaint_id).first()
    complaint_persisted = bool(db_complaint and db_complaint.title == complaint_payload['title'])
    print(f"   -> Complaint persisted in MySQL proofvoice_db? {complaint_persisted}")

    # 8. Student Complaint Listing (Self only)
    res = client.get('/api/v1/complaints/')
    status_ok = res.status_code == 200
    complaint_ids = [c['complaint_id'] for c in res.data] if status_ok else []
    results.append(('GET', '/api/v1/complaints/', 'Student Token', 200, res.status_code, status_ok, 'Reads MySQL'))
    print(f"7. GET /api/v1/complaints/ -> {res.status_code} (Student sees {len(complaint_ids)} complaints: {complaint_ids})")

    # 9. Student Complaint Details
    res = client.get(f'/api/v1/complaints/{test_complaint_id}/')
    status_ok = res.status_code == 200 and res.data.get('complaint_id') == test_complaint_id
    results.append(('GET', f'/api/v1/complaints/{test_complaint_id}/', 'Student Token', 200, res.status_code, status_ok, 'Reads MySQL'))
    print(f"8. GET /api/v1/complaints/{test_complaint_id}/ -> {res.status_code}")

    # 10. Student Dashboard
    res = client.get('/api/v1/dashboard/student/')
    status_ok = res.status_code == 200 and 'metrics' in res.data and 'total_complaints' in res.data['metrics']
    results.append(('GET', '/api/v1/dashboard/student/', 'Student Token', 200, res.status_code, status_ok, 'Reads MySQL'))
    print(f"9. GET /api/v1/dashboard/student/ -> {res.status_code} (Total: {res.data.get('metrics', {}).get('total_complaints')})")

    # 11. Student Notifications
    res = client.get('/api/v1/notifications/')
    status_ok = res.status_code == 200
    results.append(('GET', '/api/v1/notifications/', 'Student Token', 200, res.status_code, status_ok, 'Reads MySQL'))
    print(f"10. GET /api/v1/notifications/ -> {res.status_code} (Count: {len(res.data) if isinstance(res.data, list) else 0})")

    # 12. Admin Login (Apex Admin)
    client.credentials()  # Clear student auth
    test_admin_pwd = os.getenv('TEST_ADMIN_PASSWORD', 'TestAdminPassword#2026')
    admin_login_res = client.post('/api/v1/auth/login/', {'email': 'admin@apex.edu', 'password': test_admin_pwd}, format='json')
    admin_status_ok = admin_login_res.status_code == 200 and 'token' in admin_login_res.data
    admin_token = admin_login_res.data.get('token') if admin_status_ok else None
    results.append(('POST', '/api/v1/auth/login/ (Admin)', 'Public', 200, admin_login_res.status_code, admin_status_ok, 'Reads MySQL'))
    print(f"11. POST /api/v1/auth/login/ (Apex Admin) -> {admin_login_res.status_code} (Token: {bool(admin_token)})")

    # 13. Admin Complaints Desk
    client.credentials(HTTP_AUTHORIZATION='Token ' + admin_token)
    res = client.get('/api/v1/admin/complaints/')
    status_ok = res.status_code == 200
    admin_complaint_ids = [c['complaint_id'] for c in res.data] if status_ok else []
    results.append(('GET', '/api/v1/admin/complaints/', 'Admin Token', 200, res.status_code, status_ok, 'Reads MySQL'))
    print(f"12. GET /api/v1/admin/complaints/ -> {res.status_code} (Admin sees {len(admin_complaint_ids)} complaints: {admin_complaint_ids})")

    # 14. Admin Status Update
    status_update_payload = {
        'status': 'IN_PROGRESS',
        'public_remark': 'Technician dispatched to Academic Block B, Lab 304 to test network switch power supply.',
        'internal_note': 'Warranty service ticket #NET-902 logged with vendor.'
    }
    res = client.post(f'/api/v1/admin/complaints/{test_complaint_id}/status/', status_update_payload, format='json')
    status_ok = res.status_code == 200 and res.data.get('complaint', {}).get('status') == 'IN_PROGRESS'
    results.append(('POST', f'/api/v1/admin/complaints/{test_complaint_id}/status/', 'Admin Token', 200, res.status_code, status_ok, 'Writes MySQL'))
    print(f"13. POST /api/v1/admin/complaints/{test_complaint_id}/status/ -> {res.status_code}")

    # Confirm status persisted in MySQL
    db_complaint.refresh_from_db()
    status_persisted = db_complaint.status == 'IN_PROGRESS'
    history_count = db_complaint.status_history.count()
    print(f"   -> Status IN_PROGRESS in MySQL? {status_persisted} (History entries: {history_count})")

    # 15. Admin Dashboard
    res = client.get('/api/v1/dashboard/admin/')
    status_ok = res.status_code == 200 and 'metrics' in res.data and 'total_complaints' in res.data['metrics']
    results.append(('GET', '/api/v1/dashboard/admin/', 'Admin Token', 200, res.status_code, status_ok, 'Reads MySQL'))
    print(f"14. GET /api/v1/dashboard/admin/ -> {res.status_code} (Total: {res.data.get('metrics', {}).get('total_complaints')})")

    # 16. Institution Analytics
    res = client.get('/api/v1/analytics/institution/')
    status_ok = res.status_code == 200
    results.append(('GET', '/api/v1/analytics/institution/', 'Admin Token', 200, res.status_code, status_ok, 'Reads MySQL'))
    print(f"15. GET /api/v1/analytics/institution/ -> {res.status_code}")

    # 17. Multi-Tenant Isolation Test (Horizon Admin cannot see Apex complaints)
    client.credentials()
    horizon_login = client.post('/api/v1/auth/login/', {'email': 'admin@horizon.edu', 'password': test_admin_pwd}, format='json')
    if horizon_login.status_code == 200 and 'token' in horizon_login.data:
        client.credentials(HTTP_AUTHORIZATION='Token ' + horizon_login.data['token'])
        # Try to access Apex complaint directly
        cross_res = client.get(f'/api/v1/complaints/{test_complaint_id}/')
        is_isolated = cross_res.status_code == 403
        results.append(('GET', f'/api/v1/complaints/{test_complaint_id}/ (Cross-Tenant)', 'Horizon Admin Token', 403, cross_res.status_code, is_isolated, 'Enforces MySQL Isolation'))
        print(f"16. MULTI-TENANT CHECK: Horizon Admin access to Apex Complaint -> {cross_res.status_code} (Blocked: {is_isolated})")

    # 18. Gnani AI Status Endpoint
    client.credentials()
    res = client.get('/api/v1/ai/status/')
    status_ok = res.status_code == 200 and 'gnani_ai_configured' in res.data
    results.append(('GET', '/api/v1/ai/status/', 'Public', 200, res.status_code, status_ok, 'Reads Config'))
    print(f"17. GET /api/v1/ai/status/ -> {res.status_code} (Configured: {res.data.get('gnani_ai_configured')})")

    # 19. Clean up test records
    print("\nCleaning up test records from MySQL...")
    db_complaint.status_history.all().delete()
    db_complaint.delete()
    if created_student:
        created_student.notifications.all().delete()
        if hasattr(created_student, 'student_profile'):
            created_student.student_profile.delete()
        created_student.delete()
    print("Test records cleaned up successfully.")

    print("\n" + "=" * 60)
    print("SUMMARY OF ENDPOINT VERIFICATION RESULTS")
    print("=" * 60)
    all_passed = True
    for method, path, auth, exp, act, ok, db_op in results:
        status_str = "PASS" if ok else "FAIL"
        if not ok:
            all_passed = False
        print(f"[{status_str}] {method:4} {path:45} | Auth: {auth:20} | Status: {act}/{exp} | {db_op}")

    print("=" * 60)
    print(f"OVERALL RESULT: {'ALL ENDPOINTS VERIFIED & WORKING' if all_passed else 'SOME ENDPOINTS FAILED'}")
    print("=" * 60)
    return all_passed

if __name__ == '__main__':
    run_verification()
