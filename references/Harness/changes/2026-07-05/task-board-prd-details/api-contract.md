# API Contract

## Interface 1: `GET /api/projects/{project_id}/prd`

### Basic Information

| Method | Path | Purpose | Auth/Permission | Idempotency | Status |
|---|---|---|---|---|---|
| GET | `/api/projects/{project_id}/prd` | Read local Markdown PRD content for an in-page Task Board modal. | Local project registry access only. | Idempotent | Implemented |

### Path / Query Parameters

| Field | Location | Type | Required | Example | Description |
|---|---|---|---|---|---|
| `project_id` | Path | string | Yes | `agentpm` | Registered project ID. |
| `ref` | Query | string | Yes | `docs/product/02-task-progress-token-analytics-prd.md#story-1-view-task-level-progress` | PRD reference from `agentpm.yaml`; may include a Markdown anchor. |

### Request Body

No request body.

### Response Fields

| Field | Type | Example | Description |
|---|---|---|---|
| `ref` | string | `docs/product/02-task-progress-token-analytics-prd.md#story-1` | Original requested reference. |
| `path` | string | `docs/product/02-task-progress-token-analytics-prd.md` | Relative project path, or original non-Markdown reference when unavailable. |
| `anchor` | string or null | `story-1` | Fragment after `#`, when present. |
| `title` | string or null | `Codex Project Board v0.2 PRD` | First Markdown H1 when readable. |
| `content` | string | `# Codex Project Board...` | Markdown file content. Empty when unavailable. |
| `unavailable` | boolean | `false` | True for non-Markdown refs, missing files, or unreadable PRD content. |

### Error Codes

| Status Code | Scenario | Frontend Handling |
|---|---|---|
| 403 | `ref` resolves outside the selected project root. | Show error banner in the modal. |
| 404 | Project ID is not registered. | Show error banner in the modal. |

### Compatibility

| Change | Compatible | Notes |
|---|---|---|
| New endpoint | Yes | Existing endpoints are unchanged. |
| Extended `TaskItem` response fields | Yes | New fields are nullable and optional; existing `agentpm.yaml` files continue to load. |
