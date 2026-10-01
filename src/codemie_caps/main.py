from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import os

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .models import AuditEvent, Base, Project, WorkItem, WorkflowRun, WorkflowStage
from .schemas import AuditRead, ReviewDecision, StageSubmission, WorkItemCreate, WorkItemRead, WorkflowRead
from .workflow import ensure_demo_data, get_current_stage, get_workflow, log_event

APP_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = APP_ROOT / "web"


def make_engine(database_url: str):
    options = {"connect_args": {"check_same_thread": False}} if database_url.startswith("sqlite") else {}
    if database_url in ("sqlite://", "sqlite:///:memory:"):
        options["poolclass"] = StaticPool
    return create_engine(database_url, **options)


def create_app(database_url: str | None = None) -> FastAPI:
    url = database_url or os.getenv("CODIEMIE_DATABASE_URL", f"sqlite:///{APP_ROOT / 'codemiecaps.db'}")
    engine = make_engine(url)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(engine)
        with session_factory() as session:
            ensure_demo_data(session)
        yield
        engine.dispose()

    app = FastAPI(title="CodemieCaps SDLC Cockpit", version="0.1.0", lifespan=lifespan,
                  description="Assistant-driven SDLC workflow with SQLite persistence and human approval gates.")
    app.state.session_factory = session_factory

    def db_session(request: Request):
        with request.app.state.session_factory() as session:
            yield session

    app.mount("/static", StaticFiles(directory=WEB_ROOT), name="static")

    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(WEB_ROOT / "index.html")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "codemiecaps"}

    @app.get("/api/work-items", response_model=list[WorkItemRead])
    def list_work_items(session: Session = Depends(db_session)):
        return list(session.scalars(select(WorkItem).order_by(WorkItem.id)))

    @app.post("/api/work-items", response_model=WorkItemRead, status_code=201)
    def create_work_item(payload: WorkItemCreate, session: Session = Depends(db_session)):
        project = session.scalar(select(Project).where(Project.slug == "capstone-sdlc"))
        next_number = (session.query(WorkItem).count() or 0) + 1
        item = WorkItem(project_id=project.id, key=f"CAP-{next_number:03}", title=payload.title,
                        description=payload.description, item_type=payload.item_type, priority=payload.priority)
        session.add(item)
        session.commit()
        session.refresh(item)
        return item

    @app.get("/api/workflow", response_model=WorkflowRead)
    def workflow(session: Session = Depends(db_session)):
        return get_workflow(session)

    @app.post("/api/workflow/stages/{stage_key}/submit", response_model=WorkflowRead)
    def submit_stage(stage_key: str, payload: StageSubmission, session: Session = Depends(db_session)):
        run = session.scalar(select(WorkflowRun).order_by(WorkflowRun.id))
        if run is None:
            raise HTTPException(status_code=404, detail="Workflow is not initialized")
        stage = get_current_stage(session, run.id, stage_key)
        if stage.status not in ("blocked", "rejected"):
            raise HTTPException(status_code=409, detail="Stage is already awaiting review or approved")
        stage.artifact = payload.artifact
        stage.status = "in_review"
        stage.submitted_at = datetime.now(timezone.utc)
        stage.review_note = ""
        stage.reviewed_by = ""
        log_event(session, run.id, payload.actor, "stage.submitted", stage, "Artifact submitted for human review.")
        session.commit()
        return get_workflow(session)

    @app.post("/api/workflow/stages/{stage_key}/decision", response_model=WorkflowRead)
    def decide_stage(stage_key: str, payload: ReviewDecision, session: Session = Depends(db_session)):
        run = session.scalar(select(WorkflowRun).order_by(WorkflowRun.id))
        if run is None:
            raise HTTPException(status_code=404, detail="Workflow is not initialized")
        stage = get_current_stage(session, run.id, stage_key)
        if stage.status != "in_review":
            raise HTTPException(status_code=409, detail="Stage must be submitted and awaiting review")
        if payload.artifact is not None:
            stage.artifact = payload.artifact
        stage.status = "approved" if payload.decision == "approve" else "rejected"
        stage.reviewed_at = datetime.now(timezone.utc)
        stage.reviewed_by = payload.actor
        stage.review_note = payload.note
        log_event(session, run.id, payload.actor, f"stage.{payload.decision}d", stage, payload.note)
        if payload.decision == "approve":
            next_stage = session.scalar(select(WorkflowStage).where(
                WorkflowStage.run_id == run.id, WorkflowStage.position == stage.position + 1))
            if next_stage is not None:
                next_stage.status = "blocked"
            else:
                run.status = "completed"
        session.commit()
        return get_workflow(session)

    @app.get("/api/audit", response_model=list[AuditRead])
    def audit(session: Session = Depends(db_session)):
        return list(session.scalars(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(100)))

    @app.get("/api/dashboard")
    def dashboard(session: Session = Depends(db_session)):
        items = list(session.scalars(select(WorkItem)))
        stages = list(session.scalars(select(WorkflowStage).order_by(WorkflowStage.position)))
        return {"work_items": len(items), "open_items": sum(item.status != "done" for item in items),
                "stages_total": len(stages), "stages_approved": sum(stage.status == "approved" for stage in stages),
                "awaiting_review": sum(stage.status == "in_review" for stage in stages)}

    return app


app = create_app()
