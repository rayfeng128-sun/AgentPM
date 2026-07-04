from pathlib import Path
import re
import sqlite3

from fastapi import HTTPException

from .models import DirectoryBrowseResponse, DirectoryOption, DirectoryRoot, Project, ProjectCreate


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "project"


def has_plan_file(path: str) -> bool:
    return (Path(path) / "agentpm.yaml").exists()


def is_git_repo(path: str) -> bool:
    return (Path(path) / ".git").exists()


def validate_project_create(data: ProjectCreate) -> Path:
    if not data.name.strip():
        raise HTTPException(status_code=422, detail="Project name is required")
    if not data.path.strip():
        raise HTTPException(status_code=422, detail="Project path is required")
    path = Path(data.path).expanduser()
    if not path.exists():
        raise HTTPException(status_code=422, detail="Project path does not exist")
    return path.resolve()


def project_from_row(row: sqlite3.Row) -> Project:
    path = row["path"]
    return Project(
        id=row["id"],
        name=row["name"],
        path=path,
        has_plan=has_plan_file(path),
        is_git_repo=is_git_repo(path),
    )


def create_project(conn: sqlite3.Connection, data: ProjectCreate) -> Project:
    path = validate_project_create(data)
    project_id = slugify(data.name)
    conn.execute(
        "INSERT OR REPLACE INTO projects (id, name, path, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
        (project_id, data.name.strip(), str(path)),
    )
    conn.commit()
    row = conn.execute("SELECT id, name, path FROM projects WHERE path = ?", (str(path),)).fetchone()
    return project_from_row(row)


def list_projects(conn: sqlite3.Connection) -> list[Project]:
    rows = conn.execute("SELECT id, name, path FROM projects ORDER BY name").fetchall()
    return [project_from_row(row) for row in rows]


def get_project(conn: sqlite3.Connection, project_id: str) -> Project | None:
    row = conn.execute("SELECT id, name, path FROM projects WHERE id = ?", (project_id,)).fetchone()
    if row is None:
        return None
    return project_from_row(row)


def delete_project(conn: sqlite3.Connection, project_id: str) -> bool:
    cursor = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    return cursor.rowcount > 0


def browse_directories(path: str | None, roots: list[Path]) -> DirectoryBrowseResponse:
    resolved_roots = [root.expanduser().resolve() for root in roots if root.expanduser().exists()]
    if not resolved_roots:
        raise HTTPException(status_code=503, detail="Directory browsing is unavailable")

    if path:
        current_path = Path(path).expanduser().resolve()
    else:
        current_path = resolved_roots[0]

    if not any(current_path == root or root in current_path.parents for root in resolved_roots):
        raise HTTPException(status_code=403, detail="Path is outside the allowed browse roots")

    if not current_path.exists() or not current_path.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")

    directories = sorted((entry for entry in current_path.iterdir() if entry.is_dir()), key=lambda entry: entry.name.lower())
    parent_path = None
    if current_path not in resolved_roots:
        parent = current_path.parent
        if any(parent == root or root in parent.parents for root in resolved_roots):
            parent_path = str(parent)

    return DirectoryBrowseResponse(
        current_path=str(current_path),
        parent_path=parent_path,
        roots=[DirectoryRoot(label=root.name or str(root), path=str(root)) for root in resolved_roots],
        directories=[DirectoryOption(name=entry.name, path=str(entry)) for entry in directories],
    )
