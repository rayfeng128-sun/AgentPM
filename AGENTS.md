# AGENTS.md

This file is the repository-level instruction entry for agents working on AgentPM.

## CodeGraph

In repositories indexed by CodeGraph (a `.codegraph/` directory exists at the repo root), use CodeGraph first for any code analysis task.

This is the default rule for:

- understanding how code works
- locating symbols, handlers, routes, or modules
- tracing call paths or data flow
- estimating change impact before editing

Only skip CodeGraph when the task is not actually code analysis, such as documentation-only work, running verification commands, or making a tiny mechanical edit in a file that is already known.

- MCP tool: `codegraph_explore` answers most code questions in one call with relevant source and call paths.
- Shell: `codegraph explore "<symbol names or question>"` provides the same information from the command line.
- If there is no `.codegraph/` directory, skip CodeGraph entirely.

## Project Goal

AgentPM is building Codex Project Board v0.1: a local web dashboard that summarizes project progress, recent Codex activity, Git state, token usage, alerts, and the next recommended action.

## Current Phase

The project is in local MVP hardening:

- The backend skeleton, project registry, plan parser, Codex local-state reader, Git reader, briefing API, and dashboard frontend are present.
- Current progress is tracked in [agentpm.yaml](agentpm.yaml).
- The active blocked item is verification: backend tests, frontend build, and PRD smoke checks must be made reliable and recorded.

## Source Of Truth

Use these files in this order:

1. [docs/product/01-codex-project-board-prd.md](docs/product/01-codex-project-board-prd.md)
2. [agentpm.yaml](agentpm.yaml)
3. [docs/superpowers/plans/2026-06-27-codex-project-board.md](docs/superpowers/plans/2026-06-27-codex-project-board.md)
4. [docs/superpowers/specs/2026-06-27-codex-project-board-design.md](docs/superpowers/specs/2026-06-27-codex-project-board-design.md)
5. [docs/README.md](docs/README.md)

If implementation and product documents disagree, do not invent product behavior. State the difference and update the relevant document when the user confirms the change.

## Main Directories

- `backend/`: FastAPI app and backend tests.
- `frontend/`: React app and frontend build configuration.
- `docs/product/`: product requirements and acceptance criteria.
- `docs/superpowers/`: generated design and implementation planning artifacts.
- `docs/process/`: process and governance documentation.
- `AGENT/`: reusable project-agnostic agent rules.
- `references/Harness/`: optional heavier governance workflow for changes that need structured traceability.

## Engineering Rules

- Keep changes scoped to one user story, story slice, or clear technical boundary.
- Prefer existing backend and frontend structure over introducing new architecture.
- Do not expose raw private Codex transcript content through the API by default.
- Handle missing local Codex state, missing Git repositories, and missing `agentpm.yaml` as explicit unavailable or warning states.
- Do not turn inferred test or token signals into authoritative facts without labeling confidence.
- Every development change must be recorded under `references/Harness/changes/`.
- Low-risk changes must create at least a lightweight `change.md` record before or alongside implementation.
- Changes involving API, database, persistence, permissions, multi-screen flows, or architecture must be upgraded to the full Harness closure flow.
- Update `agentpm.yaml` when task status changes.
- Update product, plan, or process docs when a change affects scope, acceptance, architecture, verification, or delivery status.

## Verification

Use the smallest verification that proves the change:

- Backend behavior: `cd backend && python -m pytest`
- Frontend build: `cd frontend && npm run build`
- Documentation-only changes: inspect links and run a text search for stale project/template placeholders.

If a verification command cannot be run, report that clearly with the reason.

## Governance Entry Points

- Use [CODEX.md](CODEX.md) as the Codex-specific quick entry.
- Use [AGENT/README.md](AGENT/README.md) for the reusable rule package.
- Use [references/Harness/QUICKSTART.md](references/Harness/QUICKSTART.md) for every development change that needs a change record.

## Done Definition

A task is complete only when:

- The requested change is implemented or the blocker is clearly documented.
- The relevant source-of-truth document is still accurate.
- The corresponding `references/Harness/changes/` record is updated to match the delivered scope.
- Verification evidence is recorded in the final response.
- `agentpm.yaml` is updated if progress status changed.
