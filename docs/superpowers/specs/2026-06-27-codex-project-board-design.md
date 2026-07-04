# Codex Project Board v0.1 Design

## Summary

Codex Project Board v0.1 is a local web dashboard for tracking Codex-driven project progress. Its first version focuses on answering one question quickly: "Where is this project now, what changed recently, and what should happen next?"

The product is project-progress-first, not token-first. Token usage is still visible, but it supports the project briefing rather than becoming the main navigation model.

## Product Decisions

- The first screen is a briefing dashboard, not a timeline or Kanban board.
- Project progress comes from an explicit `agentpm.yaml` file in each monitored project.
- Codex activity and token usage come from local Codex state, especially `~/.codex/sqlite/state_5.sqlite`, rollout JSONL files, and session metadata.
- Git status and test status are supporting signals for the project briefing.
- v0.1 is local-only and read-mostly. It does not control Codex, run Codex tasks, or sync to a remote service.

## Core User Experience

The dashboard shows a sidebar of registered projects. Selecting a project opens a briefing page with:

- Progress summary from `agentpm.yaml`, such as completed tasks versus total tasks.
- Current state, such as active, idle, blocked, tests failing, or no recent activity.
- A concise project briefing summarizing recent Codex sessions, Git changes, task movement, and likely next action.
- Recent Codex sessions for the project path, including title, model, updated time, and tokens used.
- Token summary by project and session.
- Git snapshot with branch, changed files, latest commit, and dirty state.
- Alert cards for token spikes, long idle periods, repeated failures, missing plan file, and unknown test state.

## Data Sources

### Project Plan

Each monitored project may contain `agentpm.yaml`:

```yaml
project:
  name: ExamSystem
  path: /Users/ray/BaiduNetDisk/Project/ExamSystem_2

milestones:
  - id: mvp
    title: MVP
    tasks:
      - id: frontend-shell
        title: Build frontend shell
        status: done
      - id: registration-flow
        title: Implement registration flow
        status: doing
      - id: test-fixes
        title: Fix failing tests
        status: todo
```

Supported task statuses are `todo`, `doing`, `done`, and `blocked`.

Progress is calculated as:

```text
done task count / total task count
```

Blocked tasks are shown separately and do not count as done.

### Codex Local State

The dashboard reads:

- `~/.codex/sqlite/state_5.sqlite` `threads` table for thread title, cwd, model, tokens used, Git branch, and rollout path.
- Rollout JSONL files for `token_count`, `session_meta`, `agent_message`, and selected execution events.
- `~/.codex/session_index.jsonl` as a fallback thread index.

The app must not display full private conversation transcripts by default. It may show thread titles, timestamps, token totals, and generated summaries.

### Git State

For each registered project path, the backend reads:

- Current branch.
- Latest commit hash and subject.
- Dirty file count and file names.
- Whether the path is a Git repository.

### Test State

v0.1 stores test status as `unknown`, `passing`, or `failing`. Automatic test execution is out of scope for v0.1; the backend may infer recent failures from Codex session text/events where available, but the UI must clearly label inferred status as low confidence.

## Architecture

The app has three local parts:

- FastAPI backend for reading local project, Codex, Git, and plan data.
- SQLite app database for registered project paths, cached snapshots, and generated summaries.
- React dashboard for project selection, briefing cards, sessions, token charts, and alerts.

Backend modules:

- Project registry: manages project paths and checks whether `agentpm.yaml` exists.
- Plan parser: parses `agentpm.yaml` and computes task progress.
- Codex reader: reads local Codex SQLite and rollout JSONL data.
- Git reader: reads Git state for a project path.
- Snapshot service: merges plan, Codex, Git, and test signals into one project briefing payload.

## API Shape

```http
GET /api/projects
POST /api/projects
GET /api/projects/{project_id}/briefing
GET /api/projects/{project_id}/sessions
GET /api/projects/{project_id}/tokens
GET /api/health
```

`GET /api/projects/{project_id}/briefing` returns the primary dashboard payload:

```json
{
  "project": {
    "id": "exam-system",
    "name": "ExamSystem",
    "path": "/Users/ray/BaiduNetDisk/Project/ExamSystem_2"
  },
  "progress": {
    "done": 7,
    "total": 12,
    "blocked": 1,
    "percent": 58
  },
  "briefing": {
    "status": "blocked",
    "summary": "Registration flow is in progress; recent work changed frontend views and tests are currently unknown.",
    "next_action": "Update the plan file or run the relevant test suite."
  },
  "tokens": {
    "total": 346813,
    "recent_session": 43153
  },
  "git": {
    "is_repo": true,
    "branch": "main",
    "dirty_files": 4,
    "latest_commit": "abc1234"
  },
  "alerts": [
    {
      "level": "warning",
      "message": "Test state is unknown."
    }
  ]
}
```

## Out Of Scope For v0.1

- Remote hosting or phone access.
- Multi-user collaboration.
- Directly controlling Codex.
- Automatic task completion edits in `agentpm.yaml`.
- Accurate billing-grade cost accounting.
- Full transcript search by default.
- Running project tests from the dashboard.

## Acceptance Criteria

- A local web page lists registered projects.
- A project with `agentpm.yaml` shows accurate task counts and progress percentage.
- A project without `agentpm.yaml` shows a clear missing-plan warning.
- Codex sessions are grouped by project path using local Codex state.
- Token totals are visible by project and recent session.
- Git state is visible for Git repositories and gracefully unavailable for non-Git paths.
- The briefing page makes the next action visible without requiring the user to ask Codex.
