"""
Service for managing audit documentation.
"""

import logging

from django.db import transaction

from audit_management.models import AuditChanges, AuditPlanReview, AuditRecommendation, AuditSummary
from trunk.events.dispatcher import event_dispatcher
from trunk.events.types import EventType

logger = logging.getLogger(__name__)


class DocumentationService:
    """Service for managing audit documentation."""

    @staticmethod
    def update_audit_changes(audit, data, user):
        """
        Update audit changes documentation.

        Args:
            audit: The audit instance
            data: Dictionary of form data
            user: The user performing the update

        Returns:
            AuditChanges: The updated instance
        """
        with transaction.atomic():
            changes, _ = AuditChanges.objects.get_or_create(audit=audit)

            for key, value in data.items():
                setattr(changes, key, value)

            changes.save()

            event_dispatcher.emit(
                EventType.AUDIT_DOCUMENTATION_UPDATED,
                {
                    "audit_id": audit.pk,
                    "documentation_type": "changes",
                    "updated_by": user.pk,
                },
            )

            logger.info("Audit changes updated for audit %s by user %s", audit.pk, user.pk)
            return changes

    @staticmethod
    def update_audit_plan_review(audit, data, user):
        """
        Update audit plan review documentation.

        Args:
            audit: The audit instance
            data: Dictionary of form data
            user: The user performing the update

        Returns:
            AuditPlanReview: The updated instance
        """
        with transaction.atomic():
            plan_review, _ = AuditPlanReview.objects.get_or_create(audit=audit)

            for key, value in data.items():
                setattr(plan_review, key, value)

            plan_review.save()

            event_dispatcher.emit(
                EventType.AUDIT_DOCUMENTATION_UPDATED,
                {
                    "audit_id": audit.pk,
                    "documentation_type": "plan_review",
                    "updated_by": user.pk,
                },
            )

            logger.info("Audit plan review updated for audit %s by user %s", audit.pk, user.pk)
            return plan_review

    @staticmethod
    def update_audit_summary(audit, data, user):
        """
        Update audit summary documentation.

        Args:
            audit: The audit instance
            data: Dictionary of form data
            user: The user performing the update

        Returns:
            AuditSummary: The updated instance
        """
        with transaction.atomic():
            summary, _ = AuditSummary.objects.get_or_create(audit=audit)

            for key, value in data.items():
                setattr(summary, key, value)

            summary.save()

            event_dispatcher.emit(
                EventType.AUDIT_DOCUMENTATION_UPDATED,
                {
                    "audit_id": audit.pk,
                    "documentation_type": "summary",
                    "updated_by": user.pk,
                },
            )

            logger.info("Audit summary updated for audit %s by user %s", audit.pk, user.pk)
            return summary

    @staticmethod
    def update_audit_recommendation(audit, data, user):
        """
        Update audit recommendation documentation.

        Args:
            audit: The audit instance
            data: Dictionary of form data
            user: The user performing the update

        Returns:
            AuditRecommendation: The updated instance
        """
        with transaction.atomic():
            recommendation, _ = AuditRecommendation.objects.get_or_create(audit=audit)

            for key, value in data.items():
                setattr(recommendation, key, value)

            recommendation.save()

            event_dispatcher.emit(
                EventType.AUDIT_DOCUMENTATION_UPDATED,
                {
                    "audit_id": audit.pk,
                    "documentation_type": "recommendation",
                    "updated_by": user.pk,
                },
            )

            logger.info("Audit recommendation updated for audit %s by user %s", audit.pk, user.pk)
            return recommendation
