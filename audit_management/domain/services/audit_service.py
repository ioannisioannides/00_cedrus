from django.core.exceptions import ValidationError

from audit_management.domain.workflows.audit_state_machine import AuditStateMachine
from audit_management.models import Audit
from trunk.events import EventType, event_dispatcher


class AuditService:
    """Business logic for audit operations"""

    @staticmethod
    def create_audit(organization, certifications, sites, audit_data, created_by):
        """Create audit with validation"""
        # Validation
        AuditService._validate_audit_data(audit_data)

        if not certifications:
            raise ValidationError("At least one certification required")

        if not sites:
            raise ValidationError("At least one site required")

        # Prepare data for creation
        create_data = audit_data.copy()

        # Remove M2M fields if they are in audit_data
        create_data.pop("certifications", None)
        create_data.pop("sites", None)
        create_data.pop("organization", None)

        # Ensure lead_auditor is set
        if "lead_auditor" not in create_data:
            create_data["lead_auditor"] = created_by

        # Create
        audit = Audit.objects.create(organization=organization, created_by=created_by, **create_data)

        audit.certifications.set(certifications)
        audit.sites.set(sites)

        # Emit audit created event
        event_dispatcher.emit(
            EventType.AUDIT_CREATED,
            {"audit_id": audit.id, "created_by_id": created_by.id if created_by else None},
        )

        return audit

    @staticmethod
    def update_audit(audit, data):
        """Update audit details"""
        m2m_fields = ["certifications", "sites"]
        old_status = audit.status

        for key, value in data.items():
            if key in m2m_fields:
                getattr(audit, key).set(value)
            elif hasattr(audit, key) and key not in ["id", "created_by", "created_at", "updated_at"]:
                setattr(audit, key, value)

        audit.save()

        # Emit audit updated event
        event_dispatcher.emit(
            EventType.AUDIT_UPDATED,
            {"audit_id": audit.id, "old_status": old_status, "new_status": audit.status},
        )

        # Emit status change event if status changed
        if old_status != audit.status:
            event_dispatcher.emit(
                EventType.AUDIT_STATUS_CHANGED,
                {"audit_id": audit.id, "old_status": old_status, "new_status": audit.status},
            )

        return audit

    @staticmethod
    def _validate_audit_data(data):
        """Validate audit data"""
        from datetime import timedelta

        from django.utils import timezone

        if not data:
            return

        errors = []

        # Validate date ranges
        date_from = data.get("total_audit_date_from")
        date_to = data.get("total_audit_date_to")

        if date_from and date_to:
            if date_to < date_from:
                errors.append("Audit end date must be on or after start date.")

        # Validate future dates
        if date_from:
            one_year_ahead = timezone.now().date() + timedelta(days=365)
            if date_from > one_year_ahead:
                errors.append("Audit start date cannot be more than 1 year in the future.")

        # Validate audit type and duration
        audit_type = data.get("audit_type")
        if audit_type in ["stage1", "stage2", "surveillance"] and not data.get("planned_duration_hours"):
            errors.append(
                f"{audit_type.replace('_', ' ').title()} audits must have planned duration specified (IAF MD5)."
            )

        if errors:
            raise ValidationError(" ".join(errors))

    # -------------------------------------------------------------
    # Workflow operations (State Machine adapter)
    # -------------------------------------------------------------
    @staticmethod
    def transition_status(audit: Audit, new_status: str, user, notes: str = "") -> Audit:
        """
        Transition audit status using the audit state machine.

        Emits AUDIT_STATUS_CHANGED on success.
        """
        sm = AuditStateMachine(audit)
        old_status = audit.status
        audit = sm.transition(new_status, user, notes)

        # Emit status changed event
        event_dispatcher.emit(
            EventType.AUDIT_STATUS_CHANGED,
            {
                "audit_id": audit.id,
                "old_status": old_status,
                "new_status": audit.status,
                "changed_by_id": user.id if user else None,
                "notes": notes,
            },
        )
        return audit

    @staticmethod
    def get_available_transitions(audit: Audit, user) -> list[tuple[str, str]]:
        """Return available transitions for the given user."""
        sm = AuditStateMachine(audit)
        return sm.available_transitions(user)
