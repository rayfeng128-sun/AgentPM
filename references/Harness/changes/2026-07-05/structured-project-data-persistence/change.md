# Structured Project Data Persistence PRD and Design

## User Story

As a project manager relying on Task Dashboard data, when project planning files vary across repositories, I want AgentPM to normalize and persist structured project data, so that dashboard fields remain stable and traceable instead of depending on live Markdown parsing.

## Goal

Document the product and design direction for an AgentPM-owned structured data layer that treats `PLANS.md` as an optional input source, not the dashboard source of truth.

## Scope

- In scope: product PRD, design document, source priority, field provenance, data states, collection flow, persistence concepts, and dashboard API direction.
- Out of scope: database migrations, collector implementation, frontend changes, scheduling implementation, and manual review UI.

## Prototype Source

Product baseline:

- `docs/product/05-structured-project-data-prd.md`
- `docs/superpowers/specs/2026-07-05-agentpm-structured-data-persistence-design.md`

## Story Boundary

Starts when Task Dashboard field quality is found to depend on inconsistent human source files. Ends when the requirement is documented as a future feature slice with a clear product contract and technical design.

## Impact

- Product: defines v0.4 structured persistence as the next capability area.
- Backend: future work will add local persistence tables and collection runs.
- Frontend: future work will read normalized task records and show field provenance.
- Database/config/permissions: no implementation impact in this documentation-only change.
- Tests: no runtime tests required for this documentation-only change.

## Acceptance Criteria

- The PRD explains why `PLANS.md` should not be the direct dashboard data source.
- The PRD defines structured data, source priority, field states, and dashboard expectations.
- The design proposes a collector-normalizer-persistence architecture.
- The design includes a local schema concept, collection flow, API direction, error handling, and incremental delivery slices.
- Documentation is linked from `docs/README.md`.

## Verification

- Documentation inspected for incomplete markers and internal contradictions.
- Link paths checked manually through repository-relative file references.

## Risks

- The design intentionally postpones implementation, so the current dashboard behavior is unchanged until the v0.4 feature is implemented.
- `PLANS.md` extraction is intentionally low-priority and conservative, which may require later manual review UX for ambiguous projects.
