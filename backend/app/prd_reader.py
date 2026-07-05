import re
from pathlib import Path

from fastapi import HTTPException

from .models import PlanLoadResult, PrdDocumentResponse

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


def enrich_plan_with_prd_details(project_path: str, plan: PlanLoadResult) -> PlanLoadResult:
    cache: dict[str, tuple[str, list[str]]] = {}
    for milestone in plan.milestones:
        for task in milestone.tasks:
            if all([task.user_story, task.scope, task.acceptance_criteria, task.verification_method]):
                continue
            derived = derive_task_details(project_path, task.prd_refs, cache)
            if task.user_story is None:
                task.user_story = derived["user_story"]
            if task.scope is None:
                task.scope = derived["scope"]
            if task.acceptance_criteria is None:
                task.acceptance_criteria = derived["acceptance_criteria"]
            if task.verification_method is None:
                task.verification_method = derived["verification_method"]
    return plan


def derive_task_details(
    project_path: str,
    prd_refs: list[str],
    cache: dict[str, tuple[str, list[str]]] | None = None,
) -> dict[str, str | None]:
    details = {
        "user_story": None,
        "scope": None,
        "acceptance_criteria": None,
        "verification_method": None,
    }
    cache = cache or {}

    for prd_ref in prd_refs:
        ref_path, anchor = split_prd_ref(prd_ref)
        if not ref_path.endswith(".md"):
            continue
        try:
            content, lines = load_prd_content(project_path, ref_path, cache)
        except HTTPException:
            continue
        if not content:
            continue

        section_title, section_lines = section_for_anchor(lines, anchor)
        story_block = extract_story_block(section_lines) or extract_story_block(lines)
        acceptance = extract_acceptance(section_lines) or extract_named_section_bullets(lines, "Acceptance Criteria")
        verification = extract_named_section_bullets(lines, "Verification Plan")
        scope = derive_scope(anchor, section_title, story_block, lines)

        details["user_story"] = details["user_story"] or story_block
        details["scope"] = details["scope"] or scope
        details["acceptance_criteria"] = details["acceptance_criteria"] or acceptance
        details["verification_method"] = details["verification_method"] or verification

        if all(details.values()):
            break

    return details


def read_project_prd(project_path: str, prd_ref: str) -> PrdDocumentResponse:
    ref_path, anchor = split_prd_ref(prd_ref)
    if not ref_path.endswith(".md"):
        return PrdDocumentResponse(ref=prd_ref, path=ref_path, anchor=anchor, unavailable=True)

    candidate, relative_path = resolve_project_prd_path(project_path, ref_path)
    if not candidate.exists() or not candidate.is_file():
        return PrdDocumentResponse(ref=prd_ref, path=ref_path, anchor=anchor, unavailable=True)

    content = candidate.read_text(encoding="utf-8")
    return PrdDocumentResponse(
        ref=prd_ref,
        path=relative_path,
        anchor=anchor,
        title=extract_markdown_title(content),
        content=content,
        unavailable=False,
    )


def split_prd_ref(prd_ref: str) -> tuple[str, str | None]:
    path, separator, anchor = prd_ref.partition("#")
    return path, anchor if separator and anchor else None


def load_prd_content(
    project_path: str,
    ref_path: str,
    cache: dict[str, tuple[str, list[str]]],
) -> tuple[str, list[str]]:
    cached = cache.get(ref_path)
    if cached is not None:
        return cached

    candidate, _ = resolve_project_prd_path(project_path, ref_path)
    if not candidate.exists() or not candidate.is_file():
        cache[ref_path] = ("", [])
        return cache[ref_path]

    content = candidate.read_text(encoding="utf-8")
    cache[ref_path] = (content, content.splitlines())
    return cache[ref_path]


def resolve_project_prd_path(project_path: str, ref_path: str) -> tuple[Path, str]:
    project_root = Path(project_path).expanduser().resolve()
    candidate = (project_root / ref_path).resolve()
    if candidate != project_root and project_root not in candidate.parents:
        raise HTTPException(status_code=403, detail="PRD path is outside the project")
    return candidate, str(candidate.relative_to(project_root))


def section_for_anchor(lines: list[str], anchor: str | None) -> tuple[str | None, list[str]]:
    if not anchor:
        return None, lines

    for index, line in enumerate(lines):
        match = HEADING_RE.match(line.strip())
        if not match:
            continue
        level = len(match.group(1))
        title = match.group(2).strip()
        if slugify_heading(title) != anchor:
            continue
        section: list[str] = []
        for follow in lines[index + 1 :]:
            next_match = HEADING_RE.match(follow.strip())
            if next_match and len(next_match.group(1)) <= level:
                break
            section.append(follow)
        return title, section
    return None, lines


def slugify_heading(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug


def derive_scope(anchor: str | None, section_title: str | None, story_block: str | None, lines: list[str]) -> str | None:
    if anchor and section_title:
        if ":" in section_title:
            return section_title.split(":", 1)[1].strip() or section_title
        return section_title

    scope_marker = extract_list_after_marker(lines, "Scope:")
    if scope_marker:
        return scope_marker
    scope_marker = extract_list_after_marker(lines, "Scope")
    if scope_marker:
        return scope_marker

    section_bullets = extract_named_section_bullets(lines, "Scope")
    if section_bullets:
        return section_bullets

    if story_block:
        for line in story_block.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("i want "):
                return stripped
    return None


def extract_story_block(lines: list[str]) -> str | None:
    block: list[str] = []
    collecting = False
    for line in lines:
        stripped = line.strip()
        if not collecting and stripped.lower().startswith("as a "):
            collecting = True
            block.append(stripped)
            continue
        if not collecting:
            continue
        if not stripped:
            if block:
                break
            continue
        if stripped == "Acceptance:" or HEADING_RE.match(stripped):
            break
        block.append(stripped)
    return "\n".join(block) if block else first_meaningful_paragraph(lines)


def extract_acceptance(lines: list[str]) -> str | None:
    return extract_list_after_marker(lines, "Acceptance:")


def extract_named_section_bullets(lines: list[str], heading_name: str) -> str | None:
    normalized_heading = normalize_heading_title(heading_name.rstrip(":"))
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped in {heading_name, f"{heading_name}:"}:
            bullets = extract_bullets(lines[index + 1 :])
            return bullets or first_meaningful_paragraph(lines[index + 1 :])

        match = HEADING_RE.match(stripped)
        if not match:
            continue
        if normalize_heading_title(match.group(2)) != normalized_heading:
            continue
        level = len(match.group(1))
        section: list[str] = []
        for follow in lines[index + 1 :]:
            next_match = HEADING_RE.match(follow.strip())
            if next_match and len(next_match.group(1)) <= level:
                break
            section.append(follow)
        bullets = extract_bullets(section)
        return bullets or first_meaningful_paragraph(section)
    return None


def normalize_heading_title(title: str) -> str:
    normalized = re.sub(r"^[0-9]+[.)]?\s*", "", title.strip().lower())
    return normalized


def extract_list_after_marker(lines: list[str], marker: str) -> str | None:
    for index, line in enumerate(lines):
        if line.strip() != marker:
            continue
        bullets = extract_bullets(lines[index + 1 :])
        if bullets:
            return bullets
    return None


def extract_bullets(lines: list[str]) -> str | None:
    bullets: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped and bullets:
            break
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
            continue
        if bullets and not stripped.startswith("  "):
            break
        if bullets and stripped:
            bullets[-1] = f"{bullets[-1]} {stripped}"
    return "\n".join(bullets) if bullets else None


def first_meaningful_paragraph(lines: list[str]) -> str | None:
    paragraph: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if paragraph:
                break
            continue
        if HEADING_RE.match(stripped) or stripped.startswith("- ") or stripped.startswith("|"):
            if paragraph:
                break
            continue
        paragraph.append(stripped)
    return "\n".join(paragraph) if paragraph else None


def extract_markdown_title(content: str) -> str | None:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip() or None
    return None
