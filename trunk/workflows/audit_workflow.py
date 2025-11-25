"""
Audit workflow state machine.

Sprint 8, Task 8.4: Audit Status Workflow Validation
Implements state transitions and validation rules for audit lifecycle.
"""

from django.core.exceptions import ValidationError
from django.db import transaction


class AuditWorkflow:
    """
    State machine for audit workflow with transition validation.

    Valid audit statuses and their allowed transitions:
    - draft: Initial state, audit being prepared
    - scheduled: Audit date confirmed
    - in_progress: Audit actively being conducted
    - report_draft: Audit complete, report being written
    - client_review: Report sent to client for review
    - submitted: Report submitted to CB for decision
    - decided: Final certification decision made
    - cancelled: Audit cancelled
    """

    # Define valid status transitions
    TRANSITIONS = {
        "draft": ["scheduled", "cancelled"],
        "scheduled": ["in_progress", "cancelled"],
        "in_progress": ["report_draft", "cancelled"],
        "report_draft": ["client_review", "in_progress"],  # Can go back to in_progress
        "client_review": ["submitted", "report_draft"],  # Can go back for corrections
        "submitted": ["technical_review"],
        "technical_review": ["decision_pending", "report_draft"],
        "decision_pending": ["closed", "technical_review"],
        "decided": ["closed"],  # Legacy support
        "closed": [],  # Terminal state
        "cancelled": [],  # Terminal state
    }

    # Status descriptions
    STATUS_DESCRIPTIONS = {
        "draft": "Audit is being planned and prepared",
        "scheduled": "Audit date has been scheduled",
        "in_progress": "Audit is actively being conducted on-site",
        "report_draft": "Audit complete, report is being written",
        "client_review": "Report sent to client for review and feedback",
        "submitted": "Report submitted to CB for certification decision",
        "technical_review": "Audit is undergoing technical review",
        "decision_pending": "Audit is awaiting certification decision",
        "decided": "Certification decision has been made (Legacy)",
        "closed": "Audit is closed",
        "cancelled": "Audit has been cancelled",
    }

    def __init__(self, audit):
        """Initialize workflow for given audit."""
        self.audit = audit

    def can_transition_to(self, new_status):
        """
        Check if transition to new_status is valid.

        Args:
            new_status: Target status to transition to

        Returns:
            bool: True if transition is allowed
        """
        current_status = self.audit.status
        return new_status in self.TRANSITIONS.get(current_status, [])

    def validate_transition(self, new_status):
        """
        Validate if transition is allowed and meets all requirements.

        Args:
            new_status: Target status to transition to

        Raises:
            ValidationError: If transition is not valid or requirements not met
        """
        current_status = self.audit.status

        # Check if transition is in allowed list
        if not self.can_transition_to(new_status):
            allowed = ", ".join(self.TRANSITIONS.get(current_status, []))
            raise ValidationError(
                f"Cannot transition from '{current_status}' to '{new_status}'. "
                f"Allowed transitions: {allowed or 'none (terminal state)'}"
            )

        # Validate specific transition requirements
        if new_status == "scheduled":
            self._validate_scheduled()
        elif new_status == "in_progress":
            self._validate_in_progress()
        elif new_status == "report_draft":
            self._validate_report_draft()
        elif new_status == "client_review":
            self._validate_client_review()
        elif new_status == "submitted":
            self._validate_submitted()
        elif new_status == "technical_review":
            self._validate_technical_review()
        elif new_status == "decision_pending":
            self._validate_decision_pending()
        elif new_status == "closed":
            self._validate_closed()
        elif new_status == "decided":
            self._validate_decided()

    def _validate_scheduled(self):
        """Validate transition to scheduled status."""
        if not self.audit.total_audit_date_from:
            raise ValidationError("Cannot schedule audit without audit dates.")
        if not self.audit.lead_auditor:
            raise ValidationError("Cannot schedule audit without a lead auditor assigned.")

    def _validate_in_progress(self):
        """Validate transition to in_progress status."""
        if not self.audit.lead_auditor:
            raise ValidationError("Cannot start audit without a lead auditor assigned.")
        if not self.audit.total_audit_date_from:
            raise ValidationError("Cannot start audit without audit dates.")

    def _validate_report_draft(self):
        """Validate transition to report_draft status."""
        # Must have at least one finding (NC, Observation, or OFI)
        total_findings = (
            self.audit.nonconformity_set.count()
            + self.audit.observation_set.count()
            + self.audit.opportunityforimprovement_set.count()
        )
        if total_findings == 0:
            raise ValidationError(
                "Cannot move to report draft without at least one finding. "
                "Add a nonconformity, observation, or opportunity for improvement."
            )

    def _validate_client_review(self):
        """Validate transition to client_review status."""
        # Must have completed report draft
        # Could check for AuditSummary existence here if required

    def _validate_submitted(self):
        """Validate transition to submitted status."""
        # All major NCs must have client responses
        major_ncs = self.audit.nonconformity_set.filter(category="major")
        for nc in major_ncs:
            if not nc.client_root_cause or not nc.client_corrective_action:
                raise ValidationError(
                    f"Cannot submit audit: Major NC (Clause {nc.clause}) "
                    "is missing client response. Client must respond to all major NCs."
                )

    def _validate_technical_review(self):
        """Validate transition to technical_review status."""
        # Ensure submitted requirements are met (redundant but safe)
        self._validate_submitted()

    def _validate_decision_pending(self):
        """Validate transition to decision_pending status."""
        # Technical review must exist and be approved
        if not hasattr(self.audit, "technical_review"):
            raise ValidationError("Cannot move to decision pending: Technical review is required")

        technical_review = self.audit.technical_review
        if technical_review.status != "approved":
            raise ValidationError(
                f"Cannot move to decision pending: Technical review status is '{technical_review.get_status_display()}', must be 'Approved'"
            )

    def _validate_closed(self):
        """Validate transition to closed status."""
        # Stage 2 must have decided Stage 1
        if self.audit.audit_type == "stage2":
            previous_stage1 = (
                self.audit.__class__.objects.filter(
                    organization=self.audit.organization, audit_type="stage1", status="closed"
                )
                .exclude(pk=self.audit.pk)
                .exists()
            )
            if not previous_stage1:
                # Check for legacy "decided" status too
                previous_stage1_legacy = (
                    self.audit.__class__.objects.filter(
                        organization=self.audit.organization, audit_type="stage1", status="decided"
                    )
                    .exclude(pk=self.audit.pk)
                    .exists()
                )
                if not previous_stage1_legacy:
                    raise ValidationError("Stage 2 audit requires a completed Stage 1 audit before closing.")

        # Surveillance requires active certifications
        if self.audit.audit_type == "surveillance":
            has_active_cert = self.audit.certifications.filter(certificate_status="active").exists()
            if not has_active_cert:
                raise ValidationError("Surveillance audit requires active certifications. Cannot make decision.")

        # All major NCs must be verified (not open)
        open_major_ncs = self.audit.nonconformity_set.filter(category="major", verification_status="open")
        if open_major_ncs.exists():
            nc_list = ", ".join([f"Clause {nc.clause}" for nc in open_major_ncs[:3]])
            count = open_major_ncs.count()
            raise ValidationError(
                f"Cannot make decision: {count} major NC(s) still open ({nc_list}). All must be verified."
            )

    def _validate_decided(self):
        """Validate transition to decided status."""
        # All NCs must be verified (accepted or closed)
        open_ncs = self.audit.nonconformity_set.filter(verification_status="open")
        if open_ncs.exists():
            clauses = ", ".join([nc.clause for nc in open_ncs[:5]])
            count = open_ncs.count()
            raise ValidationError(
                f"Cannot make decision: {count} nonconformit{'y' if count == 1 else 'ies'} "
                f"still open (Clauses: {clauses}). All NCs must be verified before decision."
            )

    @transaction.atomic
    def transition_to(self, new_status, _user=None, _notes=""):
        """
        Transition audit to new status with validation.

        Args:
            new_status: Target status to transition to
            user: User making the transition (for history)
            notes: Optional notes about the transition

        Raises:
            ValidationError: If transition is not valid

        Returns:
            Audit: Updated audit object
        """
        # Validate transition
        self.validate_transition(new_status)

        # Update audit status
        self.audit.status = new_status
        self.audit.save()

        # Log transition (optional - could create AuditWorkflowHistory record)
        # For now, we'll skip history logging since AuditWorkflowHistory model doesn't exist yet

        return self.audit

    def get_available_transitions(self):
        """
        Get list of valid transitions from current status.

        Returns:
            list: List of (status_code, status_label, description) tuples
        """
        current_status = self.audit.status
        available = self.TRANSITIONS.get(current_status, [])

        result = []
        for status_code in available:
            try:
                # Try validation to see if it's actually available
                self.validate_transition(status_code)
                is_available = True
                reason = None
            except ValidationError as e:
                is_available = False
                reason = str(e)

            result.append(
                {
                    "code": status_code,
                    "label": status_code.replace("_", " ").title(),
                    "description": self.STATUS_DESCRIPTIONS.get(status_code, ""),
                    "available": is_available,
                    "reason": reason,
                }
            )

        return result

    @classmethod
    def get_all_statuses(cls):
        """
        Get all valid audit statuses.

        Returns:
            list: List of (code, label, description) tuples
        """
        return [
            {
                "code": status,
                "label": status.replace("_", " ").title(),
                "description": cls.STATUS_DESCRIPTIONS.get(status, ""),
            }
            for status in cls.TRANSITIONS.keys()
        ]
