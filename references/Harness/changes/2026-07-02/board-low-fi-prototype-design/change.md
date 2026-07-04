# Change Record

- Date: 2026-07-02
- Change ID: board-low-fi-prototype-design
- Flow: lightweight

## Request

Design the low-fidelity prototype for the Board experience according to the PRD first, then implement the approved Board daily token usage slice.

## Scope

- Capture the approved low-fi prototype direction for the Board.
- Implement backend daily token aggregation for the Board briefing payload.
- Fix rollout-backed Codex session timestamps so daily token usage can render real day buckets.
- Correct Board daily token usage to use reconstructed per-day rollout deltas instead of assigning full session totals to one day.
- Use each session's recorded local timezone when mapping snapshot deltas onto calendar days.
- Make `Project total` reflect project-wide reconstructable session activity, including today's in-progress session data, rather than only linked task sessions.
- Simplify the Board chart to a single `Project total` view.
- Stack each project-total day column by contributing model so model mix is visible inside the bar.
- Implement the Board daily token usage card and the approved calmer Board hierarchy.
- Keep the task drawer executive and Board state handling inline and calm.

## Outputs

- `docs/superpowers/specs/2026-07-02-calm-pm-board-low-fi-prototype-design.md`
- `docs/superpowers/specs/2026-07-01-board-daily-token-usage-design.md`
- `docs/superpowers/plans/2026-07-02-board-daily-token-usage.md`
- backend and frontend code changes for the Board daily token usage feature

## Verification

- `cd backend && ./.venv/bin/python -m pytest`
- `cd frontend && npm run test`
- `cd frontend && npm run build`
