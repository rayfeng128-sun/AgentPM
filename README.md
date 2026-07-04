# AgentPM

AgentPM is a local dashboard for checking Codex-assisted project progress. It helps a developer answer:

```text
Where is this project now, what changed recently, and what should happen next?
```

The current product target is Codex Project Board v0.1.

## Product Sources

- Product requirements: [docs/product/01-codex-project-board-prd.md](docs/product/01-codex-project-board-prd.md)
- Implementation plan: [docs/superpowers/plans/2026-06-27-codex-project-board.md](docs/superpowers/plans/2026-06-27-codex-project-board.md)
- Local progress file: [agentpm.yaml](agentpm.yaml)
- Project documentation index: [docs/README.md](docs/README.md)

The reusable agent governance framework is documented separately in [docs/process/agent-development-framework.md](docs/process/agent-development-framework.md). It is not the project README.

## Project Shape

- `backend/`: FastAPI backend.
- `frontend/`: React dashboard frontend.
- `docs/product/`: product source of truth.
- `docs/superpowers/`: generated specs and implementation plans.
- `AGENT/`: reusable agent rule package.
- `references/Harness/`: optional structured governance harness for larger changes.

## Required Project Inputs

AgentPM monitors other local projects. A project can be registered with only:

- A real local directory path.
- A project name you enter in the UI.

That is the minimum required setup, but the dashboard will only show limited information unless the project also exposes the data sources below.

### Recommended Project Sources

- `agentpm.yaml` in the project root.
  This is the main progress source. Without it, AgentPM can still register the project, but progress, milestones, task status, and PM-style next steps will show as unavailable or warning states.
- A Git repository at the project root, usually via `.git/`.
  Without Git, the project is still allowed, but branch, commit, and dirty-file signals are unavailable.
- Local Codex state on the same machine.
  AgentPM reads Codex activity from `~/.codex/sqlite/state_5.sqlite` and falls back to rollout files under `~/.codex/sessions/` and `~/.codex/archived_sessions/`. If those files are missing or unreadable, recent Codex activity and token signals are shown as unavailable.

### `agentpm.yaml` Example

```yaml
project:
  name: My Project
  path: /absolute/path/to/my-project

milestones:
  - id: mvp
    title: MVP
    tasks:
      - id: shell
        title: Build app shell
        status: done
      - id: dashboard
        title: Finish dashboard
        status: doing
        prd_refs:
          - docs/product/01-codex-project-board-prd.md#story-1-view-project-briefing
        codex_sessions:
          - 019f141c-7e6c-7d40-b43a-d2cbcd1e3b07
        token_budget: 300000
```

Supported task statuses are `todo`, `doing`, `done`, and `blocked`.

## Run Locally

Backend:

```bash
cd backend
python3 -m pip install -e ".[test]"
python3 -m uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the backend API at `http://localhost:8000`.

## Bootstrap A Codex Project For AgentPM

From the AgentPM repository:

```bash
cd backend
python3 -m pip install -e ".[test]"
agentpm-bootstrap --target /absolute/path/to/my-project --project-name "My Project" --dry-run
agentpm-bootstrap --target /absolute/path/to/my-project --project-name "My Project"
```

If your local virtual environment does not expose the `agentpm-bootstrap` console command, use the repo-local launcher instead:

```bash
cd backend
./agentpm-bootstrap --target /absolute/path/to/my-project --project-name "My Project" --dry-run
./agentpm-bootstrap --target /absolute/path/to/my-project --project-name "My Project"
```

The bootstrap command:

- creates a starter `agentpm.yaml` when it is missing
- keeps AgentPM operational state under `.agentpm/`
- asks before changing existing `agentpm.yaml`, `AGENTS.md`, or `CODEX.md`
- supports rollback with:

```bash
agentpm-bootstrap --target /absolute/path/to/my-project --rollback
```

Or from `backend/`:

```bash
./agentpm-bootstrap --target /absolute/path/to/my-project --rollback
```

## Prepare A Codex Project For AgentPM

If you do not use the bootstrap command, you can still set a project up manually:

If you want AgentPM to give useful progress and Codex summaries for one of your own projects, set that project up like this:

1. Put the project in a real local folder with a stable absolute path.
2. If possible, keep it as a Git repository so AgentPM can read branch and working-tree status.
3. Add an `agentpm.yaml` file at the project root.
4. Run Codex from that same project root so Codex sessions use the project folder as their `cwd`.
5. If you want task-level token attribution, add each task's `codex_sessions` IDs into `agentpm.yaml`.
6. Start AgentPM, register that project path in the UI, and open its briefing.

### Important Matching Rule

AgentPM matches Codex sessions to a project by the session working directory. In practice, that means:

- If your project path is `/absolute/path/to/my-project`, run Codex with that folder as the working directory.
- If Codex was run from a parent folder, sibling folder, or temporary folder, AgentPM may not associate that session with the project you registered.

### Practical Setup Flow

1. Create or update `/absolute/path/to/my-project/agentpm.yaml`.
2. Open Codex in `/absolute/path/to/my-project`.
3. Do your work there so Codex writes local session state for that path.
4. Register `/absolute/path/to/my-project` in AgentPM.
5. Refresh the project briefing and confirm you can see progress, Git state, and recent sessions.

## Verification

Backend:

```bash
cd backend
python3 -m pytest
```

Frontend:

```bash
cd frontend
npm run build
```

## Run With Docker

```bash
docker compose up --build
```

Then open `http://localhost:18080`.

The backend API is exposed at `http://localhost:8000`. The compose setup keeps app data in the `agentpm-data` Docker volume and mounts `/Users/ray/BaiduNetDisk/Project/ExamSystem_2` and `/Users/ray/BaiduNetDisk/Project/AgentPM` read-only so those projects can be verified through Docker.

For a safe smoke check, register this sample project in the UI:

```text
Name: AgentPM Docker Sample
Path: /sample-project
```

To inspect real local host projects from inside Docker, add explicit read-only bind mounts to `docker-compose.yml` for the exact directories you want the backend to read.
