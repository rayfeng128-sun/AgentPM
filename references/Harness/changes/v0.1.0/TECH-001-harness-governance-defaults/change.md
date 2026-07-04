# Lightweight Change Record

## User Story

As a developer working with Codex in AgentPM, when I start a development task, I want the governance workflow to require a real Harness change record, so that the repository keeps a visible trace of scope, verification, and delivery decisions.

## Goal

Make `references/Harness/changes/` part of the default AgentPM development workflow instead of leaving it as an optional template area.

## Scope

- In scope: root governance entry files, Harness quickstart and rule wording, and the first real lightweight change record under `v0.1.0/`.
- Out of scope: backend application code, frontend application code, and any upgrade to a full-closure feature record.

## Prototype Source

No page prototype impact.

## Story Boundary

This change only closes the governance-default behavior for development tracking. It does not retroactively create records for all historical work, and it does not redesign the full Harness artifact structure.

## Impact

- Frontend: No impact.
- Backend: No impact.
- Mock/demo data: No impact.
- Permissions: No impact.
- Config: Governance entry behavior and documentation expectations are updated.
- Tests: Documentation verification only.
- Delivery path: Future development work now has a required change-record entry point.

## Acceptance Criteria

- Root governance files state that development changes must create or update a Harness change record.
- Harness quickstart and coding rules describe lightweight records as mandatory, not optional.
- A real versioned change directory exists outside `v-template/`.
- The new governance links resolve correctly.

## Verification

- Verified by inspecting updated governance files.
- Verified with a local Markdown link-resolution check for the updated entry documents at the time of that change.

## Risks

- Older work remains undocumented in `changes/`; only new work is guaranteed to follow the default path unless historical records are backfilled later.
