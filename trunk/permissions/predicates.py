class PermissionPredicate:
    """Centralized permission checking for role-based access control."""

    @staticmethod
    def is_cb_admin(user):
        """Check if user is a Certification Body Administrator."""
        return user.groups.filter(name="cb_admin").exists()

    @staticmethod
    def is_lead_auditor(user):
        """Check if user is a Lead Auditor."""
        return user.groups.filter(name="lead_auditor").exists()

    @staticmethod
    def is_auditor(user):
        """Check if user is an Auditor or Lead Auditor."""
        return user.groups.filter(name__in=["lead_auditor", "auditor"]).exists()

    @staticmethod
    def is_client_user(user):
        """Check if user is a Client Administrator or Client User."""
        return user.groups.filter(name__in=["client_admin", "client_user"]).exists()

    @staticmethod
    def is_technical_reviewer(user):
        """Check if user can conduct technical reviews (ISO 17021 Clause 9.5)"""
        return user.groups.filter(name="technical_reviewer").exists()

    @staticmethod
    def is_decision_maker(user):
        """Check if user can make certification decisions (ISO 17021 Clause 9.6)"""
        return user.groups.filter(name="decision_maker").exists()

    @staticmethod
    def can_conduct_technical_review(user):
        """
        Check if user can conduct technical reviews.
        Technical reviewers or CB admins can conduct reviews.
        """
        return PermissionPredicate.is_technical_reviewer(user) or PermissionPredicate.is_cb_admin(user)

    @staticmethod
    def can_make_certification_decision(user):
        """
        Check if user can make certification decisions.
        Decision makers or CB admins can make decisions.
        """
        return PermissionPredicate.is_decision_maker(user) or PermissionPredicate.is_cb_admin(user)

    @staticmethod
    def can_view_audit(user, audit):
        """Composite permission check"""
        if PermissionPredicate.is_cb_admin(user):
            return True
        if audit.lead_auditor == user:
            return True
        if audit.team_members.filter(user=user).exists():
            return True
        if hasattr(user, "profile") and user.profile.organization == audit.organization:
            return True
        return False
