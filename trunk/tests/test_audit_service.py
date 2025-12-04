from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from audit_management.models import Audit
from core.models import Certification, Organization, Site, Standard
from trunk.events import EventType
from trunk.services.audit_service import AuditService


@pytest.mark.django_db
class TestAuditService:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(username="test_user", password="password")
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 Test St",
            customer_id="TEST001",
            total_employee_count=10,
        )
        self.site = Site.objects.create(
            organization=self.org,
            site_name="Test Site",
            site_address="123 Test St",
            site_employee_count=10,
        )
        self.standard = Standard.objects.create(code="ISO 9001", title="Quality Management")
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certificate_id="CERT001",
            certificate_status="active",
        )

    @patch("trunk.services.audit_service.event_dispatcher.emit")
    def test_create_audit_success(self, mock_emit):
        audit_data = {
            "audit_type": "surveillance",
            "total_audit_date_from": date.today(),
            "total_audit_date_to": date.today() + timedelta(days=2),
            "planned_duration_hours": 16,
            "status": "draft",
        }

        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data=audit_data,
            created_by=self.user,
        )

        assert audit.organization == self.org
        assert audit.created_by == self.user
        assert audit.certifications.count() == 1
        assert audit.sites.count() == 1

        mock_emit.assert_called_with(EventType.AUDIT_CREATED, {"audit_id": audit.id, "created_by_id": self.user.id})

    def test_create_audit_validation_error(self):
        audit_data = {
            "audit_type": "surveillance",
            # Missing planned_duration_hours for surveillance audit
            "total_audit_date_from": date.today(),
            "total_audit_date_to": date.today() + timedelta(days=2),
        }

        with pytest.raises(ValidationError) as exc:
            AuditService.create_audit(
                organization=self.org,
                certifications=[self.cert],
                sites=[self.site],
                audit_data=audit_data,
                created_by=self.user,
            )
        assert "must have planned duration specified" in str(exc.value)

    def test_create_audit_date_validation(self):
        audit_data = {
            "audit_type": "stage1",
            "planned_duration_hours": 8,
            "total_audit_date_from": date.today() + timedelta(days=5),
            "total_audit_date_to": date.today(),  # End date before start date
        }

        with pytest.raises(ValidationError) as exc:
            AuditService.create_audit(
                organization=self.org,
                certifications=[self.cert],
                sites=[self.site],
                audit_data=audit_data,
                created_by=self.user,
            )
        assert "Audit end date must be on or after start date" in str(exc.value)

    @patch("trunk.services.audit_service.event_dispatcher.emit")
    def test_update_audit(self, mock_emit):
        audit = Audit.objects.create(
            organization=self.org,
            created_by=self.user,
            audit_type="stage1",
            status="draft",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today(),
            planned_duration_hours=8,
        )

        update_data = {
            "planned_duration_hours": 12,
            "status": "draft",  # No status change
        }

        updated_audit = AuditService.update_audit(audit, update_data)

        assert updated_audit.planned_duration_hours == 12

        # Should emit AUDIT_UPDATED but not AUDIT_STATUS_CHANGED
        mock_emit.assert_called_with(
            EventType.AUDIT_UPDATED, {"audit_id": audit.id, "old_status": "draft", "new_status": "draft"}
        )

    @patch("trunk.services.audit_service.event_dispatcher.emit")
    def test_update_audit_status_change(self, mock_emit):
        audit = Audit.objects.create(
            organization=self.org,
            created_by=self.user,
            audit_type="stage1",
            status="draft",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today(),
            planned_duration_hours=8,
        )

        update_data = {"status": "planned"}

        updated_audit = AuditService.update_audit(audit, update_data)

        assert updated_audit.status == "planned"

        # Should emit both events
        assert mock_emit.call_count == 2

    def test_validate_future_dates(self):
        audit_data = {
            "audit_type": "stage1",
            "planned_duration_hours": 8,
            "total_audit_date_from": date.today() + timedelta(days=400),  # > 1 year
            "total_audit_date_to": date.today() + timedelta(days=402),
        }

        with pytest.raises(ValidationError) as exc:
            AuditService._validate_audit_data(audit_data)
        assert "cannot be more than 1 year in the future" in str(exc.value)
