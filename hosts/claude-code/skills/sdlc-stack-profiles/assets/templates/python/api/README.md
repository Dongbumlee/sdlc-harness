# {{ProjectName}}

<!-- One line: what this service does and who it serves. The design
phase expands this stub into the full project README. -->

## Getting started

Prerequisites: Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
cd src/{{ProjectName}}API
uv sync
uv run uvicorn app.main:app --reload --port 8080
uv run pytest
```

## Security

See [SECURITY.md](SECURITY.md) for how to report a vulnerability.

## Changelog

See [CHANGELOG.md](CHANGELOG.md). Releases are cut from version
tags (`vX.Y.Z`): the release workflow verifies the tagged tree and
publishes the matching changelog section as the GitHub Release
notes.
