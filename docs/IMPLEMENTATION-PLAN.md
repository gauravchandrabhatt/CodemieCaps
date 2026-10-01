# Implementation plan

| Increment | Outcome | Human gate | State in this starter |
|---|---|---|---|
| 1. Analyze | Record baseline gap hypotheses and acceptance criteria | BA validates actual gaps | Demo analysis artifact seeded for review |
| 2. Plan | Break enhancement into epic/story/task backlog | Product owner reviews scope | Create/list work items in UI/API |
| 3. Design | Agree architecture, data model, and wireframe | Design review | `ARCHITECTURE.md`, `DESIGN.md`, `WIREFRAME.md` |
| 4. Develop | Implement SQLite models, REST API, and dashboard | Code owner checks generated changes | Implemented locally; no Claude Code execution is claimed |
| 5. Review | Inspect code and security/quality concerns | Reviewer records outcome | Workflow gate and audit event implemented |
| 6. Test | Exercise acceptance scenarios and API | QA accepts report | Pytest suite; optional Playwright browser test |
| 7. Deploy | Run locally or in Docker | Operator smoke-checks service | PowerShell run/build scripts and Compose file |
| 8. Document | Publish final requirements and design artifacts | Owner verifies evidence | Markdown docs committed with source |

## Suggested real capstone orchestration

1. BA assistant inspects the selected baseline and proposes evidence-backed gaps.
2. Requirement assistant creates Jira epic/stories; product owner edits and approves them.
3. Planning assistant produces a scoped plan and requests a Git pull request; owner approves before merge.
4. Design assistant publishes reviewed FRD, architecture, low-level design, and wireframes to Confluence.
5. Code assistant uses Claude Code CLI via the authorized Codemie integration; developer reviews every diff.
6. Review assistant posts actionable Git review comments; developer resolves them.
7. QA assistant generates Gherkin and Playwright tests, executes them, and attaches the report to Jira.
8. Deployment assistant starts the local app; operator verifies health and approves.
9. Documentation assistant updates Confluence; document owner verifies publication.

Connectors should be idempotent, least-privileged, environment-configured, and report real success/failure. A workflow phase must not be marked complete merely because a draft artifact exists.
