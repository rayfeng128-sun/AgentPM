# Project Documentation

This directory is the formal documentation entry for the AgentPM project.

## Product

Product documents are the source of truth for user stories, scope, user flows, page behavior, and acceptance criteria.

- [docs/product/01-codex-project-board-prd.md](product/01-codex-project-board-prd.md)
- [docs/product/02-task-progress-token-analytics-prd.md](product/02-task-progress-token-analytics-prd.md)
- [docs/product/03-task-progress-token-analytics-prototype.md](product/03-task-progress-token-analytics-prototype.md)
- [docs/product/04-project-registration-usability-prd.md](product/04-project-registration-usability-prd.md)

Product document naming rule:

- Use `NN-topic-type.md`.
- `NN` is a two-digit sequence number in reading order.
- `topic` is a short kebab-case feature or subject name.
- `type` is the document kind, such as `prd` or `prototype`.

Examples:

- `01-codex-project-board-prd.md`
- `02-task-progress-token-analytics-prd.md`
- `03-task-progress-token-analytics-prototype.md`

PRD boundary rule:

- Create a new PRD when the requirement introduces a new independently named capability area, version theme, or user-story package with its own scope, non-goals, and acceptance criteria.
- Iterate on an existing PRD when the requirement only clarifies, corrects, or extends a capability that already belongs to that PRD and the original product goal still holds.
- Do not create a new PRD for pure implementation work, bug fixes, copy updates, or governance changes unless they change product scope or user value in a way that deserves a new capability definition.
- `references/Harness/changes/` tracks implementation changes; PRDs define product requirements. A change record does not automatically require a new PRD.

## Process

Process documents explain project governance, implementation planning, and agent collaboration rules. They are useful for tracing decisions, but they do not replace product requirements.

- [docs/process/agent-development-framework.md](process/agent-development-framework.md)

## Superpowers Artifacts

Superpowers specs and plans capture generated design and implementation planning artifacts. When they conflict with `docs/product/`, the product documents win unless the user explicitly updates the product source.

- [docs/superpowers/specs/2026-06-27-codex-project-board-design.md](superpowers/specs/2026-06-27-codex-project-board-design.md)
- [docs/superpowers/specs/2026-07-04-agentpm-bootstrap-setup-design.md](superpowers/specs/2026-07-04-agentpm-bootstrap-setup-design.md)
- [docs/superpowers/plans/2026-06-27-codex-project-board.md](superpowers/plans/2026-06-27-codex-project-board.md)
- [docs/superpowers/plans/2026-07-04-agentpm-bootstrap-setup.md](superpowers/plans/2026-07-04-agentpm-bootstrap-setup.md)
