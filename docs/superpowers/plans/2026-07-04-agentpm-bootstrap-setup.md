# AgentPM Bootstrap Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local bootstrap script that prepares a target Codex project for AgentPM by creating minimal metadata files, isolating setup state in `.agentpm/`, prompting before touching existing files, and supporting rollback.

**Architecture:** Keep the feature in the backend Python package as a small CLI plus a core setup module. Separate the work into template rendering, target-project inspection and apply logic, rollback bookkeeping, and a thin command entry point so the setup behavior is testable without shelling out. Store all AgentPM operational state for the target project under `.agentpm/` and treat root-level files as a narrow managed surface.

**Tech Stack:** Python 3.11+, FastAPI backend package layout, PyYAML, pytest

---

## File Structure

- Modify: `backend/pyproject.toml`
  Add a console entry point for the bootstrap command.
- Create: `backend/app/bootstrap_templates.py`
  Keep lightweight render helpers for `agentpm.yaml`, `AGENTS.md`, and `CODEX.md`.
- Create: `backend/app/bootstrap_setup.py`
  Hold inspection, setup planning, apply, manifest, backup, and rollback logic.
- Create: `backend/app/bootstrap_cli.py`
  Provide the user-facing path-based command with dry-run, apply, and rollback modes.
- Create: `backend/tests/test_bootstrap_setup.py`
  Cover planning, safe writes, existing-file prompts, manifest creation, and rollback behavior.
- Create: `backend/tests/test_bootstrap_cli.py`
  Cover CLI output, dry-run behavior, prompt handling, and rollback command wiring.
- Modify: `README.md`
  Document how to run the bootstrap script and what it creates.
- Modify: `docs/README.md`
  Add the new design and implementation plan to the Superpowers artifacts list.
- Modify: `references/Harness/changes/2026-07-04/agentpm-bootstrap-setup/change.md`
  Update outputs and verification once the implementation exists.

## Task 1: Build The Template Layer With Test-First Coverage

**Files:**
- Create: `backend/app/bootstrap_templates.py`
- Create: `backend/tests/test_bootstrap_setup.py`
- Test: `backend/tests/test_bootstrap_setup.py`

- [ ] **Step 1: Write the failing template-rendering tests**

Add these tests to `backend/tests/test_bootstrap_setup.py`:

```python
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
```

- [ ] **Step 2: Run the template tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_bootstrap_setup.py -v`

Expected: `FAIL` because `app.bootstrap_templates` does not exist yet.

- [ ] **Step 3: Create the template module with minimal render helpers**

Create `backend/app/bootstrap_templates.py` with:

```python
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
```

- [ ] **Step 4: Re-run the template tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_bootstrap_setup.py -v`

Expected: `PASS`

- [ ] **Step 5: Commit the template layer**

```bash
git add backend/app/bootstrap_templates.py backend/tests/test_bootstrap_setup.py
git commit -m "feat: add agentpm bootstrap templates"
```

## Task 2: Add Failing Core Setup Tests For Inspection, Planning, And Safe Apply

**Files:**
- Modify: `backend/tests/test_bootstrap_setup.py`
- Create: `backend/app/bootstrap_setup.py`
- Test: `backend/tests/test_bootstrap_setup.py`

- [ ] **Step 1: Write the failing core setup tests**

Append these tests to `backend/tests/test_bootstrap_setup.py`:

```python
from app.bootstrap_setup import build_setup_plan, apply_setup


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
```

- [ ] **Step 2: Run the setup tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_bootstrap_setup.py -v`

Expected: `FAIL` because `app.bootstrap_setup` does not exist yet.

- [ ] **Step 3: Implement the setup planning and apply module**

Create `backend/app/bootstrap_setup.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .bootstrap_templates import render_agentpm_yaml, render_agents_md, render_codex_md


@dataclass(frozen=True)
class PlannedFile:
    path: Path
    action: str


@dataclass(frozen=True)
class SetupPlan:
    project_path: Path
    project_name: str
    agentpm_dir: Path
    agentpm_yaml: PlannedFile
    agents_md: PlannedFile
    codex_md: PlannedFile


@dataclass(frozen=True)
class ApplyResult:
    created_files: list[Path]
    modified_files: list[Path]


def _planned_file(path: Path) -> PlannedFile:
    return PlannedFile(path=path, action="prompt" if path.exists() else "create")


def build_setup_plan(project_path: Path, project_name: str | None = None) -> SetupPlan:
    resolved = project_path.expanduser().resolve()
    if not resolved.exists() or not resolved.is_dir():
        raise ValueError("Target project path must be an existing directory")

    return SetupPlan(
        project_path=resolved,
        project_name=project_name or resolved.name,
        agentpm_dir=resolved / ".agentpm",
        agentpm_yaml=_planned_file(resolved / "agentpm.yaml"),
        agents_md=_planned_file(resolved / "AGENTS.md"),
        codex_md=_planned_file(resolved / "CODEX.md"),
    )


def apply_setup(plan: SetupPlan, decisions: dict[str, str]) -> ApplyResult:
    created_files: list[Path] = []
    modified_files: list[Path] = []
    plan.agentpm_dir.mkdir(exist_ok=True)

    writes = {
        "agentpm.yaml": render_agentpm_yaml(plan.project_name, plan.project_path),
        "AGENTS.md": render_agents_md(plan.project_name),
        "CODEX.md": render_codex_md(plan.project_name),
    }
    targets = {
        "agentpm.yaml": plan.agentpm_yaml.path,
        "AGENTS.md": plan.agents_md.path,
        "CODEX.md": plan.codex_md.path,
    }

    for name, content in writes.items():
        decision = decisions.get(name, "skip")
        target = targets[name]
        if decision == "skip":
            continue
        if target.exists():
            modified_files.append(target)
        else:
            created_files.append(target)
        target.write_text(content, encoding="utf-8")

    manifest_path = plan.agentpm_dir / "setup-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "project_path": str(plan.project_path),
                "created_files": [str(path) for path in created_files],
                "modified_files": [str(path) for path in modified_files],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    created_files.insert(0, manifest_path)
    return ApplyResult(created_files=created_files, modified_files=modified_files)
```

- [ ] **Step 4: Re-run the setup tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_bootstrap_setup.py -v`

Expected: `PASS`

- [ ] **Step 5: Commit the core setup flow**

```bash
git add backend/app/bootstrap_setup.py backend/tests/test_bootstrap_setup.py
git commit -m "feat: add agentpm bootstrap setup flow"
```

## Task 3: Add Failing Rollback Tests And Implement Backup-Aware Reversion

**Files:**
- Modify: `backend/tests/test_bootstrap_setup.py`
- Modify: `backend/app/bootstrap_setup.py`
- Test: `backend/tests/test_bootstrap_setup.py`

- [ ] **Step 1: Write the failing rollback tests**

Append these tests to `backend/tests/test_bootstrap_setup.py`:

```python
from app.bootstrap_setup import rollback_setup


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

    rollback_result = rollback_setup(project_dir)

    assert rollback_result.restored_files == [existing_agents]
    assert rollback_result.deleted_files == [project_dir / "agentpm.yaml", project_dir / "CODEX.md"]
    assert existing_agents.read_text(encoding="utf-8") == "# Existing\n"
    assert not (project_dir / "agentpm.yaml").exists()
    assert not (project_dir / "CODEX.md").exists()


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
```

- [ ] **Step 2: Run the rollback tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_bootstrap_setup.py -v`

Expected: `FAIL` because backups and rollback do not exist yet.

- [ ] **Step 3: Extend the setup module with manifest, backup, and rollback support**

Update `backend/app/bootstrap_setup.py` by adding:

```python
from dataclasses import asdict, dataclass
import hashlib
from typing import Any
from uuid import uuid4
```

Add these dataclasses near the top:

```python
@dataclass(frozen=True)
class RollbackResult:
    deleted_files: list[Path]
    restored_files: list[Path]
    warnings: list[str]
```

Add these helpers:

```python
def _sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _backup_file(target: Path, backup_dir: Path, run_id: str) -> tuple[Path, str]:
    backup_dir.mkdir(parents=True, exist_ok=True)
    content = target.read_text(encoding="utf-8")
    backup_path = backup_dir / f"{target.name}.{run_id}.bak"
    backup_path.write_text(content, encoding="utf-8")
    return backup_path, _sha256_text(content)
```

Change the manifest payload inside `apply_setup()` to include run metadata:

```python
run_id = uuid4().hex
manifest_modified: list[dict[str, str]] = []
...
if target.exists():
    backup_path, previous_sha256 = _backup_file(target, plan.agentpm_dir / "backups", run_id)
    manifest_modified.append(
        {
            "path": str(target),
            "backup_path": str(backup_path),
            "previous_sha256": previous_sha256,
            "written_sha256": _sha256_text(content),
        }
    )
...
manifest = {
    "run_id": run_id,
    "project_path": str(plan.project_path),
    "created_files": [str(path) for path in created_files],
    "modified_files": manifest_modified,
}
```

Add rollback support:

```python
def rollback_setup(project_path: Path) -> RollbackResult:
    resolved = project_path.expanduser().resolve()
    manifest_path = resolved / ".agentpm" / "setup-manifest.json"
    manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))

    deleted_files: list[Path] = []
    restored_files: list[Path] = []
    warnings: list[str] = []

    for raw_path in manifest.get("created_files", []):
        path = Path(raw_path)
        if path.name == "setup-manifest.json":
            continue
        if path.exists():
            path.unlink()
            deleted_files.append(path)

    for item in manifest.get("modified_files", []):
        target = Path(item["path"])
        if not target.exists():
            warnings.append(f"{target.name} is missing; rollback skipped it.")
            continue
        current_sha256 = _sha256_text(target.read_text(encoding="utf-8"))
        if current_sha256 != item["written_sha256"]:
            warnings.append(f"{target.name} changed after setup; rollback skipped it.")
            continue
        backup_path = Path(item["backup_path"])
        target.write_text(backup_path.read_text(encoding="utf-8"), encoding="utf-8")
        restored_files.append(target)

    return RollbackResult(
        deleted_files=deleted_files,
        restored_files=restored_files,
        warnings=warnings,
    )
```

- [ ] **Step 4: Re-run the rollback tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_bootstrap_setup.py -v`

Expected: `PASS`

- [ ] **Step 5: Commit rollback support**

```bash
git add backend/app/bootstrap_setup.py backend/tests/test_bootstrap_setup.py
git commit -m "feat: add bootstrap rollback support"
```

## Task 4: Add The CLI Entry Point With Dry-Run And Prompt Handling

**Files:**
- Create: `backend/app/bootstrap_cli.py`
- Create: `backend/tests/test_bootstrap_cli.py`
- Modify: `backend/pyproject.toml`
- Test: `backend/tests/test_bootstrap_cli.py`

- [ ] **Step 1: Write the failing CLI tests**

Create `backend/tests/test_bootstrap_cli.py` with:

```python
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
```

- [ ] **Step 2: Run the CLI tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_bootstrap_cli.py -v`

Expected: `FAIL` because `app.bootstrap_cli` does not exist yet.

- [ ] **Step 3: Create the CLI module**

Create `backend/app/bootstrap_cli.py` with:

```python
from __future__ import annotations

import argparse
from pathlib import Path

from .bootstrap_setup import apply_setup, build_setup_plan, rollback_setup


def _prompt_for_decision(label: str, action: str) -> str:
    if action == "create":
        return "create"
    response = input(f"{label} exists. Choose [skip/update/cancel]: ").strip().lower()
    if response not in {"skip", "update", "cancel"}:
        return "skip"
    return response


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentpm-bootstrap")
    parser.add_argument("--target", required=True)
    parser.add_argument("--project-name")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--rollback", action="store_true")
    args = parser.parse_args(argv)

    project_path = Path(args.target)
    if args.rollback:
        result = rollback_setup(project_path)
        for path in result.deleted_files:
            print(f"deleted: {path}")
        for path in result.restored_files:
            print(f"restored: {path}")
        for warning in result.warnings:
            print(f"warning: {warning}")
        return 0

    plan = build_setup_plan(project_path, project_name=args.project_name)
    planned = {
        "agentpm.yaml": plan.agentpm_yaml.action,
        "AGENTS.md": plan.agents_md.action,
        "CODEX.md": plan.codex_md.action,
    }

    for name, action in planned.items():
        print(f"{name}: {action}")
    if args.dry_run:
        return 0

    decisions = {
        "agentpm.yaml": _prompt_for_decision("agentpm.yaml", plan.agentpm_yaml.action),
        "AGENTS.md": _prompt_for_decision("AGENTS.md", plan.agents_md.action),
        "CODEX.md": _prompt_for_decision("CODEX.md", plan.codex_md.action),
    }
    if "cancel" in decisions.values():
        print("setup canceled")
        return 1

    result = apply_setup(plan, decisions)
    for path in result.created_files:
        print(f"created: {path}")
    for path in result.modified_files:
        print(f"modified: {path}")
    return 0
```

- [ ] **Step 4: Add the console entry point**

Update `backend/pyproject.toml` by adding:

```toml
[project.scripts]
agentpm-bootstrap = "app.bootstrap_cli:main"
```

- [ ] **Step 5: Re-run the CLI tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_bootstrap_cli.py -v`

Expected: `PASS`

- [ ] **Step 6: Commit the CLI**

```bash
git add backend/app/bootstrap_cli.py backend/tests/test_bootstrap_cli.py backend/pyproject.toml
git commit -m "feat: add agentpm bootstrap cli"
```

## Task 5: Document The User Flow And Close The Change Record

**Files:**
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `references/Harness/changes/2026-07-04/agentpm-bootstrap-setup/change.md`
- Test: documentation inspection only

- [ ] **Step 1: Add the new setup command to the README**

Update `README.md` by replacing the manual setup-only guidance with this additional section:

```md
## Bootstrap A Codex Project For AgentPM

From the AgentPM repository:

```bash
cd backend
python -m pip install -e ".[test]"
agentpm-bootstrap --target /absolute/path/to/my-project --project-name "My Project" --dry-run
agentpm-bootstrap --target /absolute/path/to/my-project --project-name "My Project"
```

The bootstrap script:

- creates a starter `agentpm.yaml` when missing
- keeps AgentPM operational metadata under `.agentpm/`
- asks before changing existing `agentpm.yaml`, `AGENTS.md`, or `CODEX.md`
- supports rollback with:

```bash
agentpm-bootstrap --target /absolute/path/to/my-project --rollback
```
```

- [ ] **Step 2: Add the new plan to the docs index**

Update `docs/README.md` by appending:

```md
- [docs/superpowers/specs/2026-07-04-agentpm-bootstrap-setup-design.md](superpowers/specs/2026-07-04-agentpm-bootstrap-setup-design.md)
- [docs/superpowers/plans/2026-07-04-agentpm-bootstrap-setup.md](superpowers/plans/2026-07-04-agentpm-bootstrap-setup.md)
```

- [ ] **Step 3: Update the change record outputs and verification**

Update `references/Harness/changes/2026-07-04/agentpm-bootstrap-setup/change.md` so `Outputs` includes:

```md
- `backend/app/bootstrap_templates.py`
- `backend/app/bootstrap_setup.py`
- `backend/app/bootstrap_cli.py`
- `backend/tests/test_bootstrap_setup.py`
- `backend/tests/test_bootstrap_cli.py`
- `README.md`
- `docs/README.md`
```

And replace `Verification` with:

```md
- `cd backend && python -m pytest tests/test_bootstrap_setup.py -v`
- `cd backend && python -m pytest tests/test_bootstrap_cli.py -v`
- `cd backend && python -m pytest`
- Verified README bootstrap instructions against the implemented CLI flags and rollback mode.
```

- [ ] **Step 4: Run documentation verification**

Run: `cd /Users/ray/BaiduNetDisk/Project/AgentPM && rg -n "agentpm-bootstrap|bootstrap-setup" README.md docs/README.md references/Harness/changes/2026-07-04/agentpm-bootstrap-setup/change.md`

Expected: matches in all three files with no stale placeholders.

- [ ] **Step 5: Commit the docs**

```bash
git add README.md docs/README.md references/Harness/changes/2026-07-04/agentpm-bootstrap-setup/change.md
git commit -m "docs: add bootstrap setup guidance"
```

## Task 6: Run Full Verification And Prepare Handoff

**Files:**
- Modify: working tree only if fixes are needed
- Test: backend verification

- [ ] **Step 1: Run the targeted bootstrap tests**

Run: `cd backend && python -m pytest tests/test_bootstrap_setup.py tests/test_bootstrap_cli.py -v`

Expected: `PASS`

- [ ] **Step 2: Run the full backend suite**

Run: `cd backend && python -m pytest`

Expected: `PASS`

- [ ] **Step 3: Inspect the final diff**

Run: `cd /Users/ray/BaiduNetDisk/Project/AgentPM && git diff -- backend/pyproject.toml backend/app/bootstrap_templates.py backend/app/bootstrap_setup.py backend/app/bootstrap_cli.py backend/tests/test_bootstrap_setup.py backend/tests/test_bootstrap_cli.py README.md docs/README.md references/Harness/changes/2026-07-04/agentpm-bootstrap-setup/change.md`

Expected: diff limited to the planned bootstrap implementation and documentation updates.

- [ ] **Step 4: Commit any final verification fixes**

```bash
git add backend/pyproject.toml backend/app/bootstrap_templates.py backend/app/bootstrap_setup.py backend/app/bootstrap_cli.py backend/tests/test_bootstrap_setup.py backend/tests/test_bootstrap_cli.py README.md docs/README.md references/Harness/changes/2026-07-04/agentpm-bootstrap-setup/change.md
git commit -m "test: verify agentpm bootstrap setup"
```

## Self-Review

- Spec coverage check: the plan covers path-based execution, `.agentpm/` isolation, starter file generation, prompt-before-overwrite behavior, rollback metadata, rollback safety, and docs updates.
- Placeholder scan: no `TBD`, `TODO`, or implied “implement later” gaps remain in the plan steps.
- Type consistency check: the plan uses one command name, `agentpm-bootstrap`, one root sidecar directory, `.agentpm/`, and one rollback entry point, `rollback_setup()`, throughout.

Plan complete and saved to `docs/superpowers/plans/2026-07-04-agentpm-bootstrap-setup.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
