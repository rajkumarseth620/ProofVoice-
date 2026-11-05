from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import User, AdministratorProfile
from apps.institutions.models import Institution, InstitutionRegistrationRequest, AdminAccessRequest
from apps.notifications.models import Notification

class InstitutionalRegistrationAndSuperAdminTests(APITestCase):

    def setUp(self):
        # Create Super Admin account
        self.superadmin = User.objects.create_user(
            email='superadmin@proofvoice.platform',
            password='Admin@ProofVoice2026',
            full_name='ProofVoice Super Admin',
            role=User.Role.PLATFORM_SUPERADMIN,
            is_staff=True,
            is_superuser=True,
            is_verified=True
        )

        # Create verified institution (Apex Institute of Technology)
        self.institution = Institution.objects.create(
            name='Apex Institute of Technology',
            code='AIT',
            institution_type=Institution.InstitutionType.COLLEGE,
            official_email='info@apextech.edu',
            official_address='Station Road, Jamshedpur',
            city='Jamshedpur',
            state='Jharkhand',
            verification_status=Institution.VerificationStatus.VERIFIED,
            is_active=True
        )

    def test_superadmin_can_login_from_any_tab(self):
        """Platform Super Admin must be able to log in from any portal tab without being blocked."""
        url = reverse('auth-login')
        
        # Test with 'student' tab active
        res_student_tab = self.client.post(url, {
            'email': 'superadmin@proofvoice.platform',
            'password': 'Admin@ProofVoice2026',
            'role': 'student'
        })
        self.assertEqual(res_student_tab.status_code, status.HTTP_200_OK)
        self.assertEqual(res_student_tab.data['role'], User.Role.PLATFORM_SUPERADMIN)

        # Test with 'admin' tab active
        res_admin_tab = self.client.post(url, {
            'email': 'superadmin@proofvoice.platform',
            'password': 'Admin@ProofVoice2026',
            'role': 'admin'
        })
        self.assertEqual(res_admin_tab.status_code, status.HTTP_200_OK)
        self.assertEqual(res_admin_tab.data['role'], User.Role.PLATFORM_SUPERADMIN)

    def test_path1_request_admin_access_validation_and_submission(self):
        """Path 1: Request Access to Existing Institution."""
        url = reverse('register-admin')

        # 1. Missing password should return 400
        fail_res = self.client.post(url, {
            'email': 'prof.verma@apextech.edu',
            'full_name': 'Prof. R. K. Verma',
            'institution_id': str(self.institution.id),
            'designation': 'HOD Physics',
            'department_name': 'Physics'
        })
        self.assertEqual(fail_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', fail_res.data)

        # 2. Valid submission with password
        success_res = self.client.post(url, {
            'email': 'prof.verma@apextech.edu',
            'password': 'VermaPhysics@2026',
            'full_name': 'Prof. R. K. Verma',
            'institution_id': str(self.institution.id),
            'designation': 'HOD Physics',
            'department_name': 'Physics'
        })
        self.assertEqual(success_res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(success_res.data['requires_approval'])

        # User is created but unverified until Super Admin approval
        user = User.objects.get(email='prof.verma@apextech.edu')
        self.assertFalse(user.is_verified)
        self.assertEqual(user.role, User.Role.INSTITUTION_ADMIN)

        # Admin access request exists in PENDING state
        access_req = AdminAccessRequest.objects.get(user=user)
        self.assertEqual(access_req.status, AdminAccessRequest.Status.PENDING)

    def test_path2_register_new_institution_and_login_after_approval(self):
        """Path 2: Register New Institution, Super Admin approves, and admin logs in."""
        reg_url = reverse('institution-reg-requests')

        # 1. Submit New Institution Registration Request
        reg_data = {
            'institution_name': 'National Institute of Technology Jamshedpur',
            'institution_type': 'COLLEGE',
            'official_email': 'dean.admin@nitjsr.ac.in',
            'official_address': 'Adityapur, Jamshedpur, Jharkhand 831014',
            'state': 'Jharkhand',
            'city': 'Jamshedpur',
            'website': 'https://nitjsr.ac.in',
            'contact_person_name': 'Dr P R Mahto',
            'applicant_designation': 'Dean of Campus',
            'contact_number': '+91 9876543210',
            'additional_information': 'Approval requested for campus grievance redressal on ProofVoice.',
            'admin_password': 'NitDeanPassword@2026'
        }

        res = self.client.post(reg_url, reg_data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        req_id = res.data['request_id']
        self.assertTrue(req_id.startswith('PV-INS-2026-'))

        # Request record exists
        inst_req = InstitutionRegistrationRequest.objects.get(request_id=req_id)
        self.assertEqual(inst_req.status, InstitutionRegistrationRequest.Status.PENDING)
        self.assertIsNotNone(inst_req.applicant_user)
        self.assertEqual(inst_req.applicant_user.email, 'dean.admin@nitjsr.ac.in')
        self.assertFalse(inst_req.applicant_user.is_verified)

        # Internal notification for Super Admins was dispatched
        super_notifs = Notification.objects.filter(
            recipient=self.superadmin,
            notification_type=Notification.NotificationType.INSTITUTION_REQUEST
        )
        self.assertTrue(super_notifs.exists())

        # 2. Login BEFORE Super Admin approval must inform user that verification is pending
        login_url = reverse('auth-login')
        unapproved_login = self.client.post(login_url, {
            'email': 'dean.admin@nitjsr.ac.in',
            'password': 'NitDeanPassword@2026',
            'role': 'admin'
        })
        self.assertEqual(unapproved_login.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('awaiting', str(unapproved_login.data).lower())

        # 3. Super Admin logs in and approves the request
        self.client.force_authenticate(user=self.superadmin)
        approve_url = reverse('institution-reg-approve', kwargs={'pk': inst_req.pk})
        approve_res = self.client.post(approve_url, {
            'action': 'approve',
            'remarks': 'Accreditation verified. Approved for full campus access.'
        })
        self.assertEqual(approve_res.status_code, status.HTTP_200_OK)

        # Verify institution is created and active
        new_inst = Institution.objects.get(name='National Institute of Technology Jamshedpur')
        self.assertEqual(new_inst.verification_status, Institution.VerificationStatus.VERIFIED)
        self.assertTrue(new_inst.is_active)
        from apps.complaints.models import ComplaintCategory
        self.assertTrue(new_inst.departments.exists())
        self.assertTrue(ComplaintCategory.objects.filter(institution=new_inst).exists())

        # Verify applicant user is now verified
        inst_req.applicant_user.refresh_from_db()
        self.assertTrue(inst_req.applicant_user.is_verified)
        self.assertTrue(inst_req.applicant_user.is_active)

        # 4. Newly approved administrator logs in with the EXACT password they chose
        self.client.force_authenticate(user=None)
        approved_login = self.client.post(login_url, {
            'email': 'dean.admin@nitjsr.ac.in',
            'password': 'NitDeanPassword@2026',
            'role': 'admin'
        })
        self.assertEqual(approved_login.status_code, status.HTTP_200_OK)
        self.assertEqual(approved_login.data['role'], User.Role.INSTITUTION_ADMIN)
        self.assertEqual(approved_login.data['institution']['name'], 'National Institute of Technology Jamshedpur')
        self.assertTrue(approved_login.data['is_approved'])
        self.assertIsNotNone(approved_login.data['token'])
