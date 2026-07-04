from pathlib import Path

from app.bootstrap_templates import render_agentpm_yaml, render_agents_md, render_codex_md


def test_render_agentpm_yaml_uses_project_name_and_absolute_path(tmp_path: Path) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()

    rendered = render_agentpm_yaml("Demo Project", project_dir)

    assert "name: Demo Project" in rendered
    assert f"path: {project_dir}" in rendered
    assert "milestones:" in rendered
    assert "status: todo" in rendered


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
