"""
Test findings CRUD operations.

Sprint 8, Task 8.1 - Phase 5: Integration Testing
Tests complete CRUD workflow for all finding types.
"""
# pylint: disable=redefined-outer-name,unused-argument

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

import pytest

from accounts.models import Profile
from audits.models import Audit, Nonconformity, Observation, OpportunityForImprovement
from core.models import Certification, Organization, Standard

User = get_user_model()


@pytest.fixture
def standard(db):
    """Create test standard."""
    return Standard.objects.create(code="ISO 9001:2015", title="Quality Management Systems")


@pytest.fixture
def organization(db):
    """Create test organization."""
    return Organization.objects.create(
        name="Test Organization",
        customer_id="TEST001",
        registered_address="123 Test St",
        total_employee_count=100,
    )


@pytest.fixture
def cb_admin_user(db, organization):
    """Create CB admin user."""
    user = User.objects.create_user(username="cbadmin", email="admin@cb.com", password="testpass")
    user.groups.create(name="CB Admin")
    Profile.objects.create(user=user, role="cb_admin", organization=organization)
    return user


@pytest.fixture
def auditor_user(db, organization):
    """Create auditor user."""
    from django.contrib.auth.models import Group

    user = User.objects.create_user(username="auditor", email="auditor@cb.com", password="testpass")
    auditor_group, _ = Group.objects.get_or_create(name="lead_auditor")
    user.groups.add(auditor_group)
    # Profile is auto-created via signal, just update it
    Profile.objects.update_or_create(user=user, defaults={"organization": None})
    return user


@pytest.fixture
def client_user(db, organization):
    """Create client user."""
    from django.contrib.auth.models import Group

    user = User.objects.create_user(username="client", email="client@org.com", password="testpass")
    client_group, _ = Group.objects.get_or_create(name="client_user")
    user.groups.add(client_group)
    # Profile is auto-created via signal, just update it
    Profile.objects.update_or_create(user=user, defaults={"organization": organization})
    return user


@pytest.fixture
def audit_scheduled(db, organization, standard, auditor_user):
    """Create audit in scheduled status."""
    audit = Audit.objects.create(
        organization=organization,
        audit_type="stage1",
        status="scheduled",
        total_audit_date_from="2025-12-01",
        total_audit_date_to="2025-12-03",
        lead_auditor=auditor_user,
        created_by=auditor_user,
    )
    # Create certification for the audit
    cert = Certification.objects.create(
        organization=organization,
        standard=standard,
        certification_scope="Quality Management",
        certificate_status="active",
        certificate_id="CERT-001",
    )
    audit.certifications.add(cert)
    return audit


@pytest.fixture
def audit_decided(db, organization, standard, auditor_user):
    """Create audit in decided status."""
    audit = Audit.objects.create(
        organization=organization,
        audit_type="stage1",
        status="decided",
        total_audit_date_from="2025-11-01",
        total_audit_date_to="2025-11-03",
        lead_auditor=auditor_user,
        created_by=auditor_user,
    )
    # Create certification for the audit
    cert = Certification.objects.create(
        organization=organization,
        standard=standard,
        certification_scope="Quality Management",
        certificate_status="active",
        certificate_id="CERT-002",
    )
    audit.certifications.add(cert)
    return audit


@pytest.mark.django_db
class TestNonconformityCRUD:
    """Test nonconformity CRUD operations."""

    def test_create_nonconformity_as_auditor(self, auditor_user, audit_scheduled, standard):
        """Test auditor can create nonconformity."""
        client = Client()
        client.force_login(auditor_user)

        url = reverse("audits:nonconformity_create", kwargs={"audit_pk": audit_scheduled.pk})
        response = client.post(
            url,
            {
                "standard": standard.pk,
                "clause": "7.1.5",
                "category": "major",
                "objective_evidence": "Test evidence",
                "statement_of_nc": "Test statement",
                "auditor_explanation": "Test explanation",
                "due_date": "2025-12-31",
            },
        )

        assert response.status_code == 302  # Redirect on success
        assert Nonconformity.objects.filter(audit=audit_scheduled).exists()
        nc = Nonconformity.objects.get(audit=audit_scheduled)
        assert nc.clause == "7.1.5"
        assert nc.category == "major"
        assert nc.created_by == auditor_user

    def test_cannot_create_nonconformity_when_decided(self, auditor_user, audit_decided, standard):
        """Test cannot create NC when audit is decided."""
        client = Client()
        client.force_login(auditor_user)

        url = reverse("audits:nonconformity_create", kwargs={"audit_pk": audit_decided.pk})
        response = client.post(
            url,
            {
                "standard": standard.pk,
                "clause": "7.1.5",
                "category": "major",
                "objective_evidence": "Test evidence",
                "statement_of_nc": "Test statement",
                "auditor_explanation": "Test explanation",
            },
        )

        assert response.status_code == 403  # Forbidden
        assert not Nonconformity.objects.filter(audit=audit_decided).exists()

    def test_view_nonconformity_detail(self, auditor_user, audit_scheduled, standard):
        """Test viewing nonconformity detail."""
        nc = Nonconformity.objects.create(
            audit=audit_scheduled,
            standard=standard,
            clause="7.1.5",
            category="major",
            objective_evidence="Test evidence",
            statement_of_nc="Test statement",
            auditor_explanation="Test explanation",
            created_by=auditor_user,
        )

        client = Client()
        client.force_login(auditor_user)

        url = reverse("audits:nonconformity_detail", kwargs={"pk": nc.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert "7.1.5" in response.content.decode()
        assert "Test evidence" in response.content.decode()

    def test_update_nonconformity(self, auditor_user, audit_scheduled, standard):
        """Test updating nonconformity."""
        nc = Nonconformity.objects.create(
            audit=audit_scheduled,
            standard=standard,
            clause="7.1.5",
            category="major",
            objective_evidence="Old evidence",
            statement_of_nc="Old statement",
            auditor_explanation="Old explanation",
            created_by=auditor_user,
        )

        client = Client()
        client.force_login(auditor_user)

        url = reverse("audits:nonconformity_update", kwargs={"pk": nc.pk})
        response = client.post(
            url,
            {
                "standard": standard.pk,
                "clause": "7.1.6",
                "category": "minor",
                "objective_evidence": "New evidence",
                "statement_of_nc": "New statement",
                "auditor_explanation": "New explanation",
            },
        )

        assert response.status_code == 302
        nc.refresh_from_db()
        assert nc.clause == "7.1.6"
        assert nc.category == "minor"
        assert nc.objective_evidence == "New evidence"

    def test_delete_nonconformity(self, auditor_user, audit_scheduled, standard):
        """Test deleting nonconformity."""
        nc = Nonconformity.objects.create(
            audit=audit_scheduled,
            standard=standard,
            clause="7.1.5",
            category="major",
            objective_evidence="Test evidence",
            statement_of_nc="Test statement",
            auditor_explanation="Test explanation",
            created_by=auditor_user,
        )

        client = Client()
        client.force_login(auditor_user)

        url = reverse("audits:nonconformity_delete", kwargs={"pk": nc.pk})
        response = client.post(url)

        assert response.status_code == 302
        assert not Nonconformity.objects.filter(pk=nc.pk).exists()

    def test_client_cannot_create_nonconformity(self, client_user, audit_scheduled, standard):
        """Test client user cannot create nonconformity."""
        client = Client()
        client.force_login(client_user)

        url = reverse("audits:nonconformity_create", kwargs={"audit_pk": audit_scheduled.pk})
        response = client.post(
            url,
            {
                "standard": standard.pk,
                "clause": "7.1.5",
                "category": "major",
                "objective_evidence": "Test evidence",
                "statement_of_nc": "Test statement",
                "auditor_explanation": "Test explanation",
            },
        )

        assert response.status_code == 403
        assert not Nonconformity.objects.filter(audit=audit_scheduled).exists()


@pytest.mark.django_db
class TestObservationCRUD:
    """Test observation CRUD operations."""

    def test_create_observation_as_auditor(self, auditor_user, audit_scheduled, standard):
        """Test auditor can create observation."""
        client = Client()
        client.force_login(auditor_user)

        url = reverse("audits:observation_create", kwargs={"audit_pk": audit_scheduled.pk})
        response = client.post(
            url,
            {
                "standard": standard.pk,
                "clause": "8.2.1",
                "statement": "Test observation evidence",
                "explanation": "Test observation explanation",
            },
        )

        assert response.status_code == 302
        assert Observation.objects.filter(audit=audit_scheduled).exists()
        obs = Observation.objects.get(audit=audit_scheduled)
        assert obs.clause == "8.2.1"
        assert obs.created_by == auditor_user

    def test_cannot_create_observation_when_decided(self, auditor_user, audit_decided, standard):
        """Test cannot create observation when audit is decided."""
        client = Client()
        client.force_login(auditor_user)

        url = reverse("audits:observation_create", kwargs={"audit_pk": audit_decided.pk})
        response = client.post(
            url,
            {
                "standard": standard.pk,
                "clause": "8.2.1",
                "statement": "Test evidence",
                "explanation": "Test explanation",
            },
        )

        assert response.status_code == 403
        assert not Observation.objects.filter(audit=audit_decided).exists()

    def test_view_observation_detail(self, auditor_user, audit_scheduled, standard):
        """Test viewing observation detail."""
        obs = Observation.objects.create(
            audit=audit_scheduled,
            standard=standard,
            clause="8.2.1",
            statement="Test observation",
            explanation="Test note",
            created_by=auditor_user,
        )

        client = Client()
        client.force_login(auditor_user)

        url = reverse("audits:observation_detail", kwargs={"pk": obs.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert "8.2.1" in response.content.decode()
        assert "Test observation" in response.content.decode()

    def test_update_observation(self, auditor_user, audit_scheduled, standard):
        """Test updating observation."""
        obs = Observation.objects.create(
            audit=audit_scheduled,
            standard=standard,
            clause="8.2.1",
            statement="Old evidence",
            explanation="Old explanation",
            created_by=auditor_user,
        )

        client = Client()
        client.force_login(auditor_user)

        url = reverse("audits:observation_update", kwargs={"pk": obs.pk})
        response = client.post(
            url,
            {
                "standard": standard.pk,
                "clause": "8.2.2",
                "statement": "New evidence",
                "explanation": "New explanation",
            },
        )

        assert response.status_code == 302
        obs.refresh_from_db()
        assert obs.clause == "8.2.2"
        assert obs.statement == "New evidence"

    def test_delete_observation(self, auditor_user, audit_scheduled, standard):
        """Test deleting observation."""
        obs = Observation.objects.create(
            audit=audit_scheduled,
            standard=standard,
            clause="8.2.1",
            statement="Test observation",
            explanation="Test note",
            created_by=auditor_user,
        )

        client = Client()
        client.force_login(auditor_user)

        url = reverse("audits:observation_delete", kwargs={"pk": obs.pk})
        response = client.post(url)

        assert response.status_code == 302
        assert not Observation.objects.filter(pk=obs.pk).exists()


@pytest.mark.django_db
class TestOFICRUD:
    """Test opportunity for improvement CRUD operations."""

    def test_create_ofi_as_auditor(self, auditor_user, audit_scheduled, standard):
        """Test auditor can create OFI."""
        client = Client()
        client.force_login(auditor_user)

        url = reverse("audits:ofi_create", kwargs={"audit_pk": audit_scheduled.pk})
        response = client.post(
            url,
            {
                "standard": standard.pk,
                "clause": "9.3",
                "description": "Test OFI evidence",
            },
        )

        assert response.status_code == 302
        assert OpportunityForImprovement.objects.filter(audit=audit_scheduled).exists()
        ofi = OpportunityForImprovement.objects.get(audit=audit_scheduled)
        assert ofi.clause == "9.3"
        assert ofi.created_by == auditor_user

    def test_cannot_create_ofi_when_decided(self, auditor_user, audit_decided, standard):
        """Test cannot create OFI when audit is decided."""
        client = Client()
        client.force_login(auditor_user)

        url = reverse("audits:ofi_create", kwargs={"audit_pk": audit_decided.pk})
        response = client.post(
            url,
            {
                "standard": standard.pk,
                "clause": "9.3",
                "description": "Test evidence",
            },
        )

        assert response.status_code == 403
        assert not OpportunityForImprovement.objects.filter(audit=audit_decided).exists()

    def test_view_ofi_detail(self, auditor_user, audit_scheduled, standard):
        """Test viewing OFI detail."""
        ofi = OpportunityForImprovement.objects.create(
            audit=audit_scheduled,
            standard=standard,
            clause="9.3",
            description="Test OFI",
            created_by=auditor_user,
        )

        client = Client()
        client.force_login(auditor_user)

        url = reverse("audits:ofi_detail", kwargs={"pk": ofi.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert "9.3" in response.content.decode()
        assert "Test OFI" in response.content.decode()

    def test_update_ofi(self, auditor_user, audit_scheduled, standard):
        """Test updating OFI."""
        ofi = OpportunityForImprovement.objects.create(
            audit=audit_scheduled,
            standard=standard,
            clause="9.3",
            description="Old evidence",
            created_by=auditor_user,
        )

        client = Client()
        client.force_login(auditor_user)

        url = reverse("audits:ofi_update", kwargs={"pk": ofi.pk})
        response = client.post(
            url,
            {
                "standard": standard.pk,
                "clause": "9.3.1",
                "description": "New evidence",
            },
        )

        assert response.status_code == 302
        ofi.refresh_from_db()
        assert ofi.clause == "9.3.1"
        assert ofi.description == "New evidence"

    def test_delete_ofi(self, auditor_user, audit_scheduled, standard):
        """Test deleting OFI."""
        ofi = OpportunityForImprovement.objects.create(
            audit=audit_scheduled,
            standard=standard,
            clause="9.3",
            description="Test OFI",
            created_by=auditor_user,
        )

        client = Client()
        client.force_login(auditor_user)

        url = reverse("audits:ofi_delete", kwargs={"pk": ofi.pk})
        response = client.post(url)

        assert response.status_code == 302
        assert not OpportunityForImprovement.objects.filter(pk=ofi.pk).exists()


@pytest.mark.django_db
class TestFindingsIntegration:
    """Test findings integration in audit detail page."""

    def test_audit_detail_shows_all_findings(self, auditor_user, audit_scheduled, standard):
        """Test audit detail page shows all finding types."""
        # Create one of each finding type
        Nonconformity.objects.create(
            audit=audit_scheduled,
            standard=standard,
            clause="7.1.5",
            category="major",
            objective_evidence="NC evidence",
            statement_of_nc="NC statement",
            auditor_explanation="NC explanation",
            created_by=auditor_user,
        )

        Observation.objects.create(
            audit=audit_scheduled,
            standard=standard,
            clause="8.2.1",
            statement="Obs evidence",
            explanation="Obs note",
            created_by=auditor_user,
        )

        OpportunityForImprovement.objects.create(
            audit=audit_scheduled,
            standard=standard,
            clause="9.3",
            description="OFI evidence",
            created_by=auditor_user,
        )

        client = Client()
        client.force_login(auditor_user)

        url = reverse("audits:audit_detail", kwargs={"pk": audit_scheduled.pk})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "7.1.5" in content  # NC clause
        assert "8.2.1" in content  # Observation clause
        assert "9.3" in content  # OFI clause
        assert "1 NCs" in content or "Total NCs" in content
        assert "1 Observations" in content or "Observations" in content
        assert "1 OFIs" in content or "OFIs" in content

    def test_audit_detail_hides_add_buttons_when_decided(self, auditor_user, audit_decided):
        """Test 'Add Finding' buttons hidden when audit is decided."""
        client = Client()
        client.force_login(auditor_user)

        url = reverse("audits:audit_detail", kwargs={"pk": audit_decided.pk})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Add Nonconformity" not in content
        assert "Add Observation" not in content
        assert "Add OFI" not in content
