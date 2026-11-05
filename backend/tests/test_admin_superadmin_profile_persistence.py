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
from apps.accounts.models import User, AdministratorProfile
from apps.accounts.views import ProfileView

def test_admin_superadmin_profile():
    print("==================================================")
    print("VERIFYING ADMIN & SUPER ADMIN PROFILE PERSISTENCE")
    print("==================================================")

    factory = APIRequestFactory()

    # 1. Test Super Admin Profile Update
    sa_email = 'superadmin_test@proofvoice.platform'
    sa, _ = User.objects.get_or_create(
        email=sa_email,
        defaults={
            'role': User.Role.PLATFORM_SUPERADMIN,
            'full_name': 'Original Super Admin',
            'is_superuser': True,
            'is_staff': True
        }
    )

    sa_payload = {
        'fullName': 'Root Super Admin Updated'
    }

    req = factory.patch('/api/v1/auth/profile/', sa_payload, format='json')
    force_authenticate(req, user=sa)
    res = ProfileView.as_view()(req)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.data}"

    sa.refresh_from_db()
    assert sa.full_name == 'Root Super Admin Updated', f"Name not updated: {sa.full_name}"
    print("  [PASS] Super Admin name updated and persisted to DB successfully!")

    # 2. Test Institution Admin Profile Update
    adm_email = 'inst_admin_test@proofvoice.edu'
    adm, _ = User.objects.get_or_create(
        email=adm_email,
        defaults={
            'role': User.Role.INSTITUTION_ADMIN,
            'full_name': 'Dean Original',
            'is_verified': True
        }
    )
    AdministratorProfile.objects.get_or_create(user=adm, defaults={'designation': 'Dean of Campus'})

    adm_payload = {
        'fullName': 'Dean P R Mahto',
        'designation': 'Dean Of Campus Operations'
    }

    req2 = factory.patch('/api/v1/auth/profile/', adm_payload, format='json')
    force_authenticate(req2, user=adm)
    res2 = ProfileView.as_view()(req2)
    assert res2.status_code == 200, f"Expected 200, got {res2.status_code}: {res2.data}"

    adm.refresh_from_db()
    assert adm.full_name == 'Dean P R Mahto', f"Admin name not updated: {adm.full_name}"
    assert adm.admin_profile.designation == 'Dean Of Campus Operations', f"Admin designation not updated: {adm.admin_profile.designation}"
    print("  [PASS] Institution Admin name & designation updated and persisted successfully!")

    # Cleanup test users
    sa.delete()
    adm.delete()
    print("==================================================")
    print(">>> ADMIN & SUPER ADMIN PROFILE PERSISTENCE VERIFIED! <<<")
    print("==================================================")

if __name__ == '__main__':
    test_admin_superadmin_profile()
