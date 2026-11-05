"""
Seed Centralized Institutional Directory for ProofVoice
Populates well-known Indian educational institutions across Jharkhand, Odisha, and Premier Institutes.
Establishes Super Admin account for superadmin@proofvoice.platform.
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.institutions.models import (
    Institution,
    InstitutionDepartment,
    ComplaintCategory,
    ComplaintRecipientConfiguration
)
from apps.accounts.models import User, AdministratorProfile

INSTITUTIONS_SEED_DATA = [
    # JHARKHAND
    {
        "name": "Arka Jain University",
        "code": "arka-jain-univ",
        "institution_type": Institution.InstitutionType.UNIVERSITY,
        "state": "Jharkhand",
        "city": "Jamshedpur",
        "official_email": "admin@arkajainuniversity.ac.in",
        "official_address": "Opposite Kerala Public School, Mohanpur, Gamharia, Jamshedpur, Jharkhand 832108",
        "website": "https://arkajainuniversity.ac.in",
        "status": Institution.VerificationStatus.VERIFIED,
        "is_active": True,
    },
    {
        "name": "Birla Institute of Technology (BIT Mesra)",
        "code": "bit-mesra",
        "institution_type": Institution.InstitutionType.INSTITUTE,
        "state": "Jharkhand",
        "city": "Ranchi",
        "official_email": "dean.students@bitmesra.ac.in",
        "official_address": "BIT Mesra Campus, Ranchi, Jharkhand 835215",
        "website": "https://www.bitmesra.ac.in",
        "status": Institution.VerificationStatus.VERIFIED,
        "is_active": True,
    },
    {
        "name": "National Institute of Technology Jamshedpur",
        "code": "nit-jsr",
        "institution_type": Institution.InstitutionType.INSTITUTE,
        "state": "Jharkhand",
        "city": "Jamshedpur",
        "official_email": "registrar@nitjsr.ac.in",
        "official_address": "Adityapur, Jamshedpur, Jharkhand 831014",
        "website": "https://www.nitjsr.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
    {
        "name": "XLRI Jamshedpur",
        "code": "xlri-jsr",
        "institution_type": Institution.InstitutionType.INSTITUTE,
        "state": "Jharkhand",
        "city": "Jamshedpur",
        "official_email": "administration@xlri.ac.in",
        "official_address": "Circuit House Area, Sonari, Jamshedpur, Jharkhand 831001",
        "website": "https://www.xlri.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },

    # ODISHA
    {
        "name": "KIIT Deemed to be University",
        "code": "kiit-univ",
        "institution_type": Institution.InstitutionType.UNIVERSITY,
        "state": "Odisha",
        "city": "Bhubaneswar",
        "official_email": "contact@kiit.ac.in",
        "official_address": "Patia, Bhubaneswar, Odisha 751024",
        "website": "https://kiit.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
    {
        "name": "Siksha 'O' Anusandhan University",
        "code": "soa-univ",
        "institution_type": Institution.InstitutionType.UNIVERSITY,
        "state": "Odisha",
        "city": "Bhubaneswar",
        "official_email": "registrar@soa.ac.in",
        "official_address": "J-15, Khandagiri, Bhubaneswar, Odisha 751030",
        "website": "https://www.soa.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
    {
        "name": "Institute of Technical Education and Research (ITER), SOA University",
        "code": "iter-soa",
        "institution_type": Institution.InstitutionType.INSTITUTE,
        "state": "Odisha",
        "city": "Bhubaneswar",
        "official_email": "iter@soa.ac.in",
        "official_address": "Jagamara, Khandagiri, Bhubaneswar, Odisha 751030",
        "website": "https://www.soa.ac.in/iter",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
    {
        "name": "CV Raman Global University",
        "code": "cvrgu-bbsr",
        "institution_type": Institution.InstitutionType.UNIVERSITY,
        "state": "Odisha",
        "city": "Bhubaneswar",
        "official_email": "info@cvrgu.edu.in",
        "official_address": "Bidyanagar, Mahura, Janla, Bhubaneswar, Odisha 752054",
        "website": "https://cvrgu.edu.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
    {
        "name": "National Institute of Technology Rourkela",
        "code": "nit-rkl",
        "institution_type": Institution.InstitutionType.INSTITUTE,
        "state": "Odisha",
        "city": "Rourkela",
        "official_email": "registrar@nitrkl.ac.in",
        "official_address": "Sector 1, Rourkela, Odisha 769008",
        "website": "https://www.nitrkl.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },

    # OTHER FAMOUS INSTITUTIONS
    {
        "name": "IIT Kharagpur",
        "code": "iit-kgp",
        "institution_type": Institution.InstitutionType.INSTITUTE,
        "state": "West Bengal",
        "city": "Kharagpur",
        "official_email": "dean.sa@iitkgp.ac.in",
        "official_address": "Kharagpur, West Bengal 721302",
        "website": "https://www.iitkgp.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
    {
        "name": "IIT (BHU) Varanasi",
        "code": "iit-bhu",
        "institution_type": Institution.InstitutionType.INSTITUTE,
        "state": "Uttar Pradesh",
        "city": "Varanasi",
        "official_email": "registrar@iitbhu.ac.in",
        "official_address": "Varanasi, Uttar Pradesh 221005",
        "website": "https://www.iitbhu.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
    {
        "name": "IIT Delhi",
        "code": "iit-delhi",
        "institution_type": Institution.InstitutionType.INSTITUTE,
        "state": "Delhi",
        "city": "New Delhi",
        "official_email": "dean.students@iitd.ac.in",
        "official_address": "Hauz Khas, New Delhi 110016",
        "website": "https://home.iitd.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
    {
        "name": "IIT Bombay",
        "code": "iit-bombay",
        "institution_type": Institution.InstitutionType.INSTITUTE,
        "state": "Maharashtra",
        "city": "Mumbai",
        "official_email": "dean.sa@iitb.ac.in",
        "official_address": "Powai, Mumbai, Maharashtra 400076",
        "website": "https://www.iitb.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
    {
        "name": "IIT Kanpur",
        "code": "iit-kanpur",
        "institution_type": Institution.InstitutionType.INSTITUTE,
        "state": "Uttar Pradesh",
        "city": "Kanpur",
        "official_email": "dosa@iitk.ac.in",
        "official_address": "Kalyanpur, Kanpur, Uttar Pradesh 208016",
        "website": "https://www.iitk.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
    {
        "name": "IIT Madras",
        "code": "iit-madras",
        "institution_type": Institution.InstitutionType.INSTITUTE,
        "state": "Tamil Nadu",
        "city": "Chennai",
        "official_email": "dost@iitm.ac.in",
        "official_address": "Sardar Patel Road, Chennai, Tamil Nadu 600036",
        "website": "https://www.iitm.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
    {
        "name": "IIT Roorkee",
        "code": "iit-roorkee",
        "institution_type": Institution.InstitutionType.INSTITUTE,
        "state": "Uttarakhand",
        "city": "Roorkee",
        "official_email": "dosa@iitr.ac.in",
        "official_address": "Roorkee, Haridwar District, Uttarakhand 247667",
        "website": "https://www.iitr.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
    {
        "name": "IIT Guwahati",
        "code": "iit-guwahati",
        "institution_type": Institution.InstitutionType.INSTITUTE,
        "state": "Assam",
        "city": "Guwahati",
        "official_email": "dosa@iitg.ac.in",
        "official_address": "Amingaon, North Guwahati, Assam 781039",
        "website": "https://www.iitg.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
    {
        "name": "IIT Bhubaneswar",
        "code": "iit-bbsr",
        "institution_type": Institution.InstitutionType.INSTITUTE,
        "state": "Odisha",
        "city": "Bhubaneswar",
        "official_email": "dosa@iitbbs.ac.in",
        "official_address": "Argul, Jatni, Khordha, Odisha 752050",
        "website": "https://www.iitbbs.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
    {
        "name": "IIT Patna",
        "code": "iit-patna",
        "institution_type": Institution.InstitutionType.INSTITUTE,
        "state": "Bihar",
        "city": "Patna",
        "official_email": "dosa@iitp.ac.in",
        "official_address": "Bihta, Patna, Bihar 801106",
        "website": "https://www.iitp.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
    {
        "name": "Delhi University",
        "code": "delhi-univ",
        "institution_type": Institution.InstitutionType.UNIVERSITY,
        "state": "Delhi",
        "city": "New Delhi",
        "official_email": "registrar@du.ac.in",
        "official_address": "Benito Juarez Road, South Campus, New Delhi 110021",
        "website": "https://www.du.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
    {
        "name": "Banaras Hindu University",
        "code": "bhu-varanasi",
        "institution_type": Institution.InstitutionType.UNIVERSITY,
        "state": "Uttar Pradesh",
        "city": "Varanasi",
        "official_email": "registrar@bhu.ac.in",
        "official_address": "Ajagara, Varanasi, Uttar Pradesh 221005",
        "website": "https://www.bhu.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
    {
        "name": "Jawaharlal Nehru University",
        "code": "jnu-delhi",
        "institution_type": Institution.InstitutionType.UNIVERSITY,
        "state": "Delhi",
        "city": "New Delhi",
        "official_email": "registrar@jnu.ac.in",
        "official_address": "New Mehrauli Road, JNU Ring Road, New Delhi 110067",
        "website": "https://www.jnu.ac.in",
        "status": Institution.VerificationStatus.DIRECTORY_ONLY,
        "is_active": True,
    },
]


def seed_institution_defaults(institution):
    """Creates default departments, categories and Dean recipient if not present."""
    default_depts = [
        ('Estate & Maintenance', 'EST'),
        ('Hostel Administration', 'HST'),
        ('Academic Affairs', 'ACD'),
        ('IT & Network Services', 'ITS'),
        ('Dean of Student Welfare', 'DSW')
    ]
    created_depts = {}
    for d_name, d_code in default_depts:
        dept, _ = InstitutionDepartment.objects.get_or_create(
            institution=institution,
            name=d_name,
            defaults={'code': d_code, 'is_active': True}
        )
        created_depts[d_name] = dept

    default_categories = [
        ('Infrastructure & Maintenance', created_depts.get('Estate & Maintenance')),
        ('Hostel & Accommodation', created_depts.get('Hostel Administration')),
        ('Academic & Faculty', created_depts.get('Academic Affairs')),
        ('Sanitation & Hygiene', created_depts.get('Estate & Maintenance')),
        ('IT & Network Issues', created_depts.get('IT & Network Services')),
        ('General Administration', created_depts.get('Dean of Student Welfare'))
    ]
    for cat_name, dept_obj in default_categories:
        ComplaintCategory.objects.get_or_create(
            institution=institution,
            name=cat_name,
            defaults={'default_department': dept_obj, 'is_active': True}
        )

    if not ComplaintRecipientConfiguration.objects.filter(institution=institution, category__isnull=True).exists():
        ComplaintRecipientConfiguration.objects.create(
            institution=institution,
            recipient_designation='The Dean',
            recipient_name='',
            recipient_address=f"Office of the Dean, {institution.name}\n{institution.official_address}"
        )


class Command(BaseCommand):
    help = "Seeds centralized Indian educational institutions directory and initializes platform super admin."

    def handle(self, *args, **options):
        self.stdout.write("Seeding Institutional Directory...")
        count_created = 0
        count_updated = 0

        for item in INSTITUTIONS_SEED_DATA:
            inst, created = Institution.objects.get_or_create(
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "institution_type": item["institution_type"],
                    "state": item["state"],
                    "city": item["city"],
                    "official_email": item["official_email"],
                    "official_address": item["official_address"],
                    "website": item["website"],
                    "verification_status": item["status"],
                    "is_active": item["is_active"],
                }
            )
            if not created:
                # Update attributes without overriding custom changes
                inst.name = item["name"]
                inst.state = item["state"]
                inst.city = item["city"]
                inst.website = item["website"]
                inst.save()
                count_updated += 1
            else:
                count_created += 1

            if inst.verification_status == Institution.VerificationStatus.VERIFIED:
                seed_institution_defaults(inst)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded institutions: {count_created} created, {count_updated} updated."
        ))

        # Ensure Super Admin account: superadmin@proofvoice.platform
        super_admin_email = "superadmin@proofvoice.platform"
        admin_user, admin_created = User.objects.get_or_create(
            email=super_admin_email,
            defaults={
                "full_name": "ProofVoice Super Admin",
                "role": User.Role.PLATFORM_SUPERADMIN,
                "is_staff": True,
                "is_superuser": True,
                "is_verified": True,
            }
        )
        if admin_created:
            import os, secrets
            init_pass = os.getenv("SUPERADMIN_INITIAL_PASSWORD") or secrets.token_urlsafe(16)
            admin_user.set_password(init_pass)
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(
                f"Created Platform Super Admin user: {super_admin_email}"
            ))
        else:
            admin_user.role = User.Role.PLATFORM_SUPERADMIN
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.is_verified = True
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(
                f"Verified existing Platform Super Admin: {super_admin_email}"
            ))
