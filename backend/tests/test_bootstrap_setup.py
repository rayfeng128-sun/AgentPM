from pathlib import Path

import yaml

from app.bootstrap_templates import render_agentpm_yaml, render_agents_md, render_codex_md


def test_render_agentpm_yaml_uses_project_name_and_absolute_path(tmp_path: Path) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()

    rendered = render_agentpm_yaml("Demo Project", project_dir)
    loaded = yaml.safe_load(rendered)

    assert loaded == {
        "project": {
            "name": "Demo Project",
            "path": str(project_dir),
        },
        "milestones": [
            {
                "id": "setup",
                "title": "Initial Setup",
                "tasks": [
                    {
                        "id": "define-scope",
                        "title": "Define initial project scope",
                        "status": "todo",
                    },
                    {
                        "id": "start-codex-work",
                        "title": "Run Codex from the project root",
                        "status": "todo",
                    },
                ],
            }
        ],
    }


def test_render_agentpm_yaml_escapes_special_characters_in_dynamic_values(tmp_path: Path) -> None:
    project_dir = (tmp_path / "demo:project #1").resolve()
    project_dir.mkdir()

    rendered = render_agentpm_yaml("Demo: Project #1", project_dir)
    loaded = yaml.safe_load(rendered)

    assert loaded["project"] == {
        "name": "Demo: Project #1",
        "path": str(project_dir),
    }


def test_render_agents_md_points_to_agentpm_yaml() -> None:
    rendered = render_agents_md("Demo Project")

    assert "# AGENTS.md" in rendered
    assert "prepared for AgentPM" in rendered
    assert "`agentpm.yaml`" in rendered


def test_render_codex_md_stays_lightweight() -> None:
    rendered = render_codex_md("Demo Project")

    assert "# CODEX.md" in rendered
    assert "AgentPM" in rendered
    assert "agentpm.yaml" in rendered
    assert "Demo Project" in rendered
