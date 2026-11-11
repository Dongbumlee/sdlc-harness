"""Domain errors — the one home for service-layer failures.

Services raise these; they never build HTTP responses. The
composition root (app.application) maps each type to its HTTP
status code, so routers stay free of translation branches and a
failure means the same thing in every project built from this
template. Add project-specific failures as subclasses of DomainError
here, not as ad-hoc exceptions in a service module.
"""


class DomainError(Exception):
    """Base for domain failures. Carries a user-facing detail."""

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class NotFoundError(DomainError):
    """The addressed resource does not exist. Maps to 404."""


class ForbiddenError(DomainError):
    """The principal may not perform this operation. Maps to 403."""


class ConflictError(DomainError):
    """The operation conflicts with current state. Maps to 409."""


class ValidationError(DomainError):
    """The request is well-formed but semantically invalid. Maps to 400."""
