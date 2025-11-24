"""
Service for handling Complaints and Appeals.
"""
from django.core.exceptions import ValidationError

from audits.models import Appeal, Complaint
from trunk.events import EventType, event_dispatcher


class ComplaintService:
    """Business logic for complaints and appeals."""

    @staticmethod
    def create_complaint(data, created_by):
        """Create a new complaint."""
        # Generate a simple unique number
        import uuid
        complaint_number = f"COMP-{uuid.uuid4().hex[:8].upper()}"
        
        complaint = Complaint.objects.create(
            complaint_number=complaint_number,
            submitted_by=created_by,
            **data
        )
        
        event_dispatcher.emit(
            EventType.COMPLAINT_RECEIVED,
            {"complaint": complaint, "created_by": created_by}
        )
        return complaint

    @staticmethod
    def update_complaint_status(complaint, new_status, user, notes=""):
        """Update complaint status."""
        old_status = complaint.status
        complaint.status = new_status
        if notes:
            complaint.resolution_notes = notes
        complaint.save()

        event_dispatcher.emit(
            EventType.COMPLAINT_STATUS_CHANGED,
            {
                "complaint": complaint,
                "old_status": old_status,
                "new_status": new_status,
                "changed_by": user
            }
        )
        return complaint

    @staticmethod
    def create_appeal(data, created_by):
        """Create a new appeal."""
        import uuid
        appeal_number = f"APP-{uuid.uuid4().hex[:8].upper()}"

        appeal = Appeal.objects.create(
            appeal_number=appeal_number,
            submitted_by=created_by,
            **data
        )

        event_dispatcher.emit(
            EventType.APPEAL_RECEIVED,
            {"appeal": appeal, "created_by": created_by}
        )
        return appeal

    @staticmethod
    def decide_appeal(appeal, decision, user, notes=""):
        """Record a decision for an appeal."""
        old_status = appeal.status
        appeal.status = "closed"  # Assuming closed after decision
        # In a real implementation, we might have specific fields for decision outcome
        # For now, we'll just use the status and notes
        appeal.resolution_notes = f"Decision: {decision}. Notes: {notes}"
        appeal.save()

        event_dispatcher.emit(
            EventType.APPEAL_DECIDED,
            {
                "appeal": appeal,
                "old_status": old_status,
                "decision": decision,
                "decided_by": user,
                "notes": notes
            }
        )
        return appeal
