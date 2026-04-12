"""Artifact generator — calls LLM to produce SDLC artifacts per phase."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from orchestrator.types import Phase, TaskResult, TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class GeneratorConfig:
    """Configuration for the artifact generator."""

    model: str = "gpt-4o"
    temperature: float = 0.2
    max_tokens: int = 4096
    timeout_seconds: int = 120


@dataclass
class GenerationRequest:
    """Request to generate an artifact."""

    phase: Phase
    task_description: str
    context: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    output_format: str = "markdown"


@dataclass
class GenerationResult:
    """Result from artifact generation."""

    content: str
    phase: Phase
    metadata: dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0


class ArtifactGenerator:
    """Generate SDLC artifacts using LLM calls.

    Each phase has specialized prompts and output formats:
    - requirements: PRD, user stories, acceptance criteria
    - design: architecture docs, API specs, diagrams
    - implement: code, tests, documentation
    - qa: test plans, security reviews, checklists
    - deploy: IaC, runbooks, configs
    - release: changelogs, announcements
    """

    def __init__(self, config: GeneratorConfig | None = None) -> None:
        self.config = config or GeneratorConfig()
        self._prompt_registry: dict[Phase, str] = self._load_prompts()

    def _load_prompts(self) -> dict[Phase, str]:
        """Load phase-specific prompt templates."""
        from orchestrator.generator_prompts import PHASE_PROMPTS

        return PHASE_PROMPTS

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate an artifact for the given request.

        In production, this calls the configured LLM. For now,
        returns a structured placeholder that validates the pipeline.
        """
        prompt = self._build_prompt(request)
        logger.info(
            "Generating %s artifact: %s",
            request.phase.value,
            request.task_description[:80],
        )

        # Placeholder: return structured content for pipeline validation
        content = self._generate_placeholder(request)

        return GenerationResult(
            content=content,
            phase=request.phase,
            metadata={
                "model": self.config.model,
                "prompt_length": len(prompt),
                "output_format": request.output_format,
            },
        )

    def _build_prompt(self, request: GenerationRequest) -> str:
        """Build the full prompt from template + request context."""
        template = self._prompt_registry.get(
            request.phase, "Generate a {phase} artifact."
        )
        prompt = template.format(
            phase=request.phase.value,
            task=request.task_description,
            output_format=request.output_format,
        )
        if request.constraints:
            prompt += "\n\nConstraints:\n"
            for c in request.constraints:
                prompt += f"- {c}\n"
        if request.context:
            prompt += f"\n\nContext:\n{json.dumps(request.context, indent=2)}"
        return prompt

    def _generate_placeholder(self, request: GenerationRequest) -> str:
        """Generate placeholder content for pipeline validation."""
        return (
            f"# {request.phase.value.title()} Artifact\n\n"
            f"## Task: {request.task_description}\n\n"
            f"**Phase:** {request.phase.value}\n"
            f"**Format:** {request.output_format}\n\n"
            "---\n\n"
            "*This is a placeholder artifact. Connect an LLM provider "
            "to generate real content.*\n"
        )

    def to_task_result(self, result: GenerationResult) -> TaskResult:
        """Convert a generation result to a TaskResult."""
        return TaskResult(
            phase=result.phase,
            status=TaskStatus.PASSED,
            content=result.content,
            metadata=result.metadata,
        )
