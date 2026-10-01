# CodemieCaps — AI-assisted SDLC cockpit

A small, runnable capstone application that demonstrates an assistant-led delivery workflow with explicit **human-in-the-loop (HITL)** approvals. The goal is to make orchestration visible—not to pretend external AI assistants or enterprise systems are connected when they are not.

## What works today

- **Persistent backend:** FastAPI REST API backed by a local SQLite database.
- **End-to-end workflow:** eight ordered phases—analysis, planning, design, development, code review, testing, deployment, and documentation.
- **Human gates:** inspect/edit a phase artifact, submit it for review, approve or request changes with a required note, and see a decision unlock only the next phase.
- **Backlog:** create epics, stories, tasks, and bugs with priority; each gets a project key.
- **Audit trail:** submissions and human decisions are stored with actor, action, time, and note.
- **Demo dashboard:** browser UI for the backlog, stage status, review actions, and activity history.
- **Capstone materials:** sample product requirements, delivery plan, architecture, design, Gherkin acceptance scenarios, API tests, and an optional Playwright smoke test.

The seeded gap-analysis artifact is a **demo fixture**, not an AI-generated finding. The UI's “assistant draft” templates are illustrative inputs; generating artifacts through Codemie/Claude Code, and publishing to Jira/Confluence, require credentials and integrations not included in this local starter.

## Run locally (Windows PowerShell)

Requirements: Python 3.10+.

1. From this directory run `./scripts/run.ps1` (creates `.venv`, installs dependencies, and starts the server), or install with `python -m pip install -e ".[test]"` then run `uvicorn codemie_caps.main:app --app-dir src --reload`.
2. Open <http://127.0.0.1:8000>. API docs: <http://127.0.0.1:8000/docs>. Health: <http://127.0.0.1:8000/api/health>.
3. Use the initial review card to approve or request changes. Approval unlocks the next phase; submit the next artifact to continue.

The SQLite file is `codemiecaps.db` in this directory by default. Set `CODIEMIE_DATABASE_URL` to use a different database URL.

## Docker

Run `docker compose up --build`, then open <http://127.0.0.1:8000>. Docker Compose persists the database in a named volume.

## Tests and build artifact

- API suite: `python -m pytest --junitxml=test-results/junit.xml`
- Optional browser smoke test: `python -m pip install -e ".[test]"`, `python -m playwright install chromium`, then set `$env:RUN_BROWSER_TESTS='1'` and run `python -m pytest tests/test_browser.py --junitxml=test-results/playwright.xml`.
- Build: `./scripts/build.ps1` (compile, tests with JUnit output, and wheel in `dist/`).

## API at a glance

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| GET / POST | `/api/work-items` | List/create backlog items |
| GET | `/api/workflow` | Current run, ordered phases, statuses, artifacts |
| POST | `/api/workflow/stages/{key}/submit` | Submit current phase for human review |
| POST | `/api/workflow/stages/{key}/decision` | Approve or reject current phase with a note |
| GET | `/api/audit` | Latest audit events |
| GET | `/api/dashboard` | Dashboard counters |

## Capstone integration boundary

This starter persists its own work items and decisions; it does **not** call Jira, Confluence, Codemie, or Claude Code. Those integrations should be added behind explicit adapters and environment-based credentials. Review the design artifacts in `docs/` before connecting real systems. Never put tokens in source control.
