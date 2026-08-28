from fastapi import APIRouter, HTTPException
from app.models.task import TaskDAG, MicroAction
from app.models.session import SessionState, PacingMode
from app.core.ai import GraniteService
from app.core.logic import DAGManager
from app.state import active_sessions, session_dags
from typing import List
import time
import uuid

router = APIRouter(tags=["tasks"])


@router.post("/decompose", response_model=TaskDAG)
async def decompose_task(description: str, pacing_mode: PacingMode = PacingMode.IN_FOCUS):
    service = GraniteService()
    dag = await service.parse_task_to_dag(description, pacing_mode)
    manager = DAGManager(dag)
    try:
        manager.topological_order()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    session_id = f"sess-{uuid.uuid4().hex[:12]}"
    session = SessionState(
        id=session_id,
        dag_id=dag.id,
        pacing_mode=pacing_mode,
        created_at=time.time(),
        updated_at=time.time(),
    )
    active_sessions[session_id] = session
    session_dags[session_id] = dag
    return dag
