# Change Record

- Date: 2026-07-04
- Change ID: agentpm-bootstrap-setup
- Flow: lightweight

## Request

Implement Task 1 of the AgentPM bootstrap flow: the lightweight template-rendering layer that later setup logic will call.

## Scope

- Add a renderer for bootstrap `agentpm.yaml` content using the provided project name and absolute project path.
- Add renderers for lightweight `AGENTS.md` and `CODEX.md` bootstrap content.
- Cover the template renderers with focused test-first pytest coverage.
- Do not add setup orchestration, CLI behavior, overwrite handling, or rollback logic in this task.

## Outputs

- `backend/app/bootstrap_templates.py`
- `backend/tests/test_bootstrap_setup.py`

## Verification

- Verified by reviewing the approved design against the user constraints.
- Verified by checking that the design keeps setup metadata out of business-facing project structure by default.
- Verified TDD red state with `cd backend && ./.venv/bin/python -m pytest tests/test_bootstrap_setup.py -v`, which failed with `ModuleNotFoundError: No module named 'app.bootstrap_templates'`.
- Verified green state with `cd backend && ./.venv/bin/python -m pytest tests/test_bootstrap_setup.py -v`, which passed with `3 passed`.
