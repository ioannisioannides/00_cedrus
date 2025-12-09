"""
Test evidence file upload functionality.
"""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from audit_management.models import Audit, EvidenceFile, Nonconformity
from core.models import Certification, Organization, Standard
from core.test_utils import TEST_PASSWORD_DEFAULT
from identity.adapters.models import Profile

User = get_user_model()


@pytest.fixture
def standard(db):  # pylint: disable=unused-argument
    """Create test standard."""
    return Standard.objects.create(code="ISO 9001:2015", title="Quality Management Systems")


@pytest.fixture
def organization(db):  # pylint: disable=unused-argument
    """Create test organization."""
    return Organization.objects.create(
        name="Test Organization",
        customer_id="TEST001",
        registered_address="123 Test St",
        total_employee_count=100,
    )


@pytest.fixture
def auditor_user(db, organization):  # pylint: disable=unused-argument
    """Create auditor user."""
    from django.contrib.auth.models import Group

    user = User.objects.create_user(username="auditor", email="auditor@cb.com", password=TEST_PASSWORD_DEFAULT)
    auditor_group, _ = Group.objects.get_or_create(name="lead_auditor")
    user.groups.add(auditor_group)
    Profile.objects.update_or_create(user=user, defaults={"organization": None})
    return user


@pytest.fixture
def audit(db, organization, standard, auditor_user):  # pylint: disable=unused-argument
    """Create audit."""
    audit = Audit.objects.create(
        organization=organization,
        audit_type="stage1",
        status="scheduled",
        total_audit_date_from="2025-12-01",
        total_audit_date_to="2025-12-03",
        lead_auditor=auditor_user,
        created_by=auditor_user,
    )
    cert = Certification.objects.create(
        organization=organization,
        standard=standard,
        certification_scope="Quality Management",
        certificate_status="active",
        certificate_id="CERT-001",
    )
    audit.certifications.add(cert)
    return audit


@pytest.mark.django_db
class TestEvidenceUpload:
    """Test evidence upload functionality."""

    @patch("audit_management.application.services.event_dispatcher.emit")
    def test_upload_evidence_file(self, mock_emit, auditor_user, audit):
        """Test uploading an evidence file."""
        client = Client()
        client.force_login(auditor_user)

        url = reverse("audit_management:evidence_file_upload", kwargs={"audit_pk": audit.pk})

        file_content = b"test file content"
        uploaded_file = SimpleUploadedFile("test_evidence.pdf", file_content, content_type="application/pdf")

        response = client.post(
            url,
            {
                "file": uploaded_file,
            },
        )

        assert response.status_code == 302
        assert EvidenceFile.objects.filter(audit=audit).exists()
        evidence = EvidenceFile.objects.get(audit=audit)
        assert "test_evidence" in evidence.file.name
        assert evidence.uploaded_by == auditor_user
        mock_emit.assert_called()

    @patch("audit_management.application.services.event_dispatcher.emit")
    def test_upload_evidence_linked_to_finding(self, mock_emit, auditor_user, audit, standard):
        """Test uploading evidence linked to a finding."""
        nc = Nonconformity.objects.create(
            audit=audit,
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

        url = reverse("audit_management:evidence_file_upload", kwargs={"audit_pk": audit.pk})

        file_content = b"test file content"
        uploaded_file = SimpleUploadedFile("nc_evidence.pdf", file_content, content_type="application/pdf")

        response = client.post(
            url,
            {
                "file": uploaded_file,
                "finding": nc.pk,
            },
        )

        assert response.status_code == 302
        assert EvidenceFile.objects.filter(audit=audit, finding=nc).exists()
        evidence = EvidenceFile.objects.get(audit=audit, finding=nc)
        assert evidence.finding == nc
        mock_emit.assert_called()

    @patch("audit_management.application.services.event_dispatcher.emit")
    def test_delete_evidence_file(self, mock_emit, auditor_user, audit):
        """Test deleting an evidence file."""
        file_content = b"test file content"
        uploaded_file = SimpleUploadedFile("test_delete.pdf", file_content, content_type="application/pdf")

        evidence = EvidenceFile.objects.create(
            audit=audit, uploaded_by=auditor_user, file=uploaded_file, evidence_type="document"
        )

        client = Client()
        client.force_login(auditor_user)

        url = reverse("audit_management:evidence_file_delete", kwargs={"file_pk": evidence.pk})
        response = client.post(url)

        assert response.status_code == 302
        assert not EvidenceFile.objects.filter(pk=evidence.pk).exists()
        mock_emit.assert_called()
