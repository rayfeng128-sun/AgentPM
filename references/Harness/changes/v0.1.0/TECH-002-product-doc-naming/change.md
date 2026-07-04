# Lightweight Change Record

## User Story

As a developer or agent working in AgentPM, when I read or add product documents, I want the PRD naming scheme to be explicit and consistent, so that product files are easy to locate and reference without one-off exceptions.

## Goal

Define the current product document naming rule and align the first PRD file with that rule.

## Scope

- In scope: `docs/README.md`, the first product PRD filename, and repository references that point to the old filename.
- Out of scope: rewriting product content, changing the order of existing product documents, or renaming the v0.2 and v0.3 product files.

## Prototype Source

No page prototype impact.

## Story Boundary

This change only standardizes the naming rule and the first inconsistent PRD filename. It does not introduce a broader document taxonomy beyond the current `NN-topic-type.md` pattern.

## Impact

- Frontend: No impact.
- Backend: No runtime impact.
- Mock/demo data: Sample references updated where they point to the renamed PRD.
- Permissions: No impact.
- Config: No impact.
- Tests: Reference consistency only.
- Delivery path: Product sources and supporting references now use one naming convention.

## Acceptance Criteria

- `docs/README.md` states the product document naming rule.
- `01-prd.md` is renamed to a topic-based filename.
- References to the old filename are updated in active project docs and sample data.

## Verification

- Verified by repository text search for stale `01-prd.md` references in active project files.
- Verified by Markdown link-resolution check for updated documentation entry points.

## Risks

- Historical references outside the checked files could still mention the old filename if new example material is added later without following the documented rule.
