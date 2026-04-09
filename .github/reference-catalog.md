# Reference Catalog: Libraries and Scaffolding Templates

> **📋 TEMPLATE:** This file ships with example entries showing the expected format.
> Replace them with your team's actual libraries, templates, and conventions.

> **SDLC alignment:** This catalog supports all SDLC phases, especially **Phase 2 (Design)**, **Phase 3 (Repo Structure)**,
> and **Phase 4 (Implementation)**. Consult it when choosing how to scaffold a new project or which libraries to use.

This document is the authoritative registry of reusable libraries and scaffolding templates maintained by your team.
Copilot and engineers MUST consult this catalog before introducing new dependencies or inventing new patterns.

---

## How to use this catalog

1. **Starting a new project?** → Pick a **Scaffolding Template** that matches your application type.
2. **Need Azure data access?** → Add a **Reusable Library** via `uv add`.
3. **Adding a new entry?** → Add it to the appropriate section below, following the same format.

```
┌──────────────────────────────────────────────────────────────┐
│                     YOUR NEW PROJECT                         │
│                                                              │
│  1. Scaffold from a template:                                │
│  ┌──────────────┐ ┌──────────────┐ ┌───────────────────────┐ │
│  │ application_  │ │ api_app_     │ │ agent_framework_      │ │
│  │ template      │ │ template     │ │ dev_template          │ │
│  │ (base app)    │ │ (FastAPI)    │ │ (AI agents)           │ │
│  └──────┬───────┘ └──────┬───────┘ └───────────┬───────────┘ │
│         └────────┬───────┴─────────────────────┘             │
│                  │                                            │
│  2. Add libraries as needed:                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐   │
│  │ your-cosmosdb-lib │ │ your-storage-lib  │ │ (future libraries) │   │
│  │ uv add       │ │ uv add       │ │                    │   │
│  └──────────────┘ └──────────────┘ └────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## 1. Reusable Libraries (install via PyPI)

These are **dependencies** — install them into any project that needs their functionality.
They do NOT define project structure; they provide building blocks.

### 1.1 your-cosmosdb-lib — Azure Cosmos DB Helper

|                  |                                                                                                     |
| ---------------- | --------------------------------------------------------------------------------------------------- |
| **Repository**   | [your-org/your-cosmosdb-library](https://github.com/your-org/your-cosmosdb-library) |
| **PyPI package** | `your-cosmosdb-lib`                                                                                      |
| **Install**      | `uv add your-cosmosdb-lib  # replace with your library`                                                                               |
| **Python**       | 3.12+                                                                                               |
| **API support**  | Cosmos DB SQL API + MongoDB API                                                                     |

**What it provides:**

- **Repository Pattern** with `RepositoryBase[TEntity, TKey]` for type-safe CRUD
- **Pydantic entities** via `RootEntityBase["EntityName", KeyType]` with full validation
- **Predicate-to-SQL conversion** — use Python dicts instead of raw SQL for most queries
- **Automatic partition key handling** and connection pooling
- **Async/sync support** with enterprise-grade error handling and retry logic
- **Azure AD authentication** (SQL API) via `azure-identity`

**When to use:**

- Any project that reads/writes Azure Cosmos DB (SQL or MongoDB API)
- Prefer this over raw `azure-cosmos` SDK usage

**Copilot behavior:**

- When asked to add Cosmos DB access, use `your-cosmosdb-lib` and follow the Repository Pattern.
- Define entities extending `RootEntityBase["EntityName", KeyType]` (type variables are mandatory).
- Define repositories extending `RepositoryBase[Entity, KeyType]`.
- For complex queries, use `query_raw_dynamic_cursor_async()` for raw SQL.
- Do NOT create raw `CosmosClient` instances; use the library's repository abstractions.
- Reference the [API Reference](https://github.com/your-org/your-cosmosdb-library/blob/main/API_REFERENCE.md) and [Hands-On Guide](https://github.com/your-org/your-cosmosdb-library/blob/main/HANDS_ON_GUIDE.md) for patterns.

**Quick example:**

```python
from your_org.cosmosdb.sql import RootEntityBase, RepositoryBase

class Customer(RootEntityBase["Customer", str]):
    name: str
    email: str
    is_active: bool = True

class CustomerRepository(RepositoryBase[Customer, str]):
    def __init__(self, connection_string: str, database_name: str):
        super().__init__(
            connection_string=connection_string,
            database_name=database_name,
            container_name="customers"
        )

async def main():
    repo = CustomerRepository("your-connection-string", "mydb")
    async with repo:
        customer = Customer(id="cust-001", name="John Doe", email="john@example.com")
        await repo.add_async(customer)
        active = await repo.find_async({"is_active": True})
```

---

### 1.2 your-storage-lib — Azure Storage Blob & Queue Helper

|                  |                                                                                                                 |
| ---------------- | --------------------------------------------------------------------------------------------------------------- |
| **Repository**   | [your-org/your-storage-library](https://github.com/your-org/your-storage-library) |
| **PyPI package** | `your-storage-lib`                                                                                                   |
| **Install**      | `uv add your-storage-lib  # replace with your library`                                                                                            |
| **Python**       | 3.12+                                                                                                           |
| **Services**     | Azure Blob Storage + Azure Queue Storage                                                                        |

**What it provides:**

- **Blob operations**: upload, download, copy, move, delete, metadata, batch ops, team URL generation
- **Queue operations**: send, receive, peek, delete, batch processing, worker patterns
- **Multiple auth methods**: DefaultAzureCredential, ManagedIdentity, Account Keys, Connection Strings
- **User Delegation SAS** with clock skew protection
- **Async/sync feature parity** with full async context manager support
- **Large file support** with progress tracking and chunked upload

**When to use:**

- Any project that uses Azure Blob Storage or Azure Queue Storage
- Prefer this over raw `azure-storage-blob` / `azure-storage-queue` SDK usage

**Copilot behavior:**

- When asked to add blob or queue operations, use `your-storage-lib`.
- Use `AsyncStorageBlobHelper` for blob operations, `AsyncStorageQueueHelper` for queue operations.
- Always use `async with` context manager for proper resource cleanup.
- For team token generation, use the built-in `generate_blob_sas_url()` method.
- Do NOT create raw `BlobServiceClient` or `QueueServiceClient` instances.
- Reference the repo README for the full API surface and examples.

**Quick example:**

```python
from your_org.storage.blob import AsyncStorageBlobHelper

async def example():
    async with AsyncStorageBlobHelper(account_name="myaccount") as helper:
        await helper.upload_blob("container", "file.txt", "Hello World!")
        sas_url = await helper.generate_blob_sas_url(
            container_name="container",
            blob_name="file.txt",
            permissions="r",
            expiry_hours=1
        )
        blobs = await helper.list_blobs("container")
```

---

## 2. Scaffolding Templates (clone to start a new project)

These define **project structure, patterns, and conventions**. Clone one as your starting point,
then add libraries from Section 1 as needed.

### 2.1 python_application_template — Base Application

|                     |                                                                                                               |
| ------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Repository**      | [your-org/your-app-template](https://github.com/your-org/your-app-template) |
| **Type**            | General-purpose Python application                                                                            |
| **Python**          | 3.12+                                                                                                         |
| **Package manager** | UV                                                                                                            |

**What it provides:**

- **Abstract base class pattern** (`Application_Base`) — extensible for any application type
- **AppContext** for dependency injection and configuration access
- **Azure App Configuration** integration with automatic env var mapping
- **Pydantic-based settings** with type validation
- **DefaultAzureCredential** for Azure authentication
- **Infrastructure-as-Code** (Bicep) for Azure resource provisioning
- **Comprehensive test suite** with Azure service mocking

**When to use:**

- Starting **any new Python application** (console app, worker, data pipeline, CLI tool)
- When you need the base patterns but NOT a web API framework
- As the foundation that `python_api_application_template` builds upon

**Project structure:**

```
src/
├── main.py                          # Entry point
├── libs/
│   ├── application/                 # AppContext, Configuration (Pydantic)
│   ├── azure/                       # Azure App Configuration helper
│   └── base/                        # Application_Base abstract class
infra/                               # Bicep templates
tests/                               # pytest suite
```

**Copilot behavior:**

- When asked to "create a new Python app/service/worker", scaffold from this template.
- Follow the `Application_Base` → concrete `Application` pattern.
- Use `AppContext` for DI, not ad-hoc global state.
- Use Pydantic `BaseSettings` for configuration, not raw `os.getenv()`.

---

### 2.2 python_api_application_template — FastAPI Service

|                     |                                                                                                                       |
| ------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Repository**      | [your-org/your-api-template](https://github.com/your-org/your-api-template) |
| **Type**            | FastAPI web API                                                                                                       |
| **Python**          | 3.12+                                                                                                                 |
| **Framework**       | FastAPI + Uvicorn                                                                                                     |
| **Package manager** | UV                                                                                                                    |

**What it provides:**

Everything from `python_application_template`, plus:

- **FastAPI** with automatic OpenAPI docs
- **Advanced DI container** — C#-style with singleton, transient, and auto-scoped lifetimes
- **Protocol-based interfaces** for type-safe service contracts
- **Router pattern** with modular route modules
- **Health/readiness probes** built in
- **Docker-ready** containerization support

**When to use:**

- Starting a **new REST API or web service**
- When you need endpoint routing, OpenAPI docs, and HTTP-level patterns

**Project structure:**

```
app/
├── main.py                          # FastAPI app + DI setup
├── routers/                         # Route modules
│   ├── http_probes.py               # Health/readiness
│   ├── router_one.py                # Business endpoints
│   └── router_di.py                 # DI demo routes
├── business_component/              # Business logic layer
└── libs/                            # Framework libraries (same base as application_template)
infra/                               # Bicep templates
tests/                               # pytest suite
```

**Copilot behavior:**

- When asked to "create a new API/endpoint/microservice", scaffold from this template.
- Register services via `app_context.add_singleton()` / `add_transient()`.
- Resolve services via `await app_context.get_service(IMyService)`.
- Define interfaces as Python `Protocol` classes.
- Follow the router pattern: one file per resource/domain area under `routers/`.

---

### 2.3 python_agent_framework_dev_template — AI Agent Application

|                     |                                                                                                                               |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **Repository**      | [your-org/your-agent-template](https://github.com/your-org/your-agent-template) |
| **Type**            | Azure AI Agent Framework application                                                                                          |
| **Python**          | 3.12+                                                                                                                         |
| **Framework**       | Azure AI Agent Framework + MCP                                                                                                |
| **Package manager** | UV                                                                                                                            |

**What it provides:**

- **Azure AI Foundry** integration for intelligent agent development
- **TaskGroup-safe MCP context manager** (`MCPContext`) with AsyncExitStack
- **Comprehensive middleware system** — debugging, logging, input observation
- **Multi-agent workflow support** with GroupChat orchestrator
- **7+ sample agents** (basic, function calling, code interpreter, image analysis, MCP, threads, multi-agent)
- **Tool sharing** across multiple agents without scope violations

**When to use:**

- Building **AI agent applications** with Azure AI Foundry
- Working with **Model Context Protocol (MCP)** tools
- Implementing **multi-agent orchestration** workflows

**Project structure:**

```
src/
├── libs/
│   └── agent_framework/            # Core framework
│       ├── mcp_context.py           # TaskGroup-safe MCP manager
│       ├── middleware/              # Debugging, logging, observation
│       └── README_ORCHESTRATOR.md   # GroupChat docs
├── samples/                        # 7+ working agent examples
│   ├── basic/
│   ├── function_calling/
│   ├── code_interpreter/
│   └── workflow/groupchat/
infra/                               # Bicep templates
tests/                               # 48+ tests
```

**Copilot behavior:**

- When asked to "create an AI agent/chatbot/assistant", scaffold from this template.
- Use `MCPContext` for MCP tool lifecycle management (never manage tool scopes manually).
- Apply middleware for debugging and logging (do not add ad-hoc print statements).
- For multi-agent scenarios, use the GroupChat orchestrator pattern.
- Follow the sample agent patterns for new agent implementations.

---

## 3. Adding new entries to this catalog

When adding a new library or template, follow this format:

### For libraries:

```markdown
### X.Y <package-name> — Short Description

|                  |                                                   |
| ---------------- | ------------------------------------------------- |
| **Repository**   | [org/repo-name](https://github.com/org/repo-name) |
| **PyPI package** | `package-name`                                    |
| **Install**      | `uv add package-name`                             |
| **Python**       | 3.12+                                             |

**What it provides:** (bullet list of capabilities)
**When to use:** (1-2 lines)
**Copilot behavior:** (specific rules for Copilot)
**Quick example:** (minimal code sample)
```

### For templates:

```markdown
### X.Y repo_name — Short Description

|                |                                                   |
| -------------- | ------------------------------------------------- |
| **Repository** | [org/repo-name](https://github.com/org/repo-name) |
| **Type**       | Application type                                  |
| **Python**     | 3.12+                                             |

**What it provides:** (bullet list)
**When to use:** (1-2 lines)
**Project structure:** (tree view)
**Copilot behavior:** (specific rules)
```
