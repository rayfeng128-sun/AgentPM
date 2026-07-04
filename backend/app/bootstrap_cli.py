from __future__ import annotations

import argparse
from pathlib import Path

from app.bootstrap_setup import PlannedFile, SetupPlan, apply_setup, build_setup_plan, rollback_setup


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentpm-bootstrap")
    parser.add_argument("--target", required=True, help="Path to the target project directory")
    parser.add_argument("--project-name", help="Override the project name written into templates")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--dry-run", action="store_true", help="Print planned actions without writing files")
    mode_group.add_argument("--rollback", action="store_true", help="Rollback the last recorded setup run")
    return parser


def _plan_files(plan: SetupPlan) -> list[tuple[str, PlannedFile]]:
    return [
        ("agentpm.yaml", plan.agentpm_yaml),
        ("AGENTS.md", plan.agents_md),
        ("CODEX.md", plan.codex_md),
    ]


def _normalize_prompt_answer(answer: str, planned_file: PlannedFile) -> str | None:
    normalized = answer.strip().lower()
    if not normalized:
        return None
    if normalized == "skip":
        return "skip"
    if planned_file.action == "create" and normalized == "create":
        return "create"
    if planned_file.action == "prompt" and normalized in {"update", "create"}:
        return "update"
    return None


def _prompt_for_decision(name: str, planned_file: PlannedFile) -> str:
    if planned_file.action == "create":
        prompt = f"{name} does not exist. Choose [create/skip]: "
    else:
        prompt = f"{name} already exists. Choose [update/skip] (or 'create' to overwrite): "

    while True:
        decision = _normalize_prompt_answer(input(prompt), planned_file)
        if decision is not None:
            return decision
        print("Please answer with one of the supported actions.")


def _run_dry_run(target: Path, project_name: str | None) -> int:
    plan = build_setup_plan(target, project_name)
    for name, planned_file in _plan_files(plan):
        print(f"{name}: {planned_file.action}")
    return 0


def _run_apply(target: Path, project_name: str | None) -> int:
    plan = build_setup_plan(target, project_name)
    decisions = {
        name: _prompt_for_decision(name, planned_file)
        for name, planned_file in _plan_files(plan)
    }
    apply_setup(plan, decisions)
    return 0


def _run_rollback(target: Path) -> int:
    result = rollback_setup(target)
    if result.warnings:
        for warning in result.warnings:
            print(warning)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        target = Path(args.target)
        if args.rollback:
            return _run_rollback(target)
        if args.dry_run:
            return _run_dry_run(target, args.project_name)
        return _run_apply(target, args.project_name)
    except SystemExit as exc:
        return int(exc.code)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
