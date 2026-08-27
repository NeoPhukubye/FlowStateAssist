import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.task import TaskDAG
from app.models.session import PacingMode

client = TestClient(app)


def test_decompose_endpoint():
    resp = client.post("/api/v1/decompose", data={"description": "Review PR #42", "pacing_mode": "in_focus"})
    assert resp.status_code == 200
    dag = resp.json()
    assert "id" in dag
    assert "nodes" in dag
    assert len(dag["nodes"]) > 0


def test_decompose_overwhelmed():
    resp = client.post("/api/v1/decompose", data={"description": "Review PR #42", "pacing_mode": "overwhelmed"})
    assert resp.status_code == 200
    dag = resp.json()
    for node in dag["nodes"].values():
        assert node["estimated_minutes"] <= 5
        assert node["cognitive_load"] == "low"


def test_session_flow():
    resp = client.post("/api/v1/decompose", data={"description": "Review PR #42", "pacing_mode": "in_focus"})
    dag = resp.json()
    session_id = "sess-" + str(int(__import__('time').time()))

    resp = client.get(f"/api/v1/session/{session_id}/next")
    assert resp.status_code == 404


def test_mode_toggle():
    resp = client.post("/api/v1/decompose", data={"description": "Initialize git repo", "pacing_mode": "in_focus"})
    dag = resp.json()
    session_id = "sess-" + str(int(__import__('time').time()))
    from app.routes.sessions import active_sessions, session_dags
    from app.models.session import SessionState
    active_sessions[session_id] = SessionState(
        id=session_id, dag_id=dag["id"], pacing_mode=PacingMode.IN_FOCUS,
        created_at=__import__('time').time(), updated_at=__import__('time').time()
    )
    session_dags[session_id] = TaskDAG(**dag)

    resp = client.post(f"/api/v1/session/{session_id}/mode", json={"session_id": session_id, "mode": "overwhelmed"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "overwhelmed"
