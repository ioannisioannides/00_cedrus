from django.core.exceptions import ValidationError
from django.db import transaction

from audit_management.application.schemas import (
    AuditChangesDTO,
    AuditCreateDTO,
    AuditPlanReviewDTO,
    AuditRecommendationDTO,
    AuditSummaryDTO,
    AuditUpdateDTO,
    EvidenceUploadDTO,
)
from audit_management.models import (
    Audit,
    AuditChanges,
    AuditPlanReview,
    AuditRecommendation,
    AuditSummary,
    EvidenceFile,
    Nonconformity,
)
from core.models import Certification, Organization, Site
from trunk.events import EventType, event_dispatcher
from trunk.workflows.audit_state_machine import AuditStateMachine


class AuditService:
    """
    Application Service for Audit operations.
    Uses Pydantic DTOs for input/output boundaries.
    """

    @staticmethod
    @transaction.atomic
    def create_audit(data: AuditCreateDTO, created_by) -> Audit:
        """
        Create a new audit.
        """
        # 1. Fetch related objects
        try:
            organization = Organization.objects.get(id=data.organization_id)
        except Organization.DoesNotExist as err:
            raise ValidationError(f"Organization with id {data.organization_id} does not exist.") from err

        certifications = Certification.objects.filter(id__in=data.certification_ids)
        if len(certifications) != len(data.certification_ids):
            raise ValidationError("One or more certifications not found.")

        sites = Site.objects.filter(id__in=data.site_ids)
        if len(sites) != len(data.site_ids):
            raise ValidationError("One or more sites not found.")

        # 2. Prepare creation data
        audit_kwargs = data.model_dump(exclude={"certification_ids", "site_ids", "organization_id"})

        if not audit_kwargs.get("lead_auditor_id"):
            audit_kwargs["lead_auditor_id"] = created_by.id

        # 3. Create Audit
        audit = Audit.objects.create(organization=organization, created_by=created_by, **audit_kwargs)

        # 4. Set M2M relationships
        audit.certifications.set(certifications)
        audit.sites.set(sites)

        # 5. Emit Event
        event_dispatcher.emit(EventType.AUDIT_CREATED, {"audit_id": audit.id, "created_by_id": created_by.id})

        return audit

    @staticmethod
    @transaction.atomic
    def update_audit(audit: Audit, data: AuditUpdateDTO, user) -> Audit:
        """
        Update an existing audit.
        """
        old_status = audit.status
        update_data = data.model_dump(exclude_unset=True)

        # Handle M2M fields separately
        cert_ids = update_data.pop("certification_ids", None)
        site_ids = update_data.pop("site_ids", None)

        # Update simple fields
        for key, value in update_data.items():
            setattr(audit, key, value)

        audit.save()

        # Update M2M fields if provided
        if cert_ids is not None:
            certifications = Certification.objects.filter(id__in=cert_ids)
            audit.certifications.set(certifications)

        if site_ids is not None:
            sites = Site.objects.filter(id__in=site_ids)
            audit.sites.set(sites)

        # Emit events
        event_dispatcher.emit(
            EventType.AUDIT_UPDATED, {"audit_id": audit.id, "old_status": old_status, "new_status": audit.status}
        )

        if old_status != audit.status:
            event_dispatcher.emit(
                EventType.AUDIT_STATUS_CHANGED,
                {"audit_id": audit.id, "old_status": old_status, "new_status": audit.status, "changed_by_id": user.id},
            )

        return audit

    @staticmethod
    def transition_status(audit: Audit, new_status: str, user, notes: str = "") -> Audit:
        """
        Transition audit status using the state machine.
        """
        sm = AuditStateMachine(audit)
        old_status = audit.status
        audit = sm.transition(new_status, user, notes)

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


class DocumentationService:
    """
    Application Service for Audit Documentation operations.
    Handles Changes, Plan Review, Summary, and Recommendations.
    """

    @staticmethod
    @transaction.atomic
    def update_audit_changes(audit: Audit, data: AuditChangesDTO) -> AuditChanges:
        """Update or create Audit Changes documentation."""
        changes, _ = AuditChanges.objects.get_or_create(audit=audit)

        for key, value in data.model_dump().items():
            setattr(changes, key, value)

        changes.save()

        event_dispatcher.emit(EventType.AUDIT_DOCUMENTATION_UPDATED, {"audit_id": audit.id, "doc_type": "changes"})
        return changes

    @staticmethod
    @transaction.atomic
    def update_audit_plan_review(audit: Audit, data: AuditPlanReviewDTO) -> AuditPlanReview:
        """Update or create Audit Plan Review documentation."""
        review, _ = AuditPlanReview.objects.get_or_create(audit=audit)

        for key, value in data.model_dump().items():
            setattr(review, key, value)

        review.save()

        event_dispatcher.emit(EventType.AUDIT_DOCUMENTATION_UPDATED, {"audit_id": audit.id, "doc_type": "plan_review"})
        return review

    @staticmethod
    @transaction.atomic
    def update_audit_summary(audit: Audit, data: AuditSummaryDTO) -> AuditSummary:
        """Update or create Audit Summary documentation."""
        summary, _ = AuditSummary.objects.get_or_create(audit=audit)

        for key, value in data.model_dump().items():
            setattr(summary, key, value)

        summary.save()

        event_dispatcher.emit(EventType.AUDIT_DOCUMENTATION_UPDATED, {"audit_id": audit.id, "doc_type": "summary"})
        return summary

    @staticmethod
    @transaction.atomic
    def update_audit_recommendation(audit: Audit, data: AuditRecommendationDTO) -> AuditRecommendation:
        """Update or create Audit Recommendation documentation."""
        recommendation, _ = AuditRecommendation.objects.get_or_create(audit=audit)

        for key, value in data.model_dump().items():
            setattr(recommendation, key, value)

        recommendation.save()

        event_dispatcher.emit(
            EventType.AUDIT_DOCUMENTATION_UPDATED, {"audit_id": audit.id, "doc_type": "recommendation"}
        )
        return recommendation


class EvidenceService:
    """
    Application Service for Evidence File operations.
    """

    @staticmethod
    @transaction.atomic
    def upload_evidence(audit: Audit, user, data: EvidenceUploadDTO) -> EvidenceFile:
        """
        Upload an evidence file.
        """
        finding = None
        if data.finding_id:
            try:
                finding = Nonconformity.objects.get(id=data.finding_id, audit=audit)
            except Nonconformity.DoesNotExist:
                raise ValidationError(f"Nonconformity with id {data.finding_id} not found in this audit.")

        evidence = EvidenceFile(
            audit=audit,
            uploaded_by=user,
            finding=finding,
            file=data.file,
            evidence_type=data.evidence_type,
            description=data.description,
        )
        evidence.full_clean()  # Validates file size/type via model clean()
        evidence.save()

        # Emit event
        event_dispatcher.emit(
            EventType.EVIDENCE_UPLOADED, {"audit_id": audit.id, "evidence_id": evidence.id, "uploaded_by_id": user.id}
        )

        return evidence

    @staticmethod
    @transaction.atomic
    def delete_evidence(evidence_file: EvidenceFile, user):
        """
        Delete an evidence file.
        """
        audit = evidence_file.audit
        filename = evidence_file.file.name
        evidence_id = evidence_file.id

        # Delete physical file and record
        evidence_file.file.delete()
        evidence_file.delete()

        # Emit event
        event_dispatcher.emit(
            EventType.EVIDENCE_DELETED,
            {"audit_id": audit.id, "evidence_id": evidence_id, "filename": filename, "deleted_by_id": user.id},
        )
