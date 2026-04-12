"""LLM Judge grader — single model evaluates output against criteria."""
from __future__ import annotations

import json
from typing import Any

from bench.graders.models import GradeResult, GraderOutput


class JudgeGrader:
    """Use a single LLM as judge to evaluate AI-generated output."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.criteria: list[str] = config.get("criteria", [])
        self.model: str = config.get("model", "gpt-4o")
        self.temperature: float = config.get("temperature", 0.0)

    def build_prompt(self, output: str, context: dict[str, Any]) -> str:
        criteria_text = "\n".join(f"- {c}" for c in self.criteria)
        return f"""Evaluate the following AI-generated output against these criteria:

CRITERIA:
{criteria_text}

ORIGINAL PROMPT:
{context.get('prompt', 'N/A')}

AI OUTPUT:
{output}

Respond with JSON:
{{
  "result": "pass" | "partial" | "fail",
  "score": 0.0-1.0,
  "reason": "brief explanation",
  "per_criterion": [
    {{"criterion": "...", "met": true/false, "note": "..."}}
  ]
}}"""

    def parse_response(self, response: str) -> GraderOutput:
        """Parse LLM judge response into GraderOutput."""
        try:
            # Try to extract JSON from response
            start = response.index("{")
            end = response.rindex("}") + 1
            data = json.loads(response[start:end])

            result_map = {
                "pass": GradeResult.PASS,
                "partial": GradeResult.PARTIAL,
                "fail": GradeResult.FAIL,
            }
            result = result_map.get(data.get("result", "fail"), GradeResult.FAIL)
            score = float(data.get("score", 0.0))
            reason = data.get("reason", "No reason provided")
            details = {"per_criterion": data.get("per_criterion", [])}

            return GraderOutput(result, score, reason, details)

        except (ValueError, json.JSONDecodeError, KeyError) as e:
            return GraderOutput(
                GradeResult.FAIL, 0.0,
                f"Failed to parse judge response: {e}",
                {"raw_response": response[:500]},
            )
