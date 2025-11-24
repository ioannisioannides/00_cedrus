"""
Audit workflow management - handles status transitions and validation.

This module implements the state machine for audit status transitions,
ensuring business rules are enforced and invalid transitions are blocked.
"""

from django.core.exceptions import ValidationError
from django.utils import timezone


class AuditWorkflow:
    """
    Manages audit status transitions and workflow validation.

    Status flow (ISO 17021-1:2015 compliant):
    draft → scheduled → in_progress → report_draft → client_review → submitted → decided

    NOTE: This is the legacy workflow. New code should use trunk.workflows.audit_workflow
    """

    # Valid transitions: (from_status, to_status)
    VALID_TRANSITIONS = {
        "draft": ["scheduled", "cancelled"],
        "scheduled": ["in_progress", "cancelled"],
        "in_progress": ["report_draft", "cancelled"],
        "report_draft": ["client_review", "in_progress"],  # Can go back to in_progress
        "client_review": ["submitted", "report_draft"],  # Can go back for corrections
        "submitted": ["decided"],
        "decided": [],  # Final state
        "cancelled": [],  # Final state
    }

    def __init__(self, audit):
        self.audit = audit
        self.current_status = audit.status

    def can_transition(self, new_status, user):
        """
        Check if the transition from current status to new_status is allowed.

        Args:
            new_status: Target status
            user: User attempting the transition

        Returns:
            tuple: (allowed: bool, reason: str)
        """
        # Check if transition is in valid transitions
        if new_status not in self.VALID_TRANSITIONS.get(self.current_status, []):
            return False, f"Invalid transition from '{self.current_status}' to '{new_status}'"

        # Check role-based permissions
        if not self._can_user_transition(user, new_status):
            return False, "You do not have permission to perform this transition"

        # Check business rules
        validation_result = self._validate_transition(new_status, user)
        if not validation_result[0]:
            return False, validation_result[1]

        return True, "Transition allowed"

    def _can_user_transition(self, user, new_status):
        """Check if user has permission to make this transition."""
        # CB Admin can make any transition (with override capability)
        if user.groups.filter(name="cb_admin").exists():
            return True

        # draft → scheduled: Lead Auditor only
        if self.current_status == "draft" and new_status == "scheduled":
            return (
                user.groups.filter(name="lead_auditor").exists() and self.audit.lead_auditor == user
            )

        # scheduled → in_progress: Lead Auditor only
        if self.current_status == "scheduled" and new_status == "in_progress":
            return (
                user.groups.filter(name="lead_auditor").exists() and self.audit.lead_auditor == user
            )

        # in_progress → report_draft: Lead Auditor only
        if self.current_status == "in_progress" and new_status == "report_draft":
            return (
                user.groups.filter(name="lead_auditor").exists() and self.audit.lead_auditor == user
            )

        # report_draft → client_review: Lead Auditor or CB Admin
        if self.current_status == "report_draft" and new_status == "client_review":
            return user.groups.filter(name="cb_admin").exists() or (
                user.groups.filter(name="lead_auditor").exists() and self.audit.lead_auditor == user
            )

        # report_draft → in_progress: Lead Auditor (going back for more findings)
        if self.current_status == "report_draft" and new_status == "in_progress":
            return (
                user.groups.filter(name="lead_auditor").exists() and self.audit.lead_auditor == user
            )

        # client_review → submitted: CB Admin or Lead Auditor (after client feedback)
        if self.current_status == "client_review" and new_status == "submitted":
            return user.groups.filter(name="cb_admin").exists() or (
                user.groups.filter(name="lead_auditor").exists() and self.audit.lead_auditor == user
            )

        # client_review → report_draft: Lead Auditor (back for corrections)
        if self.current_status == "client_review" and new_status == "report_draft":
            return (
                user.groups.filter(name="lead_auditor").exists() and self.audit.lead_auditor == user
            )

        # submitted → decided: CB Decision Maker or CB Admin
        if self.current_status == "submitted" and new_status == "decided":
            return (
                user.groups.filter(name="decision_maker").exists()
                or user.groups.filter(name="cb_admin").exists()
            )

        # Any status → cancelled: CB Admin only
        if new_status == "cancelled":
            return user.groups.filter(name="cb_admin").exists()

        return False

    def _validate_transition(self, new_status, user):
        """
        Validate business rules for the transition.

        Returns:
            tuple: (valid: bool, reason: str)
        """
        # draft → scheduled: Check lead auditor assigned
        if self.current_status == "draft" and new_status == "scheduled":
            if not self.audit.lead_auditor:
                return False, "Cannot schedule audit: Lead auditor must be assigned"
            if not self.audit.total_audit_date_from:
                return False, "Cannot schedule audit: Audit date must be set"

        # in_progress → report_draft: Check at least one finding exists
        if self.current_status == "in_progress" and new_status == "report_draft":
            total_findings = (
                self.audit.nonconformity_set.count()
                + self.audit.observation_set.count()
                + self.audit.opportunityforimprovement_set.count()
            )
            if total_findings == 0:
                return (
                    False,
                    "Cannot move to report draft: At least one finding (NC, Observation, or OFI) is required",
                )

        # report_draft → client_review: Check all major NCs are closed or have responses
        # (Don't send incomplete reports to clients)
        if self.current_status == "report_draft" and new_status == "client_review":
            major_ncs = self.audit.nonconformity_set.filter(category="major")
            open_major_ncs = major_ncs.filter(verification_status="open")
            
            if open_major_ncs.exists():
                return (
                    False,
                    f"Cannot send to client: {open_major_ncs.count()} open major nonconformity(ies) must be addressed or have client responses",
                )

        # client_review → submitted: Check all major NCs have client responses
        # AND check that technical review is approved (ISO 17021-1 Clause 9.5)
        if self.current_status == "client_review" and new_status == "submitted":
            # Check technical review exists and is approved
            if not hasattr(self.audit, "technical_review"):
                return (
                    False,
                    "Cannot submit audit: Technical review is required before submission (ISO 17021-1 Clause 9.5)",
                )
            
            technical_review = self.audit.technical_review
            if technical_review.status != "approved":
                return (
                    False,
                    f"Cannot submit audit: Technical review status is '{technical_review.get_status_display()}', must be 'Approved'",
                )
            
            major_ncs = self.audit.nonconformity_set.filter(category="major")

            for nc in major_ncs:
                if not nc.client_root_cause or not nc.client_corrective_action:
                    return (
                        False,
                        f"Cannot submit audit: Major NC (Clause {nc.clause}) is missing client response",
                    )

        # submitted → decided: Check audit requirements
        if self.current_status == "submitted" and new_status == "decided":
            # Validate audit sequence for Stage 2
            if self.audit.audit_type == "stage2":
                previous_stage1 = (
                    self.audit.__class__.objects.filter(
                        organization=self.audit.organization, audit_type="stage1", status="decided"
                    )
                    .exclude(pk=self.audit.pk)
                    .exists()
                )

                if not previous_stage1:
                    return (
                        False,
                        "Stage 2 audit requires a completed Stage 1 audit. Cannot make decision.",
                    )

            # Validate surveillance audits have active certifications
            if self.audit.audit_type == "surveillance":
                has_active_cert = self.audit.certifications.filter(
                    certificate_status="active"
                ).exists()

                if not has_active_cert:
                    return (
                        False,
                        "Surveillance audit requires active certifications. Cannot make decision.",
                    )

            # Check that all major NCs are verified
            open_major_ncs = self.audit.nonconformity_set.filter(
                category="major", verification_status="open"
            )

            if open_major_ncs.exists():
                nc_list = ", ".join([f"Clause {nc.clause}" for nc in open_major_ncs[:3]])
                count = open_major_ncs.count()
                return (
                    False,
                    f"Cannot make decision: {count} major NC(s) still open ({nc_list}). All must be verified.",
                )

        return True, "Validation passed"

    def transition(self, new_status, user, notes=None):
        """
        Perform the status transition.

        Args:
            new_status: Target status
            user: User making the transition
            notes: Optional notes about the transition

        Returns:
            Audit: Updated audit instance

        Raises:
            ValidationError: If transition is not allowed
        """
        allowed, reason = self.can_transition(new_status, user)
        if not allowed:
            raise ValidationError(reason)

        old_status = self.audit.status
        self.audit.status = new_status
        self.audit.save()

        # Create audit status log entry
        from audits.models import AuditStatusLog

        AuditStatusLog.objects.create(
            audit=self.audit,
            from_status=old_status,
            to_status=new_status,
            changed_by=user,
            notes=notes or "",
        )

        return self.audit

    def get_available_transitions(self, user):
        """
        Get list of available status transitions for the current user.

        Returns:
            list: List of (status_code, status_display) tuples
        """
        available = []
        valid_targets = self.VALID_TRANSITIONS.get(self.current_status, [])

        for target_status in valid_targets:
            if self._can_user_transition(user, target_status):
                # Get display name
                status_choices = dict(self.audit.STATUS_CHOICES)
                available.append((target_status, status_choices.get(target_status, target_status)))

        return available
