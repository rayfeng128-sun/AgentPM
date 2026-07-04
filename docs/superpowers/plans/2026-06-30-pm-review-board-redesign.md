# PM Review Board Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the current AgentPM dashboard into the high-fidelity PM review board direction shown in the approved reference, while preserving the existing project/task/token analytics behavior.

**Architecture:** Keep the current FastAPI briefing endpoints as the core source of truth, add a small amount of optional task metadata for richer task detail, and rebuild the React dashboard shell into a denser multi-panel PM workspace. Favor computed UI summaries from existing task and session data where possible, and extend the plan schema only for detail fields the reference depends on.

**Tech Stack:** FastAPI, Pydantic, React, TypeScript, Vite, CSS

---

### Task 1: Extend Task Metadata For Rich Detail Panels

**Files:**
- Modify: `backend/app/models.py`
- Modify: `backend/app/plan_parser.py`
- Modify: `backend/tests/test_plan_parser.py`
- Modify: `agentpm.yaml`

- [ ] **Step 1: Write the failing parser test**

Add a test that loads task metadata fields such as `assignee`, `created_at`, `updated_at`, and `session_note`, and asserts those fields survive parsing.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_plan_parser.py -v`
Expected: FAIL because the extra task fields are ignored or missing from the parsed model.

- [ ] **Step 3: Add optional task metadata to the backend model and parser**

Update the task schema to support:
- `assignee`
- `created_at`
- `updated_at`
- `session_note`

Keep them optional and backwards-compatible so existing plans still load.

- [ ] **Step 4: Seed the local plan with realistic metadata**

Add these fields to the richer v0.2 and backlog tasks in `agentpm.yaml` so the redesigned detail drawer has data to display.

- [ ] **Step 5: Run parser tests again**

Run: `.venv/bin/python -m pytest tests/test_plan_parser.py -v`
Expected: PASS

### Task 2: Expose The New Metadata Through Briefing Responses

**Files:**
- Modify: `backend/app/models.py`
- Modify: `backend/app/task_analytics.py`
- Modify: `backend/tests/test_task_analytics.py`

- [ ] **Step 1: Write the failing analytics/API test**

Add assertions that task token usage rows and task plan rows preserve the new metadata fields needed by the frontend detail drawer.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_task_analytics.py -v`
Expected: FAIL because the response model does not include the metadata yet.

- [ ] **Step 3: Thread the metadata through task responses**

Update the response models and task projection code so the frontend receives task detail metadata together with progress, PRD refs, sessions, and token usage.

- [ ] **Step 4: Re-run analytics tests**

Run: `.venv/bin/python -m pytest tests/test_task_analytics.py -v`
Expected: PASS

### Task 3: Rebuild The Frontend Shell Into The PM Review Board Layout

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Write a small component inventory inside the code change**

Split the monolithic screen into clear UI regions:
- app shell / left rail
- project sidebar
- top workspace header
- summary KPI cards
- roadmap section
- token chart panel
- PRD coverage matrix
- task table
- right-side detail drawer

- [ ] **Step 2: Implement the new information architecture**

Replace the current minimal shell with the approved high-fidelity structure:
- left navigation rail
- project list with health labels
- top horizontal tabs
- top toolbar with date range and filter affordance
- main center grid
- persistent right detail panel

- [ ] **Step 3: Keep existing task/token behavior while remapping presentation**

Preserve the current progress, PRD coverage, task filters, token chart, and task detail selection logic, but render them in the new panels and tables.

- [ ] **Step 4: Implement the richer detail drawer**

Add:
- `Details / Activity` tabs
- overview block
- PRD references chips
- token usage card
- linked session card
- next PM action block

- [ ] **Step 5: Refresh the visual system in CSS**

Replace the current simplified “calm board” styling with the denser, lighter enterprise dashboard treatment from the reference:
- thinner chrome
- tighter grid
- flatter white surfaces
- compact nav
- status pills
- progress bars
- table styling closer to the mockup

### Task 4: Add Derived PM-Facing Presentation Data

**Files:**
- Modify: `frontend/src/App.tsx`
- Test: visual/browser verification only

- [ ] **Step 1: Derive project and task risk labels**

Compute display-only values like:
- `Active`, `On Track`, `At Risk`, `Blocked`
- top attention count
- next PM action copy

Use current task, alert, and token data rather than inventing a second backend endpoint.

- [ ] **Step 2: Derive roadmap and matrix rows**

Use milestone/task/PRD data to populate:
- milestone roadmap table
- token usage by task list
- PRD coverage matrix
- task status table

- [ ] **Step 3: Add activity feed content for the selected task**

Build a compact activity list from session updates, alerts, timestamps, and linked metadata so the right drawer’s `Activity` tab is not empty.

### Task 5: Verify The Redesign In Browser And Docker

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`
- Verify: browser and Docker runtime

- [ ] **Step 1: Run backend tests**

Run: `cd backend && .venv/bin/python -m pytest`
Expected: PASS

- [ ] **Step 2: Run frontend production build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 3: Rebuild Docker services**

Run: `docker compose up -d --build backend frontend`
Expected: containers restart successfully on ports `8000` and `18080`

- [ ] **Step 4: Verify the rendered dashboard in the browser**

Check:
- left rail matches the approved direction
- KPI cards render
- roadmap, token panel, PRD matrix, task table, and right drawer all show together
- no console errors
- responsive desktop layout is coherent

- [ ] **Step 5: Compare against the approved reference**

Confirm at least these five points:
- overall three-column composition
- KPI row structure
- milestone roadmap table anatomy
- token usage panel anatomy
- right-side detail drawer hierarchy
