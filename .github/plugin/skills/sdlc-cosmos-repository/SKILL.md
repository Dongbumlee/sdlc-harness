---
name: sdlc-cosmos-repository
description: >-
  Implement Azure Cosmos DB data access using your-cosmosdb-lib library with Repository
  Pattern. Use when creating entities, repositories, or any Cosmos DB CRUD operations.
  Triggers on Cosmos DB, database, entity, repository, data model, or data access
  requests. Never use raw azure-cosmos SDK — always use your-cosmosdb-lib.
---

# Azure Cosmos DB — Repository Pattern with your-cosmosdb-lib

## When to use

- Creating new entities or data models backed by Cosmos DB
- Adding CRUD operations for any domain object
- Implementing queries, filtering, or pagination against Cosmos DB
- Reviewing code that accesses Cosmos DB

## Step 1: Load Cosmos DB data modeling guidance

For data modeling decisions (partition keys, denormalization, indexing):

```
mcp_awesome-copil_load_instruction(
  filename: "cosmosdb-datamodeling/SKILL.md",
  mode: "skills"
)
```

For live SDK patterns, fetch the latest from GitHub MCP:

```
mcp_github_get_file_contents(
  owner: "your-org",
  repo: "python_cosmosdb_helper",
  path: "README.md"
)
```

## Step 2: Define entities

Entities MUST extend `RootEntityBase` with explicit type variables:

```python
from your_org.cosmosdb.sql import RootEntityBase

class Customer(RootEntityBase["Customer", str]):
    """Customer entity stored in Cosmos DB.

    Attributes:
        name: Customer display name.
        email: Contact email address.
        is_active: Whether the customer account is active.
    """
    name: str
    email: str
    is_active: bool = True
```

**Rules:**
- Type variables are mandatory: `RootEntityBase["EntityName", KeyType]`
- `"EntityName"` must match the class name exactly
- `KeyType` is typically `str` (for GUID-based IDs)
- Use Pydantic field validation for constraints
- Entity goes in the **Business** layer: `src/<Name>Business/src/libs/`

## Step 3: Define repositories

Repositories MUST extend `RepositoryBase` with matching type variables:

```python
from your_org.cosmosdb.sql import RepositoryBase

class CustomerRepository(RepositoryBase[Customer, str]):
    """Repository for Customer CRUD operations."""

    def __init__(self, connection_string: str, database_name: str):
        super().__init__(
            connection_string=connection_string,
            database_name=database_name,
            container_name="customers"
        )
```

**Rules:**
- Repository goes in the **Business** layer alongside the entity
- One repository per entity (not per use case)
- Container name should be lowercase plural of the entity name

## Step 4: Use the repository

```python
async def main():
    repo = CustomerRepository(connection_string, "mydb")
    async with repo:
        # Create
        customer = Customer(id="cust-001", name="John", email="john@example.com")
        await repo.add_async(customer)

        # Read
        found = await repo.get_async("cust-001")

        # Query with predicate dict
        active = await repo.find_async({"is_active": True})

        # Update
        found.email = "john.doe@example.com"
        await repo.update_async(found)

        # Delete
        await repo.delete_async("cust-001")
```

For complex queries that predicates can't express:

```python
results = await repo.query_raw_dynamic_cursor_async(
    query="SELECT * FROM c WHERE c.name LIKE @pattern",
    parameters=[{"name": "@pattern", "value": "John%"}]
)
```

## Step 5: Write unit tests

```python
from unittest.mock import AsyncMock, patch

class TestCustomerRepository:
    def test_entity_creation(self):
        customer = Customer(id="c-1", name="Test", email="t@test.com")
        assert customer.name == "Test"
        assert customer.is_active is True

    @pytest.mark.asyncio
    async def test_add_customer(self):
        mock_repo = AsyncMock(spec=CustomerRepository)
        customer = Customer(id="c-1", name="Test", email="t@test.com")
        await mock_repo.add_async(customer)
        mock_repo.add_async.assert_called_once_with(customer)
```

## Gotchas

- **Never create raw `CosmosClient`** — `your-cosmosdb-lib` manages connection pooling,
  retry policies, and auth internally.
- **Partition key is handled automatically** by `RepositoryBase` — do not add custom
  partition key routing.
- **Cross-partition queries are expensive** — if you use `find_async` without a
  partition key filter, flag it as a performance concern.
- **Azure AD auth** is supported via `azure-identity` for SQL API — pass credential
  instead of connection string when using Managed Identity.
- **Entity goes in Business layer, NOT API layer** — the API layer imports from Business.

## Where files go

| Artifact | Location |
|---|---|
| Entity class | `src/<Name>Business/src/libs/models/` |
| Repository class | `src/<Name>Business/src/libs/repositories/` |
| Unit tests | `src/<Name>Business/tests/unit/` |
| Integration tests | `src/<Name>Business/tests/integration/` |
