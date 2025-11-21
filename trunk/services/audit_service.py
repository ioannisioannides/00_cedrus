from django.core.exceptions import ValidationError

from audits.models import Audit
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

        # Ensure lead_auditor is set
        if "lead_auditor" not in create_data:
            create_data["lead_auditor"] = created_by

        # Create
        audit = Audit.objects.create(organization=organization, created_by=created_by, **create_data)

        audit.certifications.set(certifications)
        audit.sites.set(sites)

        # Emit audit created event
        event_dispatcher.emit(EventType.AUDIT_CREATED, {"audit": audit, "created_by": created_by})

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
            EventType.AUDIT_UPDATED, {"audit": audit, "old_status": old_status, "new_status": audit.status}
        )

        # Emit status change event if status changed
        if old_status != audit.status:
            event_dispatcher.emit(
                EventType.AUDIT_STATUS_CHANGED, {"audit": audit, "old_status": old_status, "new_status": audit.status}
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
