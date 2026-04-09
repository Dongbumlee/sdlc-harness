# API Documentation: [Service Name]

> **Base URL:** `/api/v1`
> **Authentication:** Azure AD Bearer Token
> **Date:** YYYY-MM-DD

---

## Overview

<!-- Brief description of this API's purpose -->

## Authentication

All endpoints require a valid Azure AD Bearer token in the `Authorization` header:

```
Authorization: Bearer <token>
```

## Endpoints

### [Resource Name]

#### Create [Resource]

```
POST /api/v1/[resources]
```

**Request Body:**

```json
{
  "field": "value"
}
```

**Response:** `201 Created`

```json
{
  "id": "string",
  "field": "value",
  "created_at": "2026-01-01T00:00:00Z"
}
```

**Errors:**

| Status | Description |
|---|---|
| 400 | Invalid request body |
| 401 | Unauthorized |
| 409 | Resource already exists |

---

#### List [Resources]

```
GET /api/v1/[resources]
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `page` | int | No | Page number (default: 1) |
| `size` | int | No | Page size (default: 20) |

**Response:** `200 OK`

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "size": 20
}
```

---

#### Get [Resource]

```
GET /api/v1/[resources]/{id}
```

**Response:** `200 OK`

**Errors:**

| Status | Description |
|---|---|
| 404 | Resource not found |

---

#### Delete [Resource]

```
DELETE /api/v1/[resources]/{id}
```

**Response:** `204 No Content`

**Errors:**

| Status | Description |
|---|---|
| 404 | Resource not found |

---

## Error Response Format

All errors follow this format:

```json
{
  "detail": "Human-readable error message",
  "status_code": 400,
  "error_code": "VALIDATION_ERROR"
}
```

## Rate Limiting

<!-- If applicable -->

## Changelog

| Date | Version | Description |
|---|---|---|
| YYYY-MM-DD | 1.0 | Initial API documentation |
