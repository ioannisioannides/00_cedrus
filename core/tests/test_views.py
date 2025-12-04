import pytest
from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.utils import timezone

from core.models import CertificateHistory, Certification, Organization, Site, Standard, SurveillanceSchedule


@pytest.mark.django_db
class TestCoreViews:
    def setup_method(self):
        # Create CB Admin Group
        self.cb_admin_group = Group.objects.create(name="cb_admin")

        # Create User and add to group
        self.user = User.objects.create_user(username="admin", password="password")
        self.user.groups.add(self.cb_admin_group)

        # Create Organization
        self.org = Organization.objects.create(name="Test Org", customer_id="CUST-001", total_employee_count=10)

        # Create Standard
        self.standard = Standard.objects.create(
            code="ISO 9001", title="Quality Management", nace_code="1.1", ea_code="1"
        )

        # Create Certification
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certificate_id="CERT-001",
            issue_date=timezone.now().date(),
            expiry_date=timezone.now().date(),
        )

    def test_organization_list_view(self, client):
        client.force_login(self.user)
        url = reverse("core:organization_list")
        response = client.get(url)

        assert response.status_code == 200
        assert self.org in response.context["organizations"]

    def test_organization_create_view(self, client):
        client.force_login(self.user)
        url = reverse("core:organization_create")
        data = {
            "name": "New Org",
            "customer_id": "CUST-002",
            "total_employee_count": 50,
            "registered_address": "123 Street",
        }
        response = client.post(url, data)

        assert response.status_code == 302  # Redirects on success
        assert Organization.objects.filter(name="New Org").exists()

    def test_site_list_view_filter(self, client):
        client.force_login(self.user)

        site1 = Site.objects.create(organization=self.org, site_name="Site 1", site_employee_count=5)
        org2 = Organization.objects.create(name="Org 2", customer_id="CUST-002", total_employee_count=5)
        site2 = Site.objects.create(organization=org2, site_name="Site 2", site_employee_count=5)

        url = reverse("core:site_list")

        # No filter
        response = client.get(url)
        assert response.status_code == 200
        assert site1 in response.context["sites"]
        assert site2 in response.context["sites"]

        # Filter by org
        response = client.get(url, {"organization": self.org.id})
        assert response.status_code == 200
        assert site1 in response.context["sites"]
        assert site2 not in response.context["sites"]

    def test_certification_list_view_filter(self, client):
        client.force_login(self.user)

        org2 = Organization.objects.create(name="Org 2", customer_id="CUST-002", total_employee_count=5)
        cert2 = Certification.objects.create(
            organization=org2,
            standard=self.standard,
            certificate_id="CERT-002",
            issue_date=timezone.now().date(),
            expiry_date=timezone.now().date(),
        )

        url = reverse("core:certification_list")

        # No filter
        response = client.get(url)
        assert response.status_code == 200
        assert self.cert in response.context["certifications"]
        assert cert2 in response.context["certifications"]

        # Filter by org
        response = client.get(url, {"organization": self.org.id})
        assert response.status_code == 200
        assert self.cert in response.context["certifications"]
        assert cert2 not in response.context["certifications"]

    def test_certification_detail_view_context(self, client):
        client.force_login(self.user)

        # Add history
        history = CertificateHistory.objects.create(
            certification=self.cert, action="issued", action_date=timezone.now().date()
        )

        # Add schedule
        schedule = SurveillanceSchedule.objects.create(
            certification=self.cert,
            cycle_start=timezone.now().date(),
            cycle_end=timezone.now().date(),
            surveillance_1_due_date=timezone.now().date(),
            surveillance_2_due_date=timezone.now().date(),
            recertification_due_date=timezone.now().date(),
        )

        url = reverse("core:certification_detail", kwargs={"pk": self.cert.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert history in response.context["history"]
        assert response.context["surveillance_schedule"] == schedule

    def test_permission_denied(self, client):
        # Create user without cb_admin group
        user2 = User.objects.create_user(username="user2", password="password")
        client.force_login(user2)

        url = reverse("core:organization_list")
        response = client.get(url)

        assert response.status_code == 403

    def test_certificate_history_create_view(self, client):
        client.force_login(self.user)
        url = reverse("core:certificate_history_create", kwargs={"certification_pk": self.cert.pk})

        # Test GET (initial data)
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["form"].initial["certification"] == self.cert

        # Test POST
        data = {
            "certification": self.cert.pk,
            "action": "suspended",
            "action_date": timezone.now().date(),
            "description": "Test suspension",
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert CertificateHistory.objects.filter(action="suspended").exists()

    def test_surveillance_schedule_update_view(self, client):
        client.force_login(self.user)
        schedule = SurveillanceSchedule.objects.create(
            certification=self.cert,
            cycle_start=timezone.now().date(),
            cycle_end=timezone.now().date(),
            surveillance_1_due_date=timezone.now().date(),
            surveillance_2_due_date=timezone.now().date(),
            recertification_due_date=timezone.now().date(),
        )

        url = reverse("core:surveillance_schedule_update", kwargs={"pk": schedule.pk})

        data = {
            "cycle_start": schedule.cycle_start,
            "cycle_end": schedule.cycle_end,
            "surveillance_1_due_date": schedule.surveillance_1_due_date,
            "surveillance_2_due_date": schedule.surveillance_2_due_date,
            "recertification_due_date": schedule.recertification_due_date,
            "surveillance_1_completed": True,
        }

        response = client.post(url, data)
        assert response.status_code == 302
        schedule.refresh_from_db()
        assert schedule.surveillance_1_completed is True
