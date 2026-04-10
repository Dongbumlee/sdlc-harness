# Reference Catalog: Libraries and Scaffolding Templates

> **📋 TEMPLATE:** This file ships with example entries showing the expected format.
> Replace them with your team's actual libraries, templates, and conventions.

> **SDLC alignment:** This catalog supports all SDLC phases, especially **Phase 2 (Design)**, **Phase 3 (Repo Structure)**,
> and **Phase 4 (Implementation)**. Consult it when choosing how to scaffold a new project or which libraries to use.

This document is the authoritative registry of reusable libraries and scaffolding templates maintained by your team.
Copilot and engineers MUST consult this catalog before introducing new dependencies or inventing new patterns.

---

## How to use this catalog

1. **Starting a new project?** → Pick a **Scaffolding Template** that matches your language and application type.
2. **Need Azure service access?** → Add the appropriate **SDK** for your language from Section 1.
3. **Adding a new entry?** → Follow the format in Section 3.

```
┌──────────────────────────────────────────────────────────────────┐
│                      YOUR NEW PROJECT                            │
│                                                                  │
│  1. Pick your language stack:                                    │
│  ┌─────────┐ ┌──────┐ ┌────┐ ┌────┐ ┌────────────┐ ┌──────┐    │
│  │ Python  │ │ Java │ │ C# │ │ Go │ │ TypeScript │ │ Rust │    │
│  └────┬────┘ └──┬───┘ └─┬──┘ └─┬──┘ └─────┬──────┘ └──┬───┘    │
│       └─────────┴───────┴──────┴───────────┴───────────┘        │
│                          │                                       │
│  2. Scaffold from a template (see template matrix):              │
│  ┌──────────────┐ ┌──────────────┐ ┌───────────────────────┐    │
│  │  Base App    │ │  Web API     │ │  AI Agent             │    │
│  └──────┬───────┘ └──────┬───────┘ └───────────┬───────────┘    │
│         └────────┬───────┴─────────────────────┘                │
│                  │                                               │
│  3. Add Azure SDK libraries as needed:                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Cosmos DB│ │ Storage  │ │ Identity │ │ OpenAI   │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 1. Reusable Libraries (Azure SDKs by Service)

These are **dependencies** — install them into any project that needs their functionality.
They do NOT define project structure; they provide building blocks.

All SDKs below are official Azure SDK releases. Use the package for your language stack.

---

### 1.1 Azure Cosmos DB — Database Access

| Language | Library/SDK | Package | Install |
|----------|-------------|---------|---------|
| Python | azure-cosmos | `azure-cosmos` | `pip install azure-cosmos` |
| Java | azure-spring-data-cosmos | `com.azure.spring:spring-cloud-azure-starter-data-cosmos` | Maven/Gradle |
| C# | Microsoft.Azure.Cosmos | `Microsoft.Azure.Cosmos` | `dotnet add package Microsoft.Azure.Cosmos` |
| Go | azcosmos | `github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos` | `go get` |
| TypeScript | @azure/cosmos | `@azure/cosmos` | `npm install @azure/cosmos` |

**What it provides:**

- Type-safe CRUD against Cosmos DB SQL API containers
- Partition key management, cross-partition queries, and change feed
- Bulk/batch operations and transactional batch support
- Integrated retry policies and connection pooling

**When to use:** Any project that reads/writes Azure Cosmos DB.

**Copilot behavior:**

- Always authenticate via `DefaultAzureCredential` (see §1.3) — avoid hardcoded keys.
- Use the repository/service pattern appropriate to each language (Spring Data for Java, DI-registered `CosmosClient` for C#, etc.).
- Specify partition key on every point-read/write to avoid cross-partition overhead.
- For complex queries, prefer parameterized SQL over string concatenation.

**Quick examples:**

<details><summary>Python</summary>

```python
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential

client = CosmosClient("https://myaccount.documents.azure.com", DefaultAzureCredential())
db = client.get_database_client("mydb")
container = db.get_container_client("customers")

container.upsert_item({"id": "cust-001", "name": "John Doe", "pk": "us-east"})
results = container.query_items("SELECT * FROM c WHERE c.name = @name",
    parameters=[{"name": "@name", "value": "John Doe"}], partition_key="us-east")
```
</details>

<details><summary>Java (Spring Data)</summary>

```java
@Container(containerName = "customers")
public class Customer {
    @Id private String id;
    @PartitionKey private String region;
    private String name;
}

public interface CustomerRepository extends CosmosRepository<Customer, String> {
    List<Customer> findByName(String name);
}
```
</details>

<details><summary>C#</summary>

```csharp
using Microsoft.Azure.Cosmos;
using Azure.Identity;

var client = new CosmosClient("https://myaccount.documents.azure.com", new DefaultAzureCredential());
var container = client.GetContainer("mydb", "customers");

await container.UpsertItemAsync(new { id = "cust-001", name = "John Doe", pk = "us-east" },
    new PartitionKey("us-east"));
```
</details>

---

### 1.2 Azure Storage — Blob & Queue

| Language | Library/SDK | Package | Install |
|----------|-------------|---------|---------|
| Python | azure-storage-blob | `azure-storage-blob` | `pip install azure-storage-blob` |
| Java | azure-storage-blob | `com.azure:azure-storage-blob` | Maven/Gradle |
| C# | Azure.Storage.Blobs | `Azure.Storage.Blobs` | `dotnet add package Azure.Storage.Blobs` |
| Go | azblob | `github.com/Azure/azure-sdk-for-go/sdk/storage/azblob` | `go get` |
| TypeScript | @azure/storage-blob | `@azure/storage-blob` | `npm install @azure/storage-blob` |

**What it provides:**

- Blob upload, download, copy, delete, metadata, and listing
- User Delegation SAS generation with clock skew protection
- Large file support with chunked/parallel upload and progress tracking
- Queue send, receive, peek, delete, and batch processing (via `azure-storage-queue` equivalents)

**When to use:** Any project that uses Azure Blob Storage or Azure Queue Storage.

**Copilot behavior:**

- Authenticate via `DefaultAzureCredential` — prefer User Delegation SAS over account keys.
- Always dispose/close clients (use context managers in Python, `using` in C#, `defer` in Go).
- For large uploads (>256 MB), use the SDK's built-in chunked upload — do NOT implement manual chunking.
- For SAS URLs, set the shortest practical expiry and restrict permissions to the minimum needed.

**Quick examples:**

<details><summary>Python</summary>

```python
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

client = BlobServiceClient("https://myaccount.blob.core.windows.net", DefaultAzureCredential())
blob = client.get_blob_client("mycontainer", "file.txt")
blob.upload_blob(b"Hello World!", overwrite=True)
```
</details>

<details><summary>Java</summary>

```java
BlobServiceClient client = new BlobServiceClientBuilder()
    .endpoint("https://myaccount.blob.core.windows.net")
    .credential(new DefaultAzureCredentialBuilder().build())
    .buildClient();
BlobClient blob = client.getBlobContainerClient("mycontainer").getBlobClient("file.txt");
blob.upload(BinaryData.fromString("Hello World!"), true);
```
</details>

<details><summary>C#</summary>

```csharp
using Azure.Storage.Blobs;
using Azure.Identity;

var client = new BlobServiceClient(new Uri("https://myaccount.blob.core.windows.net"),
    new DefaultAzureCredential());
var blob = client.GetBlobContainerClient("mycontainer").GetBlobClient("file.txt");
await blob.UploadAsync(BinaryData.FromString("Hello World!"), overwrite: true);
```
</details>

---

### 1.3 Azure Identity — Authentication

| Language | Library | Package | Install |
|----------|---------|---------|---------|
| Python | azure-identity | `azure-identity` | `pip install azure-identity` |
| Java | azure-identity | `com.azure:azure-identity` | Maven/Gradle |
| C# | Azure.Identity | `Azure.Identity` | `dotnet add package Azure.Identity` |
| Go | azidentity | `github.com/Azure/azure-sdk-for-go/sdk/azidentity` | `go get` |
| TypeScript | @azure/identity | `@azure/identity` | `npm install @azure/identity` |

**What it provides:**

- `DefaultAzureCredential` — a single credential that works in local dev, CI, and production
- Chains: Environment → Workload Identity → Managed Identity → Azure CLI → Azure PowerShell
- Token caching and automatic refresh

**When to use:** **Every** project that talks to Azure services. This is the standard auth mechanism.

**Copilot behavior:**

- Always use `DefaultAzureCredential` unless there is a documented reason to use a specific credential type.
- Never hardcode client secrets or connection strings in source code.
- In Dockerfiles, ensure the runtime has a managed identity or workload identity configured.

**Quick examples:**

<details><summary>Python</summary>

```python
from azure.identity import DefaultAzureCredential
credential = DefaultAzureCredential()
```
</details>

<details><summary>Java</summary>

```java
DefaultAzureCredential credential = new DefaultAzureCredentialBuilder().build();
```
</details>

<details><summary>C#</summary>

```csharp
var credential = new DefaultAzureCredential();
```
</details>

---

### 1.4 AI & Agents — Microsoft Agent Framework (Primary) + Azure OpenAI SDK (Fallback)

> **Guidance:** Use **Microsoft Agent Framework** as the primary choice for building AI agents
> and LLM-powered applications. Fall back to **Azure OpenAI SDK** only for direct model access
> (e.g., simple chat completions, embeddings) where the Agent Framework is overkill.
> Use Semantic Kernel or LangChain **only** when there are specific requirements that the
> Agent Framework does not cover (e.g., existing SK/LC codebase, specific orchestration patterns).

#### Primary: Microsoft Agent Framework

| Language | Library | Package | Install |
|----------|---------|---------|---------|
| Python | azure-ai-projects | `azure-ai-projects` | `pip install azure-ai-projects` |
| C# | Azure.AI.Projects | `Azure.AI.Projects` | `dotnet add package Azure.AI.Projects` |
| TypeScript | @azure/ai-projects | `@azure/ai-projects` | `npm install @azure/ai-projects` |
| Java | azure-ai-projects | `com.azure:azure-ai-projects` | Maven/Gradle |

**What it provides:**

- Multi-agent orchestration with tool/function calling
- Built-in MCP (Model Context Protocol) tool integration
- Azure AI Foundry project lifecycle management
- File search, code interpreter, and custom tool agents
- Streaming, async execution, and enterprise-grade observability

**When to use:** Any project that builds AI agents, chatbots, multi-agent workflows, or RAG applications.

#### Fallback: Azure OpenAI SDK (Direct Model Access)

| Language | Library | Package | Install |
|----------|---------|---------|---------|
| Python | openai | `openai` | `pip install openai` |
| Java | azure-ai-openai | `com.azure:azure-ai-openai` | Maven/Gradle |
| C# | Azure.AI.OpenAI | `Azure.AI.OpenAI` | `dotnet add package Azure.AI.OpenAI` |
| Go | azopenai | `github.com/Azure/azure-sdk-for-go/sdk/ai/azopenai` | `go get` |
| TypeScript | openai / @azure/openai | `openai` or `@azure/openai` | `npm install openai` |

**When to use:** Simple, direct model calls (chat completions, embeddings, image generation)
where agent orchestration is not needed.

**Copilot behavior:**

1. **Default to Microsoft Agent Framework** for any AI/agent task.
2. Fall back to Azure OpenAI SDK only for simple, single-model interactions.
3. Do NOT introduce Semantic Kernel or LangChain unless the user explicitly requests it
   or the project already uses it.
4. For Azure-hosted models, always use `DefaultAzureCredential` — not API keys.
5. Set `api_version` explicitly; do not rely on defaults.
6. For RAG patterns, combine with Azure AI Search — do not build custom vector stores.

**Quick examples:**

<details><summary>Python — Agent Framework (Primary)</summary>

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

project = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint="https://my-project.services.ai.azure.com",
)
agent = project.agents.create_agent(
    model="gpt-4o",
    name="my-assistant",
    instructions="You are a helpful assistant.",
)
```
</details>

<details><summary>Python — Azure OpenAI SDK (Fallback)</summary>

```python
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
client = AzureOpenAI(azure_endpoint="https://my-resource.openai.azure.com",
    azure_ad_token_provider=token_provider, api_version="2024-06-01")
response = client.chat.completions.create(model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}])
```
</details>

<details><summary>C# — Agent Framework (Primary)</summary>

```csharp
using Azure.AI.Projects;
using Azure.Identity;

var client = new AIProjectClient(
    new Uri("https://my-project.services.ai.azure.com"),
    new DefaultAzureCredential());
var agent = await client.Agents.CreateAgentAsync("gpt-4o",
    name: "my-assistant", instructions: "You are a helpful assistant.");
```
</details>

---

## 2. Scaffolding Templates (clone to start a new project)

These define **project structure, patterns, and conventions**. Clone one as your starting point,
then add libraries from Section 1 as needed.

### Template Matrix

Pick the cell that matches your language + application type:

| Stack | Web App (Frontend) | Web API (Backend) | Base App | AI Agent |
|-------|-------------------|-------------------|----------|----------|
| **TypeScript** | React / Next.js / Angular | Express / NestJS | Node.js CLI | Microsoft Agent Framework |
| **Python** | Streamlit / Gradio | FastAPI + Uvicorn | Application_Base (UV) | Microsoft Agent Framework |
| **Java** | Vaadin / Thymeleaf | Spring Boot | Spring CLI | Microsoft Agent Framework |
| **C#** | Blazor / Razor Pages | ASP.NET Core Minimal API | .NET Worker Service | Microsoft Agent Framework |
| **Go** | Templ + HTMX | Gin / Echo / Chi | Cobra CLI | Microsoft Agent Framework (via REST) |
| **Rust** | Leptos / Yew / Dioxus | Actix-web / Axum | Clap CLI | Microsoft Agent Framework (via REST) |

> **Web App column:** TypeScript (React/Next.js/Angular) is the most common enterprise choice for SPAs.
> Other languages offer SSR or hybrid options for teams preferring a single-language stack.

> **AI Agent column:** Microsoft Agent Framework is the primary choice for all languages.
> For Go and Rust, use the REST API or Python/C#/TS SDK via sidecar.
> Use Semantic Kernel or LangChain only when there are specific requirements.

> **Note:** The detailed templates below describe **patterns**, not specific Python repos.
> Teams should register their own language-specific template repos following this format.

---

### 2.1 Base Application Template

|                     |                                                                 |
| ------------------- | --------------------------------------------------------------- |
| **Repository**      | *Register your team's base app template here*                   |
| **Type**            | General-purpose application (console, worker, pipeline, CLI)    |

**What it provides:**

- Application entry point with lifecycle management (startup, run, shutdown)
- Dependency injection / service container
- Configuration management (Azure App Configuration, env vars, config files)
- Azure authentication via `DefaultAzureCredential`
- Infrastructure-as-Code (Bicep) for Azure resource provisioning
- Test suite scaffolding

**Typical structure by language:**

| Language | Entry point | DI/Config | Package manager |
|----------|-------------|-----------|-----------------|
| Python | `src/main.py` | AppContext + Pydantic BaseSettings | UV / pip |
| Java | `src/main/java/.../Application.java` | Spring DI + `application.yml` | Maven / Gradle |
| C# | `Program.cs` | `IHost` + `IConfiguration` | dotnet CLI |
| Go | `cmd/app/main.go` | Wire / manual DI + Viper | go modules |
| TypeScript | `src/index.ts` | tsyringe / InversifyJS | npm / pnpm |
| Rust | `src/main.rs` | Manual DI + config crate | Cargo |

**When to use:** Any new application that does NOT need a web API framework.

**Copilot behavior:**

- Scaffold from the team's registered base template for "create a new app/service/worker" requests.
- Follow the project's DI pattern — do not introduce ad-hoc globals.
- Use the language's standard config approach, not raw environment variable reads.

---

### 2.2 Web App Template (Frontend / Full-Stack)

|                     |                                                                 |
| ------------------- | --------------------------------------------------------------- |
| **Repository**      | *Register your team's web app template here*                    |
| **Type**            | Single-page application (SPA), server-rendered, or full-stack   |

**What it provides:**

- Frontend framework with component architecture and routing
- State management (client-side or server-side)
- API client integration (REST or GraphQL) with authentication
- Build tooling, bundling, and dev server with hot reload
- Accessibility (WCAG 2.1 AA) and responsive layout scaffolding
- Unit + integration test setup (component testing)
- CI/CD-ready build output (static assets or container)

**Typical framework by language:**

| Language | SPA Framework | SSR / Hybrid | Build tool | Test framework |
|----------|--------------|-------------|------------|----------------|
| TypeScript | React + Vite / Angular | Next.js / Nuxt | Vite / Webpack | Vitest + Testing Library |
| Python | — | Streamlit / Gradio | pip | pytest |
| Java | — | Vaadin / Thymeleaf | Maven / Gradle | JUnit + Selenium |
| C# | Blazor WebAssembly | Blazor Server / Razor Pages | dotnet CLI | bUnit / Playwright |
| Go | — | Templ + HTMX | go build | go test + Playwright |
| Rust | Leptos / Yew / Dioxus | Leptos SSR | Trunk / cargo-leptos | wasm-bindgen-test |

**When to use:** Any user-facing web application — dashboards, portals, admin UIs, chat interfaces.

**Copilot behavior:**

- Scaffold from the team's registered web app template for "create a new UI/dashboard/portal" requests.
- TypeScript (React/Next.js) is the default recommendation for SPAs unless the team specifies otherwise.
- Follow component-based architecture: one component per file, co-located styles and tests.
- Use the project's API client pattern for backend calls — do not use raw `fetch()` without abstraction.
- Ensure all interactive elements meet WCAG 2.1 AA accessibility standards.

---

### 2.3 Web API Template

|                     |                                                                 |
| ------------------- | --------------------------------------------------------------- |
| **Repository**      | *Register your team's API template here*                        |
| **Type**            | REST API / web service                                          |

**What it provides:**

Everything from the Base Application Template, plus:

- Web framework with automatic API docs (OpenAPI/Swagger)
- Router/controller pattern with modular route registration
- Health/readiness probes (`/health`, `/ready`)
- Request validation and error handling middleware
- Docker-ready containerization

**Typical framework by language:**

| Language | Framework | API docs | Health probes |
|----------|-----------|----------|---------------|
| Python | FastAPI + Uvicorn | Built-in OpenAPI | Custom router |
| Java | Spring Boot | springdoc-openapi | Spring Actuator |
| C# | ASP.NET Core Minimal API | Swashbuckle / NSwag | `MapHealthChecks()` |
| Go | Gin / Echo / Chi | swaggo/swag | Custom handler |
| TypeScript | Express / NestJS | swagger-jsdoc / @nestjs/swagger | Custom middleware |
| Rust | Actix-web / Axum | utoipa | Custom handler |

**When to use:** New REST APIs, microservices, or web services needing endpoint routing.

**Copilot behavior:**

- Scaffold from the team's registered API template for "create a new API/endpoint/microservice" requests.
- Follow the router/controller pattern: one module per resource/domain area.
- Define service interfaces/contracts for testability.

---

### 2.4 AI Agent Template

|                     |                                                                 |
| ------------------- | --------------------------------------------------------------- |
| **Repository**      | *Register your team's agent template here*                      |
| **Type**            | AI agent application (Microsoft Agent Framework)                |

**What it provides:**

- Microsoft Agent Framework integration with Azure AI Foundry
- MCP (Model Context Protocol) tool lifecycle management
- Middleware system for debugging, logging, and observability
- Multi-agent orchestration patterns (group chat, handoff)
- Sample agents demonstrating common patterns

**Typical structure by language:**

| Language | Agent SDK | MCP support | Multi-agent |
|----------|-----------|-------------|-------------|
| Python | azure-ai-projects | Native | GroupChat orchestrator |
| C# | Azure.AI.Projects | Native | AgentGroupChat |
| TypeScript | @azure/ai-projects | Native | Custom orchestration |
| Java | azure-ai-projects | Native | Custom orchestration |
| Go / Rust | REST API | Via HTTP | Custom orchestration |

**When to use:** AI agent applications, chatbots, RAG systems, or multi-agent workflows.

**Copilot behavior:**

- Scaffold from the team's registered agent template for "create an AI agent/chatbot/assistant" requests.
- Use Microsoft Agent Framework as the primary approach (see §1.4).
- Use MCP context managers for tool lifecycle — never manage tool scopes manually.
- Apply middleware for debugging/logging. Use multi-agent orchestration for complex workflows.

---

## 3. Adding new entries to this catalog

When adding a new library or template, follow the language-agnostic formats below.

### For libraries:

```markdown
### X.Y <service-name> — Short Description

| Language | Library | Package | Install |
|----------|---------|---------|---------|
| Python   | ...     | `...`   | `pip install ...` |
| Java     | ...     | `...`   | Maven/Gradle |
| C#       | ...     | `...`   | `dotnet add package ...` |
| Go       | ...     | `...`   | `go get ...` |
| TypeScript | ...   | `...`   | `npm install ...` |

**What it provides:** (bullet list of capabilities)
**When to use:** (1-2 lines)
**Copilot behavior:** (specific rules for Copilot)
**Quick examples:** (one code block per language, using <details> tags)
```

### For templates:

```markdown
### X.Y repo_name — Short Description

|                    |                                                   |
| ------------------ | ------------------------------------------------- |
| **Repository**     | [org/repo-name](https://github.com/org/repo-name) |
| **Type**           | Application type                                  |
| **Language**       | Language + version                                |
| **Framework**      | Framework name                                    |
| **Package manager**| Package manager name                              |

**What it provides:** (bullet list)
**When to use:** (1-2 lines)
**Project structure:** (tree view)
**Copilot behavior:** (specific rules)
```
