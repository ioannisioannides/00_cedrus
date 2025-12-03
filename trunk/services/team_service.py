"""
Service for managing audit team members and competence checks.
"""

from django.db import transaction

from audit_management.models import AuditTeamMember
from trunk.events import EventType, event_dispatcher


class TeamService:
    """Business logic for audit team management."""

    @staticmethod
    @transaction.atomic
    def add_team_member(audit, data, user=None):
        """
        Add a team member to an audit.

        Args:
            audit: The audit instance.
            data: Dictionary containing team member data (user, name, role, dates).
            user: The user performing the action (optional).

        Returns:
            AuditTeamMember: The created team member.
        """
        # Validate data is handled by form/serializer usually, but we can add extra checks here

        # Create team member
        team_member = AuditTeamMember.objects.create(audit=audit, **data)

        # Check competence if user is assigned
        if team_member.user:
            TeamService.check_competence(audit, team_member.user)

        # Emit event
        event_dispatcher.emit(
            EventType.TEAM_MEMBER_ADDED,
            {
                "audit_id": audit.id,
                "team_member_id": team_member.id,
                "added_by_id": user.id if user else None,
            },
        )

        return team_member

    @staticmethod
    def update_team_member(team_member, data, user=None):  # pylint: disable=unused-argument
        """
        Update an audit team member.
        """
        with transaction.atomic():
            for key, value in data.items():
                setattr(team_member, key, value)
            team_member.save()

            # Re-check competence if user changed
            if "user" in data and team_member.user:
                TeamService.check_competence(team_member.audit, team_member.user)

            return team_member

    @staticmethod
    def remove_team_member(team_member, user=None):
        """
        Remove a team member from an audit.

        Args:
            team_member: The AuditTeamMember instance.
            user: The user performing the action.
        """
        audit = team_member.audit
        member_name = team_member.name

        team_member.delete()

        # Emit event
        event_dispatcher.emit(
            EventType.TEAM_MEMBER_REMOVED,
            {
                "audit_id": audit.id,
                "member_name": member_name,
                "removed_by_id": user.id if user else None,
            },
        )

    @staticmethod
    def check_competence(audit, auditor):
        """
        Check auditor competence for the given audit and issue warnings if needed.

        This is a placeholder for the actual competence logic which would likely
        involve checking the auditor's qualifications against the audit's
        standard and scope (IAF MD1).
        """
        # Logic to check competence would go here.
        # For now, we just check for existing warnings to return them?
        # Or we generate them.

        # Example: Check if auditor has sector experience
        # if not auditor.profile.has_sector(audit.organization.sector):
        #     AuditorCompetenceWarning.objects.create(...)
