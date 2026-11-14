from typing import TypeVar

from app.libs.application.configuration import Configuration

T = TypeVar("T")


class AppContext:
    """Application context: configuration + singleton service registry.

    Services are registered under their Protocol (interface) type in the
    application's composition root and resolved by that type everywhere
    else, so implementations stay replaceable.
    """

    def __init__(self, configuration: Configuration):
        self.configuration = configuration
        self._singletons: dict[type, object] = {}

    def add_singleton(self, abstraction: type[T], instance: T) -> "AppContext":
        self._singletons[abstraction] = instance
        return self

    def get(self, abstraction: type[T]) -> T:
        if abstraction not in self._singletons:
            raise KeyError(f"No service registered for {abstraction!r}")
        return self._singletons[abstraction]  # type: ignore[return-value]
