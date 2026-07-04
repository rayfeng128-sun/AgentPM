# Change Record

- Date: 2026-07-04
- Change ID: agentpm-bootstrap-setup
- Flow: lightweight

## Request

Add a new AgentPM onboarding capability: a local script that helps a user prepare a Codex project for AgentPM with minimal pollution to the target project's business scenario, interactive handling of existing files, and practical rollback support.

## Scope

- Define the v1 design for a path-based AgentPM bootstrap script.
- Keep the target project's business-facing structure clean by isolating AgentPM operational state in `.agentpm/`.
- Support creation of `agentpm.yaml` plus optional lightweight `AGENTS.md` and `CODEX.md`.
- Require interactive decisions for existing files instead of silent overwrites.
- Require rollback metadata and a reversible setup model.

## Outputs

- `docs/superpowers/specs/2026-07-04-agentpm-bootstrap-setup-design.md`
- future implementation plan for the bootstrap script
- `backend/app/bootstrap_templates.py`
- `backend/tests/test_bootstrap_setup.py`

## Verification

- Verified by reviewing the approved design against the user constraints.
- Verified by checking that the design keeps setup metadata out of business-facing project structure by default.
- Verified TDD red state with `cd backend && ./.venv/bin/python -m pytest tests/test_bootstrap_setup.py -v`, which failed with `ModuleNotFoundError: No module named 'app.bootstrap_templates'`.
- Verified green state with `cd backend && ./.venv/bin/python -m pytest tests/test_bootstrap_setup.py -v`, which passed with `3 passed`.
