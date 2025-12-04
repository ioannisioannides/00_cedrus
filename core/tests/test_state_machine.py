from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ValidationError

from core.workflows.state_machine import StateMachine


class TestStateMachine:
    def setup_method(self):
        self.obj = MagicMock()
        self.obj.status = "draft"

        self.transitions = {
            "draft": ["submitted"],
            "submitted": ["approved", "rejected"],
            "approved": [],
            "rejected": ["draft"],
        }

        def get_state(obj):
            return obj.status

        def set_state(obj, state):
            obj.status = state

        self.sm = StateMachine(obj=self.obj, get_state=get_state, set_state=set_state, transitions=self.transitions)

    def test_current_state(self):
        assert self.sm.current_state == "draft"

    def test_is_valid_transition(self):
        assert self.sm.is_valid_transition("submitted")
        assert not self.sm.is_valid_transition("approved")

    def test_transition_success(self):
        self.sm.transition("submitted")
        assert self.obj.status == "submitted"

    def test_transition_invalid(self):
        with pytest.raises(ValidationError, match="Invalid transition"):
            self.sm.transition("approved")

    def test_permission_checker_allowed(self):
        checker = MagicMock(return_value=True)
        self.sm._permission_checker = checker

        self.sm.transition("submitted", user="user")

        checker.assert_called_once_with("user", "draft", "submitted")
        assert self.obj.status == "submitted"

    def test_permission_checker_denied(self):
        checker = MagicMock(return_value=False)
        self.sm._permission_checker = checker

        with pytest.raises(ValidationError, match="permission"):
            self.sm.transition("submitted", user="user")

        assert self.obj.status == "draft"

    def test_guards_passed(self):
        guard = MagicMock(return_value=(True, "OK"))
        self.sm._guards = {("draft", "submitted"): [guard]}

        self.sm.transition("submitted")

        guard.assert_called_once_with("draft", "submitted")
        assert self.obj.status == "submitted"

    def test_guards_failed(self):
        guard = MagicMock(return_value=(False, "Guard failed"))
        self.sm._guards = {("draft", "submitted"): [guard]}

        with pytest.raises(ValidationError, match="Guard failed"):
            self.sm.transition("submitted")

        assert self.obj.status == "draft"

    def test_available_transitions(self):
        assert self.sm.available_transitions() == [("submitted", "submitted")]

        self.obj.status = "submitted"
        assert set(self.sm.available_transitions()) == {("approved", "approved"), ("rejected", "rejected")}

    def test_available_transitions_with_permission_check(self):
        # Only allow transition to approved
        def checker(user, from_state, to_state):
            return to_state == "approved"

        self.sm._permission_checker = checker
        self.obj.status = "submitted"

        assert self.sm.available_transitions() == [("approved", "approved")]
