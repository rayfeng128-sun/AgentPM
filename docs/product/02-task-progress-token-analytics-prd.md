# Codex Project Board v0.2 PRD: Task Progress and Task Token Analytics

## 1. Product Summary

Codex Project Board v0.2 extends the v0.1 briefing dashboard with two deeper project-management capabilities:

- Show the actual task list from `agentpm.yaml`, including task status, completion percentage, blocked work, and milestone progress.
- Make token usage visible at the task level with charts that show how much Codex work each task consumed.

The product goal is to help a project manager answer:

```text
Which PRD items are being implemented, which tasks are done or blocked, and which tasks consumed the most Codex tokens?
```

The dashboard must also show which model or models contributed to each task's token usage, so a PM can distinguish work driven by `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`, `DeepSeek`, or a mix of models.

## 2. Target User

Primary user:

- A project manager who needs visibility into Codex-assisted project plans, task status, PRD coverage, and token consumption so they can manage scope, progress, blockers, and delivery cost.

Secondary user:

- A developer or agentic worker preparing to resume a project and needing to identify the relevant PRD, high-cost tasks, blocked tasks, and incomplete milestones before starting new work.

## 3. User Stories

### Story 1: View Task-Level Progress

As a project manager managing a Codex-assisted project,
in the context of a project with `agentpm.yaml`,
I want to see all milestones and tasks with status, PRD association, and completion percentage,
so that I can understand delivery progress without opening the plan file manually.

Acceptance:

- The project briefing page shows overall completion percentage.
- The page shows milestone-level completion percentage.
- The page shows task rows grouped by milestone.
- Each task row shows title, status, associated PRD, linked Codex sessions, and token usage.
- `todo`, `doing`, `done`, and `blocked` statuses are visually distinct.
- Blocked tasks are counted in total work but not counted as complete.

### Story 2: Inspect Task Token Consumption

As a project manager trying to understand delivery cost,
in the context of multiple Codex sessions across tasks,
I want to see a token graph by task,
so that I can identify expensive tasks and investigate why they consumed so much.

Acceptance:

- The project dashboard includes a task token chart.
- The chart shows one bar per task by default.
- The chart can be sorted by task order or token usage.
- Each bar shows total tokens for that task.
- Each task's token usage shows the Codex model or models that contributed those tokens.
- The dashboard clearly distinguishes single-model tasks from multi-model tasks.
- Hovering or selecting a task shows input, output, cached input, reasoning output, and total tokens when available.
- Tasks without linked sessions show `0` or `No token data`.
- Token totals are labeled as estimated or direct depending on available Codex data.

### Story 3: Link Codex Sessions to Tasks

As a project manager maintaining task visibility,
in the context of Codex sessions that are naturally recorded by thread/session rather than by task,
I want a lightweight way to associate sessions with tasks,
so that task-level token charts can be accurate enough to guide decisions.

Acceptance:

- `agentpm.yaml` supports optional `codex_sessions` on each task.
- The backend maps linked sessions to task token totals.
- If a session is linked to multiple tasks, the UI labels the token attribution as shared.
- If no task links exist, the UI shows project/session token charts but marks task-level token analytics unavailable.
- The dashboard never silently invents task-level token values from unrelated sessions.

### Story 4: Compare Progress and Cost

As a project manager reviewing project efficiency,
in the context of task progress and token usage,
I want to compare task status with token usage,
so that I can spot tasks that are expensive but not complete.

Acceptance:

- The task table shows status and total tokens in the same row.
- The chart visually distinguishes done, doing, blocked, and todo tasks.
- The dashboard highlights high-token incomplete tasks.
- The dashboard highlights blocked tasks that consumed tokens after becoming blocked when that information is available.

### Story 5: Trace Tasks Back to PRDs

As a project manager reviewing delivery scope,
in the context of multiple PRDs and implementation tasks,
I want each task to show which PRD requirement it supports,
so that I can verify coverage, identify unplanned work, and discuss scope changes with the team.

Acceptance:

- `agentpm.yaml` supports optional PRD references on each task.
- The task table shows the primary PRD association for each task.
- A task may link to one or more PRD documents or requirement IDs.
- Tasks without PRD association are visible and marked as unlinked scope.
- The dashboard shows a warning when incomplete or high-token tasks have no PRD association.

## 4. Scope

v0.2 includes:

- Expanded `agentpm.yaml` task schema with optional PRD references, session links, and token budget metadata.
- Backend parsing for milestones, tasks, PRD associations, task progress, and task-to-session token attribution.
- API response fields for milestones, tasks, PRD associations, progress, and task token summaries.
- Frontend task progress table grouped by milestone.
- Frontend task token bar chart.
- Basic chart interactions: sort by task order or token usage, select task, inspect token breakdown.
- Alerts for missing PRD associations, missing task-session links, high-token incomplete tasks, and shared session attribution.
- Per-task model visibility in compact and expanded task analytics views.

## 5. Non-Goals

v0.2 does not include:

- Automatic editing of `agentpm.yaml`.
- Fully automatic task detection from raw Codex transcripts.
- Billing-grade cost calculation.
- Team-level reporting.
- Remote sync.
- Running Codex tasks from the dashboard.
- Running project tests from the dashboard.
- Historical task status timelines unless timestamps already exist in the plan file.
- Managing PRD documents from the dashboard.

## 6. `agentpm.yaml` Schema Extension

v0.2 extends the existing task structure:

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
        prd_refs:
          - docs/product/01-codex-project-board-prd.md#story-1-view-project-briefing
        codex_sessions:
          - 019ecbef-2f0c-7ef3-9721-a3dcbfc7e724
        token_budget: 250000
      - id: registration-flow
        title: Implement registration flow
        status: doing
        prd_refs:
          - docs/product/02-task-progress-token-analytics-prd.md#story-1-view-task-level-progress
          - docs/product/02-task-progress-token-analytics-prd.md#story-2-inspect-task-token-consumption
        codex_sessions:
          - 019eacb2-7096-74d0-b714-5a648f6d78b0
        token_budget: 500000
      - id: test-fixes
        title: Fix failing tests
        status: blocked
        prd_refs: []
        codex_sessions: []
        token_budget: 150000
```

Fields:

| Field | Required | Description |
|---|---:|---|
| `id` | Yes | Stable task identifier within the project. |
| `title` | Yes | Human-readable task name. |
| `status` | Yes | One of `todo`, `doing`, `done`, `blocked`. |
| `user_story` | No | User story or task intent shown directly in Task Board rows. |
| `scope` | No | Explicit scope boundary for the task. |
| `acceptance_criteria` | No | Observable acceptance standard for the task. |
| `verification_method` | No | Expected verification method or command for the task. |
| `prd_refs` | No | PRD document paths, anchors, or requirement IDs associated with this task. |
| `codex_sessions` | No | Codex thread/session IDs linked to this task. |
| `token_budget` | No | Optional target token budget for alerts and comparison. |

Rules:

- Missing `prd_refs` is treated as an empty list.
- Missing `user_story`, `scope`, `acceptance_criteria`, or `verification_method` should first attempt a best-effort fallback from associated local Markdown PRD content; if no structured value can be derived, the Task Board shows `Not specified`.
- Missing `codex_sessions` is treated as an empty list.
- Missing `token_budget` disables budget comparison for that task.
- Unknown task statuses are treated as `todo` and produce a warning alert.
- Duplicate task IDs within one project are invalid and produce an invalid-plan warning.
- The same Codex session may appear on multiple tasks, but attribution is marked as shared.
- PRD references may be local document paths, local Markdown anchors, or stable requirement IDs.

## 7. PRD Association Requirements

Task PRD association is required for project-management visibility, but v0.2 remains permissive so existing plans can load.

Recommended reference formats:

```yaml
prd_refs:
  - docs/product/01-codex-project-board-prd.md
  - docs/product/02-task-progress-token-analytics-prd.md#story-1-view-task-level-progress
  - PRD-02-STORY-1
```

Rules:

- A task can reference zero, one, or many PRD items.
- A task with zero PRD references is valid but marked as `Unlinked PRD`.
- Task Board rows should show all PRD references, not only the first reference.
- Local Markdown PRD references should be clickable and open an in-page modal with the PRD content.
- The first shipped modal experience should render readable Markdown structure for headings, paragraphs, lists, tables, links, and code blocks.
- Requirement IDs or non-Markdown references should remain visible as plain reference chips.
- The PRD modal only reads Markdown files inside the selected project root and should reject path traversal.
- PRD associations are used for visibility and alerts only; they do not change completion percentage.

## 8. Progress Requirements

Overall progress:

```text
project percent = done task count / total task count
```

Milestone progress:

```text
milestone percent = done task count in milestone / total task count in milestone
```

Task status display:

| Status | Meaning | Counts as complete |
|---|---|---:|
| `todo` | Not started | No |
| `doing` | Currently active | No |
| `blocked` | Cannot proceed without resolving a blocker | No |
| `done` | Completed | Yes |

UI requirements:

- Show project progress as both fraction and percentage, such as `7 / 12 tasks` and `58%`.
- Show milestone progress as compact progress bars.
- Show task counts by status.
- Keep blocked count visible near the main progress metric.
- Do not show missing or invalid plan as `0%`; show `Plan unavailable`.

## 9. Token Attribution Requirements

Token source priority:

1. Prefer exact token events from rollout JSONL `token_count` events when available.
2. Use `threads.tokens_used` from `~/.codex/sqlite/state_5.sqlite` when rollout breakdown is unavailable.
3. If neither source is readable, mark tokens as unavailable.

Task attribution:

- A task receives token usage from each Codex session listed in its `codex_sessions`.
- A task's token summary must include the model for each linked session when available.
- If a task has tokens from multiple models, the UI must label the task as multi-model and expose the model list or per-session model details.
- Compact views should show the primary model when only one model contributed, or `Multiple models` when more than one model contributed.
- If a linked session has detailed token breakdown, expose input, cached input, output, reasoning output, and total tokens.
- If only `threads.tokens_used` exists, expose total tokens and set breakdown fields to null.
- If a session ID cannot be found in Codex local state, show the linked session as missing and exclude it from totals.
- If one session is linked to multiple tasks, each affected task displays the session, but chart totals are marked as shared attribution.
- Unknown or missing model values should render as `Unknown model`, not as a blank field.

Budget comparison:

- If `token_budget` exists, the UI shows token usage against budget.
- If usage exceeds budget, the task receives a warning.
- If usage exceeds 2x budget, the task receives a high-severity warning.

## 10. Main UI Requirements

### 10.1 Project Briefing Enhancements

The existing project briefing page adds:

- Overall task progress card.
- Task status distribution card.
- Token usage by task card.
- PRD coverage card showing linked versus unlinked tasks.
- Highest-token incomplete task alert.

### 10.2 Task Progress Table

The task table shows:

- Milestone title.
- Task title.
- Primary PRD association.
- Status.
- Completion contribution.
- Linked session count.
- Total tokens.
- Model or models associated with the task's linked token usage.
- Token budget status when configured.

Default sort:

- Milestone order from `agentpm.yaml`.
- Task order from `agentpm.yaml`.

Alternate sort:

- Highest token usage.
- Incomplete tasks first.
- Blocked tasks first.
- Unlinked PRD tasks first.

### 10.3 Task Token Chart

The token chart shows:

- One bar per task.
- Bar length by total tokens.
- Bar color by task status.
- Model label for the task's attributed token usage.
- Empty state when no task has linked session data.
- Tooltip or side panel with token breakdown.

Required chart states:

- Loading.
- No plan.
- Invalid plan.
- No linked sessions.
- Token data unavailable.
- Shared attribution warning.
- Normal chart.

## 11. API Requirements

Add or extend these endpoints:

```http
GET /api/projects/{project_id}/tasks
GET /api/projects/{project_id}/task-token-usage
GET /api/projects/{project_id}/briefing
```

`GET /api/projects/{project_id}/tasks` returns:

```json
{
  "project_id": "exam-system",
  "progress": {
    "done": 7,
    "total": 12,
    "blocked": 1,
    "percent": 58
  },
  "milestones": [
    {
      "id": "mvp",
      "title": "MVP",
      "progress": {
        "done": 3,
        "total": 5,
        "blocked": 1,
        "percent": 60
      },
      "tasks": [
        {
          "id": "registration-flow",
          "title": "Implement registration flow",
          "status": "doing",
          "prd_refs": [
            "docs/product/02-task-progress-token-analytics-prd.md#story-1-view-task-level-progress"
          ],
          "codex_sessions": ["019eacb2-7096-74d0-b714-5a648f6d78b0"],
          "token_budget": 500000
        }
      ]
    }
  ],
  "alerts": []
}
```

`GET /api/projects/{project_id}/task-token-usage` returns:

```json
{
  "project_id": "exam-system",
  "tasks": [
    {
      "task_id": "registration-flow",
      "task_title": "Implement registration flow",
      "status": "doing",
      "prd_refs": [
        "docs/product/02-task-progress-token-analytics-prd.md#story-1-view-task-level-progress"
      ],
      "total_tokens": 22863067,
      "input_tokens": null,
      "cached_input_tokens": null,
      "output_tokens": null,
      "reasoning_output_tokens": null,
      "models": ["gpt-5.4-mini"],
      "primary_model": "gpt-5.4-mini",
      "token_budget": 500000,
      "attribution": "direct",
      "sessions": [
        {
          "id": "019eacb2-7096-74d0-b714-5a648f6d78b0",
          "title": "Review current development mode",
          "model": "gpt-5.4-mini",
          "tokens": 22863067,
          "source": "codex_state_db"
        }
      ]
    }
  ],
  "alerts": [
    {
      "level": "warning",
      "message": "Task registration-flow exceeded its token budget."
    }
  ]
}
```

Attribution values:

- `direct`: all tokens come from sessions linked only to this task.
- `shared`: at least one session is linked to multiple tasks.
- `unavailable`: token data could not be read.
- `none`: task has no linked sessions.

## 12. Alert Rules

v0.2 adds these alerts:

| Alert | Level | Trigger |
|---|---|---|
| Task missing PRD association | info | A task has no `prd_refs` |
| High-token task missing PRD association | warning | An incomplete task has no `prd_refs` and is in the top 20% of token usage |
| No task session links | info | `agentpm.yaml` has tasks, but no task has `codex_sessions` |
| Missing linked session | warning | A task references a session ID not found in local Codex state |
| Shared session attribution | info | One Codex session is linked to multiple tasks |
| Token budget exceeded | warning | Task total tokens exceed `token_budget` |
| Token budget heavily exceeded | error | Task total tokens exceed 2x `token_budget` |
| High-token incomplete task | warning | An incomplete task is in the top 20% of token usage for the project |

## 13. Privacy and Safety Requirements

- The dashboard must not show raw Codex transcript text in task token charts.
- Task-level analytics may show session title, ID, model, timestamp, and token counts.
- The backend must handle missing or unreadable Codex files gracefully.
- The backend must not mutate `agentpm.yaml` in v0.2.
- The backend must not send local Codex data to any remote service.
- PRD references should be displayed as local document references or requirement IDs, not uploaded or resolved through a remote service.

## 14. Acceptance Criteria

The v0.2 feature is acceptable when:

- A project with valid `agentpm.yaml` shows overall progress, milestone progress, and task status counts.
- Task rows show PRD association, or clearly show `Unlinked PRD` when absent.
- Task rows show user story, explicit scope, acceptance criteria, and verification method from `agentpm.yaml`.
- Task rows show every PRD reference associated with the task.
- Clicking a local Markdown PRD reference opens an in-page modal with the PRD content.
- Task rows display status, linked session count, total tokens, contributing model or models, and token budget state.
- The task token chart renders one bar per task with linked token data.
- Task token chart details show the model or models behind each task's token usage.
- Compact dashboard views show either the single contributing model or `Multiple models`.
- Tasks with no token data are shown clearly and do not break the chart.
- Shared session attribution is labeled clearly.
- Missing linked sessions produce warnings.
- The briefing page highlights high-token incomplete tasks.
- The briefing page highlights high-token incomplete tasks that have no PRD association.
- Existing v0.1 briefing behavior remains available.

## 15. Verification Plan

Backend verification:

- Unit test plan parsing with `codex_sessions` and `token_budget`.
- Unit test plan parsing with `prd_refs`.
- Unit test plan parsing with user story, scope, acceptance criteria, and verification method metadata.
- Unit test PRD content endpoint for local Markdown refs, anchors, unavailable refs, and traversal rejection.
- Unit test duplicate task ID validation.
- Unit test milestone and project progress calculation.
- Unit test task-token attribution for direct, shared, missing, none, and unavailable cases.
- Unit test missing PRD association alerts.
- Unit test budget alerts.

Frontend verification:

- Task table renders grouped milestones and statuses.
- Task table renders all PRD references and unlinked PRD state.
- Task table renders user story, explicit scope, acceptance criteria, and verification method.
- PRD reference links open an in-page modal with Markdown content.
- Task table and task token details render the model or models associated with task token usage.
- Progress cards show correct counts and percentages.
- Token chart renders normal, empty, no-plan, invalid-plan, and unavailable states.
- Sorting by token usage and task order works.
- Selecting a task highlights it in the full-width board table.

Real local smoke test:

- Register one local project with `agentpm.yaml`.
- Link at least one real Codex session ID to a task.
- Link at least one task to a PRD reference.
- Confirm the dashboard shows task progress and task token graph.

## 16. Open Product Decisions

These are intentionally deferred until after the first implementation draft:

- Whether a future version should allow editing `agentpm.yaml` from the UI.
- Whether session-to-task linking should be assisted by transcript search or AI suggestion.
- Whether token budgets should be configured globally per task type.
- Whether cost estimation should be added after token counts are stable.
