from pathlib import Path

import yaml

from app.bootstrap_setup import apply_setup, build_setup_plan
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

def test_build_setup_plan_marks_missing_files_for_creation(tmp_path: Path) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()

    plan = build_setup_plan(project_dir, project_name="Demo Project")

    assert plan.project_path == project_dir
    assert plan.project_name == "Demo Project"
    assert plan.agentpm_dir.name == ".agentpm"
    assert plan.agentpm_yaml.action == "create"
    assert plan.agents_md.action == "create"
    assert plan.codex_md.action == "create"


def test_build_setup_plan_marks_existing_files_for_prompt(tmp_path: Path) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()
    (project_dir / "agentpm.yaml").write_text("project: {}\n", encoding="utf-8")
    (project_dir / "AGENTS.md").write_text("# AGENTS.md\n", encoding="utf-8")

    plan = build_setup_plan(project_dir, project_name="Demo Project")

    assert plan.agentpm_yaml.action == "prompt"
    assert plan.agents_md.action == "prompt"
    assert plan.codex_md.action == "create"


def test_apply_setup_creates_only_approved_files(tmp_path: Path) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()
    (project_dir / "AGENTS.md").write_text("# Existing\n", encoding="utf-8")

    plan = build_setup_plan(project_dir, project_name="Demo Project")
    result = apply_setup(
        plan,
        decisions={
            "agentpm.yaml": "create",
            "AGENTS.md": "skip",
            "CODEX.md": "create",
        },
    )

    assert result.created_files == [
        project_dir / ".agentpm" / "setup-manifest.json",
        project_dir / "agentpm.yaml",
        project_dir / "CODEX.md",
    ]
    assert (project_dir / "agentpm.yaml").exists()
    assert (project_dir / "CODEX.md").exists()
    assert (project_dir / "AGENTS.md").read_text(encoding="utf-8") == "# Existing\n"
