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

### 1.4 Azure OpenAI — AI & LLM

| Language | Library | Package | Install |
|----------|---------|---------|---------|
| Python | openai | `openai` | `pip install openai` |
| Java | azure-ai-openai | `com.azure:azure-ai-openai` | Maven/Gradle |
| C# | Azure.AI.OpenAI | `Azure.AI.OpenAI` | `dotnet add package Azure.AI.OpenAI` |
| Go | azopenai | `github.com/Azure/azure-sdk-for-go/sdk/ai/azopenai` | `go get` |
| TypeScript | openai / @azure/openai | `openai` or `@azure/openai` | `npm install openai` |

**What it provides:**

- Chat completions, embeddings, and image generation via Azure OpenAI endpoints
- Streaming responses for real-time UX
- Function calling / tool-use integration
- Content filtering and responsible AI controls (Azure-hosted)

**When to use:** Any project that integrates LLM capabilities (chat, summarization, RAG, agents).

**Copilot behavior:**

- For Azure-hosted models, use the Azure OpenAI client with `DefaultAzureCredential` — not API keys.
- Set `api_version` explicitly; do not rely on defaults.
- Always handle streaming with proper error/cancellation logic.
- For RAG patterns, combine with Azure AI Search — do not build custom vector stores.

**Quick examples:**

<details><summary>Python</summary>

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

<details><summary>Java</summary>

```java
OpenAIClient client = new OpenAIClientBuilder()
    .endpoint("https://my-resource.openai.azure.com")
    .credential(new DefaultAzureCredentialBuilder().build())
    .buildClient();
ChatCompletions completions = client.getChatCompletions("gpt-4o",
    new ChatCompletionsOptions(List.of(new ChatRequestUserMessage("Hello!"))));
```
</details>

<details><summary>C#</summary>

```csharp
using Azure.AI.OpenAI;
using Azure.Identity;

var client = new AzureOpenAIClient(new Uri("https://my-resource.openai.azure.com"),
    new DefaultAzureCredential());
var chatClient = client.GetChatClient("gpt-4o");
var response = await chatClient.CompleteChatAsync([new UserChatMessage("Hello!")]);
```
</details>

---

## 2. Scaffolding Templates (clone to start a new project)

These define **project structure, patterns, and conventions**. Clone one as your starting point,
then add libraries from Section 1 as needed.

### Template Matrix

Pick the cell that matches your language + application type:

| Stack | Web API | Base App | AI Agent |
|-------|---------|----------|----------|
| **Python** | FastAPI + Uvicorn | Application_Base (UV) | Azure AI Agent Framework |
| **Java** | Spring Boot | Spring CLI | Spring AI |
| **C#** | ASP.NET Core Minimal API | .NET Worker Service | Semantic Kernel |
| **Go** | Gin / Echo / Chi | Cobra CLI | LangChainGo |
| **TypeScript** | Express / NestJS | Node.js CLI | LangChain.js |
| **Rust** | Actix-web / Axum | Clap CLI | — |

> **Note:** The detailed templates below are Python examples. Teams should add equivalent
> entries for their language stack following the same format.

---

### 2.1 python_application_template — Base Application

|                     |                                                                                                               |
| ------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Repository**      | [your-org/your-app-template](https://github.com/your-org/your-app-template) |
| **Type**            | General-purpose Python application                                                                            |
| **Python**          | 3.12+                                                                                                         |
| **Package manager** | UV                                                                                                            |

**What it provides:** `Application_Base` abstract pattern, `AppContext` DI, Azure App Configuration integration, Pydantic settings, `DefaultAzureCredential`, Bicep IaC, and a pytest suite.

**When to use:** Any new Python app (console, worker, pipeline, CLI) that does NOT need a web API framework.

**Project structure:** `src/main.py` → `src/libs/{application, azure, base}` + `infra/` (Bicep) + `tests/`

**Copilot behavior:**

- Scaffold from this template for "create a new Python app/service/worker" requests.
- Follow `Application_Base` → concrete `Application` pattern. Use `AppContext` for DI, Pydantic `BaseSettings` for config.

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
