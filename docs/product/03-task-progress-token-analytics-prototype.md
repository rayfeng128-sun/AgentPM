# Codex Project Board v0.2 Prototype: Task Progress and Token Analytics

## 1. Prototype Goal

This prototype translates `docs/product/02-task-progress-token-analytics-prd.md` into a product-manager-facing dashboard flow.

The prototype answers:

- Which PRD items are being implemented?
- Which tasks are done, active, blocked, or unlinked from PRD scope?
- What percentage of the project and each milestone is complete?
- Which tasks consumed the most Codex tokens?
- Which high-cost tasks need PM attention?

This is a low-fidelity product prototype. It defines screens, layout, content hierarchy, states, and interactions before visual design or implementation.

## 1.1 Chosen Visual Direction

This prototype uses the selected visual direction: **Option 3, Calm PM Review Board**.

That means the dashboard should feel:

- calm and executive-readable first
- PM-oriented rather than analyst-oriented
- chart-aware without letting charts dominate every surface
- rich in detail once the user drills into a task

## 2. Design Principles

- PM-first visibility: put progress, PRD coverage, blockers, and token consumption before developer-only details.
- Trustworthy numbers: show task-level token data only when sessions are explicitly linked to tasks.
- Drill down, do not overwhelm: show summary cards first, then table and chart details.
- Local and private: show metadata, IDs, and token counts; do not expose full Codex transcripts by default.
- Operational density: this should feel like a project control surface, not a marketing page.

## 3. Primary Screen: Project Delivery Dashboard

### Screen Purpose

The project delivery dashboard is the main page for a selected project. A PM should understand progress, scope coverage, token spend, and risks within one scan.

### Layout

| Region | Content |
|---|---|
| Left sidebar | Project list, selected project, status badges, add project action |
| Header | Project name, path, branch, last Codex activity, refresh action |
| Summary cards | Completion, PRD coverage, token consumption, blockers |
| Main content left | Milestone progress and task table |
| Main content right | Task token chart and attention queue |
| Detail layer | Task detail drawer opened from table or chart |

### Header Content

Example:

| Field | Example |
|---|---|
| Project | ExamSystem |
| Path | `/Users/ray/BaiduNetDisk/Project/ExamSystem_2` |
| Branch | `main` |
| Last Codex activity | 2 hours ago |
| Plan source | `agentpm.yaml` |
| Data confidence | Direct session links |

Actions:

- Refresh data.
- Open plan file location.
- View raw linked sessions metadata.

## 4. Summary Cards

### Card 1: Completion

Purpose: show delivery progress at a glance.

Content:

| Field | Example |
|---|---|
| Main metric | `58%` |
| Supporting text | `7 / 12 tasks done` |
| Status split | `3 todo · 1 doing · 1 blocked · 7 done` |
| Alert | `1 blocked task` |

Behavior:

- Selecting the card filters the task table to incomplete tasks.
- If plan is missing or invalid, show `Plan unavailable` instead of `0%`.

### Card 2: PRD Coverage

Purpose: show whether tasks are traceable to PRD scope.

Content:

| Field | Example |
|---|---|
| Main metric | `10 / 12 linked` |
| Supporting text | `83% of tasks linked to PRD scope` |
| Alert | `2 unlinked tasks` |

Behavior:

- Selecting the card filters the task table to `Unlinked PRD`.
- High-token unlinked tasks are shown as warnings.

### Card 3: Token Consumption

Purpose: show delivery cost pressure.

Content:

| Field | Example |
|---|---|
| Main metric | `23.8M tokens` |
| Supporting text | `Across 8 linked Codex sessions` |
| Secondary | `3 tasks over budget · 2 models in use` |

Behavior:

- Selecting the card sorts the task table and chart by token usage.
- If token data is unavailable, show `Token data unavailable`.

### Card 4: PM Attention

Purpose: summarize what needs management attention.

Content:

| Alert | Example |
|---|---|
| Blocker | `registration-flow is blocked` |
| High cost | `registration-flow consumed 22.8M tokens` |
| Scope gap | `test-fixes has no PRD link` |
| Attribution | `2 tasks share one Codex session` |

Behavior:

- Selecting an alert opens the relevant task detail drawer.

## 5. Milestone Progress Section

### Purpose

Show progress by milestone so a PM can distinguish overall progress from milestone-specific bottlenecks.

### Content

| Milestone | Progress | Tasks | Blocked | Token usage | PRD coverage |
|---|---:|---:|---:|---:|---:|
| MVP Foundation | 80% | 4 / 5 done | 0 | 4.2M | 5 / 5 linked |
| Task Analytics | 45% | 5 / 11 done | 1 | 23.8M | 9 / 11 linked |
| Reliability | 20% | 1 / 5 done | 2 | 3.1M | 4 / 5 linked |

Interactions:

- Select a milestone to filter the task table and chart.
- Expand a milestone to show its task rows.
- Collapsed milestones still show progress, blocked count, token total, and PRD coverage.

## 6. Task Progress Table

### Purpose

Provide the PM's primary working view for scope, status, PRD traceability, and token consumption.

### Columns

| Column | Description |
|---|---|
| Task | Task title and stable task ID |
| PRD | Primary PRD reference or `Unlinked PRD` |
| Status | `todo`, `doing`, `blocked`, `done` |
| Completion | Whether task contributes to completion |
| Sessions | Linked Codex session count |
| Tokens | Total attributed tokens |
| Model | Codex model or models that contributed the attributed tokens |
| Budget | Token budget status |
| Attention | Warnings that need PM review |

### Example Rows

| Task | PRD | Status | Sessions | Tokens | Model | Budget | Attention |
|---|---|---|---:|---:|---|---|---|
| Build frontend shell | `01-codex-project-board-prd.md#story-1-view-project-briefing` | done | 1 | 346K | `gpt-5.4-mini` | OK | None |
| Implement registration flow | `02-prd.md#task-progress` | doing | 1 | 22.8M | `gpt-5.4` | Over 2x | High-token incomplete |
| Fix failing tests | Unlinked PRD | blocked | 0 | No data | No model | No budget | Missing PRD link |
| Build task token chart | `02-prd.md#token-chart` | todo | 0 | 0 | No model | OK | No session links |

### Table Controls

| Control | Options |
|---|---|
| Status filter | All, Todo, Doing, Blocked, Done |
| PRD filter | All, Linked, Unlinked |
| Token filter | All, Over budget, No token data, Shared attribution |
| Sort | Plan order, Highest tokens, Incomplete first, Blocked first, Unlinked PRD first |

Interactions:

- Selecting a task row opens the task detail drawer.
- Selecting a PRD reference shows all tasks associated with that PRD.
- Selecting a token value highlights the task in the token chart.
- Selecting `Unlinked PRD` filters other unlinked tasks.

## 7. Task Token Chart

### Purpose

Make task-level token consumption visible and comparable.

### Default View

Chart type:

- Horizontal bar chart.

Encoding:

| Visual Element | Meaning |
|---|---|
| Bar length | Total attributed tokens |
| Bar color | Task status |
| Marker line | Optional token budget |
| Warning marker | Over budget or shared attribution |

Default sort:

- Highest token usage.

Required chart labels:

- Task title.
- Total tokens.
- Status.
- Model label, such as `gpt-5.5`, `gpt-5.4`, `DeepSeek`, or `Multiple models`.
- Attribution label: `direct`, `shared`, `none`, or `unavailable`.

### Chart Interaction

Selecting a bar:

- Opens the task detail drawer.
- Highlights the matching task row.
- Shows token breakdown when available.

Hover or focus content:

| Field | Example |
|---|---|
| Task | Implement registration flow |
| Status | doing |
| Total tokens | 22,863,067 |
| Model | `gpt-5.4` |
| Input tokens | unavailable |
| Output tokens | unavailable |
| Cached input | unavailable |
| Reasoning output | unavailable |
| Attribution | direct |
| Budget | 500,000, over 2x |

Empty states:

| State | Message |
|---|---|
| No linked sessions | Task-level token chart needs `codex_sessions` in `agentpm.yaml`. |
| Token data unavailable | Codex local token data could not be read. |
| No plan | Add `agentpm.yaml` to show task token analytics. |
| Shared attribution | Some sessions are linked to multiple tasks, so totals are shared. |

## 8. PRD Coverage View

### Purpose

Help the PM verify that implementation work maps back to requirements.

### Content

| PRD Reference | Tasks | Done | Incomplete | Tokens | Attention |
|---|---:|---:|---:|---:|---|
| `01-codex-project-board-prd.md` | 4 | 3 | 1 | 1.2M | None |
| `02-task-progress-token-analytics-prd.md` | 8 | 4 | 4 | 25.9M | 2 over budget |
| Unlinked PRD | 2 | 0 | 2 | 3.1M | Scope review needed |

Interactions:

- Select a PRD row to filter task table and chart.
- Select `Unlinked PRD` to show unplanned or untraceable work.
- PRD coverage should be accessible from the summary card and as a tab in the main content.

## 9. Task Detail Drawer

### Purpose

Let the PM inspect a task without losing dashboard context.

### Drawer Sections

#### Task Summary

| Field | Example |
|---|---|
| Title | Implement registration flow |
| ID | `registration-flow` |
| Status | doing |
| Milestone | Task Analytics |
| Completion contribution | Not complete |

#### PRD Association

| Field | Example |
|---|---|
| Primary PRD | `02-task-progress-token-analytics-prd.md#story-1-view-task-level-progress` |
| Additional PRDs | `02-task-progress-token-analytics-prd.md#story-2-inspect-task-token-consumption` |
| Coverage state | Linked |

For unlinked tasks:

- Show `Unlinked PRD`.
- Show attention text: `This task is not traceable to a PRD. Confirm whether it is planned scope.`

#### Token Usage

| Field | Example |
|---|---|
| Total tokens | 22,863,067 |
| Budget | 500,000 |
| Budget state | Heavily exceeded |
| Primary model | `gpt-5.4` |
| Attribution | direct |
| Models | `gpt-5.4` or `Multiple models` when linked sessions used more than one model |
| Breakdown | available or unavailable by source |

#### Linked Codex Sessions

| Field | Example |
|---|---|
| Session ID | `019eacb2-7096-74d0-b714-5a648f6d78b0` |
| Title | Review current development mode |
| Model | `gpt-5.4-mini` |
| Updated | Jun 15, 2026 |
| Tokens | 22,863,067 |
| Source | `codex_state_db` |

Actions:

- Copy session ID.
- Filter chart to this task.
- Filter table to same PRD.
- Open local PRD path when available.

## 10. State Prototype

### Normal State

User sees:

- Completion card has a valid percent.
- PRD coverage card has linked/unlinked counts.
- Token card has total linked tokens.
- Task table is populated.
- Token chart renders one bar per task with linked token data.

### Missing Plan

User sees:

- Summary cards show `Plan unavailable`.
- Task table is replaced by a plan setup empty state.
- Token chart shows no task-level data.
- Action text explains that `agentpm.yaml` is required.

### Invalid Plan

User sees:

- Invalid plan alert.
- Parser error summary, without crashing the dashboard.
- No misleading `0%` completion.

### No PRD Links

User sees:

- PRD coverage card shows `0 / N linked`.
- Task table marks each task as `Unlinked PRD`.
- Attention queue asks the PM to confirm scope traceability.

### No Token Links

User sees:

- Task progress still works.
- Token chart empty state explains that task-level analytics require `codex_sessions`.
- Project/session token totals may still appear outside the task chart.

### Shared Attribution

User sees:

- Chart renders but uses shared attribution labels.
- Detail drawer lists the shared session.
- Attention queue explains that totals are not exclusive to one task.

### Multi-Model Task

User sees:

- Task row shows `Multiple models` in the model column.
- Token chart tooltip shows the exact contributing model list.
- Task detail drawer breaks model contribution down by linked session.

## 11. Navigation Model

Primary navigation:

- Projects.
- Dashboard.
- Tasks.
- PRD Coverage.
- Token Analytics.
- Settings.

For v0.2, `Dashboard`, `Tasks`, `PRD Coverage`, and `Token Analytics` may be tabs within the selected project instead of separate routes.

Recommended default:

- One selected-project page with tabs.
- First tab: Dashboard.
- Second tab: Tasks.
- Third tab: PRD Coverage.
- Fourth tab: Token Analytics.

## 12. Responsive Behavior

Desktop:

- Sidebar remains visible.
- Summary cards appear in one row.
- Task table and token chart can sit side by side or stacked depending on width.
- Detail drawer opens from the right.

Tablet:

- Sidebar collapses.
- Summary cards use two columns.
- Task table and chart stack vertically.

Mobile:

- Project selector becomes a top dropdown.
- Summary cards stack.
- Task table becomes a card list.
- Token chart remains horizontal but scrollable.
- Detail drawer becomes a full-screen sheet.

## 13. Prototype Data

Use this fixture data for design and frontend implementation:

| Task ID | Title | Status | PRD refs | Sessions | Tokens | Model | Budget |
|---|---|---|---:|---:|---:|---|---:|
| `frontend-shell` | Build frontend shell | done | 1 | 1 | 346,813 | `gpt-5.4-mini` | 250,000 |
| `registration-flow` | Implement registration flow | doing | 2 | 1 | 22,863,067 | `gpt-5.4` | 500,000 |
| `test-fixes` | Fix failing tests | blocked | 0 | 0 | 0 | No model | 150,000 |
| `task-token-chart` | Build task token chart | todo | 1 | 0 | 0 | No model | 300,000 |
| `prd-coverage` | Build PRD coverage view | todo | 1 | 1 | 1,420,000 | `gpt-5.4-mini` | 250,000 |

Expected computed summary:

| Metric | Value |
|---|---:|
| Done tasks | 1 |
| Total tasks | 5 |
| Blocked tasks | 1 |
| Completion | 20% |
| PRD-linked tasks | 4 |
| Unlinked tasks | 1 |
| Total linked tokens | 24,629,880 |
| Over-budget tasks | 3 |

## 14. Prototype Acceptance Checklist

- The first screen makes project completion, PRD coverage, token consumption, and blockers visible.
- A PM can find unlinked PRD work in one click.
- A PM can find the highest-token incomplete task in one click.
- A task row shows PRD association, status, linked sessions, token total, contributing model, and budget state.
- The token chart can show normal, empty, unavailable, and shared attribution states.
- The task detail drawer shows PRD refs, token breakdown, linked Codex sessions, and contributing model details.
- Missing or invalid `agentpm.yaml` never appears as `0%` progress.
- Raw Codex transcripts are not displayed by default.
