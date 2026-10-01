# High- and low-level design

## High-level design
The reviewer operates a project dashboard. The API returns a workflow snapshot and accepts backlog changes, artifact submissions, and explicit human decisions. The persistence layer stores the result locally. The workflow service is the only component that decides whether a stage is current; frontend button visibility is not a security boundary.

## Low-level design
- **Entities:** `Project`, `WorkItem`, `WorkflowRun`, `WorkflowStage`, `AuditEvent`.
- **Submission:** validate artifact and actor → locate current stage → permit blocked/rejected only → set `in_review` → append `stage.submitted` event.
- **Decision:** validate approve/reject, actor, note → locate current stage → require `in_review` → persist reviewer and timestamp → append audit event → approval completes this stage; final approval completes run.
- **Concurrency note:** this demo targets one local reviewer. Add optimistic locking/transactions or row-level locking before concurrent multi-user use.
- **API errors:** 422 for invalid fields; 404 for unknown stage; 409 for invalid ordering/state.

## Data retention and integrations
SQLite is suitable for a local demo, not a multi-user production deployment. No JIRA, Confluence, Git host, Codemie, or Claude Code connector is active. Add thin integration adapters with scoped tokens and explicit audit events, and require a reviewer decision before publishing externally.
