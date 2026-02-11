"""
Django management command to create/update demo users from environment variables.

Reads credentials from environment variables so that passwords are **never**
hardcoded in source code.  Suitable for CI, Docker, and local development.

Required environment variables (per user):
    DEMO_CBADMIN_PASSWORD
    DEMO_AUDITOR_PASSWORD
    DEMO_TECHREVIEWER_PASSWORD
    DEMO_DECISIONMAKER_PASSWORD
    DEMO_CLIENTADMIN_PASSWORD

All variables are optional — if a variable is missing the corresponding user
is skipped with a warning.
"""

from __future__ import annotations

import os

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

# ─── Demo user definitions ────────────────────────────────────────────────────
# Each tuple: (username, email, first_name, last_name, group_name, env_var)
DEMO_USERS: list[tuple[str, str, str, str, str, str]] = [
    ("cbadmin", "cbadmin@cedrus.example", "CB", "Administrator", "cb_admin", "DEMO_CBADMIN_PASSWORD"),
    ("auditor1", "auditor1@cedrus.example", "Lead", "Auditor", "lead_auditor", "DEMO_AUDITOR_PASSWORD"),
    (
        "techreviewer",
        "techreviewer@cedrus.example",
        "Technical",
        "Reviewer",
        "technical_reviewer",
        "DEMO_TECHREVIEWER_PASSWORD",
    ),
    (
        "decisionmaker",
        "decisionmaker@cedrus.example",
        "Decision",
        "Maker",
        "decision_maker",
        "DEMO_DECISIONMAKER_PASSWORD",
    ),
    (
        "clientadmin",
        "clientadmin@cedrus.example",
        "Client",
        "Administrator",
        "client_admin",
        "DEMO_CLIENTADMIN_PASSWORD",
    ),
]


class Command(BaseCommand):
    help = "Create or update demo users using passwords from environment variables."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force-update",
            action="store_true",
            help="Update existing users' passwords even if the user already exists.",
        )

    def handle(self, *args, **options):
        force_update: bool = options["force_update"]
        created_count = 0
        updated_count = 0
        skipped_count = 0

        # Ensure all referenced groups exist
        for _uname, _email, _fn, _ln, group_name, _env in DEMO_USERS:
            Group.objects.get_or_create(name=group_name)

        for username, email, first_name, last_name, group_name, env_var in DEMO_USERS:
            password = os.environ.get(env_var)

            if not password:
                self.stdout.write(self.style.WARNING(f"  ⏭  Skipping {username}: ${env_var} not set"))
                skipped_count += 1
                continue

            group = Group.objects.get(name=group_name)
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )

            if created:
                user.set_password(password)
                user.save()
                user.groups.add(group)
                self.stdout.write(self.style.SUCCESS(f"  ✅ Created {first_name} {last_name} ({username})"))
                created_count += 1
            elif force_update:
                user.email = email
                user.first_name = first_name
                user.last_name = last_name
                user.set_password(password)
                user.save()
                user.groups.clear()
                user.groups.add(group)
                self.stdout.write(self.style.SUCCESS(f"  🔄 Updated {first_name} {last_name} ({username})"))
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⏭  {first_name} {last_name} already exists (use --force-update to overwrite)"
                    )
                )
                skipped_count += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(f"Done: {created_count} created, {updated_count} updated, {skipped_count} skipped")
        )
