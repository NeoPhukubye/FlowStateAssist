from fastapi import APIRouter, HTTPException
from app.models.task import TaskDAG, MicroAction
from typing import List

router = APIRouter(tags=["tasks"])

# In-memory storage for demonstration
active_sessions: dict[str, TaskDAG] = {}

@router.post("/decompose", response_model=TaskDAG)
async def decompose_task(description: str):
    # This will later call IBM Granite to generate the DAG
    # For now, returning a mock DAG
    mock_dag = TaskDAG(
        id="mock-1",
        goal=description,
        nodes={
            "step1": MicroAction(
                id="step1",
                title="Initialize Git Repo",
                description="Run git init in the project directory.",
                cognitive_load="low",
                command="git init"
            )
        },
        entry_nodes=["step1"]
    )
    active_sessions[mock_dag.id] = mock_dag
    return mock_dag

@router.get("/session/{session_id}", response_model=TaskDAG)
async def get_session(session_id: str):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return active_sessions[session_id]
