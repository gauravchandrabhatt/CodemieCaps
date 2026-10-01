# Product requirements — CodemieCaps

## Purpose
Provide a small, functional application to demonstrate the capstone's central value: orchestrating role-based SDLC work while keeping humans accountable for consequential transitions.

## Problem and gap hypothesis
A basic task tracker can hold tasks but does not provide one visible, ordered delivery workflow, explicit human approval, or an audit trail across assistant-produced artifacts. This is a **sample gap hypothesis** to validate against the actual baseline application in a real analysis phase.

## Personas
- **Business analyst / requirement assistant:** proposes gaps, epics, stories, and acceptance criteria.
- **Design / development / QA assistants:** produce phase artifacts for human review.
- **Human reviewer:** edits artifacts, approves or requests changes, and supplies a rationale.
- **Demo operator:** launches the app locally and presents status and history.

## Scope

### Functional requirements
1. Seed a sample project and ordered eight-phase workflow on first launch.
2. Persist project work items, workflow phases, review decisions, and audit events in SQLite.
3. List and create epics, stories, tasks, or bugs with title, description, and priority.
4. Allow artifact submission, approval, rejection, and resubmission only for the current phase.
5. Require reviewer identity and a note for a decision; unlock only the immediate next phase on approval.
6. Display phase status, backlog, counters, and recent audit activity in a browser dashboard.
7. Expose health and OpenAPI documentation for local validation.

### Non-functional requirements
- Run locally using Python 3.10+ without cloud dependencies.
- Validate request data and return clear HTTP errors for invalid workflow transitions.
- Keep an append-only-by-application audit history for review decisions.
- Do not claim that external assistants, Jira, or Confluence were called.

## Acceptance criteria
- The first run creates a demo project and an analysis phase awaiting review.
- A valid approval moves the current phase to planning and persists actor/note.
- Out-of-order phase mutation returns HTTP 409.
- A rejected phase can be resubmitted and reviewed again.
- Work items survive application restarts in the configured SQLite database.
- API tests cover happy paths, validation, and transition guards.

## Out of scope / next increments
Authentication/RBAC, multiple projects and runs, true LLM/Claude Code invocation, Jira/Confluence synchronization, pull-request creation, deployment automation, and production database migrations. These need explicit credentials, integration contracts, and security review.
