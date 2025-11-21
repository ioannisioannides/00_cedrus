"""
Django management command to seed initial data.

Creates:
- User groups (cb_admin, lead_auditor, auditor, client_admin, client_user)
- Sample users for each role
- Sample organization, site, standard, and certification
- Sample audit in "draft" status
"""

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from accounts.models import Profile
from audits.models import Audit
from core.models import Certification, Organization, Site, Standard


class Command(BaseCommand):
    help = "Seed initial data for development"

    def handle(self, *args, **options):
        self.stdout.write("Seeding data...")

        # Create groups
        groups = {
            "cb_admin": Group.objects.get_or_create(name="cb_admin")[0],
            "lead_auditor": Group.objects.get_or_create(name="lead_auditor")[0],
            "auditor": Group.objects.get_or_create(name="auditor")[0],
            "client_admin": Group.objects.get_or_create(name="client_admin")[0],
            "client_user": Group.objects.get_or_create(name="client_user")[0],
        }
        self.stdout.write(self.style.SUCCESS("✓ Created user groups"))

        # Create CB Admin user
        cb_admin, created = User.objects.get_or_create(
            username="cbadmin",
            defaults={
                "email": "cbadmin@cedrus.example",
                "first_name": "CB",
                "last_name": "Administrator",
            },
        )
        if created:
            cb_admin.set_password("password123")
            cb_admin.save()
            cb_admin.groups.add(groups["cb_admin"])
            self.stdout.write(self.style.SUCCESS("✓ Created CB Admin user (cbadmin/password123)"))
        else:
            self.stdout.write(self.style.WARNING("  CB Admin user already exists"))

        # Create Lead Auditor user
        lead_auditor, created = User.objects.get_or_create(
            username="auditor1",
            defaults={
                "email": "auditor1@cedrus.example",
                "first_name": "Lead",
                "last_name": "Auditor",
            },
        )
        if created:
            lead_auditor.set_password("password123")
            lead_auditor.save()
            lead_auditor.groups.add(groups["lead_auditor"])
            self.stdout.write(
                self.style.SUCCESS("✓ Created Lead Auditor user (auditor1/password123)")
            )
        else:
            self.stdout.write(self.style.WARNING("  Lead Auditor user already exists"))

        # Create Client Admin user
        client_admin, created = User.objects.get_or_create(
            username="clientadmin",
            defaults={
                "email": "clientadmin@cedrus.example",
                "first_name": "Client",
                "last_name": "Administrator",
            },
        )
        if created:
            client_admin.set_password("password123")
            client_admin.save()
            client_admin.groups.add(groups["client_admin"])
            self.stdout.write(
                self.style.SUCCESS("✓ Created Client Admin user (clientadmin/password123)")
            )
        else:
            self.stdout.write(self.style.WARNING("  Client Admin user already exists"))

        # Create sample organization
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

        # Link client admin to organization
        if hasattr(client_admin, "profile"):
            client_admin.profile.organization = org
            client_admin.profile.save()
        else:
            Profile.objects.create(user=client_admin, organization=org)
        self.stdout.write(self.style.SUCCESS("✓ Linked Client Admin to organization"))

        # Create sample site
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

        # Create sample standard
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

        # Create sample certification
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

        # Create sample audit
        from datetime import date, timedelta

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

        self.stdout.write(self.style.SUCCESS("\n✓ Seeding complete!"))
        self.stdout.write(self.style.SUCCESS("\nYou can now log in with:"))
        self.stdout.write(self.style.SUCCESS("  - CB Admin: cbadmin / password123"))
        self.stdout.write(self.style.SUCCESS("  - Lead Auditor: auditor1 / password123"))
        self.stdout.write(self.style.SUCCESS("  - Client Admin: clientadmin / password123"))
