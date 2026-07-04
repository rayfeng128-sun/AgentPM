# Change Record

- Date: 2026-07-05
- Change ID: agentpm-bootstrap-cli
- Flow: lightweight

## Request

Implement Task 4 of the AgentPM bootstrap flow: add the CLI entry point with dry-run output, interactive prompt handling, rollback support, and the package script entry.

## Scope

- Add `backend/app/bootstrap_cli.py` as a thin CLI wrapper over the existing bootstrap core plan/apply/rollback behavior.
- Add focused pytest coverage for CLI dry-run, interactive apply, and rollback flows.
- Register the CLI as `agentpm-bootstrap` in `backend/pyproject.toml`.
- Keep the change scoped to the backend bootstrap CLI surface; do not alter the underlying planning/apply/rollback semantics except for user-input mapping at the CLI boundary.

## Outputs

- `backend/app/bootstrap_cli.py`
- `backend/tests/test_bootstrap_cli.py`
- `backend/pyproject.toml`

## Verification

- Verified the red state with `cd backend && ./.venv/bin/python -m pytest tests/test_bootstrap_cli.py -v`, which failed with `ModuleNotFoundError: No module named 'app.bootstrap_cli'` before the CLI module existed.
- Verified the delivered CLI slice with `cd backend && ./.venv/bin/python -m pytest tests/test_bootstrap_cli.py -v`, which now passes with `3 passed`.
