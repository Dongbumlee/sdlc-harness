"""Planner agent — analyzes requirements and produces execution plans.

The Planner is the first agent in the 3-agent pipeline:
  Planner -> Generator -> Evaluator

It reads project context (repo structure, config profile, user prompt)
and outputs an ExecutionPlan with ordered SDLC phases and per-phase config.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from orchestrator.planner_prompts import PLAN_SYSTEM_PROMPT, PLAN_USER_TEMPLATE
from orchestrator.types import ExecutionPlan, OrchestratorConfig, SDLCPhase

logger = logging.getLogger(__name__)


@dataclass
class PlannerContext:
    """Input context for the Planner agent."""
    project_name: str
    user_prompt: str
    repo_structure: list[str] = field(default_factory=list)
    config_profile: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)


class Planner:
    """Planner agent that creates execution plans from project context.

    Uses an LLM to analyze project requirements and determine which
    SDLC phases to execute and in what order.
    """

    def __init__(self, config: OrchestratorConfig | None = None):
        self.config = config or OrchestratorConfig()

    async def create_plan(
        self,
        context: PlannerContext,
        llm_client: Any = None,
    ) -> ExecutionPlan:
        """Create an execution plan from project context.

        Args:
            context: Project context including prompt and constraints.
            llm_client: LLM client for plan generation (optional for testing).

        Returns:
            ExecutionPlan with ordered phases.
        """
        if llm_client is None:
            return self._create_default_plan(context)

        prompt = PLAN_USER_TEMPLATE.format(
            project_name=context.project_name,
            user_prompt=context.user_prompt,
            repo_structure="\n".join(context.repo_structure[:50]),
            constraints="\n".join(f"- {c}" for c in context.constraints),
        )

        response = await llm_client.complete(
            system=PLAN_SYSTEM_PROMPT,
            prompt=prompt,
            model=self.config.model,
        )

        return self._parse_plan(context.project_name, response)

    def _create_default_plan(self, context: PlannerContext) -> ExecutionPlan:
        """Create a default full-lifecycle plan."""
        phases = [
            SDLCPhase.REQUIREMENTS,
            SDLCPhase.DESIGN,
            SDLCPhase.SCAFFOLD,
            SDLCPhase.IMPLEMENT,
            SDLCPhase.QA,
            SDLCPhase.DEPLOY,
            SDLCPhase.DOCUMENT,
            SDLCPhase.RELEASE,
        ]
        return ExecutionPlan(
            project_name=context.project_name,
            phases=phases,
            config={"source": "default", "profile": context.config_profile},
        )

    def _parse_plan(self, project_name: str, response: str) -> ExecutionPlan:
        """Parse LLM response into an ExecutionPlan."""
        try:
            data = json.loads(response)
            phases = [SDLCPhase(p) for p in data.get("phases", [])]
            config = data.get("config", {})
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse plan response: %s", e)
            phases = list(SDLCPhase)
            config = {"parse_error": str(e)}

        return ExecutionPlan(
            project_name=project_name,
            phases=phases,
            config=config,
        )
