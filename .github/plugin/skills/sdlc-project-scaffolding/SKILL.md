---
name: sdlc-project-scaffolding
description: >-
  Scaffold new application project structures from templates with CI/CD pipelines,
  Dockerfiles, and devcontainers. Use when creating a new service, restructuring
  a project, or setting up CI/CD. Triggers on scaffold, new project, new service,
  project structure, CI/CD pipeline, or Dockerfile requests.
---

# SDLC Project Scaffolding — application Accelerator Pattern

## When to use

- Starting a new Python API, business layer, agent, or web frontend
- Adding a new service to an existing application project
- Setting up CI/CD pipelines for a project
- Creating Dockerfiles or devcontainer configurations

## Step 1: Fetch the actual template files from GitHub MCP

**CRITICAL: Do NOT generate code from your training data. You MUST read the actual
template files from the private repo and replicate their patterns.**

For API projects, fetch these key files and use them as the basis for scaffolding:

```
# 1. Read the app entry point pattern
mcp_github_get_file_contents(owner: "your-org", repo: "python_api_application_template", path: "app/main.py")

# 2. Read the Application class (core framework pattern)
mcp_github_get_file_contents(owner: "your-org", repo: "python_api_application_template", path: "app/application.py")

# 3. Read the libs/ framework structure
mcp_github_get_file_contents(owner: "your-org", repo: "python_api_application_template", path: "app/libs")

# 4. Read the DI pattern with Protocol interfaces
mcp_github_get_file_contents(owner: "your-org", repo: "python_api_application_template", path: "app/services")

# 5. Read the Dockerfile pattern
mcp_github_get_file_contents(owner: "your-org", repo: "python_api_application_template", path: "Dockerfile")

# 6. Read the pyproject.toml pattern
mcp_github_get_file_contents(owner: "your-org", repo: "python_api_application_template", path: "pyproject.toml")

# 7. Read the health probes router
mcp_github_get_file_contents(owner: "your-org", repo: "python_api_application_template", path: "app/routers/http_probes.py")
```

**Read each file's content, then adapt it for the new project.** Do not skip this step.

## Step 2: Template patterns you MUST follow

These are the exact patterns from `python_api_application_template`. Follow them
the same way you follow `RootEntityBase` for your-cosmosdb-lib.

### main.py — Application factory pattern (NOT bare FastAPI)

```python
from application import Application

_app_instance = None

def get_app():
    global _app_instance
    if _app_instance is None:
        _app_instance = Application()
    return _app_instance.app

app = get_app()
```

**NEVER create `app = FastAPI()` directly in main.py.** Always use `Application()`.

### application.py — Application_Base with DI container

```python
from libs.base.application_base import Application_Base
from libs.base.typed_fastapi import TypedFastAPI

class Application(Application_Base):
    app: TypedFastAPI

    def __init__(self):
        super().__init__(env_file_path=os.path.join(os.path.dirname(__file__), ".env"))

    def initialize(self):
        self.app = TypedFastAPI(title="My API", version="1.0.0")
        self.app.set_app_context(self.application_context)

        # Health probes
        self.app.include_router(http_probes)

        # DI registration
        self._register_dependencies()
        self._config_routers()

    def _register_dependencies(self):
        (
            self.application_context
            .add_singleton(IMyService, MyServiceImpl)
            .add_async_scoped(my_repository)
        )

    def _config_routers(self):
        routers = [http_probes, my_router.router]
        for router in routers:
            self.app.include_router(router)
```

### app/libs/ — Framework directory (MANDATORY)

```
app/libs/
├── __init__.py
├── application/          ← AppContext, Configuration (Pydantic BaseSettings)
├── azure/                ← Azure App Configuration helpers
└── base/                 ← Application_Base, TypedFastAPI
```

Copy `libs/` from the template repo via GitHub MCP. This is the framework foundation.

### services/ — Protocol-based interfaces (NOT direct class injection)

```python
# app/services/interfaces.py
from typing import Protocol

class IFeedbackService(Protocol):
    async def create_feedback_async(self, request) -> FeedbackResponse: ...
    async def get_feedback_async(self, feedback_id: str) -> FeedbackResponse: ...

# app/services/implementations.py
class FeedbackService:
    def __init__(self, repository: FeedbackRepository):
        self._repository = repository

    async def create_feedback_async(self, request) -> FeedbackResponse:
        ...
```

Register services in `application.py`:
```python
self.application_context.add_singleton(IFeedbackService, FeedbackService)
```

### Dockerfile — Template pattern (NOT generic Python)

```dockerfile
FROM mcr.microsoft.com/azurelinux/base/python:3.12

WORKDIR /app

# Install uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy and install dependencies
COPY . /app
RUN uv sync --frozen --no-cache

# Run the application
CMD [".venv/bin/uvicorn", "app.main:app", "--port", "80", "--host", "0.0.0.0", "--workers", "4"]
```

**NEVER use `pip install uv` or `uv pip install`.** Always use `COPY --from=ghcr.io/astral-sh/uv:latest` + `uv sync --frozen`.

### pyproject.toml — Template pattern

```toml
[project]
name = "<project-name>"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]>=0.115.12",
    "uvicorn>=0.34.3",
    "pydantic>=2.11.5",
    "pydantic-settings>=2.9.1",
    "azure-identity>=1.23.0",
    "your-cosmosdb-lib>=1.0.0",          # Add if Cosmos DB needed
    "your-storage-lib>=1.0.0",           # Add if Blob/Queue needed
]

[dependency-groups]
dev = [
    "pytest>=8.4.0",
    "pytest-asyncio>=1.1.0",
    "pytest-cov>=6.2.1",
]

[tool.pytest.ini_options]
pythonpath = ["."]
addopts = ["--import-mode=importlib"]
```

**Use `[dependency-groups] dev` (NOT `[project.optional-dependencies]`).**

## Step 3: Select the template type

| Application Type | Template Repo | Code Root Inside Project |
|---|---|---|
| REST API / web service | `python_api_application_template` | `app/` |
| Console / worker / CLI | `python_application_template` | `src/` (nested inside project) |
| AI agent / chatbot / MCP | `python_agent_framework_dev_template` | `src/` (nested inside project) |
| Web frontend | React + TypeScript (custom) | `src/` (nested inside project) |

**IMPORTANT: "Code Root" refers to the folder INSIDE the project folder, NOT the
repo-level `src/` directory.** For example, an API project has its code at
`src/CustomerFeedbackAPI/app/` — the `app/` is the code root inside the project.

Also load containerization best practices:

```
mcp_awesome-copil_load_instruction(
  filename: "containerization-docker-best-practices.instructions.md",
  mode: "instructions"
)
```

## Step 4: Create the project structure

### Rule: EVERY repo has a `src/` directory at the root — this is the PROJECT CONTAINER

The `src/` directory at the repository root is a **container for project folders**.
It is NOT a code root. You NEVER put source files (like `main.py`, `__init__.py`,
`models/`, `routers/`) directly inside `src/`.

**WRONG** (source files directly in `src/`):
```
root/
├── pyproject.toml          ← WRONG: at repo root
├── src/
│   ├── main.py             ← WRONG: code directly in src/
│   ├── models/             ← WRONG
│   ├── routers/            ← WRONG
│   └── services/           ← WRONG
└── tests/                  ← WRONG: at repo root
```

**CORRECT** (named project folder inside `src/`):
```
root/
└── src/
    └── CustomerFeedbackAPI/        ← Named project folder
        ├── app/                    ← Code root for API template
        │   ├── main.py
        │   ├── routers/
        │   ├── services/
        │   └── libs/
        ├── tests/                  ← Tests inside project folder
        ├── pyproject.toml          ← Inside project folder
        └── Dockerfile              ← Inside project folder
```

### Naming convention

Project folders use `<ProjectName><Layer>` format:
- `CustomerFeedbackAPI` — API layer
- `CustomerFeedbackBusiness` — Business/domain layer
- `CustomerFeedbackAgent` — AI agent layer
- `CustomerFeedbackWeb` — Web frontend layer

For a single-service project with only an API, still use the naming convention:
`src/CustomerFeedbackAPI/` — never just `src/` as the code root.

### Multi-project layout (application standard)

```
src/
├── <Name>API/               ← python_api_application_template
│   ├── app/                 ← Code root (NOT src/)
│   │   ├── main.py
│   │   ├── application.py
│   │   ├── routers/
│   │   ├── services/
│   │   ├── business_component/
│   │   └── libs/
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── .devcontainer/
├── <Name>Business/          ← python_application_template
│   ├── src/                 ← Code root (NOT app/)
│   │   ├── main.py
│   │   └── libs/
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── .devcontainer/
├── <Name>Agent/             ← python_agent_framework_dev_template
│   ├── src/                 ← Code root (NOT app/)
│   │   ├── libs/agent_framework/
│   │   └── samples/
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── .devcontainer/
└── <Name>Web/               ← React + TypeScript
    ├── src/
    │   ├── Components/      ← PascalCase (application convention)
    │   ├── Pages/
    │   └── Services/
    ├── Dockerfile
    ├── package.json
    └── .devcontainer/
```

## Step 5: Additional project files

For each project, also create these files using the template as reference:

- `.devcontainer/devcontainer.json` — per-project dev container config
- `.env.example` — environment variable template
- `.gitignore` — Python/Node ignore patterns
- `.dockerignore` — exclude tests, docs, .git from Docker builds
- `.python-version` — `3.12`
- `uv.lock` — generated by running `uv sync` (include in git)

## Step 6: CI/CD pipeline stub

Create `azure_cicd.yaml` per project:

```yaml
trigger:
  paths:
    include:
      - src/<ProjectName>/**

stages:
  - stage: Build
    jobs:
      - job: BuildAndTest
        steps:
          - script: uv sync --frozen
          - script: uv run pytest --cov --junitxml=results.xml
          - script: docker build -t $(imageName) .

  - stage: Deploy
    dependsOn: Build
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployToACA
```

## Gotchas

- **ALL projects MUST be under `src/`** — even single-project repos. NEVER place
  `app/`, `pyproject.toml`, or `Dockerfile` directly at the repository root.
- **NEVER generate generic FastAPI code.** Always read the actual template files from
  GitHub MCP and replicate their patterns (`Application_Base`, `libs/`, DI container).
- **API template uses `app/` as code root** — the code root inside an API project
  is `app/` (path: `src/<Name>API/app/`), NOT `src/`.
- **The `libs/` directory is MANDATORY** for API projects — copy it from the template.
  It contains `Application_Base`, `TypedFastAPI`, `AppContext`, and Azure helpers.
- **Use Protocol interfaces** for service contracts — `services/interfaces.py` +
  `services/implementations.py`, not direct class injection.
- **Dockerfile must use `COPY --from=ghcr.io/astral-sh/uv:latest`** — never `pip install uv`.
- **`pyproject.toml` uses `[dependency-groups] dev`** — not `[project.optional-dependencies]`.
- **Tests are always at `tests/` in the project root** — never inside `app/` or the inner `src/`.
- **Each project gets its own Dockerfile, pyproject.toml, and .devcontainer/**.
- **Use `uv` everywhere** — never `pip`, never `poetry`.
