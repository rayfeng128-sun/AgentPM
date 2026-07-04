# AGENTS.md

This file scopes the default Harness governance workflow for AgentPM development.

The repository-level source of truth remains [../../AGENTS.md](../../AGENTS.md). This file explains how `references/Harness/` must be used to track development changes.

## Purpose

`references/Harness/` is a structured governance area for larger or riskier AgentPM changes. It provides:

1. `AGENTS.md`: this Harness scope file.
2. `rules/`: process, architecture, coding, and change-management rules.
3. `agents/`: role definitions for decomposed work.
4. `skills/`: role-specific execution templates.
5. `changes/`: versioned change records and delivery evidence.

For small documentation edits, local UI polish, or isolated bug fixes, a lightweight Harness record is still required. The difference is only whether the change stays lightweight or upgrades to the full closure flow.

## AgentPM Baseline

- Product: Codex Project Board v0.1.
- Backend: `backend/`, FastAPI.
- Frontend: `frontend/`, React.
- Product source: `docs/product/01-codex-project-board-prd.md`.
- Progress source: `agentpm.yaml`.
- Generated design and plan artifacts: `docs/superpowers/`.
- Reusable rule package: `AGENT/`.

AgentPM is not the reusable governance template project. Template methodology belongs in `docs/process/agent-development-framework.md` or under `templates/`, not in the project-facing README.

## When To Use Harness

Use this Harness workflow for every development change. Start with a lightweight change record, then upgrade to the full closure flow when a change touches one or more of these areas:

- API response shape or data contract.
- Privacy-sensitive Codex local-state parsing.
- Project registration or persistence behavior.
- Git-state interpretation.
- Progress calculation from `agentpm.yaml`.
- Multi-screen frontend flow.
- Cross-cutting architecture or governance rules.

Every tracked change must create or update a record under `references/Harness/changes/` and include goal, scope, acceptance criteria, verification, and risks.

## Collaboration Rules

- Start from root [AGENTS.md](../../AGENTS.md), then read [QUICKSTART.md](QUICKSTART.md) if Harness applies.
- Keep requirements story-first and acceptance-driven.
- Do not expose private Codex transcript text by default.
- Label inferred signals, especially test confidence and token summaries.
- Keep unsupported local state explicit instead of silently falling back to misleading values.
- Update `agentpm.yaml` when progress status changes.
- Update `docs/` when product, architecture, process, or verification expectations change.

## Delivery Gate

A Harness-tracked change is not complete until:

- The change record describes scope, acceptance criteria, verification, and residual risks.
- Relevant backend tests, frontend build, or documentation checks have been run.
- The final handoff states whether the change used the lightweight root workflow or Harness workflow.
