import json
from pathlib import Path

import pytest
import yaml

from app.bootstrap_setup import apply_setup, build_setup_plan, rollback_setup
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


def test_apply_setup_updates_existing_file_only_with_explicit_update(tmp_path: Path) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()
    (project_dir / "AGENTS.md").write_text("# Existing\n", encoding="utf-8")

    plan = build_setup_plan(project_dir, project_name="Demo Project")
    result = apply_setup(
        plan,
        decisions={
            "agentpm.yaml": "create",
            "AGENTS.md": "update",
            "CODEX.md": "skip",
        },
    )

    assert result.created_files == [
        project_dir / ".agentpm" / "setup-manifest.json",
        project_dir / "agentpm.yaml",
    ]
    assert result.modified_files == [project_dir / "AGENTS.md"]
    assert (project_dir / "AGENTS.md").read_text(encoding="utf-8") == render_agents_md("Demo Project")


def test_apply_setup_writes_manifest_with_created_and_modified_files(tmp_path: Path) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()
    (project_dir / "AGENTS.md").write_text("# Existing\n", encoding="utf-8")

    plan = build_setup_plan(project_dir, project_name="Demo Project")
    apply_setup(
        plan,
        decisions={
            "agentpm.yaml": "create",
            "AGENTS.md": "update",
            "CODEX.md": "skip",
        },
    )

    manifest = json.loads((project_dir / ".agentpm" / "setup-manifest.json").read_text(encoding="utf-8"))

    assert manifest["project_path"] == str(project_dir)
    assert manifest["run_id"]
    assert manifest["created_files"] == [str(project_dir / "agentpm.yaml")]
    assert manifest["modified_files"] == [str(project_dir / "AGENTS.md")]
    assert manifest["created_file_details"] == [
        {
            "path": str(project_dir / "agentpm.yaml"),
            "written_sha256": manifest["created_file_details"][0]["written_sha256"],
        }
    ]
    assert manifest["modified_file_details"] == [
        {
            "path": str(project_dir / "AGENTS.md"),
            "backup_path": manifest["modified_file_details"][0]["backup_path"],
            "original_sha256": manifest["modified_file_details"][0]["original_sha256"],
            "written_sha256": manifest["modified_file_details"][0]["written_sha256"],
        }
    ]
    assert Path(manifest["modified_file_details"][0]["backup_path"]).exists()


def test_apply_setup_backs_up_existing_files_before_update(tmp_path: Path) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()
    existing_agents = project_dir / "AGENTS.md"
    existing_agents.write_text("# Existing\n", encoding="utf-8")

    plan = build_setup_plan(project_dir, project_name="Demo Project")
    result = apply_setup(
        plan,
        decisions={
            "agentpm.yaml": "create",
            "AGENTS.md": "update",
            "CODEX.md": "skip",
        },
    )

    backup_dir = project_dir / ".agentpm" / "backups"
    assert result.modified_files == [existing_agents]
    assert backup_dir.exists()
    assert any(path.name.startswith("AGENTS.md.") for path in backup_dir.iterdir())


def test_rollback_removes_created_files_and_restores_backups(tmp_path: Path) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()
    existing_agents = project_dir / "AGENTS.md"
    existing_agents.write_text("# Existing\n", encoding="utf-8")

    plan = build_setup_plan(project_dir, project_name="Demo Project")
    apply_setup(
        plan,
        decisions={
            "agentpm.yaml": "create",
            "AGENTS.md": "update",
            "CODEX.md": "create",
        },
    )
    manifest = json.loads((project_dir / ".agentpm" / "setup-manifest.json").read_text(encoding="utf-8"))
    backup_path = Path(manifest["modified_file_details"][0]["backup_path"])

    rollback_result = rollback_setup(project_dir)

    assert rollback_result.restored_files == [existing_agents]
    assert rollback_result.deleted_files == [project_dir / "agentpm.yaml", project_dir / "CODEX.md"]
    assert existing_agents.read_text(encoding="utf-8") == "# Existing\n"
    assert not (project_dir / "agentpm.yaml").exists()
    assert not (project_dir / "CODEX.md").exists()
    assert not backup_path.exists()


def test_rollback_stops_when_file_changed_after_setup(tmp_path: Path) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()
    existing_agents = project_dir / "AGENTS.md"
    existing_agents.write_text("# Existing\n", encoding="utf-8")

    plan = build_setup_plan(project_dir, project_name="Demo Project")
    apply_setup(
        plan,
        decisions={
            "agentpm.yaml": "skip",
            "AGENTS.md": "update",
            "CODEX.md": "skip",
        },
    )
    existing_agents.write_text("# User changed this later\n", encoding="utf-8")

    rollback_result = rollback_setup(project_dir)

    assert rollback_result.warnings == ["AGENTS.md changed after setup; rollback skipped it."]
    assert existing_agents.read_text(encoding="utf-8") == "# User changed this later\n"


@pytest.mark.parametrize(
    ("decisions", "message"),
    [
        (
            {
                "agentpm.yaml": "overwrite",
                "AGENTS.md": "skip",
                "CODEX.md": "skip",
            },
            "Unsupported decision",
        ),
        (
            {
                "agentpm.yaml": "skip",
                "AGENTS.md": "create",
                "CODEX.md": "skip",
            },
            "Incompatible decision",
        ),
    ],
)
def test_apply_setup_rejects_invalid_decisions(
    tmp_path: Path, decisions: dict[str, str], message: str
) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()
    (project_dir / "AGENTS.md").write_text("# Existing\n", encoding="utf-8")

    plan = build_setup_plan(project_dir, project_name="Demo Project")

    with pytest.raises(ValueError, match=message):
        apply_setup(plan, decisions=decisions)

    assert not (project_dir / ".agentpm").exists()
    assert not (project_dir / ".agentpm" / "setup-manifest.json").exists()
