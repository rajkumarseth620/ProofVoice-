"""
Management command to seed initial platform demo data.
Creates institutions, departments, categories, recipient configs,
superadmin, institution admins, students, and sample complaints.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import User, StudentProfile, AdministratorProfile
from apps.institutions.models import (
    Institution,
    InstitutionDepartment,
    ComplaintCategory,
    ComplaintRecipientConfiguration
)
from apps.complaints.models import Complaint, ComplaintStatusHistory
from apps.complaints.services import FormalApplicationGenerator

class Command(BaseCommand):
    help = 'Seeds initial multi-institution demo data for ProofVoice'

    def handle(self, *args, **options):
        self.stdout.write("Starting ProofVoice seed data...")

        # 1. Platform Superadmin
        superadmin, _ = User.objects.get_or_create(
            email='superadmin@proofvoice.edu',
            defaults={
                'full_name': 'ProofVoice System Admin',
                'role': User.Role.PLATFORM_SUPERADMIN,
                'is_staff': True,
                'is_superuser': True,
                'is_verified': True
            }
        )
        superadmin.set_password('Admin@12345')
        superadmin.is_active = True
        superadmin.save()
        self.stdout.write(self.style.SUCCESS("Seeded Superadmin: superadmin@proofvoice.edu (Pass: Admin@12345)"))

        superadmin_alt, _ = User.objects.get_or_create(
            email='platform.admin@proofvoice.io',
            defaults={
                'full_name': 'Platform Root Admin',
                'role': User.Role.PLATFORM_SUPERADMIN,
                'is_staff': True,
                'is_superuser': True,
                'is_verified': True
            }
        )
        superadmin_alt.set_password('Admin@12345')
        superadmin_alt.is_active = True
        superadmin_alt.save()

        # 2. Institutions
        apex, _ = Institution.objects.get_or_create(
            code='apex-tech',
            defaults={
                'name': 'Apex Institute of Technology',
                'institution_type': Institution.InstitutionType.INSTITUTE,
                'official_email': 'contact@apextech.edu',
                'official_address': 'Sector 62, Institutional Area, Knowledge Park, Noida, Uttar Pradesh 201309',
                'country': 'India',
                'state': 'Uttar Pradesh',
                'city': 'Noida',
                'website': 'https://apextech.edu',
                'verification_status': Institution.VerificationStatus.VERIFIED,
                'is_active': True
            }
        )

        horizon, _ = Institution.objects.get_or_create(
            code='horizon-univ',
            defaults={
                'name': 'Horizon State University',
                'institution_type': Institution.InstitutionType.UNIVERSITY,
                'official_email': 'grievances@horizonuniv.ac.in',
                'official_address': 'University Campus, Ring Road, Bhopal, Madhya Pradesh 462001',
                'country': 'India',
                'state': 'Madhya Pradesh',
                'city': 'Bhopal',
                'website': 'https://horizonuniv.ac.in',
                'verification_status': Institution.VerificationStatus.VERIFIED,
                'is_active': True
            }
        )

        greenfield, _ = Institution.objects.get_or_create(
            code='greenfield-poly',
            defaults={
                'name': 'Greenfield Polytechnic',
                'institution_type': Institution.InstitutionType.POLYTECHNIC,
                'official_email': 'office@greenfieldpoly.edu.in',
                'official_address': 'NH-48, Industrial Corridor, Pune, Maharashtra 411019',
                'country': 'India',
                'state': 'Maharashtra',
                'city': 'Pune',
                'website': 'https://greenfieldpoly.edu.in',
                'verification_status': Institution.VerificationStatus.VERIFIED,
                'is_active': True
            }
        )

        self.stdout.write(self.style.SUCCESS("Created 3 Multi-Tenant Institutions: Apex Tech, Horizon Univ, Greenfield Poly"))

        # 3. Setup Apex Tech Departments & Categories
        apex_depts = {
            'Estate & Maintenance': InstitutionDepartment.objects.get_or_create(institution=apex, name='Estate & Maintenance', defaults={'code': 'EST', 'contact_email': 'estate@apextech.edu'})[0],
            'Hostel Administration': InstitutionDepartment.objects.get_or_create(institution=apex, name='Hostel Administration', defaults={'code': 'HST', 'contact_email': 'hostels@apextech.edu'})[0],
            'Academic Affairs': InstitutionDepartment.objects.get_or_create(institution=apex, name='Academic Affairs', defaults={'code': 'ACD', 'contact_email': 'academics@apextech.edu'})[0],
            'IT & Network Services': InstitutionDepartment.objects.get_or_create(institution=apex, name='IT & Network Services', defaults={'code': 'ITS', 'contact_email': 'itsupport@apextech.edu'})[0],
            'Dean of Student Welfare': InstitutionDepartment.objects.get_or_create(institution=apex, name='Dean of Student Welfare', defaults={'code': 'DSW', 'contact_email': 'dsw@apextech.edu'})[0],
        }

        apex_cats = {
            'Hostel & Accommodation': ComplaintCategory.objects.get_or_create(institution=apex, name='Hostel & Accommodation', defaults={'default_department': apex_depts['Hostel Administration']})[0],
            'Infrastructure & Maintenance': ComplaintCategory.objects.get_or_create(institution=apex, name='Infrastructure & Maintenance', defaults={'default_department': apex_depts['Estate & Maintenance']})[0],
            'Academic & Faculty': ComplaintCategory.objects.get_or_create(institution=apex, name='Academic & Faculty', defaults={'default_department': apex_depts['Academic Affairs']})[0],
            'Sanitation & Hygiene': ComplaintCategory.objects.get_or_create(institution=apex, name='Sanitation & Hygiene', defaults={'default_department': apex_depts['Estate & Maintenance']})[0],
            'IT & Network Issues': ComplaintCategory.objects.get_or_create(institution=apex, name='IT & Network Issues', defaults={'default_department': apex_depts['IT & Network Services']})[0],
        }

        # Recipient Config for Apex Tech
        ComplaintRecipientConfiguration.objects.get_or_create(
            institution=apex,
            category=None,
            defaults={
                'recipient_designation': 'The Dean',
                'recipient_name': 'Prof. R. K. Mukherjee',
                'recipient_address': f"Office of Student Affairs, Academic Block-A\n{apex.name}\n{apex.official_address}"
            }
        )
        ComplaintRecipientConfiguration.objects.get_or_create(
            institution=apex,
            category=apex_cats['Hostel & Accommodation'],
            defaults={
                'recipient_designation': 'The Chief Warden',
                'recipient_name': 'Dr. S. K. Gupta',
                'recipient_address': f"Central Hostel Directorate\n{apex.name}\n{apex.official_address}"
            }
        )

        # 4. Setup Horizon Univ Departments & Categories
        horizon_depts = {
            'Estate Office': InstitutionDepartment.objects.get_or_create(institution=horizon, name='Estate Office', defaults={'code': 'EST', 'contact_email': 'estate@horizonuniv.ac.in'})[0],
            'Dean of Students': InstitutionDepartment.objects.get_or_create(institution=horizon, name='Dean of Students', defaults={'code': 'DOS', 'contact_email': 'dean@horizonuniv.ac.in'})[0],
        }
        ComplaintCategory.objects.get_or_create(institution=horizon, name='Campus Amenities', defaults={'default_department': horizon_depts['Estate Office']})
        ComplaintRecipientConfiguration.objects.get_or_create(
            institution=horizon,
            category=None,
            defaults={
                'recipient_designation': 'The Dean of Students',
                'recipient_name': 'Dr. Meenakshi Sundaram',
                'recipient_address': f"Administrative Bhavan\n{horizon.name}\n{horizon.official_address}"
            }
        )

        # 5. Administrators
        # Apex Admin (Dr. Arvind Sharma & Dr. Vikram Roy)
        admin_apex, _ = User.objects.get_or_create(
            email='admin@apex.edu',
            defaults={
                'full_name': 'Dr. Arvind Sharma',
                'role': User.Role.INSTITUTION_ADMIN,
                'is_staff': True,
                'is_verified': True
            }
        )
        admin_apex.set_password('Admin@12345')
        admin_apex.is_active = True
        admin_apex.save()
        apex_admin_profile, _ = AdministratorProfile.objects.get_or_create(
            user=admin_apex,
            defaults={
                'institution': apex,
                'designation': 'Dean of Student Welfare',
                'department_name': 'Dean Office',
                'approval_status': AdministratorProfile.ApprovalStatus.APPROVED,
                'approved_by': superadmin,
                'approved_at': timezone.now()
            }
        )

        admin_roy, _ = User.objects.get_or_create(
            email='v.roy@apextech.edu',
            defaults={
                'full_name': 'Dr. Vikram Roy',
                'role': User.Role.INSTITUTION_ADMIN,
                'is_staff': True,
                'is_verified': True
            }
        )
        admin_roy.set_password('Admin@12345')
        admin_roy.is_active = True
        admin_roy.save()
        AdministratorProfile.objects.get_or_create(
            user=admin_roy,
            defaults={
                'institution': apex,
                'designation': 'Dean of Academic Grievance Redressal',
                'department_name': 'Dean Office',
                'approval_status': AdministratorProfile.ApprovalStatus.APPROVED,
                'approved_by': superadmin,
                'approved_at': timezone.now()
            }
        )

        # Horizon Admin
        admin_horizon, _ = User.objects.get_or_create(
            email='admin@horizon.edu',
            defaults={
                'full_name': 'Prof. Rajesh Kulkarni',
                'role': User.Role.INSTITUTION_ADMIN,
                'is_staff': True,
                'is_verified': True
            }
        )
        admin_horizon.set_password('Admin@12345')
        admin_horizon.is_active = True
        admin_horizon.save()
        AdministratorProfile.objects.get_or_create(
            user=admin_horizon,
            defaults={
                'institution': horizon,
                'designation': 'Registrar',
                'approval_status': AdministratorProfile.ApprovalStatus.APPROVED,
                'approved_by': superadmin,
                'approved_at': timezone.now()
            }
        )

        self.stdout.write(self.style.SUCCESS("Seeded Admins: admin@apex.edu, v.roy@apextech.edu, admin@horizon.edu (Pass: Admin@12345)"))

        # 6. Students
        # Apex Student (Priya Sharma & Maya Sharma)
        student_apex, _ = User.objects.get_or_create(
            email='student@apex.edu',
            defaults={
                'full_name': 'Priya Sharma',
                'role': User.Role.STUDENT,
                'is_verified': True
            }
        )
        student_apex.set_password('Student@12345')
        student_apex.is_active = True
        student_apex.save()
        apex_stud_profile, _ = StudentProfile.objects.get_or_create(
            user=student_apex,
            defaults={
                'student_id': 'AJU/22/0451',
                'institution': apex,
                'department': 'Computer Science & Engineering',
                'course': 'B.Tech CSE',
                'semester': '6th Semester',
                'phone': '+91 98765 43210',
                'address': 'Room 304, Block-B, Girls Hostel-1, Apex Tech Campus',
                'is_profile_complete': True
            }
        )

        student_maya, _ = User.objects.get_or_create(
            email='maya.sharma@apextech.edu',
            defaults={
                'full_name': 'Maya Sharma',
                'role': User.Role.STUDENT,
                'is_verified': True
            }
        )
        student_maya.set_password('Student@12345')
        student_maya.is_active = True
        student_maya.save()
        StudentProfile.objects.get_or_create(
            user=student_maya,
            defaults={
                'student_id': 'AIT-2023-CS-042',
                'institution': apex,
                'department': 'Computer Science & Engineering',
                'course': 'B.Tech CSE',
                'semester': '3rd Year, 5th Semester',
                'phone': '+91 98765 43210',
                'address': 'Room 312, Sarojini Hall of Residence, Apex Tech Campus, Jamshedpur 831014',
                'is_profile_complete': True
            }
        )

        # Horizon Student (Rahul Verma)
        student_horizon, _ = User.objects.get_or_create(
            email='student@horizon.edu',
            defaults={
                'full_name': 'Rahul Verma',
                'role': User.Role.STUDENT,
                'is_verified': True
            }
        )
        student_horizon.set_password('Student@12345')
        student_horizon.is_active = True
        student_horizon.save()
        StudentProfile.objects.get_or_create(
            user=student_horizon,
            defaults={
                'student_id': 'HSU/23/1029',
                'institution': horizon,
                'department': 'Department of Physics',
                'course': 'B.Sc Physics',
                'semester': '4th Semester',
                'phone': '+91 91234 56789',
                'address': 'Boys Hostel 2, Horizon University Campus',
                'is_profile_complete': True
            }
        )

        self.stdout.write(self.style.SUCCESS("Seeded Students: student@apex.edu, maya.sharma@apextech.edu, student@horizon.edu (Pass: Student@12345)"))

        # 7. Seed Sample Complaints with Formal Letters
        if not Complaint.objects.filter(student=student_apex).exists():
            # Complaint 1: Submitted
            letter_1 = FormalApplicationGenerator.generate_letter(
                student=student_apex,
                institution=apex,
                title='Water Supply Disruption in Girls Hostel Block B',
                description='Severe water supply disruption has been occurring in Block B for the last 3 days. Taps have run dry on the 2nd and 3rd floors, severely impacting sanitation and morning preparation.',
                category=apex_cats['Hostel & Accommodation'],
                location_details='Girls Hostel 1, Block B, 3rd Floor'
            )
            c1 = Complaint.objects.create(
                complaint_id='PV-2026-1042',
                institution=apex,
                student=student_apex,
                title='Water Supply Disruption in Girls Hostel Block B',
                original_description='Severe water supply disruption has been occurring in Block B for the last 3 days. Taps have run dry on the 2nd and 3rd floors, severely impacting sanitation and morning preparation.',
                final_submitted_application=letter_1['application_text'],
                category=apex_cats['Hostel & Accommodation'],
                priority=Complaint.Priority.HIGH,
                source_type=Complaint.SourceType.TEXT,
                building='Girls Hostel 1',
                floor='3rd Floor',
                room_number='Block B',
                full_issue_location='Girls Hostel 1, Block B, 3rd Floor',
                assigned_department=apex_depts['Hostel Administration'],
                assigned_admin=admin_apex,
                status=Complaint.Status.IN_PROGRESS,
                submission_timestamp=timezone.now() - timezone.timedelta(days=2)
            )
            ComplaintStatusHistory.objects.create(
                complaint=c1,
                previous_status=Complaint.Status.DRAFT,
                new_status=Complaint.Status.SUBMITTED,
                changed_by=student_apex,
                public_remark='Formal complaint submitted to institutional administration.'
            )
            ComplaintStatusHistory.objects.create(
                complaint=c1,
                previous_status=Complaint.Status.SUBMITTED,
                new_status=Complaint.Status.ASSIGNED,
                changed_by=admin_apex,
                assignment_change='Assigned to Hostel Administration',
                public_remark='Maintenance engineer dispatched to inspect overhead booster pump.',
                internal_note='Vendor contacted to repair damaged inlet valve by 5 PM.'
            )
            ComplaintStatusHistory.objects.create(
                complaint=c1,
                previous_status=Complaint.Status.ASSIGNED,
                new_status=Complaint.Status.IN_PROGRESS,
                changed_by=admin_apex,
                public_remark='Replacement valve installation in progress.'
            )

            # Complaint 2: Resolved
            letter_2 = FormalApplicationGenerator.generate_letter(
                student=student_apex,
                institution=apex,
                title='Faulty Projector and Lighting in CS Seminar Hall',
                description='The ceiling projector in Seminar Hall 2 flickers continuously and turns off mid-presentation. The central lighting panel also has dead fluorescent tubes.',
                category=apex_cats['Infrastructure & Maintenance'],
                location_details='CS Block, 2nd Floor, Room 204'
            )
            c2 = Complaint.objects.create(
                complaint_id='PV-2026-1015',
                institution=apex,
                student=student_apex,
                title='Faulty Projector and Lighting in CS Seminar Hall',
                original_description='The ceiling projector in Seminar Hall 2 flickers continuously and turns off mid-presentation. The central lighting panel also has dead fluorescent tubes.',
                final_submitted_application=letter_2['application_text'],
                category=apex_cats['Infrastructure & Maintenance'],
                priority=Complaint.Priority.MEDIUM,
                source_type=Complaint.SourceType.TEXT,
                building='CS Block',
                floor='2nd Floor',
                room_number='Room 204',
                full_issue_location='CS Block, 2nd Floor, Room 204',
                assigned_department=apex_depts['Estate & Maintenance'],
                status=Complaint.Status.RESOLVED,
                submission_timestamp=timezone.now() - timezone.timedelta(days=7),
                resolution_timestamp=timezone.now() - timezone.timedelta(days=5),
                resolution_details='Projector HDMI transmitter replaced and 4 LED panels fitted.'
            )
            ComplaintStatusHistory.objects.create(
                complaint=c2,
                previous_status=Complaint.Status.DRAFT,
                new_status=Complaint.Status.SUBMITTED,
                changed_by=student_apex,
                public_remark='Complaint submitted.'
            )
            ComplaintStatusHistory.objects.create(
                complaint=c2,
                previous_status=Complaint.Status.IN_PROGRESS,
                new_status=Complaint.Status.RESOLVED,
                changed_by=admin_apex,
                public_remark='Resolution: Projector HDMI transmitter replaced and 4 LED panels fitted.'
            )

            self.stdout.write(self.style.SUCCESS("Created Sample Complaints PV-2026-1042 and PV-2026-1015"))

        self.stdout.write(self.style.SUCCESS("Demo seeding completed successfully!"))
