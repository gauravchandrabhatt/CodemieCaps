from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AuditEvent, Project, WorkItem, WorkflowRun, WorkflowStage
from .schemas import WorkflowRead

STAGES = [
    ("analysis", "Gap analysis", "Business Analyst"),
    ("planning", "Stories & plan", "Requirement Assistant"),
    ("design", "Architecture & UX", "Design Assistant"),
    ("development", "Implementation", "Code Assistant"),
    ("code-review", "Code review", "Review Assistant"),
    ("testing", "Acceptance & tests", "QA Assistant"),
    ("deployment", "Local deployment", "Deployment Assistant"),
    ("documentation", "Documentation", "Documentation Assistant"),
]


def ensure_demo_data(session: Session) -> None:
    project = session.scalar(select(Project).where(Project.slug == "capstone-sdlc"))
    if project is None:
        project = Project(
            slug="capstone-sdlc",
            name="Capstone SDLC Demo",
            description="A sample project demonstrating assistant-led delivery with human approval gates.",
        )
        session.add(project)
        session.flush()

    run = session.scalar(select(WorkflowRun).where(WorkflowRun.project_id == project.id).order_by(WorkflowRun.id))
    if run is None:
        run = WorkflowRun(project_id=project.id)
        session.add(run)
        session.flush()
        for position, (key, title, persona) in enumerate(STAGES, start=1):
            session.add(WorkflowStage(
                run_id=run.id,
                key=key,
                title=title,
                persona=persona,
                position=position,
                status="in_review" if position == 1 else "blocked",
                artifact=("Demo finding: the sample task tracker needs clear ownership, due dates, and a visible approval trail. "
                          "Human review is required before this gap analysis is accepted.") if position == 1 else "",
                submitted_at=datetime.now(timezone.utc) if position == 1 else None,
            ))
        session.add(AuditEvent(
            run_id=run.id,
            actor="system",
            action="workflow.seeded",
            entity_type="workflow",
            entity_key=str(run.id),
            details="Demo workflow created; gap analysis is waiting for human review.",
        ))

    session.flush()
    count = session.scalar(select(WorkflowStage.id).where(WorkflowStage.run_id == run.id).limit(1))
    if not count:
        for position, (key, title, persona) in enumerate(STAGES, start=1):
            session.add(WorkflowStage(run_id=run.id, key=key, title=title, persona=persona,
                                     position=position, status="in_review" if position == 1 else "blocked"))
    existing_item = session.scalar(select(WorkItem.id).where(WorkItem.project_id == project.id).limit(1))
    if not existing_item:
        session.add_all([
            WorkItem(project_id=project.id, key="CAP-001", title="Make delivery progress visible",
                     description="Show the current SDLC phase and approval status.", item_type="story", priority="high"),
            WorkItem(project_id=project.id, key="CAP-002", title="Keep a review decision trail",
                     description="Record who approved or requested changes and why.", item_type="story", priority="high"),
            WorkItem(project_id=project.id, key="CAP-003", title="Prevent skipping approval gates",
                     description="Unlock the next workflow phase only after human approval.", item_type="task", priority="critical"),
        ])
    session.commit()


def get_workflow(session: Session) -> WorkflowRead:
    project = session.scalar(select(Project).where(Project.slug == "capstone-sdlc"))
    if project is None:
        raise HTTPException(status_code=404, detail="Demo project is not initialized")
    run = session.scalar(select(WorkflowRun).where(WorkflowRun.project_id == project.id).order_by(WorkflowRun.id))
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow is not initialized")
    stages = list(session.scalars(select(WorkflowStage).where(WorkflowStage.run_id == run.id)
                                  .order_by(WorkflowStage.position)))
    current = next((stage.key for stage in stages if stage.status != "approved"), None)
    return WorkflowRead(run_id=run.id, project=project.name, status="completed" if current is None else run.status,
                        current_stage=current, stages=stages)


def get_current_stage(session: Session, run_id: int, stage_key: str) -> WorkflowStage:
    stages = list(session.scalars(select(WorkflowStage).where(WorkflowStage.run_id == run_id)
                                  .order_by(WorkflowStage.position)))
    stage = next((item for item in stages if item.key == stage_key), None)
    if stage is None:
        raise HTTPException(status_code=404, detail=f"Unknown workflow stage: {stage_key}")
    current = next((item for item in stages if item.status != "approved"), None)
    if current is None or current.id != stage.id:
        raise HTTPException(status_code=409, detail="Only the current workflow stage can be changed")
    return stage


def log_event(session: Session, run_id: int, actor: str, action: str, stage: WorkflowStage, details: str) -> None:
    session.add(AuditEvent(run_id=run_id, actor=actor, action=action, entity_type="stage",
                           entity_key=stage.key, details=details))
