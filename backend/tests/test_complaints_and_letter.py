from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User, StudentProfile, AdministratorProfile
from apps.institutions.models import (
    Institution,
    InstitutionDepartment,
    ComplaintCategory,
    ComplaintRecipientConfiguration
)
from apps.complaints.models import Complaint, ComplaintStatusHistory
from apps.complaints.services import FormalApplicationGenerator

class ComplaintWorkflowAndLetterTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.institution = Institution.objects.create(
            code='apex-tech',
            name='Apex Institute of Technology',
            official_email='info@apex.edu',
            official_address='Knowledge Park III, Greater Noida',
            verification_status=Institution.VerificationStatus.VERIFIED
        )

        self.department = InstitutionDepartment.objects.create(
            institution=self.institution,
            name='Hostel Administration',
            code='HST'
        )

        self.category = ComplaintCategory.objects.create(
            institution=self.institution,
            name='Hostel & Accommodation',
            default_department=self.department
        )

        # Default recipient: The Dean
        ComplaintRecipientConfiguration.objects.create(
            institution=self.institution,
            category=None,
            recipient_designation='The Dean',
            recipient_name='Prof. R. K. Mukherjee'
        )

        # Category-specific recipient: The Chief Warden
        ComplaintRecipientConfiguration.objects.create(
            institution=self.institution,
            category=self.category,
            recipient_designation='The Chief Warden',
            recipient_name='Dr. S. K. Gupta'
        )

        # Student
        self.student = User.objects.create_user(
            email='priya@apex.edu',
            password='Password123',
            full_name='Priya Sharma',
            role=User.Role.STUDENT,
            is_verified=True
        )
        StudentProfile.objects.create(
            user=self.student,
            institution=self.institution,
            student_id='AJU/22/0451',
            department='Computer Science & Engineering',
            course='B.Tech CSE',
            semester='6th Semester',
            phone='+91 9876543210',
            is_profile_complete=True
        )

        # Admin
        self.admin = User.objects.create_user(
            email='dean@apex.edu',
            password='AdminPassword123',
            full_name='Dr. Arvind Sharma',
            role=User.Role.INSTITUTION_ADMIN,
            is_verified=True
        )
        AdministratorProfile.objects.create(
            user=self.admin,
            institution=self.institution,
            approval_status=AdministratorProfile.ApprovalStatus.APPROVED
        )

    def test_unique_complaint_id_generation(self):
        """Verifies server generates unique IDs matching PV-YYYY-XXXX format."""
        cid = Complaint.generate_unique_complaint_id()
        self.assertTrue(cid.startswith('PV-'))
        parts = cid.split('-')
        self.assertEqual(len(parts), 3)

    def test_formal_application_generation_with_recipient(self):
        """Verifies formal application generation interpolates verified profile and recipient."""
        # 1. Test with specific category (recipient: The Chief Warden)
        result = FormalApplicationGenerator.generate_letter(
            student=self.student,
            institution=self.institution,
            title='Ceiling Fan Malfunction in Room 204',
            description='The ceiling fan bearing has failed and makes high-pitched noise.',
            category=self.category,
            location_details='Girls Hostel 1, Room 204'
        )
        text = result['application_text']
        self.assertIn('To,\nThe Chief Warden', text)
        self.assertIn('Dr. S. K. Gupta', text)
        self.assertIn('Priya Sharma', text)
        self.assertIn('AJU/22/0451', text)
        self.assertIn('Computer Science & Engineering', text)
        self.assertIn('6th Semester', text)
        self.assertIn('Ceiling Fan Malfunction in Room 204', text)
        self.assertIn('Yours faithfully', text)

        # 2. Test without category (defaults to The Dean)
        result_default = FormalApplicationGenerator.generate_letter(
            student=self.student,
            institution=self.institution,
            title='Campus Cafeteria Overpricing',
            description='Cafeteria vendor is charging above MRP.',
            category=None
        )
        self.assertIn('To,\nThe Dean', result_default['application_text'])
        self.assertIn('Prof. R. K. Mukherjee', result_default['application_text'])

    def test_complaint_creation_draft_and_submission(self):
        """Verifies full lifecycle: Draft -> Preview Letter -> Review -> Submit -> Resolve."""
        self.client.force_authenticate(user=self.student)

        # Step 1: Create draft
        create_payload = {
            'title': 'Leaking Washroom Tap in Academic Block',
            'original_description': 'Water leaking continuously on the 1st floor.',
            'category_id': self.category.id,
            'campus': 'Main Campus',
            'building': 'Block A',
            'floor': '1st Floor',
            'room_number': '102',
            'submit_now': False
        }
        res_create = self.client.post('/api/v1/complaints/', create_payload, format='json')
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        complaint_data = res_create.data['complaint']
        complaint_id = complaint_data['complaint_id']
        self.assertEqual(complaint_data['status'], 'DRAFT')

        # Step 2: Generate application preview
        res_preview = self.client.post(f'/api/v1/complaints/{complaint_id}/generate-application/')
        self.assertEqual(res_preview.status_code, status.HTTP_200_OK)
        self.assertIn('application_text', res_preview.data)
        generated_letter = res_preview.data['application_text']

        # Step 3: Explicit student submission after review
        submit_payload = {
            'final_application': generated_letter + "\n\n[P.S. Added urgent note during student review]"
        }
        res_submit = self.client.post(f'/api/v1/complaints/{complaint_id}/submit/', submit_payload, format='json')
        self.assertEqual(res_submit.status_code, status.HTTP_200_OK)
        self.assertEqual(res_submit.data['complaint']['status'], 'SUBMITTED')
        self.assertIn('[P.S. Added urgent note during student review]', res_submit.data['complaint']['final_submitted_application'])

        # Step 4: Administrator resolves complaint
        self.client.force_authenticate(user=self.admin)
        res_resolve = self.client.post(
            f'/api/v1/admin/complaints/{complaint_id}/resolution/',
            {'resolution_details': 'Plumbing contractor replaced ceramic washer and shutoff valve.'},
            format='json'
        )
        self.assertEqual(res_resolve.status_code, status.HTTP_200_OK)
        self.assertEqual(res_resolve.data['complaint']['status'], 'RESOLVED')
        self.assertIn('ceramic washer', res_resolve.data['complaint']['resolution_details'])
