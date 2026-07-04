# Change Record

- Date: 2026-07-04
- Change ID: agentpm-bootstrap-setup
- Flow: lightweight

## Request

Implement Task 2 of the AgentPM bootstrap flow: core setup planning and safe apply behavior, plus the focused decision-validation follow-up needed before later tasks.

## Scope

- Add planning models and `build_setup_plan()` so bootstrap setup can inspect whether `agentpm.yaml`, `AGENTS.md`, and `CODEX.md` should be created or prompted.
- Add `apply_setup()` so bootstrap setup can create approved new files, update approved existing files, and write a `.agentpm/setup-manifest.json` record.
- Validate decisions explicitly by rejecting unsupported values, rejecting state-incompatible combinations, and requiring `update` rather than `create` for prompted existing files.
- Cover the planning/apply flow with focused test-first pytest coverage, including modified file reporting, manifest content, and invalid-decision rejection.
- Do not add CLI behavior, rollback behavior, or broader bootstrap orchestration beyond this planning/apply slice.

## Outputs

- `backend/app/bootstrap_templates.py`
- `backend/app/bootstrap_setup.py`
- `backend/tests/test_bootstrap_setup.py`

## Verification

- Verified the original Task 2 red state with `cd backend && ./.venv/bin/python -m pytest tests/test_bootstrap_setup.py -v`, which failed with `ModuleNotFoundError: No module named 'app.bootstrap_setup'` before `backend/app/bootstrap_setup.py` existed.
- Verified the quality follow-up red state with `cd backend && ./.venv/bin/python -m pytest tests/test_bootstrap_setup.py -v`, which failed in `test_apply_setup_rejects_invalid_decisions` because `apply_setup()` accepted invalid decisions.
- Verified the delivered Task 2 slice with `cd backend && ./.venv/bin/python -m pytest tests/test_bootstrap_setup.py -v`, which now passes with `11 passed`.
