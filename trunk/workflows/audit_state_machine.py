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
        "submitted": ["technical_review"],
        "technical_review": ["decision_pending", "report_draft"],
        "decision_pending": ["closed", "technical_review"],
        "decided": ["closed"],
        "closed": [],
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
        from trunk.permissions.policies import PBACPolicy
        from trunk.permissions.predicates import PermissionPredicate

        # CB Admin can make any transition (with override capability)
        if PermissionPredicate.is_cb_admin(user):
            return True

        # draft → scheduled: Lead Auditor only
        if from_state == "draft" and to_state == "scheduled":
            ok, _ = PBACPolicy.is_assigned_to_audit(user, self.audit)
            return PermissionPredicate.is_lead_auditor(user) and self.audit.lead_auditor == user and ok

        # scheduled → in_progress: Lead Auditor only
        if from_state == "scheduled" and to_state == "in_progress":
            ok, _ = PBACPolicy.is_assigned_to_audit(user, self.audit)
            return PermissionPredicate.is_lead_auditor(user) and self.audit.lead_auditor == user and ok

        # in_progress → report_draft: Lead Auditor only
        if from_state == "in_progress" and to_state == "report_draft":
            ok, _ = PBACPolicy.is_assigned_to_audit(user, self.audit)
            return PermissionPredicate.is_lead_auditor(user) and self.audit.lead_auditor == user and ok

        # report_draft → client_review: Lead Auditor or CB Admin
        if from_state == "report_draft" and to_state == "client_review":
            if PermissionPredicate.is_cb_admin(user):
                return True
            ok, _ = PBACPolicy.is_assigned_to_audit(user, self.audit)
            return PermissionPredicate.is_lead_auditor(user) and self.audit.lead_auditor == user and ok

        # report_draft → in_progress: Lead Auditor (going back for more findings)
        if from_state == "report_draft" and to_state == "in_progress":
            ok, _ = PBACPolicy.is_assigned_to_audit(user, self.audit)
            return PermissionPredicate.is_lead_auditor(user) and self.audit.lead_auditor == user and ok

        # client_review → submitted: CB Admin or Lead Auditor (after client feedback)
        if from_state == "client_review" and to_state == "submitted":
            if PermissionPredicate.is_cb_admin(user):
                return True
            ok, _ = PBACPolicy.is_assigned_to_audit(user, self.audit)
            return PermissionPredicate.is_lead_auditor(user) and self.audit.lead_auditor == user and ok

        # client_review → report_draft: Lead Auditor (back for corrections)
        if from_state == "client_review" and to_state == "report_draft":
            ok, _ = PBACPolicy.is_assigned_to_audit(user, self.audit)
            return PermissionPredicate.is_lead_auditor(user) and self.audit.lead_auditor == user and ok

        # submitted → technical_review: CB Admin or Technical Reviewer
        if from_state == "submitted" and to_state == "technical_review":
            return PermissionPredicate.can_conduct_technical_review(user)

        # technical_review → decision_pending: CB Admin or Technical Reviewer
        if from_state == "technical_review" and to_state == "decision_pending":
            return PermissionPredicate.can_conduct_technical_review(user)

        # decision_pending → closed: CB Decision Maker or CB Admin
        if from_state == "decision_pending" and to_state == "closed":
            if PermissionPredicate.is_decision_maker(user):
                ok, _ = PBACPolicy.is_independent_for_decision(user, self.audit)
                return ok
            return PermissionPredicate.is_cb_admin(user)

        # Any state → cancelled: CB Admin only (handled above)
        if to_state == "cancelled":
            return PermissionPredicate.is_cb_admin(user)

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
            # Major NCs must have client responses
            major_ncs = self.audit.nonconformity_set.filter(category="major")
            for nc in major_ncs:
                if not nc.client_root_cause or not nc.client_corrective_action:
                    return (
                        False,
                        f"Cannot submit audit: Major NC (Clause {nc.clause}) is missing client response",
                    )
            return True, "Validation passed"

        def guard_technical_review_to_decision_pending(_from: str, _to: str):
            # Technical review must exist and be approved
            if not hasattr(self.audit, "technical_review"):
                return (
                    False,
                    "Cannot move to decision pending: Technical review is required",
                )
            technical_review = self.audit.technical_review
            if technical_review.status != "approved":
                return (
                    False,
                    f"Cannot move to decision pending: Technical review status is '{technical_review.get_status_display()}', must be 'Approved'",
                )
            return True, "Validation passed"

        def guard_decision_pending_to_closed(_from: str, _to: str):
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
                    return (
                        False,
                        "Stage 2 audit requires a completed Stage 1 audit before closing.",
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
            ("technical_review", "decision_pending"): [guard_technical_review_to_decision_pending],
            ("decision_pending", "closed"): [guard_decision_pending_to_closed],
        }
