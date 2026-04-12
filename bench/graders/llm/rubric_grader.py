"""Rubric grader — LLM evaluates against a detailed scoring rubric."""
from __future__ import annotations

import json
from typing import Any

from bench.graders.models import GradeResult, GraderOutput


class RubricGrader:
    """Evaluate AI output against a multi-dimension scoring rubric."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.rubric: list[dict[str, Any]] = config.get("rubric", [])
        self.model: str = config.get("model", "gpt-4o")
        self.pass_threshold: float = config.get("pass_threshold", 0.7)

    def build_prompt(self, output: str, context: dict[str, Any]) -> str:
        rubric_text = ""
        for dim in self.rubric:
            rubric_text += f"\n### {dim['dimension']} (weight: {dim.get('weight', 1.0)})\n"
            rubric_text += f"{dim.get('description', '')}\n"
            for level, desc in dim.get("levels", {}).items():
                rubric_text += f"  - {level}: {desc}\n"

        return f"""Evaluate this AI output against the rubric below.

RUBRIC:
{rubric_text}

ORIGINAL PROMPT:
{context.get('prompt', 'N/A')}

AI OUTPUT:
{output}

Respond with JSON:
{{
  "dimensions": [
    {{
      "dimension": "name",
      "score": 0.0-1.0,
      "level": "excellent|good|adequate|poor",
      "note": "explanation"
    }}
  ],
  "overall_score": 0.0-1.0,
  "summary": "brief overall assessment"
}}"""

    def parse_response(self, response: str) -> GraderOutput:
        """Parse rubric evaluation response."""
        try:
            start = response.index("{")
            end = response.rindex("}") + 1
            data = json.loads(response[start:end])

            score = float(data.get("overall_score", 0.0))
            summary = data.get("summary", "No summary")

            if score >= self.pass_threshold:
                result = GradeResult.PASS
            elif score >= self.pass_threshold * 0.6:
                result = GradeResult.PARTIAL
            else:
                result = GradeResult.FAIL

            return GraderOutput(result, score, summary,
                                {"dimensions": data.get("dimensions", [])})

        except (ValueError, json.JSONDecodeError) as e:
            return GraderOutput(GradeResult.FAIL, 0.0, f"Parse error: {e}")
