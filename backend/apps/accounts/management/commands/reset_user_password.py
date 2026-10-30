"""
Management command to list registered accounts and reset any user's password.
Usage:
  python manage.py reset_user_password --list
  python manage.py reset_user_password user@example.edu NewPassword123!
"""

from django.core.management.base import BaseCommand
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Lists registered users or resets password for a specified email'

    def add_arguments(self, parser):
        parser.add_argument('email', nargs='?', type=str, help='Email of the user to reset')
        parser.add_argument('password', nargs='?', type=str, help='New password')
        parser.add_argument('--list', action='store_true', help='List all registered user emails, roles, and status')

    def handle(self, *args, **options):
        if options['list'] or not options['email']:
            users = User.objects.all().order_by('-created_at')
            count = users.count()
            self.stdout.write(self.style.SUCCESS(f"\nTotal Registered Users in Database: {count}"))
            self.stdout.write("=" * 65)
            for u in users:
                self.stdout.write(f" * Email: {u.email:<32} | Role: {u.role:<18} | Name: {u.full_name}")
            self.stdout.write("=" * 65)
            if not options['email']:
                self.stdout.write(self.style.NOTICE("To reset a user password run:\n  python manage.py reset_user_password <email> <new_password>\n"))
                return

        email = options['email'].strip().lower()
        password = options.get('password') or 'Password@123'
        user = User.objects.filter(email=email).first()
        if not user:
            self.stdout.write(self.style.ERROR(f"Error: User with email '{email}' does not exist in the database."))
            self.stdout.write("Run with --list to see available registered accounts.")
            return

        user.set_password(password)
        user.is_active = True
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Success! Password for '{email}' has been set to: {password}"))
