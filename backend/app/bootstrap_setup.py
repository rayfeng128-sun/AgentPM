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
