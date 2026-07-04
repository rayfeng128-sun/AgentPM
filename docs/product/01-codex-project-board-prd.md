# Codex Project Board v0.1 PRD

## 1. Product Summary

Codex Project Board v0.1 is a local web dashboard for tracking Codex-driven project progress. It answers one primary question:

```text
Where is this project now, what changed recently, and what should happen next?
```

The product is project-progress-first, not token-first. Token usage is visible, but it supports the project briefing instead of becoming the main navigation model.

## 2. Target User

Primary user:

- A developer or project owner who uses Codex across multiple local repositories and wants a quick project status briefing without manually opening each thread, plan file, Git state, and token summary.

Secondary user:

- An agentic worker reading the project state before deciding what task should happen next.

## 3. User Stories

### Story 1: View Project Briefing

As a developer managing Codex-assisted projects,
in the context of checking ongoing local work,
I want to open one dashboard and select a project,
so that I can quickly understand current progress, recent activity, risks, and the next recommended action.

Acceptance:

- The page lists registered projects.
- Selecting a project opens a briefing view.
- The briefing view shows progress, current status, recent sessions, token usage, Git state, alerts, and next action.
- The user can understand what to do next without asking Codex for a separate summary.

### Story 2: Track Plan Progress

As a developer maintaining a project plan,
in the context of a project that contains `agentpm.yaml`,
I want the dashboard to calculate milestone task progress,
so that I can see whether the project is moving, blocked, or missing planning data.

Acceptance:

- A project with `agentpm.yaml` shows accurate task counts and progress percentage.
- A project without `agentpm.yaml` shows a missing-plan warning.
- Supported task statuses are `todo`, `doing`, `done`, and `blocked`.
- Blocked tasks are displayed separately and do not count as done.

### Story 3: Review Recent Codex Activity

As a developer returning to a project,
in the context of multiple Codex sessions,
I want to see recent sessions grouped by project path,
so that I can understand what changed recently without reading full private transcripts by default.

Acceptance:

- Sessions are grouped by registered project path.
- Each session shows title, model, updated time, and token usage when available.
- Full conversation transcript content is not shown by default.
- If Codex local state is unavailable, the UI shows a clear unavailable state instead of failing silently.

### Story 4: Inspect Supporting Signals

As a developer preparing the next task,
in the context of local Git and test uncertainty,
I want to see branch, dirty files, latest commit, and test confidence,
so that I can avoid starting work from a misleading project state.

Acceptance:

- Git state is visible for Git repositories.
- Non-Git project paths are handled gracefully.
- Test state is shown as `unknown`, `passing`, or `failing`.
- Inferred test state is labeled as low confidence.

## 4. Scope

v0.1 includes:

- Local web dashboard with project list and project briefing page.
- Project registration by name and local path.
- Reading project progress from `agentpm.yaml`.
- Reading Codex session and token signals from local Codex state where available.
- Reading Git state for registered project paths.
- Showing briefing status, summary, next action, and alert cards.
- Storing registered projects in a local app SQLite database.

## 5. Non-Goals

v0.1 does not include:

- Remote hosting or phone access.
- Multi-user collaboration.
- Directly controlling Codex.
- Running Codex tasks.
- Automatically editing `agentpm.yaml`.
- Running project tests from the dashboard.
- Accurate billing-grade cost accounting.
- Full transcript search by default.
- Cloud sync or remote telemetry.

## 6. Core Experience

The first screen is a briefing dashboard, not a timeline or Kanban board.

The dashboard has:

- Sidebar or project list of registered projects.
- Primary briefing panel for the selected project.
- Progress summary from `agentpm.yaml`.
- Current status: `active`, `idle`, `blocked`, `tests_failing`, `missing_plan`, or `unknown`.
- Recent Codex sessions for the selected project.
- Token summary by project and recent session.
- Git snapshot with branch, changed files, latest commit, and dirty state.
- Alert cards for missing plan, unknown test state, token spike, long idle period, repeated failure signal, and unavailable local state.

## 7. Main User Flow

1. User opens the local dashboard.
2. User sees registered projects.
3. User adds a project if it is not registered yet.
4. User selects a project.
5. Dashboard loads plan, Codex, Git, and cached app data.
6. Dashboard renders a briefing with progress, recent activity, risks, and next action.
7. User uses the next action to decide whether to update the plan, resume Codex work, inspect Git changes, or run tests manually.

## 8. Project Registration Rules

Project registration captures:

- Project name.
- Local absolute path.

Validation:

- Empty name is rejected.
- Empty path is rejected.
- Duplicate path updates or replaces the existing registration for that path.
- Path that does not exist is rejected.
- Path that exists but is not a Git repository is allowed and shown with Git unavailable.
- Path without `agentpm.yaml` is allowed and shown with a missing-plan warning.

Project ID:

- Derived from project name using a deterministic slug.
- If two project names generate the same slug, the existing project may be replaced in v0.1. Collision-safe IDs are out of scope for v0.1 unless implementation discovers this causes data loss during normal use.

## 9. Data Sources

### 9.1 Project Plan

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

Supported task statuses:

- `todo`
- `doing`
- `done`
- `blocked`

Progress calculation:

```text
done task count / total task count
```

Rules:

- `blocked` tasks count in total.
- `blocked` tasks do not count as done.
- Unknown statuses are treated as `todo` and should produce a warning alert.
- Missing or invalid `agentpm.yaml` produces a warning alert and progress should be unavailable, not zero.

### 9.2 Codex Local State

The dashboard reads local Codex state where available:

- `~/.codex/sqlite/state_5.sqlite` `threads` table for thread title, cwd, model, tokens used, Git branch, and rollout path.
- Rollout JSONL files for `token_count`, `session_meta`, `agent_message`, and selected execution events.
- `~/.codex/session_index.jsonl` as a fallback thread index.

Privacy rules:

- Full private conversation transcripts must not be displayed by default.
- The UI may show thread titles, timestamps, model, token totals, and generated or extracted summaries.
- If summary generation requires reading message content, the implementation must keep processing local and avoid exposing raw transcript text in the API response by default.
- Missing, locked, or unreadable Codex state must produce an explicit unavailable state.

### 9.3 Git State

For each registered project path, the backend reads:

- Whether the path is a Git repository.
- Current branch.
- Latest commit hash and subject.
- Dirty file count.
- Dirty file names.

Rules:

- Non-Git paths are valid projects.
- Git unavailable state should not block the rest of the briefing.

### 9.4 Test State

v0.1 stores or infers test status as:

- `unknown`
- `passing`
- `failing`

Rules:

- Automatic test execution is out of scope.
- Inferred test state from Codex events or text must be labeled low confidence.
- If no reliable signal exists, status is `unknown`.

## 10. Briefing Status Rules

The briefing status should be calculated using this priority order:

1. `missing_plan`: project has no readable `agentpm.yaml`.
2. `blocked`: one or more tasks in `agentpm.yaml` have status `blocked`.
3. `tests_failing`: test state is `failing`.
4. `active`: there is Codex activity or Git activity within the recent activity window.
5. `idle`: the project has a plan but no recent activity within the idle threshold.
6. `unknown`: required local state is unavailable and no stronger status applies.

Default thresholds:

- Recent activity window: 48 hours.
- Idle threshold: 7 days without Codex session update or Git commit.

## 11. Alert Rules

v0.1 should support these alerts:

| Alert | Level | Trigger |
|---|---|---|
| Missing plan | warning | Project path has no readable `agentpm.yaml` |
| Invalid plan | warning | `agentpm.yaml` exists but cannot be parsed or has unsupported structure |
| Unknown task status | warning | A task status is not `todo`, `doing`, `done`, or `blocked` |
| Blocked task | warning | One or more tasks are `blocked` |
| Test state unknown | warning | No reliable test signal exists |
| Tests failing | error | Test state is `failing` |
| Token spike | info | Most recent session token count is greater than 2x the average of the previous five sessions for the project |
| Long idle | info | No Codex session update or Git commit in 7 days |
| Codex state unavailable | warning | Local Codex DB and fallback index cannot be read |
| Git unavailable | info | Path is not a Git repository or Git state cannot be read |

## 12. API Requirements

Required endpoints:

```http
GET /api/health
GET /api/projects
POST /api/projects
GET /api/projects/{project_id}
GET /api/projects/{project_id}/briefing
GET /api/projects/{project_id}/sessions
GET /api/projects/{project_id}/tokens
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

API behavior:

- Missing project returns 404.
- Unavailable plan, Codex, Git, or test signals should be represented in the briefing payload instead of causing a 500 response.
- Unexpected backend errors may return 500, but predictable local-state gaps should be graceful.

## 13. UI States

The frontend must handle:

- Loading project list.
- Empty project list.
- Project selected.
- No project selected.
- Project creation success.
- Project creation validation error.
- Missing plan.
- Invalid plan.
- Non-Git path.
- Codex state unavailable.
- Token data unavailable.
- Test state unknown.
- Backend unavailable.

## 14. Acceptance Criteria

The v0.1 product is acceptable when:

- A local web page lists registered projects.
- A user can register a local project by name and path.
- A project with `agentpm.yaml` shows accurate task counts and progress percentage.
- A project without `agentpm.yaml` shows a clear missing-plan warning.
- Codex sessions are grouped by project path using local Codex state when available.
- Token totals are visible by project and recent session when available.
- Git state is visible for Git repositories.
- Non-Git paths and unreadable Git state are handled gracefully.
- The briefing page makes the next action visible without requiring the user to ask Codex.
- Full private transcripts are not displayed by default.
- Missing local signals produce clear UI states instead of blank or broken screens.

## 15. Verification Plan

Minimum verification for v0.1:

- Backend unit tests for project registration, plan parsing, progress calculation, and briefing status priority.
- Backend tests for missing plan, invalid plan, non-Git path, and unavailable Codex state.
- Frontend manual smoke test for empty state, add project, briefing page, missing-plan warning, and backend unavailable state.
- One real local project smoke test with `agentpm.yaml`.
- One real or fixture Git repository smoke test.

## 16. Source References

This PRD formalizes the v0.1 design from:

- `docs/superpowers/specs/2026-06-27-codex-project-board-design.md`
- `docs/superpowers/plans/2026-06-27-codex-project-board.md`
