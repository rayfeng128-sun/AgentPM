# Change Record

- Date: 2026-07-04
- Change ID: agentpm-bootstrap-setup
- Flow: lightweight

## Request

Implement the AgentPM bootstrap feature end to end: generate starter project files, plan and apply setup safely, keep operational state under `.agentpm/`, support rollback, expose the workflow through the `agentpm-bootstrap` CLI, and document how to use it from this repository.

## Scope

- Add the bootstrap template layer for starter `agentpm.yaml`, `AGENTS.md`, and `CODEX.md` content.
- Add planning models and `build_setup_plan()` so bootstrap setup can inspect whether `agentpm.yaml`, `AGENTS.md`, and `CODEX.md` should be created or prompted.
- Add `apply_setup()` so bootstrap setup can create approved new files, update approved existing files, and write `.agentpm/setup-manifest.json` plus any needed backups under `.agentpm/backups/`.
- Validate decisions explicitly by rejecting unsupported values, rejecting state-incompatible combinations, and requiring `update` rather than `create` for prompted existing files.
- Add `rollback_setup()` so bootstrap setup can safely delete managed created files, restore managed backups, and stop with warnings when user changes or unsafe paths are detected.
- Add `backend/app/bootstrap_cli.py` plus the `agentpm-bootstrap` console script entry for dry-run, interactive apply, cancel-safe prompting, and rollback.
- Document the implemented bootstrap command, created files, operational-state location, and rollback behavior in the project docs.

## Outputs

- `backend/app/bootstrap_templates.py`
- `backend/app/bootstrap_setup.py`
- `backend/app/bootstrap_cli.py`
- `backend/tests/test_bootstrap_setup.py`
- `backend/tests/test_bootstrap_cli.py`
- `backend/pyproject.toml`
- `README.md`
- `docs/README.md`

## Verification

- Historical red-state verification for the setup core used `cd backend && ./.venv/bin/python -m pytest tests/test_bootstrap_setup.py -v`, which first failed with `ModuleNotFoundError: No module named 'app.bootstrap_setup'` before `backend/app/bootstrap_setup.py` existed.
- Historical hardening verification for the setup core used `cd backend && ./.venv/bin/python -m pytest tests/test_bootstrap_setup.py -v`, which failed in `test_apply_setup_rejects_invalid_decisions` before invalid decision handling was added.
- Historical red-state verification for the CLI used `cd backend && ./.venv/bin/python -m pytest tests/test_bootstrap_cli.py -v`, which first failed with `ModuleNotFoundError: No module named 'app.bootstrap_cli'` before `backend/app/bootstrap_cli.py` existed.
- Historical CLI hardening verification used `cd backend && ./.venv/bin/python -m pytest tests/test_bootstrap_cli.py -v`, which failed on missing apply and rollback output plus missing cancel and interruption handling before those behaviors were added.
- Final targeted bootstrap verification used `cd backend && ./.venv/bin/python -m pytest tests/test_bootstrap_setup.py tests/test_bootstrap_cli.py -v`, which passed with `25 passed`.
- Full backend verification used `cd backend && ./.venv/bin/python -m pytest`, which passed with `77 passed` and 4 warnings.
- Editable-install smoke verification was attempted with `cd /Users/ray/BaiduNetDisk/Project/AgentPM && backend/.venv/bin/python -m pip install -e "./backend[test]"` and `--no-build-isolation`, but could not complete in this environment because the local repo venv does not contain `setuptools` or `wheel`, and outbound network access is restricted. The backend package now declares an explicit build system in `backend/pyproject.toml`, so the remaining blocker is the local environment rather than the bootstrap code path.
- Documentation closure verification used `rg -n "agentpm-bootstrap|bootstrap-setup|2026-07-04-agentpm-bootstrap" README.md docs/README.md references/Harness/changes/2026-07-04/agentpm-bootstrap-setup/change.md`, which matched the README bootstrap commands, the docs index entries, and this consolidated change record with no stale bootstrap placeholders.
