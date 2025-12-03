"""
Service for technical reviews and certification decisions.
"""

from django.core.exceptions import ValidationError
from django.db import transaction

from certification.models import CertificationDecision, TechnicalReview
from trunk.events import EventType, event_dispatcher
from trunk.services.audit_service import AuditService
from trunk.services.certificate_service import CertificateService


class ReviewService:
    """Business logic for reviews and decisions."""

    @staticmethod
    @transaction.atomic
    def conduct_technical_review(audit, reviewer, data):
        """
        Create or update a technical review.

        Args:
            audit: The audit instance.
            reviewer: The user conducting the review.
            data: Dictionary of review data.

        Returns:
            TechnicalReview: The created/updated review.
        """
        # Check if review exists
        if hasattr(audit, "technical_review"):
            review = audit.technical_review
            for key, value in data.items():
                setattr(review, key, value)
            review.save()
        else:
            review = TechnicalReview.objects.create(audit=audit, reviewer=reviewer, **data)

        # Handle workflow transition if approved
        if review.status == "approved" and audit.status == "technical_review":
            AuditService.transition_status(
                audit, "decision_pending", reviewer, notes=f"Technical review approved by {reviewer.get_full_name()}"
            )

        # Emit event
        event_type = (
            EventType.TECHNICAL_REVIEW_COMPLETED if review.status == "approved" else EventType.TECHNICAL_REVIEW_UPDATED
        )
        event_dispatcher.emit(
            event_type,
            {
                "audit_id": audit.id,
                "review_id": review.id,
                "reviewer_id": reviewer.id if reviewer else None,
            },
        )

        return review

    @staticmethod
    @transaction.atomic
    def make_certification_decision(audit, decision_maker, data):
        """
        Make a certification decision.

        Args:
            audit: The audit instance.
            decision_maker: The user making the decision.
            data: Dictionary of decision data.

        Returns:
            CertificationDecision: The created decision.
        """
        if hasattr(audit, "certification_decision"):
            raise ValidationError("Certification decision already exists for this audit.")

        # Extract M2M data
        certifications = data.pop("certifications_affected", [])

        decision = CertificationDecision.objects.create(audit=audit, decision_maker=decision_maker, **data)
        decision.certifications_affected.set(certifications)

        # Transition audit status
        AuditService.transition_status(
            audit,
            "closed",
            decision_maker,
            notes=f"Decision: {decision.get_decision_display()} by {decision_maker.get_full_name()}",
        )

        # Record certificate history
        CertificateService.record_decision(decision)

        # Emit event
        event_dispatcher.emit(
            EventType.CERTIFICATION_DECISION_MADE,
            {
                "audit_id": audit.id,
                "decision_id": decision.id,
                "maker_id": decision_maker.id if decision_maker else None,
            },
        )

        return decision

    @staticmethod
    @transaction.atomic
    def update_certification_decision(decision, decision_maker, data):
        """
        Update an existing certification decision.

        Args:
            decision: The CertificationDecision instance.
            decision_maker: The user updating the decision.
            data: Dictionary of decision data.

        Returns:
            CertificationDecision: The updated decision.
        """
        # Extract M2M data
        certifications = data.pop("certifications_affected", None)

        for key, value in data.items():
            setattr(decision, key, value)
        decision.save()

        if certifications is not None:
            decision.certifications_affected.set(certifications)

        # Emit event
        event_dispatcher.emit(
            EventType.CERTIFICATION_DECISION_UPDATED,
            {
                "audit_id": decision.audit.id,
                "decision_id": decision.id,
                "maker_id": decision_maker.id if decision_maker else None,
            },
        )

        return decision
