# AgentPM

AgentPM is a local dashboard for checking Codex-assisted project progress. It helps a developer answer:

```text
Where is this project now, what changed recently, and what should happen next?
```

The current product target is Codex Project Board v0.1.

## Product Sources

- Product requirements: [docs/product/01-prd.md](docs/product/01-prd.md)
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

## Run Locally

Backend:

```bash
cd backend
python -m pip install -e ".[test]"
python -m uvicorn app.main:app --reload --port 8000
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
python -m pip install -e ".[test]"
agentpm-bootstrap --target /absolute/path/to/my-project --project-name "My Project" --dry-run
agentpm-bootstrap --target /absolute/path/to/my-project --project-name "My Project"
```

The bootstrap command:

- creates a starter `agentpm.yaml` when it is missing
- keeps AgentPM operational state under `.agentpm/`
- asks before changing existing `agentpm.yaml`, `AGENTS.md`, or `CODEX.md`
- supports rollback with:

```bash
agentpm-bootstrap --target /absolute/path/to/my-project --rollback
```

## Verification

Backend:

```bash
cd backend
python -m pytest
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
