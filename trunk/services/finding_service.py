from django.core.exceptions import ValidationError
from django.utils import timezone

from audits.models import Nonconformity, Observation, OpportunityForImprovement
from trunk.events import EventType, event_dispatcher


class FindingService:
    """
    Service for managing audit findings (Nonconformities, Observations, OFIs).
    Handles creation, updates, and status transitions.
    """

    @staticmethod
    def create_nonconformity(audit, user, data):
        """Create a new nonconformity."""
        nc = Nonconformity(audit=audit, created_by=user, verification_status="open", **data)
        nc.save()

        # Emit finding created event
        event_dispatcher.emit(
            EventType.FINDING_CREATED,
            {"finding": nc, "finding_type": "nonconformity", "audit": audit, "created_by": user},
        )

        return nc

    @staticmethod
    def create_observation(audit, user, data):
        """Create a new observation."""
        obs = Observation(audit=audit, created_by=user, **data)
        obs.save()

        # Emit finding created event
        event_dispatcher.emit(
            EventType.FINDING_CREATED,
            {"finding": obs, "finding_type": "observation", "audit": audit, "created_by": user},
        )

        return obs

    @staticmethod
    def create_ofi(audit, user, data):
        """Create a new opportunity for improvement."""
        ofi = OpportunityForImprovement(audit=audit, created_by=user, **data)
        ofi.save()

        # Emit finding created event
        event_dispatcher.emit(
            EventType.FINDING_CREATED, {"finding": ofi, "finding_type": "ofi", "audit": audit, "created_by": user}
        )

        return ofi

    @staticmethod
    def respond_to_nonconformity(nc, response_data):
        """
        Handle client response to a nonconformity.

        Args:
            nc: Nonconformity instance
            response_data: Dict containing client response fields
        """
        for field, value in response_data.items():
            setattr(nc, field, value)

        nc.verification_status = "client_responded"
        nc.save()

        # Emit client response event
        event_dispatcher.emit(
            EventType.NC_CLIENT_RESPONDED, {"nonconformity": nc, "audit": nc.audit, "response_data": response_data}
        )

        return nc

    @staticmethod
    def verify_nonconformity(nc, user, action, notes=None):
        """
        Handle auditor verification of a nonconformity.

        Args:
            nc: Nonconformity instance
            user: User performing verification
            action: 'accept', 'request_changes', or 'close'
            notes: Optional verification notes
        """
        if notes:
            nc.verification_notes = notes

        if action == "accept":
            nc.verification_status = "accepted"
            nc.verified_by = user
            nc.verified_at = timezone.now()

            # Emit verification accepted event
            event_dispatcher.emit(
                EventType.NC_VERIFIED_ACCEPTED, {"nonconformity": nc, "verified_by": user, "notes": notes}
            )

        elif action == "request_changes":
            nc.verification_status = "open"

            # Emit verification rejected event
            event_dispatcher.emit(
                EventType.NC_VERIFIED_REJECTED, {"nonconformity": nc, "verified_by": user, "notes": notes}
            )

        elif action == "close":
            if nc.verification_status != "accepted":
                raise ValidationError("Cannot close nonconformity that hasn't been accepted.")
            nc.verification_status = "closed"

            # Emit NC closed event
            event_dispatcher.emit(EventType.NC_CLOSED, {"nonconformity": nc, "closed_by": user})

        nc.save()
        return nc

    @staticmethod
    def update_nonconformity(nc, data, user=None):
        """
        Update an existing nonconformity.

        Args:
            nc: Nonconformity instance
            data: Dictionary of fields to update
            user: User performing the update (optional)
        """
        for field, value in data.items():
            setattr(nc, field, value)
        nc.save()

        # Emit finding updated event
        event_dispatcher.emit(
            EventType.FINDING_UPDATED,
            {"finding": nc, "finding_type": "nonconformity", "audit": nc.audit, "updated_by": user},
        )
        return nc

    @staticmethod
    def update_observation(observation, data, user=None):
        """
        Update an existing observation.

        Args:
            observation: Observation instance
            data: Dictionary of fields to update
            user: User performing the update (optional)
        """
        for field, value in data.items():
            setattr(observation, field, value)
        observation.save()

        # Emit finding updated event
        event_dispatcher.emit(
            EventType.FINDING_UPDATED,
            {"finding": observation, "finding_type": "observation", "audit": observation.audit, "updated_by": user},
        )
        return observation

    @staticmethod
    def update_ofi(ofi, data, user=None):
        """
        Update an existing opportunity for improvement.

        Args:
            ofi: OpportunityForImprovement instance
            data: Dictionary of fields to update
            user: User performing the update (optional)
        """
        for field, value in data.items():
            setattr(ofi, field, value)
        ofi.save()

        # Emit finding updated event
        event_dispatcher.emit(
            EventType.FINDING_UPDATED,
            {"finding": ofi, "finding_type": "ofi", "audit": ofi.audit, "updated_by": user},
        )
        return ofi

    @staticmethod
    def delete_finding(finding, user=None):
        """
        Delete a finding.

        Args:
            finding: The finding instance (NC, Observation, or OFI)
            user: User performing the deletion (optional)
        """
        audit = finding.audit
        finding_type = finding.__class__.__name__.lower()

        finding.delete()

        event_dispatcher.emit(
            EventType.FINDING_DELETED,
            {"finding_type": finding_type, "audit": audit, "deleted_by": user},
        )
