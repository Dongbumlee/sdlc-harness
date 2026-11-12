"""The stream contract: results on stdout (plain or JSON),
diagnostics on stderr, and colour only where a human is looking at
a terminal — never in piped data.
"""

from __future__ import annotations

import json
import os
import sys


class Output:
    """Owns printing for one execution, under the resolved options."""

    def __init__(self, fmt: str, no_color: bool, quiet: bool) -> None:
        self._format = fmt
        self._color = color_enabled(no_color)
        self._quiet = quiet

    def result(self, value: str, extra: dict | None = None) -> None:
        """Print a command's primary data to stdout.

        In JSON mode the value is wrapped in an object with a stable
        `result` field; callers may add fields but the shape never
        changes within a major version.
        """
        if self._format == "json":
            payload = {"result": value, **(extra or {})}
            print(json.dumps(payload))
        else:
            print(value)

    def diagnostic(self, message: str) -> None:
        """Print a human-only note to stderr, unless --quiet.

        Diagnostics never carry primary data.
        """
        if self._quiet:
            return
        if self._color:
            print(f"\033[2m{message}\033[0m", file=sys.stderr)
        else:
            print(message, file=sys.stderr)


def color_enabled(no_color_flag: bool) -> bool:
    """Decide whether styled diagnostics are appropriate.

    An explicit --no-color or the NO_COLOR environment variable
    wins, and colour is only ever used on a terminal.
    """
    if no_color_flag:
        return False
    if "NO_COLOR" in os.environ:
        return False
    return sys.stdout.isatty()
