# Support Ticket Tracker

A deliberately small, API-first support ticket application. There is no custom frontend: FastAPI provides an interactive API page at `/docs` for creating and managing tickets.

## Stack

- Python 3.10+
- FastAPI and Uvicorn
- SQLite (created automatically at `support_tickets.db`)

## Run locally

From this directory, create and activate a virtual environment if desired, then run:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open <http://127.0.0.1:8000/docs> to try the endpoints. The health endpoint is <http://127.0.0.1:8000/health>.

Set `DATABASE_PATH` to use a different SQLite file, for example `$env:DATABASE_PATH = 'C:\\data\\tickets.db'` in PowerShell before starting the app.

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Check that the service is running |
| `POST` | `/tickets` | Create a ticket with title, optional description, and requester |
| `GET` | `/tickets` | List tickets; optionally filter with `?status=open` |
| `GET` | `/tickets/{ticket_id}` | Get one ticket |
| `PATCH` | `/tickets/{ticket_id}/status` | Set status to `open`, `in_progress`, or `resolved` |

Tickets are stored in SQLite and remain available after restarting the app. Authentication and automated tests are intentionally not included in this minimal starter.
