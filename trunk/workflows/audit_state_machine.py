"""
Audit-specific state machine that mirrors legacy rules in audits/workflows.py
while providing a reusable, modular implementation.
"""

from typing import Dict, Iterable, List, Tuple

from django.core.exceptions import ValidationError

from trunk.workflows.state_machine import StateMachine


class AuditStateMachine:
    """
    Wraps the generic StateMachine for the Audit domain object and mirrors
    permission checks and guards currently implemented in audits/workflows.py.
    """

    TRANSITIONS: Dict[str, Iterable[str]] = {
        "draft": ["scheduled", "cancelled"],
        "scheduled": ["in_progress", "cancelled"],
        "in_progress": ["report_draft", "cancelled"],
        "report_draft": ["client_review", "in_progress"],
        "client_review": ["submitted", "report_draft"],
        "submitted": ["decided"],
        "decided": [],
        "cancelled": [],
    }

    def __init__(self, audit):
        self.audit = audit
        self._sm = StateMachine(
            obj=audit,
            get_state=lambda a: a.status,
            set_state=self._set_state,
            transitions=self.TRANSITIONS,
            permission_checker=self._permission_checker,
            guards=self._guards(),
            get_status_label=self._get_status_label,
        )

    # ----- Public API -----
    def can_transition(self, to_state: str, user) -> Tuple[bool, str]:
        return self._sm.can_transition(to_state, user)

    def transition(self, to_state: str, user, notes: str = ""):
        ok, reason = self.can_transition(to_state, user)
        if not ok:
            raise ValidationError(reason)
        old_status = self.audit.status
        self._sm.transition(to_state, user)
        # Create audit status log entry (preserve legacy behavior)
        from audits.models import AuditStatusLog

        AuditStatusLog.objects.create(
            audit=self.audit,
            from_status=old_status,
            to_status=to_state,
            changed_by=user,
            notes=notes or "",
        )
        return self.audit

    def available_transitions(self, user) -> List[Tuple[str, str]]:
        return self._sm.available_transitions(user)

    # ----- Internal helpers -----
    def _set_state(self, audit, new_status: str) -> None:
        audit.status = new_status
        audit.save()

    def _get_status_label(self, status_code: str) -> str:
        return dict(self.audit.STATUS_CHOICES).get(status_code, status_code)

    def _permission_checker(self, user, from_state: str, to_state: str) -> bool:
        # CB Admin can make any transition (with override capability)
        if user.groups.filter(name="cb_admin").exists():
            return True

        # draft → scheduled: Lead Auditor only
        if from_state == "draft" and to_state == "scheduled":
            return user.groups.filter(name="lead_auditor").exists() and self.audit.lead_auditor == user

        # scheduled → in_progress: Lead Auditor only
        if from_state == "scheduled" and to_state == "in_progress":
            return user.groups.filter(name="lead_auditor").exists() and self.audit.lead_auditor == user

        # in_progress → report_draft: Lead Auditor only
        if from_state == "in_progress" and to_state == "report_draft":
            return user.groups.filter(name="lead_auditor").exists() and self.audit.lead_auditor == user

        # report_draft → client_review: Lead Auditor or CB Admin
        if from_state == "report_draft" and to_state == "client_review":
            return user.groups.filter(name="cb_admin").exists() or (
                user.groups.filter(name="lead_auditor").exists() and self.audit.lead_auditor == user
            )

        # report_draft → in_progress: Lead Auditor (going back for more findings)
        if from_state == "report_draft" and to_state == "in_progress":
            return user.groups.filter(name="lead_auditor").exists() and self.audit.lead_auditor == user

        # client_review → submitted: CB Admin or Lead Auditor (after client feedback)
        if from_state == "client_review" and to_state == "submitted":
            return user.groups.filter(name="cb_admin").exists() or (
                user.groups.filter(name="lead_auditor").exists() and self.audit.lead_auditor == user
            )

        # client_review → report_draft: Lead Auditor (back for corrections)
        if from_state == "client_review" and to_state == "report_draft":
            return user.groups.filter(name="lead_auditor").exists() and self.audit.lead_auditor == user

        # submitted → decided: CB Decision Maker or CB Admin
        if from_state == "submitted" and to_state == "decided":
            return user.groups.filter(name="decision_maker").exists() or user.groups.filter(name="cb_admin").exists()

        # Any state → cancelled: CB Admin only (handled above)
        if to_state == "cancelled":
            return user.groups.filter(name="cb_admin").exists()

        return False

    def _guards(self):
        def guard_draft_to_scheduled(_from: str, _to: str):
            if not self.audit.lead_auditor:
                return False, "Cannot schedule audit: Lead auditor must be assigned"
            if not self.audit.total_audit_date_from:
                return False, "Cannot schedule audit: Audit date must be set"
            return True, "Validation passed"

        def guard_in_progress_to_report_draft(_from: str, _to: str):
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
            return True, "Validation passed"

        def guard_client_review_to_submitted(_from: str, _to: str):
            # Technical review must exist and be approved
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

            # Major NCs must have client responses
            major_ncs = self.audit.nonconformity_set.filter(category="major")
            for nc in major_ncs:
                if not nc.client_root_cause or not nc.client_corrective_action:
                    return (
                        False,
                        f"Cannot submit audit: Major NC (Clause {nc.clause}) is missing client response",
                    )
            return True, "Validation passed"

        def guard_submitted_to_decided(_from: str, _to: str):
            # Stage 2 must have decided Stage 1
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

            # Surveillance requires active certifications
            if self.audit.audit_type == "surveillance":
                has_active_cert = self.audit.certifications.filter(certificate_status="active").exists()
                if not has_active_cert:
                    return (
                        False,
                        "Surveillance audit requires active certifications. Cannot make decision.",
                    )

            # All major NCs must be verified (not open)
            open_major_ncs = self.audit.nonconformity_set.filter(category="major", verification_status="open")
            if open_major_ncs.exists():
                nc_list = ", ".join([f"Clause {nc.clause}" for nc in open_major_ncs[:3]])
                count = open_major_ncs.count()
                return (
                    False,
                    f"Cannot make decision: {count} major NC(s) still open ({nc_list}). All must be verified.",
                )
            return True, "Validation passed"

        return {
            ("draft", "scheduled"): [guard_draft_to_scheduled],
            ("in_progress", "report_draft"): [guard_in_progress_to_report_draft],
            ("client_review", "submitted"): [guard_client_review_to_submitted],
            ("submitted", "decided"): [guard_submitted_to_decided],
        }
