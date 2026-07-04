from pathlib import Path

from app.bootstrap_cli import main


def test_cli_dry_run_prints_planned_actions(tmp_path: Path, capsys) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()

    exit_code = main(["--target", str(project_dir), "--project-name", "Demo Project", "--dry-run"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "agentpm.yaml: create" in output
    assert "AGENTS.md: create" in output
    assert "CODEX.md: create" in output


def test_cli_apply_respects_prompt_answers(tmp_path: Path, monkeypatch) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()
    (project_dir / "AGENTS.md").write_text("# Existing\n", encoding="utf-8")
    answers = iter(["create", "skip", "create"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    exit_code = main(["--target", str(project_dir), "--project-name", "Demo Project"])

    assert exit_code == 0
    assert (project_dir / "agentpm.yaml").exists()
    assert (project_dir / "CODEX.md").exists()
    assert (project_dir / "AGENTS.md").read_text(encoding="utf-8") == "# Existing\n"


def test_cli_rollback_restores_last_setup_run(tmp_path: Path, monkeypatch) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()
    answers = iter(["create", "create", "create"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert main(["--target", str(project_dir), "--project-name", "Demo Project"]) == 0

    exit_code = main(["--target", str(project_dir), "--rollback"])

    assert exit_code == 0
    assert not (project_dir / "agentpm.yaml").exists()
    assert not (project_dir / "CODEX.md").exists()
