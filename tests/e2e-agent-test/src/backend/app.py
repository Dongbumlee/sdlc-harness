# CANARY: No copyright header (Code Quality Reviewer should catch)

import os
import json
from fastapi import FastAPI
from azure.cosmos import CosmosClient  # CANARY: Raw SDK — should use approved Cosmos DB library
from azure.storage.blob import BlobServiceClient  # CANARY: Raw SDK — should use approved Storage library

app = FastAPI()

# CANARY: Hardcoded API key (Security Reviewer should catch)
OPENAI_API_KEY = "sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234"

# CANARY: Hardcoded connection string (Security Reviewer should catch)
COSMOS_CONNECTION_STRING = "AccountEndpoint=https://myaccount.documents.azure.com:443/;AccountKey=abc123def456ghi789=="

# CANARY: No structured logging — using print (Deployment Readiness Reviewer should catch)
print("Starting application...")


def get_cosmos_client():
    """CANARY: Direct CosmosClient instantiation — violates Repository Pattern."""
    client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
    return client


def get_blob_client():
    """CANARY: Raw BlobServiceClient — should use approved Storage library with async with."""
    return BlobServiceClient.from_connection_string(
        "DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=abc123=="
    )


# CANARY: No global exception handler (Deployment Readiness Reviewer should catch)
# CANARY: No health endpoint (Deployment Readiness Reviewer should catch)


@app.get("/api/documents")
def list_documents():
    """CANARY: No docstring on public API (Code Quality Reviewer should catch)
    CANARY: No auth check (Security Reviewer should catch — A01 Broken Access Control)
    CANARY: Unbounded query — no pagination (Deployment Readiness Reviewer should catch)
    """
    client = get_cosmos_client()
    db = client.get_database_client("documents")
    container = db.get_container_client("items")
    # CANARY: No LIMIT/TOP — returns all items
    items = list(container.query_items("SELECT * FROM c", enable_cross_partition_query=True))
    return items


@app.get("/api/documents/{doc_id}")
def get_document(doc_id: str):
    # CANARY: No input validation — doc_id could be anything
    client = get_cosmos_client()
    db = client.get_database_client("documents")
    container = db.get_container_client("items")
    item = container.read_item(doc_id, partition_key=doc_id)
    return item


@app.post("/api/documents")
def create_document(data: dict):
    # CANARY: No type annotation on 'data' — should use Pydantic model
    # CANARY: No input sanitization
    client = get_cosmos_client()
    db = client.get_database_client("documents")
    container = db.get_container_client("items")
    container.create_item(data)
    return {"status": "created"}


@app.post("/api/chat")
def chat(message: dict):
    """CANARY: No timeout on external HTTP call (Deployment Readiness Reviewer)
    CANARY: No retry logic for LLM calls (LLM Behavior Reviewer)
    """
    import requests

    # CANARY: No timeout parameter
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": message["text"]}],
            # CANARY: No max_tokens limit (LLM Behavior Reviewer should catch)
        },
    )
    result = response.json()
    return result


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
    """CANARY: No authorization check — anyone can delete."""
    client = get_cosmos_client()
    db = client.get_database_client("documents")
    container = db.get_container_client("items")
    container.delete_item(doc_id, partition_key=doc_id)
    return {"status": "deleted"}


# CANARY: Error handler returns raw exception details (Security + Deployment Readiness)
@app.exception_handler(Exception)
async def generic_error_handler(request, exc):
    return {"error": str(exc), "traceback": repr(exc.__traceback__)}
