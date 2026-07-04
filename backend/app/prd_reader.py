from pathlib import Path

from fastapi import HTTPException

from .models import PrdDocumentResponse


def read_project_prd(project_path: str, prd_ref: str) -> PrdDocumentResponse:
    ref_path, anchor = split_prd_ref(prd_ref)
    if not ref_path.endswith(".md"):
        return PrdDocumentResponse(ref=prd_ref, path=ref_path, anchor=anchor, unavailable=True)

    project_root = Path(project_path).expanduser().resolve()
    candidate = (project_root / ref_path).resolve()
    if candidate != project_root and project_root not in candidate.parents:
        raise HTTPException(status_code=403, detail="PRD path is outside the project")

    if not candidate.exists() or not candidate.is_file():
        return PrdDocumentResponse(ref=prd_ref, path=ref_path, anchor=anchor, unavailable=True)

    content = candidate.read_text(encoding="utf-8")
    return PrdDocumentResponse(
        ref=prd_ref,
        path=str(candidate.relative_to(project_root)),
        anchor=anchor,
        title=extract_markdown_title(content),
        content=content,
        unavailable=False,
    )


def split_prd_ref(prd_ref: str) -> tuple[str, str | None]:
    path, separator, anchor = prd_ref.partition("#")
    return path, anchor if separator and anchor else None


def extract_markdown_title(content: str) -> str | None:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip() or None
    return None
