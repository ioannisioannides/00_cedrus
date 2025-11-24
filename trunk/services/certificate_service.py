"""Certificate lifecycle service utilities.

Handles creation of certificate history entries and surveillance schedule
automation following certification decisions (ISO 17021-1 Clause 9.6).
"""

from datetime import timedelta

from django.utils import timezone

from audits.models import CertificationDecision
from core.models import CertificateHistory, Certification, SurveillanceSchedule
from trunk.events import EventType, event_dispatcher


class CertificateService:
    """Service operations for certificate lifecycle management."""

    @staticmethod
    def record_decision(decision: CertificationDecision):
        """Create certificate history entry when a certification decision occurs."""
        certification_qs = decision.audit.certifications.all()
        if not certification_qs.exists():
            return
        # For simplicity assume first certification (single-standard audits typical in MVP)
        certification = certification_qs.first()

        history = CertificateHistory.objects.create(
            certification=certification,
            action="issued" if decision.audit.audit_type == "stage2" else "renewed",
            action_date=decision.decided_at.date(),
            related_audit=decision.audit,
            related_decision=decision,
            certificate_number_snapshot=certification.certificate_id,
            certification_scope_snapshot=certification.certification_scope,
            valid_from=certification.issue_date,
            valid_to=certification.expiry_date,
            action_by=decision.decision_maker,
            action_reason=decision.decision_notes,
        )

        event_dispatcher.emit(
            EventType.CERTIFICATE_HISTORY_CREATED,
            {"history": history, "certification": certification, "decision": decision},
        )

        # Create surveillance schedule for new cycle (stage2 or recertification)
        if decision.audit.audit_type in ["stage2", "recertification"] and not hasattr(
            certification, "surveillance_schedule"
        ):
            cycle_start = certification.issue_date or timezone.now().date()
            schedule = SurveillanceSchedule.objects.create(
                certification=certification,
                cycle_start=cycle_start,
                cycle_end=cycle_start + timedelta(days=1095),  # 3 years
                surveillance_1_due_date=cycle_start + timedelta(days=365),
                surveillance_2_due_date=cycle_start + timedelta(days=730),
                recertification_due_date=cycle_start + timedelta(days=1095),
            )

            event_dispatcher.emit(
                EventType.SURVEILLANCE_SCHEDULE_CREATED, {"schedule": schedule, "certification": certification}
            )
