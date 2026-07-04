import subprocess
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


def test_repo_launcher_runs_cli_dry_run(tmp_path: Path) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()
    launcher = Path(__file__).resolve().parents[1] / "agentpm-bootstrap"

    result = subprocess.run(
        [str(launcher), "--target", str(project_dir), "--project-name", "Demo Project", "--dry-run"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "agentpm.yaml: create" in result.stdout
    assert "AGENTS.md: create" in result.stdout
    assert "CODEX.md: create" in result.stdout


def test_cli_apply_respects_prompt_answers(tmp_path: Path, monkeypatch, capsys) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()
    (project_dir / "AGENTS.md").write_text("# Existing\n", encoding="utf-8")
    answers = iter(["create", "skip", "create"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    exit_code = main(["--target", str(project_dir), "--project-name", "Demo Project"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert (project_dir / "agentpm.yaml").exists()
    assert (project_dir / "CODEX.md").exists()
    assert (project_dir / "AGENTS.md").read_text(encoding="utf-8") == "# Existing\n"
    assert f"Created: {project_dir / 'agentpm.yaml'}" in output
    assert f"Created: {project_dir / 'CODEX.md'}" in output


def test_cli_apply_retries_invalid_answers_and_supports_cancel(tmp_path: Path, monkeypatch, capsys) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()
    answers = iter(["maybe", "cancel"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    exit_code = main(["--target", str(project_dir), "--project-name", "Demo Project"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Please answer with one of the supported actions." in output
    assert "Cancelled. No files were changed." in output
    assert not (project_dir / "agentpm.yaml").exists()
    assert not (project_dir / "AGENTS.md").exists()
    assert not (project_dir / "CODEX.md").exists()


def test_cli_apply_handles_eof_without_mutating_files(tmp_path: Path, monkeypatch, capsys) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()
    monkeypatch.setattr("builtins.input", lambda _: (_ for _ in ()).throw(EOFError()))

    exit_code = main(["--target", str(project_dir), "--project-name", "Demo Project"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Cancelled. No files were changed." in output
    assert not (project_dir / "agentpm.yaml").exists()
    assert not (project_dir / "AGENTS.md").exists()
    assert not (project_dir / "CODEX.md").exists()


def test_cli_rollback_restores_last_setup_run(tmp_path: Path, monkeypatch, capsys) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()
    answers = iter(["create", "create", "create"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert main(["--target", str(project_dir), "--project-name", "Demo Project"]) == 0

    exit_code = main(["--target", str(project_dir), "--rollback"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert not (project_dir / "agentpm.yaml").exists()
    assert not (project_dir / "CODEX.md").exists()
    assert f"Deleted: {project_dir / 'agentpm.yaml'}" in output
    assert f"Deleted: {project_dir / 'CODEX.md'}" in output


def test_cli_rollback_warnings_return_nonzero(tmp_path: Path, monkeypatch, capsys) -> None:
    project_dir = (tmp_path / "demo-project").resolve()
    project_dir.mkdir()
    answers = iter(["create", "skip", "skip"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert main(["--target", str(project_dir), "--project-name", "Demo Project"]) == 0
    (project_dir / "agentpm.yaml").write_text("project:\n  name: Changed later\n", encoding="utf-8")

    exit_code = main(["--target", str(project_dir), "--rollback"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "agentpm.yaml changed after setup; rollback skipped it." in output
