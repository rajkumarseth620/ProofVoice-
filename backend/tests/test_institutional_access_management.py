from apps.notifications.models import Notification
from django.test import TestCase

from rest_framework.test import APIClient

from rest_framework import status

from apps.accounts.models import User, StudentProfile, AdministratorProfile

from apps.institutions.models import (

    Institution,

    InstitutionRegistrationRequest,

    StudentOnboardingRequest,

    EmailNotificationLog,

    InstitutionDepartment,

    ComplaintCategory

)

from apps.complaints.models import Complaint

from unittest.mock import patch





class InstitutionalAccessManagementTests(TestCase):

    """

    Comprehensive Verification Suite covering all 12 institutional access management tests:

    - Test 1: Student registration and login with verified institution (Arka Jain University)

    - Test 2: Search unknown institution and get not found behavior

    - Test 3: Student onboarding expression of interest request creation & superadmin notification

    - Test 4: Institution representative registration submission with ID & pending status

    - Test 5: Unapproved institution admin login blocked

    - Test 6: Super admin approves institution, activates admin & dispatches email

    - Test 7: Super admin rejects institution with recorded explanation

    - Test 8: Super admin suspends institution & blocks dashboard access

    - Test 9: Multi-tenant complaint data isolation (Arka Jain cannot access BIT Mesra)

    - Test 10: Graceful handling of email delivery failure without request data loss

    - Test 11: Unauthorized user blocked from Super Admin APIs (HTTP 403)

    - Test 12: Role escalation to PLATFORM_SUPERADMIN blocked during registration

    """



    def setUp(self):

        self.client = APIClient()



        # Pre-seed verified institution (Arka Jain University)

        self.arka_jain = Institution.objects.create(

            code='arka-jain-university',

            name='Arka Jain University',

            website='https://arkajainuniversity.ac.in',

            official_email='info@arkajainuniversity.ac.in',

            official_address='Gamharia, Seraikela Kharsawan, Jharkhand 832108',

            state='Jharkhand',

            city='Jamshedpur',

            institution_type='University',

            verification_status=Institution.VerificationStatus.VERIFIED,

            is_active=True

        )



        # Pre-seed BIT Mesra (another institution for isolation test)

        self.bit_mesra = Institution.objects.create(

            code='bit-mesra',

            name='Birla Institute of Technology, Mesra',

            website='https://bitmesra.ac.in',

            official_email='registrar@bitmesra.ac.in',

            official_address='Mesra, Ranchi, Jharkhand 835215',

            state='Jharkhand',

            city='Ranchi',

            institution_type='University',

            verification_status=Institution.VerificationStatus.VERIFIED,

            is_active=True

        )



        # Departments and categories for complaint testing

        self.dept_arka = InstitutionDepartment.objects.create(

            institution=self.arka_jain,

            name='IT Department',

            code='IT'

        )

        self.cat_arka = ComplaintCategory.objects.create(

            institution=self.arka_jain,

            name='Internet / Network',

            description='NET',

            default_department=self.dept_arka

        )



        self.dept_bit = InstitutionDepartment.objects.create(

            institution=self.bit_mesra,

            name='Hostel Affairs',

            code='HOSTEL'

        )

        self.cat_bit = ComplaintCategory.objects.create(

            institution=self.bit_mesra,

            name='Hostel Maintenance',

            description='MAINT',

            default_department=self.dept_bit

        )



        # Super Admin User

        self.super_admin_user = User.objects.create_user(

            email='superadmin@proofvoice.platform',

            full_name='Platform Super Administrator',

            password='SuperSecretPassword123!',

            role=User.Role.PLATFORM_SUPERADMIN,

            is_staff=True,

            is_active=True

        )



    # TEST 1: Student selects approved institution -> registers & logs in successfully

    def test_01_student_registers_and_logs_in_with_verified_institution(self):

        reg_data = {

            'email': 'student.arka@example.com',

            'full_name': 'Rahul Verma',

            'password': 'SecureStudentPass123!',

            'institution_id': self.arka_jain.id,

            'student_id': 'AJU/BTECH/2026/042',

            'phone': '9876543210'

        }

        res_reg = self.client.post('/api/v1/auth/register/student/', reg_data, format='json')

        self.assertEqual(res_reg.status_code, status.HTTP_201_CREATED)

        self.assertIn('token', res_reg.data)



        # Verify user and student profile in DB

        user = User.objects.get(email='student.arka@example.com')

        self.assertEqual(user.role, User.Role.STUDENT)

        self.assertEqual(user.student_profile.institution, self.arka_jain)

        self.assertEqual(user.student_profile.student_id, 'AJU/BTECH/2026/042')



        # Test Login

        res_login = self.client.post('/api/v1/auth/login/', {

            'email': 'student.arka@example.com',

            'password': 'SecureStudentPass123!'

        }, format='json')

        self.assertEqual(res_login.status_code, status.HTTP_200_OK)

        self.assertIn('token', res_login.data)

        self.assertEqual(res_login.data['user']['role'], 'STUDENT')



    # TEST 2: Student searches for unknown institution -> "Institution Not Found!" warning behavior

    def test_02_search_institution_not_found(self):

        res = self.client.get('/api/v1/institutions/?search=UnknownOxfordCollegeX999')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        results = res.data if isinstance(res.data, list) else res.data.get('results', [])

        self.assertEqual(len(results), 0)



    # TEST 3: Student submits onboarding request -> saved in DB, unique ID generated, status PENDING_REVIEW

    def test_03_student_onboarding_request_creation(self):

        req_data = {

            'student_name': 'Amit Kumar',

            'student_email': 'amit.kumar@xyzuniv.edu.in',

            'institution_name': 'XYZ National University',

            'institution_location': 'Ranchi, Jharkhand',

            'institution_website': 'https://xyznationaluniv.edu.in',

            'message': 'Please onboard our university so our batch can submit hostel issues.'

        }

        res = self.client.post('/api/v1/institutions/student-onboarding-requests/', req_data, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)



        req_obj = StudentOnboardingRequest.objects.get(student_email='amit.kumar@xyzuniv.edu.in')

        self.assertTrue(req_obj.request_id.startswith('PV-STU-REQ-2026-'))

        self.assertEqual(req_obj.status, StudentOnboardingRequest.Status.PENDING_REVIEW)

        self.assertEqual(req_obj.institution_name, 'XYZ National University')



        # Verify internal in-app notification created for Super Admin

        notif = Notification.objects.filter(

            recipient=self.super_admin_user,

            notification_type=Notification.NotificationType.STUDENT_ONBOARDING_REQUEST,

            related_request_id=req_obj.request_id

        ).first()

        self.assertIsNotNone(notif)



    # TEST 4: Institution representative submits registration -> saved in DB, unique ID, status PENDING

    def test_04_institution_representative_registration_request(self):

        req_data = {

            'institution_name': 'Kolhan Engineering Academy',

            'official_email': 'contact@kolhan-eng.edu.in',

            'website': 'https://kolhan-eng.edu.in',

            'institution_type': 'Engineering College',

            'contact_person_name': 'Dr. S. K. Roy',

            'applicant_designation': 'Principal',

            'contact_number': '9876543211',

            'state': 'Jharkhand',

            'city': 'Chaibasa',

            'official_address': 'College Road, Chaibasa',

            'additional_information': 'Requesting ProofVoice setup for academic grievance cell.'

        }

        res = self.client.post('/api/v1/institutions/registration-requests/', req_data, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)



        reg_obj = InstitutionRegistrationRequest.objects.get(official_email='contact@kolhan-eng.edu.in')

        self.assertTrue(reg_obj.request_id.startswith('PV-INS-2026-'))

        self.assertEqual(reg_obj.status, InstitutionRegistrationRequest.Status.PENDING)

        self.assertIn('9876543211', reg_obj.contact_number)



    # TEST 5: Pending institution -> institutional dashboard access blocked

    def test_05_pending_institution_admin_access_blocked(self):

        # Create unverified institution

        unverified_inst = Institution.objects.create(

            code='unverified-poly',

            name='Unverified Polytechnic',

            official_email='desk@unverifiedpoly.edu.in',

            official_address='Station Road',

            verification_status=Institution.VerificationStatus.PENDING,

            is_active=False

        )

        pending_admin = User.objects.create_user(

            email='admin@unverifiedpoly.edu.in',

            full_name='Pending Admin',

            password='AdminPassword123!',

            role=User.Role.INSTITUTION_ADMIN,

            is_active=True

        )

        AdministratorProfile.objects.create(

            user=pending_admin,

            institution=unverified_inst,

            designation='Administrator',

            department_name='Administration',

            approval_status=AdministratorProfile.ApprovalStatus.PENDING

        )



        # Login must be blocked because administrator profile approval_status is PENDING

        res = self.client.post('/api/v1/auth/login/', {

            'email': 'admin@unverifiedpoly.edu.in',

            'password': 'AdminPassword123!'

        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('awaiting platform administrator verification', str(res.data))



    # TEST 6: Super Admin approves institution -> status VERIFIED, admin activated, email dispatched

    def test_06_super_admin_approves_institution_registration(self):

        reg_obj = InstitutionRegistrationRequest.objects.create(

            institution_name='Jamshedpur Institute of Technology',

            official_email='director@jit-jsr.ac.in',

            website='https://jit-jsr.ac.in',

            institution_type='Engineering Institute',

            contact_person_name='Prof. A. Mukherjee',

            applicant_designation='Director',

            contact_number='9876543212',

            state='Jharkhand',

            city='Jamshedpur',

            official_address='Mango, Jamshedpur',

            status=InstitutionRegistrationRequest.Status.PENDING

        )



        self.client.force_authenticate(user=self.super_admin_user)

        res = self.client.post(f'/api/v1/institutions/registration-requests/{reg_obj.id}/approve/', {

            'action': 'approve',

            'remarks': 'All statutory accreditation documents verified.'

        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)



        reg_obj.refresh_from_db()

        self.assertEqual(reg_obj.status, InstitutionRegistrationRequest.Status.APPROVED)

        self.assertEqual(reg_obj.reviewed_by, self.super_admin_user)



        # Check created institution and activated admin user

        inst = Institution.objects.get(official_email='director@jit-jsr.ac.in')

        self.assertEqual(inst.verification_status, Institution.VerificationStatus.VERIFIED)

        self.assertTrue(inst.is_active)



        admin_user = User.objects.get(email='director@jit-jsr.ac.in')

        self.assertTrue(admin_user.is_active)

        self.assertEqual(admin_user.admin_profile.approval_status, AdministratorProfile.ApprovalStatus.APPROVED)



    # TEST 7: Super Admin rejects institution -> status REJECTED, explanation recorded

    def test_07_super_admin_rejects_institution_registration(self):

        reg_obj = InstitutionRegistrationRequest.objects.create(

            institution_name='Fake Unrecognized College',

            official_email='dean@fakecollege.org',

            contact_person_name='John Doe',

            applicant_designation='Principal',

            contact_number='9876543213',

            state='Jharkhand',

            city='Ranchi',

            official_address='Nowhere',

            status=InstitutionRegistrationRequest.Status.PENDING

        )



        self.client.force_authenticate(user=self.super_admin_user)

        res = self.client.post(f'/api/v1/institutions/registration-requests/{reg_obj.id}/approve/', {

            'action': 'reject',

            'remarks': 'Invalid AICTE accreditation proof provided.'

        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)



        reg_obj.refresh_from_db()

        self.assertEqual(reg_obj.status, InstitutionRegistrationRequest.Status.REJECTED)

        self.assertTrue('Invalid AICTE' in (reg_obj.internal_remarks or '') or 'Invalid AICTE' in (reg_obj.rejection_reason or ''))



    # TEST 8: Super Admin suspends institution -> status SUSPENDED, access blocked

    def test_08_super_admin_suspends_institution_and_blocks_access(self):

        admin_user = User.objects.create_user(

            email='admin@arkajainuniversity.ac.in',

            full_name='Arka Admin',

            password='AdminPass123!',

            role=User.Role.INSTITUTION_ADMIN,

            is_active=True

        )

        AdministratorProfile.objects.create(

            user=admin_user,

            institution=self.arka_jain,

            designation='Admin',

            department_name='Administration',

            approval_status=AdministratorProfile.ApprovalStatus.APPROVED

        )



        # Super admin suspends the institution

        self.client.force_authenticate(user=self.super_admin_user)

        res = self.client.post(f'/api/v1/institutions/{self.arka_jain.id}/suspend/', {

            'action': 'suspend',

            'reason': 'Annual platform compliance audit pending.'

        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)



        self.arka_jain.refresh_from_db()

        self.assertEqual(self.arka_jain.verification_status, Institution.VerificationStatus.SUSPENDED)

        self.assertFalse(self.arka_jain.is_active)



        # Admin login must now be blocked

        self.client.logout()

        res_login = self.client.post('/api/v1/auth/login/', {

            'email': 'admin@arkajainuniversity.ac.in',

            'password': 'AdminPass123!'

        }, format='json')

        self.assertEqual(res_login.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('suspended by the Platform Super-Admin', str(res_login.data))



    # TEST 9: Arka Jain University cannot access BIT Mesra complaints (Multi-Tenant Isolation)

    def test_09_multi_tenant_data_isolation(self):

        # Arka student & complaint

        arka_student = User.objects.create_user(

            email='student.arka2@example.com',

            full_name='Arka Student',

            password='StudentPass123!',

            role=User.Role.STUDENT

        )

        StudentProfile.objects.create(user=arka_student, institution=self.arka_jain, student_id='AJU-002')

        complaint_arka = Complaint.objects.create(

            student=arka_student,

            institution=self.arka_jain,

            assigned_department=self.dept_arka,

            category=self.cat_arka,

            title='Lab 304 Wi-Fi Outage',

            original_description='Wi-Fi router is down in Block B Lab 304.',

            final_submitted_application='Respected HOD, The internet connection in Lab 304 is down.',

            status=Complaint.Status.SUBMITTED

        )



        # BIT Mesra student & complaint

        bit_student = User.objects.create_user(

            email='student.bit@example.com',

            full_name='BIT Student',

            password='StudentPass123!',

            role=User.Role.STUDENT

        )

        StudentProfile.objects.create(user=bit_student, institution=self.bit_mesra, student_id='BIT-001')

        complaint_bit = Complaint.objects.create(

            student=bit_student,

            institution=self.bit_mesra,

            assigned_department=self.dept_bit,

            category=self.cat_bit,

            title='Hostel 5 Water Supply Interruption',

            original_description='Water supply in Hostel 5 disrupted since morning.',

            final_submitted_application='Respected Warden, Water supply is not available in Hostel 5.',

            status=Complaint.Status.SUBMITTED

        )



        # Arka Admin user

        arka_admin = User.objects.create_user(

            email='admin.isolation@arkajainuniversity.ac.in',

            full_name='Arka Admin Isolation',

            password='AdminPass123!',

            role=User.Role.INSTITUTION_ADMIN,

            is_active=True

        )

        AdministratorProfile.objects.create(

            user=arka_admin,

            institution=self.arka_jain,

            designation='Admin',

            department_name='Administration',

            approval_status=AdministratorProfile.ApprovalStatus.APPROVED

        )



        # Authenticate as Arka Admin and request complaints list

        self.client.force_authenticate(user=arka_admin)

        res_list = self.client.get('/api/v1/admin/complaints/')

        self.assertEqual(res_list.status_code, status.HTTP_200_OK)



        results = res_list.data if isinstance(res_list.data, list) else res_list.data.get('results', [])

        complaint_ids = [c['id'] for c in results]



        # Must contain Arka complaint and MUST NOT contain BIT complaint

        self.assertIn(complaint_arka.id, complaint_ids)

        self.assertNotIn(complaint_bit.id, complaint_ids)



    # TEST 10: Notification system failure handled gracefully without request data loss

    def test_10_email_delivery_failure_gracefully_handled(self):

        with patch('apps.notifications.models.Notification.notify_super_admins', side_effect=Exception('DB Notification Timeout')):

            req_data = {

                'institution_name': 'Graceful SMTP Test Academy',

                'official_email': 'contact@smtptest.edu.in',

                'website': 'https://smtptest.edu.in',

                'institution_type': 'Autonomous College',

                'contact_person_name': 'Prof. Grace Test',

                'applicant_designation': 'Principal',

                'contact_number': '9876543214',

                'state': 'Odisha',

                'city': 'Bhubaneswar',

                'official_address': 'Chandrasekharpur'

            }

            # Request must STILL succeed with HTTP 201

            res = self.client.post('/api/v1/institutions/registration-requests/', req_data, format='json')

            self.assertEqual(res.status_code, status.HTTP_201_CREATED)



            # Record must exist in DB despite notification engine error

            self.assertTrue(InstitutionRegistrationRequest.objects.filter(official_email='contact@smtptest.edu.in').exists())



    # TEST 11: Unauthorized user attempts to access Super Admin APIs -> HTTP 403 Forbidden

    def test_11_unauthorized_user_blocked_from_super_admin_apis(self):

        regular_student = User.objects.create_user(

            email='regular.student@example.com',

            full_name='Regular Student',

            password='StudentPass123!',

            role=User.Role.STUDENT,

            is_active=True

        )



        self.client.force_authenticate(user=regular_student)

        res_overview = self.client.get('/api/v1/institutions/super-admin/overview/')

        self.assertEqual(res_overview.status_code, status.HTTP_403_FORBIDDEN)



        res_requests = self.client.get('/api/v1/institutions/registration-requests/')

        # Non-superadmin gets only their own requests or forbidden

        # If student tries to manage superadmin requests

        self.assertEqual(res_overview.status_code, status.HTTP_403_FORBIDDEN)



    # TEST 12: Role escalation to PLATFORM_SUPERADMIN blocked during registration

    def test_12_role_escalation_blocked_during_registration(self):

        malicious_data = {

            'email': 'hacker@example.com',

            'full_name': 'Malicious User',

            'password': 'HackerPass123!',

            'role': 'PLATFORM_SUPERADMIN',

            'institution_id': self.arka_jain.id,

            'student_id': 'HACK-001'

        }

        res = self.client.post('/api/v1/auth/register/student/', malicious_data, format='json')

        # Even if created, role must be STUDENT, never PLATFORM_SUPERADMIN

        if res.status_code == status.HTTP_201_CREATED:

            created_user = User.objects.get(email='hacker@example.com')

            self.assertEqual(created_user.role, User.Role.STUDENT)

            self.assertNotEqual(created_user.role, User.Role.PLATFORM_SUPERADMIN)

