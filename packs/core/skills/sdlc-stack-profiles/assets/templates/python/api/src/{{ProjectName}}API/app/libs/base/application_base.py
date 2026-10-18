from abc import ABC, abstractmethod

from app.libs.application.configuration import Configuration
from app.libs.application.context import AppContext


class Application_Base(ABC):
    """Base class for the application factory.

    Loads configuration, builds the application context, then delegates
    app construction to the subclass's initialize().
    """

    def __init__(self, env_file_path: str | None = None):
        configuration = Configuration(_env_file=env_file_path)
        self.application_context = AppContext(configuration)
        self.initialize()

    @abstractmethod
    def initialize(self) -> None:
        raise NotImplementedError
