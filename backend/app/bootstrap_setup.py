from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

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


@dataclass(frozen=True)
class RollbackResult:
    deleted_files: list[Path]
    restored_files: list[Path]
    warnings: list[str]


@dataclass(frozen=True)
class CreatedFileManifestEntry:
    path: str
    written_sha256: str


@dataclass(frozen=True)
class ModifiedFileManifestEntry:
    path: str
    backup_path: str
    original_sha256: str
    written_sha256: str


@dataclass(frozen=True)
class CreatedRollbackOperation:
    target: Path


@dataclass(frozen=True)
class ModifiedRollbackOperation:
    target: Path
    backup_path: Path
    backup_content: str


def _validate_decision(name: str, planned_file: PlannedFile, decision: str) -> None:
    allowed_decisions = {"skip", "create", "update"}
    if decision not in allowed_decisions:
        raise ValueError(f"Unsupported decision for {name}: {decision}")

    allowed_by_state = {"skip", "create"} if planned_file.action == "create" else {"skip", "update"}
    if decision not in allowed_by_state:
        raise ValueError(
            f"Incompatible decision for {name}: {decision} is not allowed when action is {planned_file.action}"
        )


def _planned_file(path: Path) -> PlannedFile:
    return PlannedFile(path=path, action="prompt" if path.exists() else "create")


def _sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _backup_file(target: Path, backup_dir: Path, run_id: str) -> tuple[Path, str]:
    backup_dir.mkdir(parents=True, exist_ok=True)
    content = target.read_text(encoding="utf-8")
    backup_path = backup_dir / f"{target.name}.{run_id}.bak"
    backup_path.write_text(content, encoding="utf-8")
    return backup_path, _sha256_text(content)


def _resolve_manifest_path(path_value: str) -> Path:
    return Path(path_value).expanduser().resolve(strict=False)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _managed_target_paths(project_path: Path) -> set[Path]:
    return {
        project_path / "agentpm.yaml",
        project_path / "AGENTS.md",
        project_path / "CODEX.md",
    }


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
    created_manifest_entries: list[CreatedFileManifestEntry] = []
    modified_manifest_entries: list[ModifiedFileManifestEntry] = []
    run_id = uuid4().hex

    writes = {
        "agentpm.yaml": render_agentpm_yaml(plan.project_name, plan.project_path),
        "AGENTS.md": render_agents_md(plan.project_name),
        "CODEX.md": render_codex_md(plan.project_name),
    }
    planned_files = {
        "agentpm.yaml": plan.agentpm_yaml,
        "AGENTS.md": plan.agents_md,
        "CODEX.md": plan.codex_md,
    }

    for name in decisions:
        if name not in planned_files:
            raise ValueError(f"Unsupported decision target: {name}")

    for name in writes:
        decision = decisions.get(name, "skip")
        planned_file = planned_files[name]
        _validate_decision(name, planned_file, decision)

    plan.agentpm_dir.mkdir(exist_ok=True)
    backup_dir = plan.agentpm_dir / "backups"

    for name, content in writes.items():
        decision = decisions.get(name, "skip")
        if decision == "skip":
            continue
        planned_file = planned_files[name]
        target = planned_file.path
        if target.exists():
            modified_files.append(target)
            backup_path, original_sha256 = _backup_file(target, backup_dir, run_id)
            modified_manifest_entries.append(
                ModifiedFileManifestEntry(
                    path=str(target),
                    backup_path=str(backup_path),
                    original_sha256=original_sha256,
                    written_sha256=_sha256_text(content),
                )
            )
        else:
            created_files.append(target)
            created_manifest_entries.append(
                CreatedFileManifestEntry(path=str(target), written_sha256=_sha256_text(content))
            )
        target.write_text(content, encoding="utf-8")

    manifest_path = plan.agentpm_dir / "setup-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "project_path": str(plan.project_path),
                "run_id": run_id,
                "created_files": [str(path) for path in created_files],
                "modified_files": [str(path) for path in modified_files],
                "created_file_details": [asdict(entry) for entry in created_manifest_entries],
                "modified_file_details": [asdict(entry) for entry in modified_manifest_entries],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    created_files.insert(0, manifest_path)
    return ApplyResult(created_files=created_files, modified_files=modified_files)


def rollback_setup(project_path: Path) -> RollbackResult:
    resolved = project_path.expanduser().resolve()
    manifest_path = resolved / ".agentpm" / "setup-manifest.json"
    backup_root = resolved / ".agentpm" / "backups"
    managed_targets = _managed_target_paths(resolved)
    manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))

    deleted_files: list[Path] = []
    restored_files: list[Path] = []
    warnings: list[str] = []
    created_operations: list[CreatedRollbackOperation] = []
    modified_operations: list[ModifiedRollbackOperation] = []

    for entry in manifest.get("created_file_details", []):
        target = _resolve_manifest_path(entry["path"])
        if target == manifest_path:
            continue
        if not _is_within(target, resolved):
            warnings.append(f"Unsafe rollback target path for {target.name}; rollback skipped.")
            continue
        if target not in managed_targets:
            warnings.append(f"Unmanaged rollback target path for {target.name}; rollback skipped.")
            continue
        if not target.exists():
            warnings.append(f"{target.name} missing during rollback; rollback skipped it.")
            continue

        current_content = target.read_text(encoding="utf-8")
        if _sha256_text(current_content) != entry["written_sha256"]:
            warnings.append(f"{target.name} changed after setup; rollback skipped it.")
            continue

        created_operations.append(CreatedRollbackOperation(target=target))

    for entry in manifest.get("modified_file_details", []):
        target = _resolve_manifest_path(entry["path"])
        backup_path = _resolve_manifest_path(entry["backup_path"])
        if not _is_within(target, resolved):
            warnings.append(f"Unsafe rollback target path for {target.name}; rollback skipped.")
            continue
        if target not in managed_targets:
            warnings.append(f"Unmanaged rollback target path for {target.name}; rollback skipped.")
            continue
        if not _is_within(backup_path, backup_root):
            warnings.append(f"Unsafe rollback backup path for {target.name}; rollback skipped.")
            continue
        if not target.exists():
            warnings.append(f"{target.name} missing during rollback; rollback skipped it.")
            continue

        current_content = target.read_text(encoding="utf-8")
        if _sha256_text(current_content) != entry["written_sha256"]:
            warnings.append(f"{target.name} changed after setup; rollback skipped it.")
            continue

        try:
            backup_content = backup_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            warnings.append(f"Backup for {target.name} is missing or unreadable; rollback skipped.")
            continue

        modified_operations.append(
            ModifiedRollbackOperation(
                target=target,
                backup_path=backup_path,
                backup_content=backup_content,
            )
        )

    if warnings:
        return RollbackResult(
            deleted_files=[],
            restored_files=[],
            warnings=warnings,
        )

    for operation in created_operations:
        operation.target.unlink()
        deleted_files.append(operation.target)

    for operation in modified_operations:
        operation.target.write_text(operation.backup_content, encoding="utf-8")
        operation.backup_path.unlink()
        restored_files.append(operation.target)

    return RollbackResult(
        deleted_files=deleted_files,
        restored_files=restored_files,
        warnings=warnings,
    )
