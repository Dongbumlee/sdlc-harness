"""Application configuration, split the way the web type requires.

The split is structural, not a naming habit. Values a browser may
see live in :class:`PublicConfig` and are the only ones templates
and client-side code ever receive. Server-only values live in
:class:`ServerConfig`, are read from the environment at startup,
and must never be rendered, logged, or sent to a client — leaking
one into a page is this type's signature security defect, and the
test suite pins a sentinel secret out of every response.
"""

import os
from dataclasses import dataclass

_PREFIX = "{{project-name}}".upper().replace("-", "_") + "_"


@dataclass(frozen=True)
class PublicConfig:
    """Browser-safe values: fine to render into any page."""

    app_name: str


@dataclass(frozen=True)
class ServerConfig:
    """Server-only values: never rendered, never sent to a client."""

    api_key: str


def load_public_config() -> PublicConfig:
    return PublicConfig(app_name=os.environ.get(_PREFIX + "PUBLIC_APP_NAME", "{{ProjectName}}"))


def load_server_config() -> ServerConfig:
    return ServerConfig(api_key=os.environ.get(_PREFIX + "SERVER_API_KEY", ""))
