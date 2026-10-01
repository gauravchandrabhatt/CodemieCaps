"""Minimal API-first support ticket tracker backed by SQLite."""

from contextlib import asynccontextmanager, closing
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
from typing import Generator, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

TicketStatus = Literal["open", "in_progress", "resolved"]


class TicketCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=5000)
    requester: str = Field(default="Anonymous", min_length=1, max_length=120)


class TicketStatusUpdate(BaseModel):
    status: TicketStatus


class TicketRead(BaseModel):
    id: int
    title: str
    description: str
    requester: str
    status: TicketStatus
    created_at: str
    updated_at: str


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection(request: Request) -> Generator[sqlite3.Connection, None, None]:
    connection = sqlite3.connect(request.app.state.database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def create_app(database_path: str | Path | None = None) -> FastAPI:
    db_path = Path(database_path or os.getenv("DATABASE_PATH", "support_tickets.db")).resolve()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(db_path)) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    requester TEXT NOT NULL DEFAULT 'Anonymous',
                    status TEXT NOT NULL DEFAULT 'open'
                        CHECK (status IN ('open', 'in_progress', 'resolved')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )
            connection.commit()
        yield

    app = FastAPI(
        title="Support Ticket Tracker",
        description="A small ticket API with interactive documentation at /docs.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.database_path = str(db_path)

    @app.get("/health", tags=["service"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/tickets", response_model=TicketRead, status_code=status.HTTP_201_CREATED,
              tags=["tickets"], summary="Create a support ticket")
    def create_ticket(payload: TicketCreate, connection: sqlite3.Connection = Depends(get_connection)):
        created_at = now_utc()
        cursor = connection.execute(
            "INSERT INTO tickets (title, description, requester, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (payload.title, payload.description, payload.requester, created_at, created_at),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM tickets WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)

    @app.get("/tickets", response_model=list[TicketRead], tags=["tickets"], summary="List tickets")
    def list_tickets(
        ticket_status: TicketStatus | None = Query(default=None, alias="status"),
        connection: sqlite3.Connection = Depends(get_connection),
    ):
        if ticket_status:
            rows = connection.execute(
                "SELECT * FROM tickets WHERE status = ? ORDER BY id DESC", (ticket_status,)
            ).fetchall()
        else:
            rows = connection.execute("SELECT * FROM tickets ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]

    @app.get("/tickets/{ticket_id}", response_model=TicketRead, tags=["tickets"], summary="Get a ticket")
    def get_ticket(ticket_id: int, connection: sqlite3.Connection = Depends(get_connection)):
        row = connection.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return dict(row)

    @app.patch("/tickets/{ticket_id}/status", response_model=TicketRead,
               tags=["tickets"], summary="Update a ticket's status")
    def update_ticket_status(
        ticket_id: int,
        payload: TicketStatusUpdate,
        connection: sqlite3.Connection = Depends(get_connection),
    ):
        updated_at = now_utc()
        cursor = connection.execute(
            "UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?",
            (payload.status, updated_at, ticket_id),
        )
        connection.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ticket not found")
        row = connection.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        return dict(row)

    return app


app = create_app()
