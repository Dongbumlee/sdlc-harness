"""Core types for the SDLC Harness orchestrator."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SDLCPhase(str, Enum):
    """Phases of the software development lifecycle."""
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    SCAFFOLD = "scaffold"
    IMPLEMENT = "implement"
    QA = "qa"
    DEPLOY = "deploy"
    DOCUMENT = "document"
    RELEASE = "release"
    RAI = "rai"


class PlanStatus(str, Enum):
    """Status of an execution plan."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class PhaseResult:
    """Result from executing a single SDLC phase."""
    phase: SDLCPhase
    status: PlanStatus
    artifacts: list[str] = field(default_factory=list)
    score: float | None = None
    feedback: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    """Plan for orchestrating SDLC phases."""
    project_name: str
    phases: list[SDLCPhase]
    config: dict[str, Any] = field(default_factory=dict)
    results: list[PhaseResult] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING

    @property
    def current_phase(self) -> SDLCPhase | None:
        completed = {r.phase for r in self.results if r.status == PlanStatus.COMPLETED}
        for phase in self.phases:
            if phase not in completed:
                return phase
        return None


@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator."""
    model: str = "gpt-4o"
    max_retries: int = 2
    parallel_phases: bool = False
    evaluation_mode: str = "comprehensive"
    canary_path: str | None = None


# Backward-compat aliases
Phase = SDLCPhase
TaskStatus = PlanStatus


@dataclass
class TaskResult:
    """Legacy result type kept for backward compatibility."""

    phase: SDLCPhase
    content: str = ""
    status: PlanStatus = PlanStatus.COMPLETED
    metadata: dict[str, Any] = field(default_factory=dict)
