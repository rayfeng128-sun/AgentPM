from pathlib import Path


def render_agentpm_yaml(project_name: str, project_path: Path) -> str:
    return f"""project:
  name: {project_name}
  path: {project_path}

milestones:
  - id: setup
    title: Initial Setup
    tasks:
      - id: define-scope
        title: Define initial project scope
        status: todo
      - id: start-codex-work
        title: Run Codex from the project root
        status: todo
"""


def render_agents_md(project_name: str) -> str:
    return f"""# AGENTS.md

This repository is prepared for AgentPM.

- Project: {project_name}
- Main project-tracking file: `agentpm.yaml`
- Keep AgentPM-specific operational metadata under `.agentpm/` when possible.
"""


def render_codex_md(project_name: str) -> str:
    return f"""# CODEX.md

This repository is prepared for AgentPM.

## Read First

1. `agentpm.yaml`
2. `AGENTS.md`

Run Codex from this project root so AgentPM can match Codex sessions to this repository path.
"""
