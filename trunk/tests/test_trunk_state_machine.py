from unittest.mock import Mock

import pytest
from django.core.exceptions import ValidationError

from trunk.workflows.state_machine import StateMachine


class TestStateMachine:
    def setup_method(self):
        self.obj = Mock()
        self.obj.status = "draft"
        self.transitions = {
            "draft": ["review", "cancelled"],
            "review": ["published", "draft"],
            "published": ["archived"],
            "archived": [],
            "cancelled": [],
        }
        self.sm = StateMachine(
            obj=self.obj,
            get_state=lambda o: o.status,
            set_state=lambda o, s: setattr(o, "status", s),
            transitions=self.transitions,
        )

    def test_current_state(self):
        assert self.sm.current_state == "draft"

    def test_is_valid_transition(self):
        assert self.sm.is_valid_transition("review") is True
        assert self.sm.is_valid_transition("cancelled") is True
        assert self.sm.is_valid_transition("published") is False

    def test_transition_success(self):
        self.sm.transition("review")
        assert self.obj.status == "review"
        assert self.sm.current_state == "review"

    def test_transition_invalid(self):
        with pytest.raises(ValidationError, match="Invalid transition"):
            self.sm.transition("published")
        assert self.obj.status == "draft"

    def test_permission_checker_allow(self):
        checker = Mock(return_value=True)
        sm = StateMachine(
            obj=self.obj,
            get_state=lambda o: o.status,
            set_state=lambda o, s: setattr(o, "status", s),
            transitions=self.transitions,
            permission_checker=checker,
        )
        user = Mock()
        sm.transition("review", user)
        checker.assert_called_once_with(user, "draft", "review")
        assert self.obj.status == "review"

    def test_permission_checker_deny(self):
        checker = Mock(return_value=False)
        sm = StateMachine(
            obj=self.obj,
            get_state=lambda o: o.status,
            set_state=lambda o, s: setattr(o, "status", s),
            transitions=self.transitions,
            permission_checker=checker,
        )
        user = Mock()
        with pytest.raises(ValidationError, match="You do not have permission"):
            sm.transition("review", user)
        assert self.obj.status == "draft"

    def test_guards_pass(self):
        guard = Mock(return_value=(True, "OK"))
        guards = {("draft", "review"): [guard]}
        sm = StateMachine(
            obj=self.obj,
            get_state=lambda o: o.status,
            set_state=lambda o, s: setattr(o, "status", s),
            transitions=self.transitions,
            guards=guards,
        )
        sm.transition("review")
        guard.assert_called_once_with("draft", "review")
        assert self.obj.status == "review"

    def test_guards_fail(self):
        guard = Mock(return_value=(False, "Guard failed"))
        guards = {("draft", "review"): [guard]}
        sm = StateMachine(
            obj=self.obj,
            get_state=lambda o: o.status,
            set_state=lambda o, s: setattr(o, "status", s),
            transitions=self.transitions,
            guards=guards,
        )
        with pytest.raises(ValidationError, match="Guard failed"):
            sm.transition("review")
        assert self.obj.status == "draft"

    def test_available_transitions(self):
        transitions = self.sm.available_transitions()
        assert len(transitions) == 2
        assert ("review", "review") in transitions
        assert ("cancelled", "cancelled") in transitions

    def test_available_transitions_filtered_by_permission(self):
        def checker(user, from_state, to_state):
            return to_state == "review"  # Only allow review, deny cancelled

        sm = StateMachine(
            obj=self.obj,
            get_state=lambda o: o.status,
            set_state=lambda o, s: setattr(o, "status", s),
            transitions=self.transitions,
            permission_checker=checker,
        )
        transitions = sm.available_transitions(Mock())
        assert len(transitions) == 1
        assert transitions[0][0] == "review"

    def test_custom_status_label(self):
        sm = StateMachine(
            obj=self.obj,
            get_state=lambda o: o.status,
            set_state=lambda o, s: setattr(o, "status", s),
            transitions=self.transitions,
            get_status_label=lambda s: s.upper(),
        )
        transitions = sm.available_transitions()
        assert ("review", "REVIEW") in transitions
