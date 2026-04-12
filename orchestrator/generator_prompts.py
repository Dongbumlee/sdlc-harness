"""Phase-specific prompt templates for the artifact generator."""

from orchestrator.types import Phase

PHASE_PROMPTS: dict[Phase, str] = {
    Phase.REQUIREMENTS: (
        "You are a senior product manager. Generate a {output_format} "
        "requirements document for the following task:\n\n{task}\n\n"
        "Include: user stories, acceptance criteria, non-functional requirements, "
        "and success metrics."
    ),
    Phase.DESIGN: (
        "You are a senior software architect. Create a {output_format} "
        "design document for:\n\n{task}\n\n"
        "Include: architecture overview, component diagram, API contracts, "
        "data models, and key design decisions."
    ),
    Phase.IMPLEMENT: (
        "You are an expert software engineer. Implement the following:\n\n{task}\n\n"
        "Output format: {output_format}\n"
        "Follow best practices: clean code, proper error handling, "
        "type hints, and inline documentation."
    ),
    Phase.QA: (
        "You are a QA engineer and security specialist. Create a {output_format} "
        "review for:\n\n{task}\n\n"
        "Include: test plan, security checklist, edge cases, "
        "performance considerations, and risk assessment."
    ),
    Phase.DEPLOY: (
        "You are a DevOps engineer. Create {output_format} deployment artifacts "
        "for:\n\n{task}\n\n"
        "Include: infrastructure as code, deployment runbook, "
        "rollback procedures, and monitoring setup."
    ),
    Phase.RELEASE: (
        "You are a release manager. Create {output_format} release documentation "
        "for:\n\n{task}\n\n"
        "Include: changelog, migration guide, known issues, "
        "and stakeholder communication."
    ),
}
