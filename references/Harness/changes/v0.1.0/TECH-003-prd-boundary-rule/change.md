# Lightweight Change Record

## User Story

As a developer or agent working from incoming requests, when I decide whether a new requirement needs a new PRD or an update to an existing one, I want a written repository rule for that boundary, so that product scope stays consistent and PRD creation does not become arbitrary.

## Goal

Document the rule for when AgentPM should create a new PRD versus iterating on an existing PRD.

## Scope

- In scope: product-documentation guidance in `docs/README.md`, repository product rules in `AGENT/PRODUCT_RULES.md`, and a lightweight Harness record for this governance update.
- Out of scope: renaming existing PRDs, changing existing product scope, or creating a new product feature definition.

## Prototype Source

No page prototype impact.

## Story Boundary

This change only defines the decision rule. It does not retroactively reclassify older PRDs or create a new intake workflow UI.

## Impact

- Frontend: No impact.
- Backend: No impact.
- Mock/demo data: No impact.
- Permissions: No impact.
- Config: No impact.
- Tests: Documentation verification only.
- Delivery path: Future requirement intake now has a clearer PRD decision boundary.

## Acceptance Criteria

- `docs/README.md` explains when to create a new PRD and when to iterate on an existing one.
- `AGENT/PRODUCT_RULES.md` contains the same boundary in repository rule form.
- The rule explains the difference between PRDs and `references/Harness/changes/`.

## Verification

- Verified by inspecting the updated product documentation and product rules.
- Verified by Markdown link-resolution check for the updated governance entry files.

## Risks

- Some borderline product requests may still need human judgment when they partially extend an existing capability while also opening a new theme; the rule reduces ambiguity but does not remove the need for product judgment.
