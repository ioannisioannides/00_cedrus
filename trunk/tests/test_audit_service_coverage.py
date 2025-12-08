from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from trunk.events import EventType
from trunk.services.audit_service import AuditService


@pytest.mark.django_db
class TestAuditServiceCoverage:
    def test_create_audit_no_certifications(self):
        """Test creating audit without certifications raises ValidationError."""
        with pytest.raises(ValidationError, match="At least one certification required"):
            AuditService.create_audit(
                organization=MagicMock(), certifications=[], sites=[MagicMock()], audit_data={}, created_by=MagicMock()
            )

    def test_create_audit_no_sites(self):
        """Test creating audit without sites raises ValidationError."""
        with pytest.raises(ValidationError, match="At least one site required"):
            AuditService.create_audit(
                organization=MagicMock(), certifications=[MagicMock()], sites=[], audit_data={}, created_by=MagicMock()
            )

    @patch("trunk.services.audit_service.Audit.objects.create")
    @patch("trunk.services.audit_service.event_dispatcher.emit")
    def test_create_audit_no_lead_auditor_in_data(self, mock_emit, mock_create):
        """Test creating audit where lead_auditor is not in audit_data (defaults to created_by)."""
        organization = MagicMock()
        created_by = MagicMock()
        created_by.id = 123
        certifications = [MagicMock()]
        sites = [MagicMock()]
        audit_data = {"some_field": "value"}

        mock_audit = MagicMock()
        mock_audit.id = 456
        mock_create.return_value = mock_audit

        AuditService.create_audit(
            organization=organization,
            certifications=certifications,
            sites=sites,
            audit_data=audit_data,
            created_by=created_by,
        )

        # Verify create was called with lead_auditor=created_by
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["lead_auditor"] == created_by
        assert call_kwargs["some_field"] == "value"

    @patch("trunk.services.audit_service.Audit.objects.create")
    @patch("trunk.services.audit_service.event_dispatcher.emit")
    def test_create_audit_no_created_by(self, mock_emit, mock_create):
        """Test creating audit with created_by=None."""
        organization = MagicMock()
        certifications = [MagicMock()]
        sites = [MagicMock()]
        audit_data = {"lead_auditor": MagicMock()}  # Must provide lead_auditor if created_by is None

        mock_audit = MagicMock()
        mock_audit.id = 456
        mock_create.return_value = mock_audit

        AuditService.create_audit(
            organization=organization,
            certifications=certifications,
            sites=sites,
            audit_data=audit_data,
            created_by=None,
        )

        # Verify event emitted with created_by_id=None
        mock_emit.assert_called_once_with(EventType.AUDIT_CREATED, {"audit_id": 456, "created_by_id": None})

    @patch("trunk.services.audit_service.event_dispatcher.emit")
    def test_update_audit_generic_attribute(self, mock_emit):
        """Test updating a generic attribute that is not in the exclusion list."""
        audit = MagicMock()
        audit.status = "DRAFT"
        audit.some_attribute = "old_value"

        # Mock hasattr to return True for 'some_attribute'
        # We need to wrap the mock to allow setting attributes
        audit.some_attribute = "old_value"

        data = {"some_attribute": "new_value"}

        AuditService.update_audit(audit, data)

        assert audit.some_attribute == "new_value"
        audit.save.assert_called_once()

    @patch("trunk.services.audit_service.event_dispatcher.emit")
    def test_update_audit_m2m_fields(self, mock_emit):
        """Test updating M2M fields (certifications, sites)."""
        audit = MagicMock()
        audit.status = "DRAFT"

        # Mock M2M managers
        audit.certifications = MagicMock()
        audit.sites = MagicMock()

        new_certs = [MagicMock()]
        new_sites = [MagicMock()]

        data = {"certifications": new_certs, "sites": new_sites}

        AuditService.update_audit(audit, data)

        audit.certifications.set.assert_called_once_with(new_certs)
        audit.sites.set.assert_called_once_with(new_sites)
        audit.save.assert_called_once()

    def test_validate_audit_data_empty(self):
        """Test validation with empty data returns None."""
        assert AuditService._validate_audit_data(None) is None
        assert AuditService._validate_audit_data({}) is None

    def test_validate_audit_data_future_date_too_far(self):
        """Test validation fails if start date is > 1 year in future."""
        future_date = timezone.now().date() + timedelta(days=367)
        data = {"total_audit_date_from": future_date}

        with pytest.raises(ValidationError, match="Audit start date cannot be more than 1 year in the future"):
            AuditService._validate_audit_data(data)

    def test_validate_audit_data_missing_duration(self):
        """Test validation fails if duration missing for specific audit types."""
        data = {"audit_type": "stage1"}

        with pytest.raises(ValidationError, match="Stage1 audits must have planned duration specified"):
            AuditService._validate_audit_data(data)
