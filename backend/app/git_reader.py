from pathlib import Path
import subprocess

from .models import GitState


def run_git(project_path: str, args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", project_path, *args],
            check=True,
            text=True,
            capture_output=True,
            timeout=3,
        )
        return result.stdout.strip()
    except Exception:
        return None


def read_git_state(project_path: str) -> GitState:
    if not (Path(project_path) / ".git").exists():
        return GitState(is_repo=False, branch=None, dirty_files=0, latest_commit=None)
    branch = run_git(project_path, ["branch", "--show-current"])
    status = run_git(project_path, ["status", "--porcelain"])
    latest = run_git(project_path, ["rev-parse", "--short", "HEAD"])
    if status is None and latest is None:
        return GitState(is_repo=True, branch=branch or None, dirty_files=0, latest_commit=None, unavailable=True)
    status_lines = (status or "").splitlines()
    dirty_file_names = [line[3:] for line in status_lines if len(line) > 3]
    return GitState(
        is_repo=True,
        branch=branch or None,
        dirty_files=len([line for line in status_lines if line.strip()]),
        latest_commit=latest,
        dirty_file_names=dirty_file_names,
    )
