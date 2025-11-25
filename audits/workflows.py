"""
Audit workflow management - handles status transitions and validation.

This module implements the state machine for audit status transitions,
ensuring business rules are enforced and invalid transitions are blocked.
"""

from django.core.exceptions import ValidationError
from django.utils import timezone

from trunk.workflows.audit_state_machine import AuditStateMachine


class AuditWorkflow:
    """
    Manages audit status transitions and workflow validation.
    Delegates all logic to AuditStateMachine.
    """

    def __init__(self, audit):
        self.audit = audit
        self.sm = AuditStateMachine(audit)

    def can_transition(self, new_status, user):
        """
        Check if the transition from current status to new_status is allowed.
        """
        return self.sm.can_transition(new_status, user)

    def transition(self, new_status, user, notes=None):
        """
        Perform the status transition.
        """
        return self.sm.transition(new_status, user, notes)

    def get_available_transitions(self, user):
        """
        Get list of available status transitions for the current user.
        """
        return self.sm.available_transitions(user)

