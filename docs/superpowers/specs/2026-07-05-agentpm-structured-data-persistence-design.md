# AgentPM Structured Data Persistence Design

## Summary

This design defines a local structured data layer for AgentPM. The layer collects project inputs such as `agentpm.yaml`, PRDs, optional `PLANS.md`, git state, and Codex local sessions, normalizes them into AgentPM-owned records, and serves dashboard APIs from that stable data model.

The key decision is that `PLANS.md` should not become a direct Task Dashboard contract. It remains a human-readable planning entry point and an optional extraction source. The dashboard should depend on AgentPM's normalized schema.

## Design Brief

- Product area: AgentPM project intelligence and Task Dashboard reliability
- Primary user: project manager monitoring multiple Codex-assisted local projects
- Problem: dashboard task fields can become inconsistent when inferred directly from semi-structured Markdown
- Direction: local collector plus persisted normalized state
- Trust requirement: preserve provenance and confidence for every inferred field
- Compatibility requirement: keep `agentpm.yaml` working as the lightweight structured source

## Goals

- Make Task Dashboard output stable across projects with different document conventions.
- Preserve source traceability for task fields.
- Avoid making `PLANS.md` a strict template or direct dashboard dependency.
- Support repeatable local collection runs.
- Let AgentPM distinguish explicit values, inferred values, missing values, and unavailable source data.
- Keep the first implementation small enough to ship incrementally.

## Non-Goals

- Building a full task editor.
- Replacing project documents with an AgentPM-only workflow.
- Requiring LLM extraction.
- Implementing cloud sync.
- Performing destructive writes to project files.
- Perfectly parsing arbitrary Markdown.

## Approved Product Direction

AgentPM should use a collector-normalizer-persistence model:

```text
Registered local project
        |
        v
Collection run
        |
        v
Source readers: agentpm.yaml, PRDs, PLANS.md, Codex sessions, git
        |
        v
Normalizer and resolver
        |
        v
AgentPM local database
        |
        v
Task Dashboard API
```

The dashboard reads the latest normalized snapshot. Source readers can evolve without changing the dashboard contract.

## Data Ownership Model

AgentPM should treat source files as inputs, not as the final display model.

### Stable Sources

`agentpm.yaml` remains the preferred lightweight structured project input. Values explicitly present in this file should be trusted before inferred text.

### Human Sources

`PLANS.md` and PRDs are useful because they contain intent, scope, and acceptance language. They should be read as optional source documents. Their extracted content becomes a candidate value with provenance and confidence.

### Activity Sources

Codex sessions and git state describe work activity. They are useful for attribution, recency, token usage, and evidence, but they should not silently define product scope.

## Proposed Local Schema

The first durable schema can be implemented in the existing SQLite app database.

### `collection_runs`

Records each ingestion pass.

| Field | Purpose |
|---|---|
| `id` | Stable run id. |
| `project_id` | Registered project. |
| `started_at` | Collection start time. |
| `finished_at` | Collection end time. |
| `status` | `success`, `partial`, or `failed`. |
| `warnings_json` | Non-fatal source and extraction warnings. |

### `source_documents`

Records files or local session records inspected during a run.

| Field | Purpose |
|---|---|
| `id` | Stable source id. |
| `project_id` | Registered project. |
| `run_id` | Collection run. |
| `source_type` | `agentpm_yaml`, `prd`, `plans_md`, `codex_session`, or `git`. |
| `path_or_id` | Relative file path or session id. |
| `content_hash` | Hash used to detect changes. |
| `available` | Whether source content was readable. |

### `normalized_tasks`

Stores dashboard-ready task identity and state.

| Field | Purpose |
|---|---|
| `id` | Internal row id. |
| `project_id` | Registered project. |
| `run_id` | Source collection run. |
| `task_key` | Stable project task id. |
| `title` | Task title. |
| `status` | `todo`, `doing`, `done`, or `blocked`. |
| `milestone_id` | Optional milestone key. |
| `milestone_title` | Optional milestone label. |

### `task_field_values`

Stores structured field values with provenance.

| Field | Purpose |
|---|---|
| `task_id` | Normalized task row. |
| `field_name` | `user_story`, `scope`, `acceptance_criteria`, or `verification_method`. |
| `value` | Display value. |
| `state` | `explicit`, `inferred`, `needs_review`, `missing`, or `unavailable`. |
| `source_document_id` | Source that produced the value, when known. |
| `source_locator` | File anchor, line range, or session locator. |
| `confidence` | Numeric confidence from 0.0 to 1.0. |

### `task_references`

Stores PRD and requirement references.

| Field | Purpose |
|---|---|
| `task_id` | Normalized task row. |
| `ref_type` | `prd`, `requirement_id`, or `source`. |
| `ref` | Original reference string. |
| `available` | Whether referenced local content can be read. |

### `task_session_links`

Stores task to Codex session attribution.

| Field | Purpose |
|---|---|
| `task_id` | Normalized task row. |
| `session_id` | Codex session id. |
| `link_type` | `explicit`, `inferred`, or `shared`. |

## Source Priority

When multiple sources produce the same field, the resolver should prefer:

1. AgentPM manual override
2. explicit `agentpm.yaml` field
3. anchored PRD story or acceptance section
4. structured `PLANS.md` section
5. Codex session evidence

Lower-priority sources should be retained as evidence but should not replace higher-priority explicit values.

## Collection Flow

### Trigger

Collection can run in two modes:

- manual refresh from the selected project
- periodic background refresh for registered projects

The first implementation can ship manual refresh first, then add scheduling.

### Steps

1. Load project registration.
2. Create a `collection_runs` row with `status=partial`.
3. Read `agentpm.yaml` if present.
4. Read PRD files referenced by structured tasks.
5. Read `PLANS.md` if present and record it as an optional source.
6. Read Codex local sessions for the project path.
7. Build normalized task candidates.
8. Resolve conflicts using source priority.
9. Persist normalized tasks, field values, references, and warnings.
10. Mark the run `success`, `partial`, or `failed`.

## Extraction Strategy

Extraction should be deterministic in the first version.

### `agentpm.yaml`

Use existing YAML parsing and treat supported fields as explicit:

- `id`
- `title`
- `status`
- `user_story`
- `scope`
- `acceptance_criteria`
- `verification_method`
- `prd_refs`
- `codex_sessions`
- `token_budget`

### PRDs

Use existing Markdown heading and anchor parsing. Anchored PRD refs are more reliable than full-document refs. Extract:

- story block after an anchored story heading
- `Acceptance:` bullets
- `Verification Plan` section bullets
- local PRD title and path

### `PLANS.md`

Treat `PLANS.md` as optional and low-priority.

For the first implementation, only extract from clearly labeled sections or tables. If a task cannot be matched to an existing `task_key`, store the extraction as a warning or future candidate instead of creating a trusted task silently.

### Codex Sessions

Use sessions for activity evidence and token attribution. Do not infer acceptance criteria or scope from raw transcript content in the first implementation.

## Dashboard Behavior

Task Dashboard should read normalized task records.

For each structured field:

- `explicit`: show normally
- `inferred`: show value with a subtle source indicator
- `needs_review`: show a review indicator or fallback text
- `missing`: show `Not specified`
- `unavailable`: show `Unavailable`

PRD links continue to open the existing in-page modal. The modal still reads local Markdown through the safe PRD endpoint.

## API Shape

The existing task endpoint can evolve without changing the frontend layout radically:

```text
GET /api/projects/{project_id}/tasks
```

Response task fields should include field metadata:

```json
{
  "user_story": {
    "value": "As a PM...",
    "state": "explicit",
    "source": {
      "type": "agentpm_yaml",
      "path": "agentpm.yaml"
    },
    "confidence": 1.0
  }
}
```

For frontend compatibility, the backend may temporarily expose both:

- legacy string fields: `user_story`, `scope`, `acceptance_criteria`, `verification_method`
- new metadata fields: `field_details`

## Error Handling

- Invalid `agentpm.yaml`: keep the latest successful normalized snapshot and show a collection warning.
- Missing `PLANS.md`: no warning by default.
- Missing PRD file: mark the specific reference unavailable.
- Path traversal attempt: reject and record a warning.
- Codex local state unavailable: keep task data and mark session/token data unavailable.

## Incremental Delivery

### Slice 1: Persistence Foundation

- Add collection run tables.
- Persist normalized tasks from `agentpm.yaml`.
- Keep dashboard behavior equivalent to current output.

### Slice 2: Field Provenance

- Store field-level state and source metadata.
- Add API metadata while preserving legacy strings.
- Update Task Dashboard to display source state subtly.

### Slice 3: PRD and `PLANS.md` Inputs

- Move current PRD fallback into the collector.
- Add low-priority `PLANS.md` extraction for clearly structured sections.
- Mark ambiguous values `needs_review`.

### Slice 4: Refresh UX

- Add manual refresh action.
- Add latest collection status and warnings to dashboard.
- Add periodic refresh later if manual refresh is stable.

## Verification Expectations

- Unit tests for schema initialization and idempotent collection runs.
- Parser tests proving `agentpm.yaml` explicit values outrank PRD and `PLANS.md` values.
- Tests proving missing `PLANS.md` is not an error.
- Tests proving invalid source files do not erase the previous good snapshot.
- API tests for legacy string compatibility and new field metadata.
- Frontend build verification after API type changes.

## Why This Fits The Product

AgentPM is becoming a project intelligence layer, not just a file viewer. A local persistence layer lets it respect project documents while protecting dashboard stability. This keeps human files flexible and makes structured task reporting reliable enough for multi-project monitoring.
