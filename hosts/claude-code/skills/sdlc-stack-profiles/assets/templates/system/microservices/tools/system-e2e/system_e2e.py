#!/usr/bin/env python3
"""Thin system-level smoke check for a microservices system.

This is the system's own test, deliberately small: it runs against
DEPLOYED versions of the services (the system-e2e pipeline, on a
schedule or before a release), never as a per-service PR gate —
contract tests are the integration layer; this suite only proves
the composed system is alive and wired. It reads the system map
(system.json), the single source of truth the scaffolder also uses
to render docker-compose.yaml:

  python3 system_e2e.py --map ../../system.json [--check]
  python3 system_e2e.py --map ../../system.json --base items-api=http://localhost:8081

Modes:
  (default)  probe every service's health path over HTTP and verify
             a pact file exists for every declared boundary.
  --check    validate the map and the pact files only (no HTTP) —
             what the system repository's own CI runs.

Exit code: 0 when every check passes, 1 otherwise. Standard library
only — the suite must run anywhere Python 3 does, including inside
the runner image (see the Dockerfile beside this file).
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


def load_map(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    for key in ("system", "services", "boundaries"):
        if key not in data:
            raise ValueError(f"system map is missing '{key}'")
    names = [s["name"] for s in data["services"]]
    if len(names) != len(set(names)):
        raise ValueError("service names in the system map must be unique")
    for service in data["services"]:
        for key in ("name", "port", "health"):
            if key not in service:
                raise ValueError(f"service entry is missing '{key}': {service!r}")
    return data


def check_boundaries(system_map: dict, map_dir: Path) -> list[str]:
    """Every declared boundary needs its pact file on disk — a
    boundary without a contract is exactly what this type exists
    to prevent."""
    problems: list[str] = []
    known = {s["name"] for s in system_map["services"]}
    for boundary in system_map["boundaries"]:
        for role in ("consumer", "provider"):
            if boundary.get(role) not in known:
                problems.append(
                    f"boundary {boundary.get('name')!r}: {role} "
                    f"{boundary.get(role)!r} is not a service in the map"
                )
        pact = boundary.get("pact")
        if not pact:
            problems.append(f"boundary {boundary.get('name')!r}: no pact file declared")
        elif not (map_dir / pact).is_file():
            problems.append(
                f"boundary {boundary.get('name')!r}: pact file {pact} not found"
            )
    return problems


def probe(url: str, timeout: float = 5.0) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read(4096).decode("utf-8", errors="replace")
            if response.status == 200 and '"ok"' in body:
                return True, f"{url} -> 200"
            return False, f"{url} -> {response.status} without the health payload"
    except (urllib.error.URLError, OSError) as error:
        return False, f"{url} -> unreachable ({error})"


def run(system_map: dict, map_dir: Path, bases: dict[str, str], check_only: bool) -> int:
    failures = 0
    for problem in check_boundaries(system_map, map_dir):
        print(f"FAIL boundary: {problem}")
        failures += 1
    if not check_only:
        for service in system_map["services"]:
            base = bases.get(
                service["name"], f"http://{service['name']}:{service['port']}"
            )
            ok, detail = probe(f"{base}{service['health']}")
            print(f"{'PASS' if ok else 'FAIL'} health {service['name']}: {detail}")
            failures += 0 if ok else 1
    print(
        f"system {system_map['system']}: "
        f"{len(system_map['services'])} services, "
        f"{len(system_map['boundaries'])} boundaries, "
        f"{'FAILED' if failures else 'OK'} ({failures} failure(s))"
    )
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", required=True, help="path to system.json")
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the map and pact files only; do not probe HTTP",
    )
    parser.add_argument(
        "--base",
        action="append",
        default=[],
        metavar="NAME=URL",
        help="override a service's base URL (repeatable), e.g. for local compose ports",
    )
    args = parser.parse_args(argv)
    map_path = Path(args.map)
    try:
        system_map = load_map(map_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL system map: {error}")
        return 1
    bases = dict(item.split("=", 1) for item in args.base)
    return run(system_map, map_path.parent, bases, args.check)


if __name__ == "__main__":
    sys.exit(main())
