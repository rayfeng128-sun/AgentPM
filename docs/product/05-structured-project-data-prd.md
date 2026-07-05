# Codex Project Board v0.4 PRD: Structured Project Data Persistence

## 1. Product Summary

Codex Project Board v0.4 introduces an AgentPM-owned structured data layer for project planning, task metadata, source traceability, and dashboard-ready task fields.

The current dashboard reads `agentpm.yaml` directly and uses best-effort PRD extraction when task fields are missing. This is useful for a local MVP, but it becomes fragile when users expect the dashboard to agree with human-maintained files such as `PLANS.md`, PRDs, Codex session notes, or repository-specific governance docs. Those files vary by project and should not be treated as stable dashboard contracts.

The product goal is to help a project manager answer:

```text
What is the current structured state of each monitored project, and which source files or Codex sessions produced that state?
```

AgentPM should periodically collect project data, normalize it into a stable schema, persist it locally, and let the dashboard read the normalized state instead of parsing human Markdown on every request.

## 2. Target User

Primary user:

- A project manager monitoring multiple Codex-assisted local projects who needs consistent task, PRD, progress, and verification data even when each project has slightly different planning documents.

Secondary users:

- A developer using AgentPM to resume work and understand which task fields are reliable, missing, inferred, or awaiting review.
- An agentic worker using AgentPM as a stable source of structured context before changing a project.

## 3. Problem Statement

`PLANS.md` is a useful human-readable planning entry point, but it is not a safe direct dashboard data source.

Reasons:

- Different projects may use different `PLANS.md` structures.
- Markdown headings, tables, lists, and wording may drift over time.
- Human notes often include ambiguity, narrative context, or stale status.
- Re-parsing Markdown on every dashboard request makes display quality depend on source formatting details.
- The dashboard needs stable field semantics such as `user_story`, `scope`, `acceptance_criteria`, and `verification_method`, not merely nearby text snippets.

The product should avoid coupling Task Dashboard output to raw `PLANS.md` structure. `PLANS.md` may become one collection input, but AgentPM must own the normalized result.

## 4. User Stories

### Story 1: View Stable Task Data

As a project manager reviewing a Task Dashboard,
in the context of projects with different planning file styles,
I want the dashboard to show task fields from a stable AgentPM schema,
so that task rows do not change unpredictably because a Markdown file was reformatted.

Acceptance:

- Task Dashboard reads normalized task records from AgentPM's persisted project state.
- Each task can expose `user_story`, `scope`, `acceptance_criteria`, and `verification_method`.
- Missing fields are explicit and do not silently use unrelated Markdown paragraphs.
- The dashboard can show whether a field is explicit, inferred, missing, or needs review.

### Story 2: Preserve Source Traceability

As a project manager auditing why a task field appears in the dashboard,
in the context of data collected from `agentpm.yaml`, PRDs, `PLANS.md`, and Codex sessions,
I want each structured field to reference its source,
so that I can trust the dashboard and resolve inconsistencies.

Acceptance:

- Each normalized task field stores its source type.
- Supported source types include `agentpm.yaml`, `prd`, `plans.md`, `codex_session`, and `manual`.
- Each source reference stores enough location metadata to inspect the original source, such as file path, anchor, line range, or session id when available.
- The dashboard can distinguish user-authored explicit values from inferred values.

### Story 3: Collect Project Data Periodically

As a project manager monitoring local Codex projects,
in the context of projects changing over time,
I want AgentPM to periodically refresh its structured project state,
so that the dashboard reflects recent planning and Codex activity without manual file inspection.

Acceptance:

- AgentPM can run a local collection pass for each registered project.
- Collection reads local project metadata, task files, PRDs, git state, and Codex local session data when available.
- Collection stores a timestamped run record.
- Collection failures are recorded as unavailable states, not hidden from the dashboard.
- A manual refresh can trigger a collection pass for a selected project.

### Story 4: Review Inferred Data Before Trusting It

As a project manager using inferred task metadata,
in the context of imperfect source files,
I want inferred values to be labeled and reviewable,
so that AgentPM does not present guesses as facts.

Acceptance:

- Inferred fields carry a confidence value.
- Low-confidence extraction results are marked `needs_review`.
- The dashboard can show `Not specified` when no reliable value exists.
- Future manual review can promote an inferred value to an explicit AgentPM-owned value.

### Story 5: Keep Human Files Flexible

As a project owner,
in the context of existing project governance files,
I want `PLANS.md` and PRDs to remain human-friendly,
so that AgentPM does not force every project to adopt one rigid Markdown layout.

Acceptance:

- AgentPM does not require `PLANS.md` to follow a single strict template.
- `PLANS.md` is treated as optional input, not the dashboard source of truth.
- `agentpm.yaml` remains supported as a lightweight structured input.
- The persisted AgentPM schema is the dashboard contract.

## 5. Scope

v0.4 includes:

- Local AgentPM persistence for normalized project state.
- Collection run records for registered projects.
- Normalized task records with structured delivery metadata.
- Field-level provenance for task metadata.
- Best-effort extraction from `agentpm.yaml`, PRDs, and optional `PLANS.md`.
- Explicit states for missing, inferred, unavailable, and needs-review data.
- Dashboard API changes so Task Dashboard reads normalized state.
- Manual refresh support for a selected project.

## 6. Non-Goals

v0.4 does not include:

- Cloud sync or multi-user collaboration.
- Automatic editing of `PLANS.md`, PRDs, or `agentpm.yaml`.
- A full manual task editor UI.
- LLM-based extraction as a required dependency.
- Perfect parsing of arbitrary Markdown.
- Billing-grade task cost accounting.
- Replacing Codex's own local session storage.

## 7. Source Priority

AgentPM should use a deterministic source priority when multiple sources mention the same task field:

| Priority | Source | Role |
|---:|---|---|
| 1 | AgentPM manual override | User-confirmed structured value. |
| 2 | `agentpm.yaml` structured task field | Explicit project-owned machine-readable value. |
| 3 | PRD anchored section | Product requirement source, useful for story and acceptance. |
| 4 | `PLANS.md` structured section | Human planning input, useful as candidate data. |
| 5 | Codex session metadata | Supporting activity evidence, not primary scope definition. |

Rules:

- Higher-priority explicit values should not be overwritten by lower-priority inferred values.
- Lower-priority sources can still be stored as supporting evidence.
- `PLANS.md` extraction should never override explicit `agentpm.yaml` values.
- Ambiguous extraction should produce a candidate with `needs_review`, not a trusted field.

## 8. Data States

Every normalized task field should carry a state:

| State | Meaning | Dashboard Behavior |
|---|---|---|
| `explicit` | Read from a structured source or user-confirmed value. | Show normally. |
| `inferred` | Extracted from semi-structured text with adequate confidence. | Show with inferred/source label. |
| `needs_review` | Extracted but uncertain or conflicting. | Show review indicator or fallback. |
| `missing` | No reliable value found. | Show `Not specified`. |
| `unavailable` | Source could not be read. | Show unavailable warning when relevant. |

## 9. Persistence Requirements

AgentPM should persist local structured data in its backend database.

Minimum persisted concepts:

- registered projects
- collection runs
- source documents
- normalized tasks
- task field values
- task PRD references
- task Codex session links
- extraction warnings

Collection must be repeatable. Re-running collection for a project should update the latest normalized view while preserving enough run history for debugging recent changes.

## 10. Dashboard Requirements

Task Dashboard should read from the normalized task API rather than parsing raw files directly.

Dashboard behavior:

- Show task title, status, PRD refs, user story, scope, acceptance criteria, and verification method from normalized task records.
- Show `Not specified` only when the normalized field state is `missing`.
- Provide source affordances for field provenance in a compact form.
- Keep PRD links clickable through the existing PRD modal.
- Surface collection warnings without blocking the whole dashboard.

## 11. Error Handling

Collection errors should be visible but non-fatal.

Rules:

- Missing `agentpm.yaml` should produce a warning and allow other sources to be inspected.
- Missing `PLANS.md` should not be an error.
- Unreadable PRD files should mark affected references unavailable.
- Invalid YAML should not destroy the previous good normalized snapshot.
- Path traversal or files outside the project root must be rejected.

## 12. Acceptance Criteria

- AgentPM has a documented structured persistence model for project task data.
- `PLANS.md` is documented as an optional input source, not the dashboard source of truth.
- Task Dashboard requirements point to normalized AgentPM data instead of live Markdown parsing.
- The design includes source priority, field provenance, data states, collection runs, and error handling.
- Existing `agentpm.yaml`-based projects remain supported.
- The feature can be implemented incrementally without requiring a full task editor in the first slice.
