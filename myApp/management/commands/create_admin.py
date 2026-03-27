"""
Django management command to create admin accounts.

Usage:
    python manage.py create_admin

Creates:
  - Django superuser (for /admin/ panel)
  - Website login account (email-based, same credentials)

Credentials after running:
  Django Admin   → username: admin        / password: Admin@1234
  Website Login  → email: admin@alphamart.com / password: Admin@1234
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create Django superuser + website admin account (non-interactive)'

    def handle(self, *args, **options):

        ADMIN_USERNAME = 'admin'
        ADMIN_EMAIL    = 'admin@alphamart.com'
        ADMIN_PASSWORD = 'Admin@1234'

        # ── 1. Django superuser (for /admin/) ─────────────────
        user_qs = User.objects.filter(username=ADMIN_USERNAME)

        if user_qs.exists():
            user = user_qs.first()
            changed = False

            if not user.is_superuser:
                user.is_superuser = True
                changed = True
            if not user.is_staff:
                user.is_staff = True
                changed = True
            if not user.is_active:
                user.is_active = True
                changed = True
            # Always reset password so it's known
            user.set_password(ADMIN_PASSWORD)
            user.save()

            if changed:
                self.stdout.write(self.style.WARNING(
                    f"[UPDATED] '{ADMIN_USERNAME}' upgraded to superuser with known password."
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"[OK] Superuser '{ADMIN_USERNAME}' already exists. Password reset to Admin@1234."
                ))
        else:
            user = User.objects.create_superuser(
                username   = ADMIN_USERNAME,
                email      = ADMIN_EMAIL,
                password   = ADMIN_PASSWORD,
                first_name = 'Site',
                last_name  = 'Admin',
            )
            self.stdout.write(self.style.SUCCESS(
                f"[CREATED] Django superuser '{ADMIN_USERNAME}' created."
            ))

        # ── 2. UserProfile for website navigation ─────────────
        # Import here to avoid app registry issues
        try:
            from myApp.models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            if created or not profile.phone:
                profile.role        = 'seller'
                profile.phone       = '9800000000'
                profile.address     = 'Kathmandu, Nepal'
                profile.is_verified = True
                profile.save()
                self.stdout.write(self.style.SUCCESS(
                    f"[CREATED] UserProfile for '{ADMIN_USERNAME}' set up."
                ))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"[WARN] UserProfile setup skipped: {e}"))

        # ── 3. Summary ─────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 55))
        self.stdout.write(self.style.SUCCESS('  ADMIN ACCOUNTS READY'))
        self.stdout.write(self.style.SUCCESS('=' * 55))
        self.stdout.write('')
        self.stdout.write('  Django Admin  →  http://127.0.0.1:8000/admin/')
        self.stdout.write(f'    Username : {ADMIN_USERNAME}')
        self.stdout.write(f'    Password : {ADMIN_PASSWORD}')
        self.stdout.write('')
        self.stdout.write('  Website Login →  http://127.0.0.1:8000/login/')
        self.stdout.write(f'    Email    : {ADMIN_EMAIL}')
        self.stdout.write(f'    Password : {ADMIN_PASSWORD}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 55))
