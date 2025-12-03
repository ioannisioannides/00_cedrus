"""
Generic state machine engine.

Provides reusable primitives for defining states, transitions, permission checks,
and validation guards. Concrete workflows should subclass or compose this engine.
"""

from typing import Callable, Dict, Iterable, List, Optional, Tuple

GuardResult = Tuple[bool, str]
PermissionChecker = Callable[[object, str, str], bool]
GuardChecker = Callable[[str, str], GuardResult]


class StateMachine:
    """
    Reusable state machine with permissions and guards.

    - transitions: mapping of state -> iterable of allowed target states
    - permission_checker: callable(obj, from_state, to_state) -> bool
    - guards: mapping of (from_state, to_state) -> list of guard callables
      where each guard returns (is_valid: bool, reason: str)
    """

    def __init__(
        self,
        *,
        obj: object,
        get_state: Callable[[object], str],
        set_state: Callable[[object, str], None],
        transitions: Dict[str, Iterable[str]],
        permission_checker: Optional[PermissionChecker] = None,
        guards: Optional[Dict[Tuple[str, str], List[GuardChecker]]] = None,
        get_status_label: Optional[Callable[[str], str]] = None,
    ) -> None:
        self._obj = obj
        self._get_state = get_state
        self._set_state = set_state
        self._transitions = transitions
        self._permission_checker = permission_checker
        self._guards = guards or {}
        self._get_status_label = get_status_label or (lambda s: s)

    @property
    def current_state(self) -> str:
        return self._get_state(self._obj)

    def is_valid_transition(self, to_state: str) -> bool:
        return to_state in self._transitions.get(self.current_state, [])

    def _check_permissions(self, to_state: str, user: object) -> GuardResult:
        if not self._permission_checker:
            return True, "Allowed"
        allowed = self._permission_checker(user, self.current_state, to_state)
        if not allowed:
            return False, "You do not have permission to perform this transition"
        return True, "Allowed"

    def _run_guards(self, to_state: str) -> GuardResult:
        checks = self._guards.get((self.current_state, to_state), [])
        for guard in checks:
            ok, reason = guard(self.current_state, to_state)
            if not ok:
                return ok, reason
        return True, "Validation passed"

    def can_transition(self, to_state: str, user: Optional[object] = None) -> GuardResult:
        if not self.is_valid_transition(to_state):
            return False, f"Invalid transition from '{self.current_state}' to '{to_state}'"
        ok, reason = self._check_permissions(to_state, user)
        if not ok:
            return ok, reason
        return self._run_guards(to_state)

    def transition(self, to_state: str, user: Optional[object] = None) -> None:
        ok, reason = self.can_transition(to_state, user)
        if not ok:
            from django.core.exceptions import ValidationError

            raise ValidationError(reason)
        self._set_state(self._obj, to_state)

    def available_transitions(self, user: Optional[object] = None) -> List[Tuple[str, str]]:
        results: List[Tuple[str, str]] = []
        for target in self._transitions.get(self.current_state, []):
            ok, _ = self.can_transition(target, user)
            if ok:
                results.append((target, self._get_status_label(target)))
        return results
