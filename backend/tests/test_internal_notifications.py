from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from apps.accounts.models import User, StudentProfile, AdministratorProfile
from apps.institutions.models import Institution, InstitutionRegistrationRequest, StudentOnboardingRequest
from apps.notifications.models import Notification
from unittest.mock import patch


class InternalNotificationSystemTests(TestCase):
    """
    Automated Test Suite for ProofVoice Internal Notification System.
    Verifies all 9 scenarios:
    - TEST 1: Institution submits registration request -> Super Admin notification created.
    - TEST 2: Student requests onboarding -> Super Admin student onboarding notification created.
    - TEST 3: Super Admin retrieves notification with related request tracking ID.
    - TEST 4: Super Admin marks notification as read -> unread counter decreases.
    - TEST 5: Super Admin marks all notifications as read -> unread counter becomes zero.
    - TEST 6: Student tries to access Super Admin notifications -> tenant isolation / access denied.
    - TEST 7: Institution admin tries to access Super Admin notifications -> tenant isolation / access denied.
    - TEST 8: Polling endpoint returns newly arrived notifications with updated unread counter.
    - TEST 9: Notification creation error handled gracefully -> original registration request preserved.
    """

    def setUp(self):
        self.client = APIClient()

        # Platform Super Admin
        self.super_admin = User.objects.create_user(
            email='superadmin.test@proofvoice.platform',
            full_name='Platform Super Administrator',
            password='AdminPassword123!',
            role=User.Role.PLATFORM_SUPERADMIN,
            is_staff=True,
            is_active=True
        )

        # Pre-seed verified institution for testing
        self.institution = Institution.objects.create(
            code='test-univ',
            name='Test University',
            official_email='info@testuniv.edu.in',
            official_address='Station Road, Campus',
            state='Jharkhand',
            city='Ranchi',
            institution_type='University',
            verification_status=Institution.VerificationStatus.VERIFIED,
            is_active=True
        )

        # Institutional Admin user
        self.inst_admin = User.objects.create_user(
            email='admin@testuniv.edu.in',
            full_name='Campus Administrator',
            password='Password123!',
            role=User.Role.INSTITUTION_ADMIN,
            is_active=True
        )
        AdministratorProfile.objects.create(
            user=self.inst_admin,
            institution=self.institution,
            designation='Dean',
            department_name='Administration',
            approval_status=AdministratorProfile.ApprovalStatus.APPROVED
        )

        # Student user
        self.student = User.objects.create_user(
            email='student@testuniv.edu.in',
            full_name='Rahul Kumar',
            password='Password123!',
            role=User.Role.STUDENT,
            is_active=True
        )
        StudentProfile.objects.create(
            user=self.student,
            institution=self.institution,
            student_id='STU/2026/001'
        )

    # TEST 1: Institution submits a registration request -> Notification created for Super Admin
    def test_01_institution_registration_creates_superadmin_notification(self):
        req_data = {
            'institution_name': 'Ranchi Engineering Institute',
            'official_email': 'contact@ranchi-eng.edu.in',
            'website': 'https://ranchi-eng.edu.in',
            'institution_type': 'Engineering College',
            'contact_person_name': 'Dr. P. Sharma',
            'applicant_designation': 'Principal',
            'contact_number': '9876543210',
            'state': 'Jharkhand',
            'city': 'Ranchi',
            'official_address': 'Main Road, Ranchi'
        }
        res = self.client.post('/api/v1/institutions/registration-requests/', req_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        reg_obj = InstitutionRegistrationRequest.objects.get(official_email='contact@ranchi-eng.edu.in')

        # Verify Super Admin in-app notification exists
        notif = Notification.objects.filter(
            recipient=self.super_admin,
            notification_type=Notification.NotificationType.INSTITUTION_REQUEST,
            related_request_id=reg_obj.request_id
        ).first()

        self.assertIsNotNone(notif)
        self.assertEqual(notif.title, 'New Institutional Access Request')
        self.assertIn('Ranchi Engineering Institute', notif.message)
        self.assertFalse(notif.is_read)
        self.assertFalse(notif.is_archived)

    # TEST 2: Student requests onboarding for unknown institution -> Notification created
    def test_02_student_onboarding_request_creates_superadmin_notification(self):
        req_data = {
            'student_name': 'Anjali Singh',
            'student_email': 'anjali@dhanbadpoly.edu.in',
            'institution_name': 'Dhanbad Polytechnic',
            'institution_location': 'Dhanbad, Jharkhand',
            'institution_website': 'https://dhanbadpoly.edu.in',
            'message': 'Please onboard our polytechnic so we can report campus issues.'
        }
        res = self.client.post('/api/v1/institutions/student-onboarding-requests/', req_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        req_obj = StudentOnboardingRequest.objects.get(student_email='anjali@dhanbadpoly.edu.in')

        # Verify Super Admin in-app notification exists
        notif = Notification.objects.filter(
            recipient=self.super_admin,
            notification_type=Notification.NotificationType.STUDENT_ONBOARDING_REQUEST,
            related_request_id=req_obj.request_id
        ).first()

        self.assertIsNotNone(notif)
        self.assertEqual(notif.title, 'New Student Institution Request')
        self.assertIn('Dhanbad Polytechnic', notif.message)
        self.assertFalse(notif.is_read)

    # TEST 3: Super Admin opens the notification & retrieves related request ID
    def test_03_super_admin_retrieves_notification_with_related_request(self):
        notif = Notification.objects.create(
            recipient=self.super_admin,
            recipient_role=User.Role.PLATFORM_SUPERADMIN,
            notification_type=Notification.NotificationType.INSTITUTION_REQUEST,
            title='New Institutional Access Request',
            message='Jamshedpur Academy submitted registration.',
            related_request_id='PV-INS-2026-999',
            metadata={'institution_name': 'Jamshedpur Academy'}
        )

        self.client.force_authenticate(user=self.super_admin)
        res = self.client.get('/api/v1/notifications/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        notif_item = next((n for n in res.data['notifications'] if n['id'] == notif.id), None)
        self.assertIsNotNone(notif_item)
        self.assertEqual(notif_item['related_request_id'], 'PV-INS-2026-999')
        self.assertIn('super-admin.html', notif_item['action_url'])

    # TEST 4: Super Admin marks the notification as read -> unread counter decreases
    def test_04_mark_single_notification_read_decreases_unread_count(self):
        notif1 = Notification.objects.create(
            recipient=self.super_admin,
            recipient_role=User.Role.PLATFORM_SUPERADMIN,
            notification_type=Notification.NotificationType.INSTITUTION_REQUEST,
            title='Request 1',
            message='First request',
            is_read=False
        )
        notif2 = Notification.objects.create(
            recipient=self.super_admin,
            recipient_role=User.Role.PLATFORM_SUPERADMIN,
            notification_type=Notification.NotificationType.STUDENT_ONBOARDING_REQUEST,
            title='Request 2',
            message='Second request',
            is_read=False
        )

        self.client.force_authenticate(user=self.super_admin)
        res_initial = self.client.get('/api/v1/notifications/')
        self.assertEqual(res_initial.data['unread_count'], 2)

        # Mark notif1 as read
        res_mark = self.client.post(f'/api/v1/notifications/{notif1.id}/read/')
        self.assertEqual(res_mark.status_code, status.HTTP_200_OK)
        self.assertEqual(res_mark.data['unread_count'], 1)

        notif1.refresh_from_db()
        self.assertTrue(notif1.is_read)
        self.assertIsNotNone(notif1.read_at)

    # TEST 5: Super Admin marks all notifications as read -> unread counter becomes zero
    def test_05_mark_all_notifications_read(self):
        for i in range(3):
            Notification.objects.create(
                recipient=self.super_admin,
                recipient_role=User.Role.PLATFORM_SUPERADMIN,
                notification_type=Notification.NotificationType.INSTITUTION_REQUEST,
                title=f'Request Batch {i}',
                message=f'Message {i}',
                is_read=False
            )

        self.client.force_authenticate(user=self.super_admin)
        res_mark_all = self.client.post('/api/v1/notifications/read-all/')
        self.assertEqual(res_mark_all.status_code, status.HTTP_200_OK)
        self.assertEqual(res_mark_all.data['unread_count'], 0)

        # Verify all notifications in DB are marked read
        self.assertEqual(Notification.objects.filter(recipient=self.super_admin, is_read=False).count(), 0)

    # TEST 6: Student tries to access Super Admin notifications -> Access Denied / Scoped to self
    def test_06_student_cannot_access_super_admin_notifications(self):
        # Create Super Admin private notification
        notif_sa = Notification.objects.create(
            recipient=self.super_admin,
            recipient_role=User.Role.PLATFORM_SUPERADMIN,
            notification_type=Notification.NotificationType.INSTITUTION_REQUEST,
            title='Confidential Institutional Audit Request',
            message='Super admin only data',
            related_request_id='PV-INS-CONFIDENTIAL'
        )

        # Authenticate as regular student
        self.client.force_authenticate(user=self.student)
        res = self.client.get('/api/v1/notifications/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Student's result list must NOT contain the Super Admin's notification
        retrieved_ids = [n['id'] for n in res.data['notifications']]
        self.assertNotIn(notif_sa.id, retrieved_ids)

        # Attempt to mark Super Admin notification as read -> 404 (not found in student scope)
        res_mark = self.client.post(f'/api/v1/notifications/{notif_sa.id}/read/')
        self.assertEqual(res_mark.status_code, status.HTTP_404_NOT_FOUND)

    # TEST 7: Institutional administrator tries to access Super Admin notifications -> Denied / Scoped
    def test_07_institution_admin_cannot_access_super_admin_notifications(self):
        notif_sa = Notification.objects.create(
            recipient=self.super_admin,
            recipient_role=User.Role.PLATFORM_SUPERADMIN,
            notification_type=Notification.NotificationType.INSTITUTION_SUSPENDED,
            title='Super Admin Suspension Action',
            message='Confidential suspension order',
            related_request_id='PV-SUSPEND-001'
        )

        # Authenticate as institution admin
        self.client.force_authenticate(user=self.inst_admin)
        res = self.client.get('/api/v1/notifications/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        retrieved_ids = [n['id'] for n in res.data['notifications']]
        self.assertNotIn(notif_sa.id, retrieved_ids)

        # Direct delete or mark read must be 404
        res_delete = self.client.delete(f'/api/v1/notifications/{notif_sa.id}/')
        self.assertEqual(res_delete.status_code, status.HTTP_404_NOT_FOUND)

    # TEST 8: Periodic polling returns newly arrived notifications with updated unread counter
    def test_08_polling_returns_new_notifications_and_counter(self):
        self.client.force_authenticate(user=self.super_admin)

        # Poll 1: Empty state
        res1 = self.client.get('/api/v1/notifications/')
        self.assertEqual(res1.data['unread_count'], 0)

        # Event occurs in background: new notification created
        Notification.notify_super_admins(
            title="New Institutional Access Request",
            message="Bokaro Institute of Technology requested onboarding.",
            notification_type=Notification.NotificationType.INSTITUTION_REQUEST,
            related_request_id="PV-INS-2026-BOKARO"
        )

        # Poll 2: Super Admin client polls 15 seconds later
        res2 = self.client.get('/api/v1/notifications/')
        self.assertEqual(res2.data['unread_count'], 1)
        self.assertEqual(len(res2.data['notifications']), 1)
        self.assertEqual(res2.data['notifications'][0]['related_request_id'], 'PV-INS-2026-BOKARO')

    # TEST 9: Notification creation fails -> Original registration request preserved
    def test_09_notification_failure_preserves_registration_request(self):
        # Simulate an unexpected database error in Notification.notify_super_admins
        with patch('apps.notifications.models.Notification.notify_super_admins', side_effect=Exception('DB Connection Timeout on Notifications')):
            req_data = {
                'institution_name': 'Resilient Technical Institute',
                'official_email': 'contact@resilient-tech.edu.in',
                'website': 'https://resilient-tech.edu.in',
                'institution_type': 'Engineering College',
                'contact_person_name': 'Dr. Resilient',
                'applicant_designation': 'Principal',
                'contact_number': '9876543212',
                'state': 'Odisha',
                'city': 'Bhubaneswar',
                'official_address': 'Patia, Bhubaneswar'
            }
            # Request must STILL succeed with HTTP 201 Created
            res = self.client.post('/api/v1/institutions/registration-requests/', req_data, format='json')
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)

            # Record must safely exist in DB despite notification engine error
            saved_request = InstitutionRegistrationRequest.objects.filter(official_email='contact@resilient-tech.edu.in').first()
            self.assertIsNotNone(saved_request)
            self.assertTrue(saved_request.request_id.startswith('PV-INS-2026-'))
            self.assertEqual(saved_request.institution_name, 'Resilient Technical Institute')
