from fastapi.testclient import TestClient

from codemie_caps.main import create_app


def make_client():
    app = create_app("sqlite://")
    return TestClient(app)


def test_demo_seeds_workflow_and_backlog_is_creatable():
    with make_client() as client:
        assert client.get("/api/health").json()["status"] == "ok"
        workflow = client.get("/api/workflow").json()
        assert workflow["current_stage"] == "analysis"
        assert workflow["stages"][0]["status"] == "in_review"
        assert len(workflow["stages"]) == 8

        created = client.post("/api/work-items", json={
            "title": "Show review history", "description": "Keep a decision record.",
            "item_type": "story", "priority": "high",
        })
        assert created.status_code == 201
        assert created.json()["key"].startswith("CAP-")
        titles = {item["title"] for item in client.get("/api/work-items").json()}
        assert "Show review history" in titles


def test_human_approval_unlocks_next_stage_and_is_audited():
    with make_client() as client:
        response = client.post("/api/workflow/stages/analysis/decision", json={
            "decision": "approve", "actor": "Reviewer", "note": "Gap is accurate.",
        })
        assert response.status_code == 200
        workflow = response.json()
        assert workflow["current_stage"] == "planning"
        assert workflow["stages"][0]["status"] == "approved"
        assert workflow["stages"][1]["status"] == "blocked"
        assert any(event["action"] == "stage.approved" for event in client.get("/api/audit").json())


def test_workflow_blocks_out_of_order_and_requires_review_note():
    with make_client() as client:
        early = client.post("/api/workflow/stages/testing/submit", json={"artifact": "test plan", "actor": "QA"})
        assert early.status_code == 409
        no_note = client.post("/api/workflow/stages/analysis/decision", json={
            "decision": "approve", "actor": "Reviewer", "note": "x",
        })
        assert no_note.status_code == 422


def test_rejected_phase_can_be_resubmitted():
    with make_client() as client:
        rejected = client.post("/api/workflow/stages/analysis/decision", json={
            "decision": "reject", "actor": "Reviewer", "note": "Please add impact.",
        })
        assert rejected.status_code == 200
        assert rejected.json()["current_stage"] == "analysis"
        submitted = client.post("/api/workflow/stages/analysis/submit", json={
            "artifact": "Revised finding with impact and evidence.", "actor": "Assistant",
        })
        assert submitted.status_code == 200
        assert submitted.json()["stages"][0]["status"] == "in_review"
