"""State machine for SDLC phase transitions.

Manages the lifecycle of an execution plan through SDLC phases,
enforcing valid transitions and tracking state history.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable

from orchestrator.types import ExecutionPlan, PhaseResult, PlanStatus, SDLCPhase

logger = logging.getLogger(__name__)

# Valid phase transitions: phase -> set of allowed next phases
VALID_TRANSITIONS: dict[SDLCPhase, set[SDLCPhase]] = {
    SDLCPhase.REQUIREMENTS: {SDLCPhase.DESIGN, SDLCPhase.SCAFFOLD},
    SDLCPhase.DESIGN: {SDLCPhase.SCAFFOLD},
    SDLCPhase.SCAFFOLD: {SDLCPhase.IMPLEMENT},
    SDLCPhase.IMPLEMENT: {SDLCPhase.QA},
    SDLCPhase.QA: {SDLCPhase.DEPLOY, SDLCPhase.IMPLEMENT},  # Can loop back
    SDLCPhase.DEPLOY: {SDLCPhase.DOCUMENT},
    SDLCPhase.DOCUMENT: {SDLCPhase.RELEASE},
    SDLCPhase.RELEASE: {SDLCPhase.RAI},
    SDLCPhase.RAI: set(),  # Terminal
}


@dataclass
class StateTransition:
    """Record of a state transition."""
    from_phase: SDLCPhase | None
    to_phase: SDLCPhase
    result: PhaseResult | None = None


@dataclass
class StateMachine:
    """Manages SDLC phase transitions for an execution plan."""

    plan: ExecutionPlan
    history: list[StateTransition] = field(default_factory=list)
    _hooks: dict[str, list[Callable]] = field(default_factory=dict)

    @property
    def current_phase(self) -> SDLCPhase | None:
        return self.plan.current_phase

    def can_transition(self, to_phase: SDLCPhase) -> bool:
        """Check if transition to the given phase is valid."""
        current = self.current_phase
        if current is None:
            # First phase — must be first in plan
            return to_phase == self.plan.phases[0]
        return to_phase in VALID_TRANSITIONS.get(current, set())

    def transition(self, to_phase: SDLCPhase, result: PhaseResult | None = None) -> bool:
        """Attempt to transition to a new phase.

        Args:
            to_phase: Target phase.
            result: Result from the current phase (if completing it).

        Returns:
            True if transition succeeded.
        """
        current = self.current_phase
        if not self.can_transition(to_phase):
            logger.warning(
                "Invalid transition: %s -> %s", current, to_phase
            )
            return False

        if result:
            self.plan.results.append(result)

        transition = StateTransition(
            from_phase=current, to_phase=to_phase, result=result
        )
        self.history.append(transition)
        self._fire_hooks("on_transition", transition)

        logger.info("Transition: %s -> %s", current, to_phase)
        return True

    def complete_phase(self, result: PhaseResult) -> bool:
        """Mark the current phase as complete and advance."""
        current = self.current_phase
        if current is None:
            return False
        if result.phase != current:
            logger.warning("Result phase %s != current %s", result.phase, current)
            return False

        self.plan.results.append(result)
        self._fire_hooks("on_phase_complete", result)

        # Auto-advance to next phase if possible
        next_phase = self.plan.current_phase
        if next_phase:
            self.plan.status = PlanStatus.IN_PROGRESS
        else:
            self.plan.status = PlanStatus.COMPLETED
            self._fire_hooks("on_plan_complete", self.plan)
        return True

    def register_hook(self, event: str, callback: Callable) -> None:
        """Register a callback for state machine events."""
        self._hooks.setdefault(event, []).append(callback)

    def _fire_hooks(self, event: str, data: object) -> None:
        for hook in self._hooks.get(event, []):
            try:
                hook(data)
            except Exception:
                logger.exception("Hook error for event %s", event)
