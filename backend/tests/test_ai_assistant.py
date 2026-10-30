from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User, StudentProfile
from apps.institutions.models import Institution
from apps.integrations.ai_assistant import AiAssistantService


class AiAssistantTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.institution = Institution.objects.create(
            name="Apex Institute of Technology",
            code="AIT-TEST",
            official_address="Test Address, City"
        )
        self.student = User.objects.create_user(
            email="student_ai@apex.edu",
            password="StrongPassword123!",
            role=User.Role.STUDENT,
            full_name="Laxmi Kumari"
        )
        StudentProfile.objects.create(
            user=self.student,
            institution=self.institution,
            student_id="AIT/22/0102",
            department="Computer Science"
        )

    def test_categorization_and_department_routing(self):
        # Hostel issue
        res_hostel = AiAssistantService.categorize_and_route("The water cooler in the hostel 2nd floor is broken.")
        self.assertEqual(res_hostel['category'], 'HOSTEL')
        self.assertEqual(res_hostel['department'], 'Hostel Administration')

        # IT issue
        res_it = AiAssistantService.categorize_and_route("The campus wifi keeps disconnecting in the computer lab.")
        self.assertEqual(res_it['category'], 'IT_SERVICES')
        self.assertEqual(res_it['department'], 'Information Technology Support')

        # Urgent security / fire issue
        res_urgent = AiAssistantService.categorize_and_route("Electric sparking and short circuit in lab switchboard!")
        self.assertEqual(res_urgent['priority'], 'URGENT')

    def test_title_synthesis(self):
        title = AiAssistantService.generate_title("Regarding malfunctioning ceiling projector in computer lab 305.")
        self.assertIn("Projector", title)

    def test_grammar_refinement(self):
        raw = "plz fix the wifi asap. u need to check the router."
        refined = AiAssistantService.refine_grammar(raw)
        self.assertIn("Please", refined)
        self.assertIn("Wi-Fi", refined)
        self.assertTrue("You" in refined or "you" in refined)

    def test_ai_process_endpoint(self):
        self.client.force_authenticate(user=self.student)
        payload = {
            "text": "The water cooler in hostel B block is leaking and stopped cooling since yesterday. Plz repair asap."
        }
        resp = self.client.post('/api/v1/ai/process/', payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['success'])
        data = resp.data['data']
        self.assertEqual(data['category'], 'HOSTEL')
        self.assertEqual(data['suggested_department'], 'Hostel Administration')
        self.assertTrue(len(data['title']) > 0)
        self.assertTrue(len(data['summary']) > 0)
        self.assertIn("Please", data['refined_description'])

    def test_ai_summarize_and_refine_endpoints(self):
        self.client.force_authenticate(user=self.student)

        # Summarize
        sum_resp = self.client.post('/api/v1/ai/summarize/', {"text": "Long complaint text describing multiple facility failures across campus."}, format='json')
        self.assertEqual(sum_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(sum_resp.data['success'])

        # Refine
        ref_resp = self.client.post('/api/v1/ai/refine/', {"text": "plz repair the washroom tap u must see this."}, format='json')
        self.assertEqual(ref_resp.status_code, status.HTTP_200_OK)
        self.assertIn("Please", ref_resp.data['refined_text'])
