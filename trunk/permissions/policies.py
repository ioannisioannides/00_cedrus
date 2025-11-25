"""
Policy-based access control (PBAC) for audit workflows.

Implements policy checks for ISO 17021-1 compliance:
- Independence of decision (9.6): Decision maker cannot be involved in the audit
- Scoping by organization: Users may only operate on audits for their assigned organization
- Audit team scoping: Auditors may only transition audits they are assigned to
"""


class PBACPolicy:
    """Policy-based access control checks for audit workflows."""

    @staticmethod
    def is_independent_for_decision(user, audit) -> tuple[bool, str]:
        """
        Verify decision maker has independence from the audit (ISO 17021-1 Clause 9.6).

        Decision maker must NOT be:
        - Lead auditor for this audit
        - Team member for this audit
        - Technical reviewer for this audit

        CB Admin can override with documented justification.
        """
        # CB Admin bypass: can always make decision (with justification requirement enforced at UI level)
        from trunk.permissions.predicates import PermissionPredicate

        if PermissionPredicate.is_cb_admin(user):
            return True, "CB Admin override"

        # Check if decision maker was involved in the audit
        if audit.lead_auditor == user:
            return (
                False,
                "Decision maker cannot be the lead auditor for the audit (ISO 17021-1 Clause 9.6)",
            )

        if audit.team_members.filter(user=user).exists():
            return (
                False,
                "Decision maker cannot be a team member for the audit (ISO 17021-1 Clause 9.6)",
            )

        if hasattr(audit, "technical_review") and audit.technical_review.reviewer == user:
            return (
                False,
                "Decision maker cannot be the technical reviewer for the audit (ISO 17021-1 Clause 9.6)",
            )

        return True, "Decision maker has independence from the audit"

    @staticmethod
    def can_user_access_organization(user, audit) -> tuple[bool, str]:
        """
        Check if user can access audits for this organization.

        - CB Admin: can access all organizations
        - Auditors: can access all organizations (they work for the CB)
        - Client users: can only access their own organization
        """
        from trunk.permissions.predicates import PermissionPredicate

        if PermissionPredicate.is_cb_admin(user):
            return True, "CB Admin can access all organizations"

        if PermissionPredicate.is_auditor(user):
            return True, "Auditors can access all organizations"

        # Client users can only access their own organization
        if PermissionPredicate.is_client_user(user):
            if hasattr(user, "profile") and user.profile.organization == audit.organization:
                return True, "User belongs to this organization"
            return False, "Client users can only access audits for their own organization"

        return False, "User does not have permission to access this organization"

    @staticmethod
    def is_assigned_to_audit(user, audit) -> tuple[bool, str]:
        """
        Check if user is assigned to the audit (lead auditor or team member).

        Used for auditor-level permissions (not CB Admin).
        """
        from trunk.permissions.predicates import PermissionPredicate

        if PermissionPredicate.is_cb_admin(user):
            return True, "CB Admin can access all audits"

        if audit.lead_auditor == user:
            return True, "User is the lead auditor"

        if audit.team_members.filter(user=user).exists():
            return True, "User is a team member"

        return False, "User is not assigned to this audit"

    @staticmethod
    def can_conduct_technical_review(user, audit) -> tuple[bool, str]:
        """
        Check if user can conduct technical review for this audit.

        Must be technical reviewer or CB Admin, and must NOT be:
        - Lead auditor for this audit
        - Team member for this audit
        """
        from trunk.permissions.predicates import PermissionPredicate

        if not (PermissionPredicate.is_technical_reviewer(user) or PermissionPredicate.is_cb_admin(user)):
            return False, "User must be a technical reviewer or CB Admin"

        # Check independence
        if audit.lead_auditor == user:
            return False, "Technical reviewer cannot be the lead auditor"

        if audit.team_members.filter(user=user).exists():
            return False, "Technical reviewer cannot be a team member"

        return True, "User can conduct technical review"

    @staticmethod
    def can_make_certification_decision(user, audit) -> tuple[bool, str]:
        """
        Check if user can make a certification decision for this audit.

        Must be decision maker or CB Admin, and must have independence.
        """
        from trunk.permissions.predicates import PermissionPredicate

        if not (PermissionPredicate.is_decision_maker(user) or PermissionPredicate.is_cb_admin(user)):
            return False, "User must be a decision maker or CB Admin"

        # Check independence
        return PBACPolicy.is_independent_for_decision(user, audit)
