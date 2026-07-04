# Task Board PRD Details Upgrade

## User Story

As a project manager reviewing Task Board scope, when I inspect task rows and PRD links, I want complete PRD references plus story, scope, acceptance, and verification details in the board itself, so that I can validate delivery traceability without opening a separate task drawer.

## Goal

Make Task Board the primary full-width task review surface by removing the right-side Task Details drawer, showing richer task metadata inline, and opening local PRD Markdown content in an in-page modal.

## Scope

- In scope: backend task metadata parsing, PRD read API, Task Board table layout, PRD modal, v0.2 product documentation, and verification tests.
- Out of scope: Markdown rendering beyond readable plain text, remote PRD URLs, arbitrary filesystem access, and database or persistence changes.

## Prototype Source

Product baseline: `docs/product/02-task-progress-token-analytics-prd.md`.

## Story Boundary

Starts when `agentpm.yaml` includes task rows with optional delivery metadata and PRD refs. Ends when the briefing response and Task Board can show those details, and local Markdown PRD refs open in a page modal. Follow-up rich Markdown rendering and PRD editing remain out of scope.

## Impact

- Frontend: Task Board becomes single-column/full-width; task rows show all PRD refs plus user story, scope, acceptance criteria, and verification method; local Markdown refs open a modal.
- Backend: `TaskItem` accepts four optional metadata fields and exposes a read-only PRD endpoint.
- API: Adds `GET /api/projects/{project_id}/prd?ref=<prd_ref>`.
- Database/config/permissions: No impact.
- Tests: Adds parser and API tests; frontend build verifies TypeScript and JSX.

## Acceptance Criteria

- The right-side Task Details drawer is not rendered.
- Task Board rows show every PRD reference, not only the primary reference.
- Task Board rows show user story, scope, acceptance criteria, and verification method, using `Not specified` when missing.
- Clicking a local `.md` PRD ref opens a modal with Markdown content.
- Non-Markdown refs remain visible without trying to read arbitrary files.
- PRD reads are limited to files inside the selected project root and reject traversal attempts.

## Verification

- Red-state parser test failed before implementation because `TaskItem` had no `user_story` field.
- Red-state PRD API tests failed before implementation because `/api/projects/{project_id}/prd` returned 404.
- Targeted parser verification passed: `cd backend && ./.venv/bin/python -m pytest tests/test_plan_parser.py::test_task_delivery_metadata_is_optional_and_preserved -q`.
- Targeted PRD API verification passed: `cd backend && ./.venv/bin/python -m pytest tests/test_projects.py::test_read_project_prd_returns_markdown_content_and_anchor tests/test_projects.py::test_read_project_prd_marks_missing_or_non_markdown_refs_unavailable tests/test_projects.py::test_read_project_prd_rejects_path_traversal -q`.
- Full backend verification passed: `cd backend && ./.venv/bin/python -m pytest` with `82 passed, 4 warnings`.
- Frontend build passed: `cd frontend && npm run build`.

## Risks

- PRD modal displays Markdown as plain preformatted text in this slice.
- `agentpm.yaml` must provide the new structured fields; the UI does not infer them from PRD text.
