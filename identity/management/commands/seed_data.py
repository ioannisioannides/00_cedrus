"""
Django management command to seed initial data.

Creates:
- User groups (cb_admin, lead_auditor, auditor, client_admin, client_user)
- Sample users for each role (passwords read from environment variables)
- Sample organization, site, standard, and certification
- Sample audit in "draft" status

Environment variables for demo user passwords:
    DEMO_CBADMIN_PASSWORD, DEMO_AUDITOR_PASSWORD,
    DEMO_TECHREVIEWER_PASSWORD, DEMO_DECISIONMAKER_PASSWORD,
    DEMO_CLIENTADMIN_PASSWORD

If a password env-var is not set, the user is created with a random
unusable password (you can reset it later with ``manage.py changepassword``).
"""

import os
from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from audit_management.models import Audit
from core.models import Certification, Organization, Site, Standard
from identity.adapters.models import Profile


class Command(BaseCommand):
    help = "Seed initial data for development"

    def handle(self, *args, **options):
        self.stdout.write("Seeding data...")

        groups = self._create_groups()
        users = self._create_users(groups)
        org = self._create_organization()
        self._link_client_admin(users["client_admin"], org)
        site = self._create_site(org)
        standard = self._create_standard()
        cert = self._create_certification(org, standard)
        self._create_audit(org, cert, site, users["cb_admin"], users["lead_auditor"])

        self._print_summary()

    def _create_groups(self):
        groups = {
            "cb_admin": Group.objects.get_or_create(name="cb_admin")[0],
            "lead_auditor": Group.objects.get_or_create(name="lead_auditor")[0],
            "auditor": Group.objects.get_or_create(name="auditor")[0],
            "technical_reviewer": Group.objects.get_or_create(name="technical_reviewer")[0],
            "decision_maker": Group.objects.get_or_create(name="decision_maker")[0],
            "client_admin": Group.objects.get_or_create(name="client_admin")[0],
            "client_user": Group.objects.get_or_create(name="client_user")[0],
        }
        self.stdout.write(self.style.SUCCESS("✓ Created user groups"))
        return groups

    def _create_user(self, username, email, first_name, last_name, group, env_var):  # pylint: disable=too-many-positional-arguments
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        if created:
            password = os.environ.get(env_var)
            if password:
                user.set_password(password)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Created {first_name} {last_name} ({username}) — password from ${env_var}")
                )
            else:
                user.set_unusable_password()
                self.stdout.write(
                    self.style.WARNING(
                        f"✓ Created {first_name} {last_name} ({username}) — "
                        f"no password (${env_var} not set, use 'manage.py changepassword {username}')"
                    )
                )
            user.save()
            user.groups.add(group)
        else:
            self.stdout.write(self.style.WARNING(f"  {first_name} {last_name} already exists"))
        return user

    def _create_users(self, groups):
        cb_admin = self._create_user(
            "cbadmin", "cbadmin@cedrus.example", "CB", "Administrator", groups["cb_admin"], "DEMO_CBADMIN_PASSWORD"
        )
        lead_auditor = self._create_user(
            "auditor1", "auditor1@cedrus.example", "Lead", "Auditor", groups["lead_auditor"], "DEMO_AUDITOR_PASSWORD"
        )
        tech_reviewer = self._create_user(
            "techreviewer",
            "techreviewer@cedrus.example",
            "Technical",
            "Reviewer",
            groups["technical_reviewer"],
            "DEMO_TECHREVIEWER_PASSWORD",
        )
        decision_maker = self._create_user(
            "decisionmaker",
            "decisionmaker@cedrus.example",
            "Decision",
            "Maker",
            groups["decision_maker"],
            "DEMO_DECISIONMAKER_PASSWORD",
        )
        client_admin = self._create_user(
            "clientadmin",
            "clientadmin@cedrus.example",
            "Client",
            "Administrator",
            groups["client_admin"],
            "DEMO_CLIENTADMIN_PASSWORD",
        )
        return {
            "cb_admin": cb_admin,
            "lead_auditor": lead_auditor,
            "client_admin": client_admin,
            "tech_reviewer": tech_reviewer,
            "decision_maker": decision_maker,
        }

    def _create_organization(self):
        org, created = Organization.objects.get_or_create(
            customer_id="CUST001",
            defaults={
                "name": "Acme Manufacturing Ltd.",
                "registered_id": "REG123456",
                "registered_address": "123 Industrial Way, Manufacturing City, MC 12345",
                "total_employee_count": 150,
                "contact_telephone": "+1-555-0100",
                "contact_email": "info@acme.example",
                "contact_website": "https://acme.example",
                "signatory_name": "John Doe",
                "signatory_title": "CEO",
                "ms_representative_name": "Jane Smith",
                "ms_representative_title": "Quality Manager",
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS("✓ Created sample organization"))
        else:
            self.stdout.write(self.style.WARNING("  Sample organization already exists"))
        return org

    def _link_client_admin(self, client_admin, org):
        if hasattr(client_admin, "profile"):
            client_admin.profile.organization = org
            client_admin.profile.save()
        else:
            Profile.objects.create(user=client_admin, organization=org)
        self.stdout.write(self.style.SUCCESS("✓ Linked Client Admin to organization"))

    def _create_site(self, org):
        site, created = Site.objects.get_or_create(
            organization=org,
            site_name="Main Production Facility",
            defaults={
                "site_address": "123 Industrial Way, Manufacturing City, MC 12345",
                "site_employee_count": 120,
                "active": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS("✓ Created sample site"))
        else:
            self.stdout.write(self.style.WARNING("  Sample site already exists"))
        return site

    def _create_standard(self):
        standard, created = Standard.objects.get_or_create(
            code="ISO 9001:2015",
            defaults={
                "title": "Quality management systems — Requirements",
                "nace_code": "25.11",
                "ea_code": "EA-7/03",
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS("✓ Created sample standard"))
        else:
            self.stdout.write(self.style.WARNING("  Sample standard already exists"))
        return standard

    def _create_certification(self, org, standard):
        cert, created = Certification.objects.get_or_create(
            organization=org,
            standard=standard,
            defaults={
                "certification_scope": "Design, development, and manufacture of industrial components",
                "certificate_id": "CERT-2024-001",
                "certificate_status": "active",
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS("✓ Created sample certification"))
        else:
            self.stdout.write(self.style.WARNING("  Sample certification already exists"))
        return cert

    def _create_audit(self, org, cert, site, cb_admin, lead_auditor):  # pylint: disable=too-many-positional-arguments
        audit, created = Audit.objects.get_or_create(
            organization=org,
            audit_type="surveillance",
            total_audit_date_from=date.today() + timedelta(days=30),
            defaults={
                "total_audit_date_to": date.today() + timedelta(days=32),
                "planned_duration_hours": 16.0,
                "status": "draft",
                "created_by": cb_admin,
                "lead_auditor": lead_auditor,
            },
        )
        if created:
            audit.certifications.add(cert)
            audit.sites.add(site)
            self.stdout.write(self.style.SUCCESS("✓ Created sample audit"))
        else:
            self.stdout.write(self.style.WARNING("  Sample audit already exists"))
        return audit

    def _print_summary(self):
        self.stdout.write(self.style.SUCCESS("\n✓ Seeding complete!"))
        self.stdout.write(self.style.SUCCESS("\nDemo users:"))
        self.stdout.write(self.style.SUCCESS("  - CB Admin:           cbadmin"))
        self.stdout.write(self.style.SUCCESS("  - Lead Auditor:       auditor1"))
        self.stdout.write(self.style.SUCCESS("  - Technical Reviewer: techreviewer"))
        self.stdout.write(self.style.SUCCESS("  - Decision Maker:     decisionmaker"))
        self.stdout.write(self.style.SUCCESS("  - Client Admin:       clientadmin"))
        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "Passwords were set from DEMO_*_PASSWORD environment variables.\n"
                "If a password was not set, use: manage.py changepassword <username>"
            )
        )
