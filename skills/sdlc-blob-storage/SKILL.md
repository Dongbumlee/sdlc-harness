---
name: sdlc-blob-storage
description: >-
  Implement Azure Blob Storage and Queue operations using the approved Storage library library.
  Use when uploading, downloading, listing, or managing blobs and queues.
  Triggers on blob, storage, file upload, queue, or Azure Storage requests.
  Never use raw azure-storage-blob or azure-storage-queue — always use the approved Storage library.
---

# Azure Blob Storage & Queue — the approved Storage library Library

## When to use

- Uploading or downloading files to/from Azure Blob Storage
- Listing, copying, moving, or deleting blobs
- Generating team URLs for blob access
- Sending or receiving messages from Azure Queue Storage
- Reviewing code that interacts with Azure Storage

## Step 1: Load live SDK patterns

Fetch the latest patterns from GitHub MCP:

```
mcp_github_get_file_contents(
  owner: "the project's GitHub org",
  repo: "the Storage library repo",
  path: "README.md"
)
```

## Step 2: Blob operations

Always use `AsyncStorageBlobHelper` with `async with` context manager:

```python
from <project_storage_lib>.blob import AsyncStorageBlobHelper

async def upload_document(account_name: str, container: str, name: str, data: bytes):
    """Upload a document to blob storage."""
    async with AsyncStorageBlobHelper(account_name=account_name) as helper:
        await helper.upload_blob(container, name, data)

async def download_document(account_name: str, container: str, name: str) -> bytes:
    """Download a document from blob storage."""
    async with AsyncStorageBlobHelper(account_name=account_name) as helper:
        return await helper.download_blob(container, name)

async def generate_read_url(account_name: str, container: str, name: str) -> str:
    """Generate a time-limited read-only team URL."""
    async with AsyncStorageBlobHelper(account_name=account_name) as helper:
        return await helper.generate_blob_sas_url(
            container_name=container,
            blob_name=name,
            permissions="r",
            expiry_hours=1
        )

async def list_all_blobs(account_name: str, container: str) -> list:
    """List all blobs in a container."""
    async with AsyncStorageBlobHelper(account_name=account_name) as helper:
        return await helper.list_blobs(container)
```

## Step 3: Queue operations

Use `AsyncStorageQueueHelper` with `async with` context manager:

```python
from <project_org>.storage.queue import AsyncStorageQueueHelper

async def send_message(account_name: str, queue_name: str, message: str):
    """Send a message to the queue."""
    async with AsyncStorageQueueHelper(account_name=account_name) as helper:
        await helper.send_message(queue_name, message)

async def receive_messages(account_name: str, queue_name: str, max_messages: int = 10):
    """Receive and process messages from the queue."""
    async with AsyncStorageQueueHelper(account_name=account_name) as helper:
        messages = await helper.receive_messages(queue_name, max_messages=max_messages)
        for msg in messages:
            # Process message...
            await helper.delete_message(queue_name, msg)
```

## Step 4: Authentication

The library supports multiple auth methods (in order of preference):

1. **DefaultAzureCredential** (production) — automatic Managed Identity
2. **Account name only** — uses `DefaultAzureCredential` internally
3. **Connection string** (local dev only) — pass `connection_string=` parameter

```python
# Production (Managed Identity)
async with AsyncStorageBlobHelper(account_name="myaccount") as helper:
    ...

# Local development (connection string)
async with AsyncStorageBlobHelper(connection_string="UseDevelopmentStorage=true") as helper:
    ...
```

## Step 5: Write unit tests

```python
from unittest.mock import AsyncMock, patch

class TestDocumentStorage:
    @pytest.mark.asyncio
    async def test_upload_document(self):
        mock_helper = AsyncMock(spec=AsyncStorageBlobHelper)
        with patch("mymodule.AsyncStorageBlobHelper", return_value=mock_helper):
            mock_helper.__aenter__ = AsyncMock(return_value=mock_helper)
            mock_helper.__aexit__ = AsyncMock(return_value=None)
            await upload_document("acct", "container", "file.txt", b"data")
            mock_helper.upload_blob.assert_called_once()
```

## Gotchas

- **Never create raw `BlobServiceClient` or `QueueServiceClient`** — `the approved Storage library`
  manages connection lifecycle, retry policies, and auth.
- **Always use `async with`** — this ensures proper resource cleanup. Forgetting it
  causes connection leaks.
- **SAS URL generation uses User Delegation SAS** with clock skew protection — do NOT
  generate team tokens manually.
- **Large file uploads** support progress tracking and chunked upload — use the
  library's built-in support, do NOT implement custom chunking.
- **Storage operations go in the Business layer** — the API layer calls Business
  services, which call storage helpers.

## Where files go

| Artifact | Location |
|---|---|
| Storage service class | `src/<Name>Business/src/libs/services/` |
| Unit tests | `src/<Name>Business/tests/unit/` |
| Integration tests | `src/<Name>Business/tests/integration/` |
