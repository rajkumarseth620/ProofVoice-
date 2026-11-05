import secrets
import string
from django.core.management.base import BaseCommand
from apps.accounts.models import User
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = "Securely initialize, configure, or rotate Platform Super Admin credentials."

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='superadmin@proofvoice.platform',
            help='Super Admin email address'
        )
        parser.add_argument(
            '--password',
            type=str,
            default=None,
            help='Specific password to set (if omitted, a secure 16-character password is generated)'
        )
        parser.add_argument(
            '--name',
            type=str,
            default='Platform Super Administrator',
            help='Full name for Super Admin'
        )
        parser.add_argument(
            '--rotate',
            action='store_true',
            help='Force password rotation and invalidate active session tokens'
        )

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        full_name = options['name'].strip()
        custom_password = options.get('password')

        # Generate a high-entropy password if not provided
        if not custom_password:
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(secrets.choice(alphabet) for _ in range(16))
        else:
            password = custom_password

        user = User.objects.filter(email=email).first()

        if user:
            user.role = User.Role.PLATFORM_SUPERADMIN
            user.full_name = full_name or user.full_name
            user.is_staff = True
            user.is_superuser = True
            user.is_verified = True
            user.is_active = True
            user.set_password(password)
            user.save()

            # Invalidate all prior tokens for security
            Token.objects.filter(user=user).delete()
            new_token = Token.objects.create(user=user)

            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(self.style.SUCCESS("  PROOFVOICE PLATFORM SUPER ADMIN CREDENTIALS UPDATED"))
            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(f"Email:    {email}")
            self.stdout.write(f"Role:     {user.role} (Superuser)")
            self.stdout.write(f"Password: {password}")
            self.stdout.write(f"Token:    {new_token.key}")
            self.stdout.write(self.style.WARNING("All previous session tokens have been invalidated for security."))
            self.stdout.write(self.style.SUCCESS("=" * 60))
        else:
            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                role=User.Role.PLATFORM_SUPERADMIN,
                is_staff=True,
                is_superuser=True,
                is_verified=True,
                is_active=True
            )
            token = Token.objects.create(user=user)

            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(self.style.SUCCESS("  PROOFVOICE PLATFORM SUPER ADMIN CREATED"))
            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(f"Email:    {email}")
            self.stdout.write(f"Role:     {user.role} (Superuser)")
            self.stdout.write(f"Password: {password}")
            self.stdout.write(f"Token:    {token.key}")
            self.stdout.write(self.style.SUCCESS("=" * 60))
