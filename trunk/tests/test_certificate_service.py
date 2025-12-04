from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from audit_management.models import Audit
from certification.models import CertificationDecision
from core.models import CertificateHistory, Certification, Organization, Standard, SurveillanceSchedule
from trunk.events import EventType
from trunk.services.certificate_service import CertificateService


@pytest.mark.django_db
class TestCertificateService:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(username="test_user", password="password")
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 Test St",
            customer_id="TEST001",
            total_employee_count=10,
        )
        self.standard = Standard.objects.create(code="ISO 9001", title="Quality Management")
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certificate_id="CERT001",
            certificate_status="active",
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=1095),
        )
        self.audit = Audit.objects.create(
            organization=self.org,
            created_by=self.user,
            audit_type="stage2",
            status="decision_pending",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today(),
            planned_duration_hours=8,
        )
        self.audit.certifications.add(self.cert)

    @patch("trunk.services.certificate_service.event_dispatcher.emit")
    def test_record_decision_creates_history_and_schedule(self, mock_emit):
        decision = CertificationDecision.objects.create(
            audit=self.audit,
            decision="granted",
            decision_maker=self.user,
            decision_notes="Approved",
            decided_at=timezone.now(),
        )

        CertificateService.record_decision(decision)

        # Check History Created
        history = CertificateHistory.objects.filter(related_decision=decision).first()
        assert history is not None
        assert history.action == "issued"
        assert history.certificate_number_snapshot == "CERT001"

        # Check Schedule Created
        schedule = SurveillanceSchedule.objects.filter(certification=self.cert).first()
        assert schedule is not None
        assert schedule.cycle_end == self.cert.issue_date + timedelta(days=1095)

        # Check Events
        assert mock_emit.call_count == 2
        mock_emit.assert_any_call(
            EventType.CERTIFICATE_HISTORY_CREATED,
            {"history_id": history.id, "certification_id": self.cert.id, "decision_id": decision.id},
        )
        mock_emit.assert_any_call(
            EventType.SURVEILLANCE_SCHEDULE_CREATED, {"schedule_id": schedule.id, "certification_id": self.cert.id}
        )

    @patch("trunk.services.certificate_service.event_dispatcher.emit")
    def test_record_decision_no_schedule_for_surveillance(self, mock_emit):
        self.audit.audit_type = "surveillance"
        self.audit.save()

        decision = CertificationDecision.objects.create(
            audit=self.audit,
            decision="maintained",
            decision_maker=self.user,
            decision_notes="Maintained",
            decided_at=timezone.now(),
        )

        CertificateService.record_decision(decision)

        # Check History Created
        history = CertificateHistory.objects.filter(related_decision=decision).first()
        assert history is not None
        assert history.action == "renewed"  # Logic in service says "renewed" if not stage2.
        # Actually logic is: action="issued" if decision.audit.audit_type == "stage2" else "renewed"

        # Check NO Schedule Created
        schedule = SurveillanceSchedule.objects.filter(certification=self.cert).first()
        assert schedule is None

        # Check Events (Only History)
        assert mock_emit.call_count == 1
        mock_emit.assert_called_with(
            EventType.CERTIFICATE_HISTORY_CREATED,
            {"history_id": history.id, "certification_id": self.cert.id, "decision_id": decision.id},
        )

    def test_record_decision_no_certifications(self):
        self.audit.certifications.clear()
        decision = CertificationDecision.objects.create(
            audit=self.audit, decision="granted", decision_maker=self.user, decided_at=timezone.now()
        )

        # Should not raise error
        CertificateService.record_decision(decision)

        assert CertificateHistory.objects.count() == 0

    @patch("trunk.services.certificate_service.event_dispatcher.emit")
    def test_update_certifications_suspension(self, mock_emit):
        recommendation = MagicMock()
        recommendation.suspension_recommended = True
        recommendation.revocation_recommended = False

        CertificateService.update_certifications_from_recommendation(self.audit, recommendation)

        self.cert.refresh_from_db()
        assert self.cert.certificate_status == "suspended"

        mock_emit.assert_called_with(
            EventType.CERTIFICATION_SUSPENDED, {"certification_id": self.cert.id, "audit_id": self.audit.id}
        )

    @patch("trunk.services.certificate_service.event_dispatcher.emit")
    def test_update_certifications_revocation(self, mock_emit):
        recommendation = MagicMock()
        recommendation.suspension_recommended = False
        recommendation.revocation_recommended = True

        CertificateService.update_certifications_from_recommendation(self.audit, recommendation)

        self.cert.refresh_from_db()
        assert self.cert.certificate_status == "withdrawn"

        mock_emit.assert_called_with(
            EventType.CERTIFICATION_REVOKED, {"certification_id": self.cert.id, "audit_id": self.audit.id}
        )
