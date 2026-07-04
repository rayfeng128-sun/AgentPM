# CODEX.md

This is the Codex-specific entry point for AgentPM.

## Read Order

1. [AGENTS.md](AGENTS.md)
2. [docs/product/01-codex-project-board-prd.md](docs/product/01-codex-project-board-prd.md)
3. [agentpm.yaml](agentpm.yaml)
4. [docs/README.md](docs/README.md)
5. [AGENT/README.md](AGENT/README.md)

For any development change, also read:

1. [references/Harness/QUICKSTART.md](references/Harness/QUICKSTART.md)
2. [references/Harness/AGENTS.md](references/Harness/AGENTS.md)
3. The relevant file under `references/Harness/rules/`

## Codex Working Notes

- Treat AgentPM as a FastAPI + React local app.
- If `.codegraph/` exists, use CodeGraph first for code analysis before `rg`, `find`, or manual file reading.
- Create or update a record under `references/Harness/changes/` for every development change.
- Do not assume this repository is the reusable governance template itself.
- Keep template methodology in `docs/process/` and project instructions in root files.
- Prefer concise documentation updates over copying whole template documents into project-facing README files.
- Before claiming completion, run a fresh verification appropriate to the change.
