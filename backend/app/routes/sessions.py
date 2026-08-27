from fastapi import APIRouter, HTTPException
from app.models.task import TaskDAG
from app.models.session import (
    SessionState, PacingMode, TimerState, TimerStatus,
    FeedbackRequest, CompleteStepRequest
)
from app.core.logic import DAGManager, PacingEngine, CommandGenerator
from datetime import datetime
import time

router = APIRouter(tags=["sessions"])

active_sessions: dict[str, SessionState] = {}
session_dags: dict[str, TaskDAG] = {}


def _get_or_404(session_id: str) -> tuple[SessionState, TaskDAG]:
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return active_sessions[session_id], session_dags[session_id]


@router.post("/session/{session_id}/mode")
async def update_mode(session_id: str, req: FeedbackRequest):
    session, dag = _get_or_404(session_id)
    session.pacing_mode = req.mode
    session.updated_at = time.time()
    adjusted = PacingEngine.adjust_dag(dag, req.mode)
    session_dags[session_id] = adjusted
    return {"session_id": session_id, "mode": req.mode, "adjusted_dag": adjusted}


@router.get("/session/{session_id}/next")
async def get_next_step(session_id: str):
    session, dag = _get_or_404(session_id)
    manager = DAGManager(dag)
    step = manager.get_next_step(session.pacing_mode)
    if step:
        session.current_step_id = step.id
        session.updated_at = time.time()
    return {
        "session_id": session_id,
        "current_step": step.dict() if step else None,
        "pacing_mode": session.pacing_mode,
        "timer": session.timer.dict(),
    }


@router.post("/session/{session_id}/step/{step_id}/complete")
async def complete_step(session_id: str, step_id: str):
    session, dag = _get_or_404(session_id)
    manager = DAGManager(dag)
    if step_id not in dag.nodes:
        raise HTTPException(status_code=404, detail="Step not found")
    manager.mark_completed(step_id)
    session_dags[session_id] = dag
    session.updated_at = time.time()
    if manager.is_goal_reached():
        return {
            "session_id": session_id,
            "status": "completed",
            "message": "All steps completed. Great work!",
            "dag": dag.dict(),
        }
    next_step = manager.get_next_step(session.pacing_mode)
    session.current_step_id = next_step.id if next_step else None
    return {
        "session_id": session_id,
        "status": "in_progress",
        "completed_step_id": step_id,
        "next_step": next_step.dict() if next_step else None,
        "dag": dag.dict(),
    }


@router.get("/session/{session_id}/step/{step_id}/commands")
async def get_step_commands(session_id: str, step_id: str):
    session, dag = _get_or_404(session_id)
    if step_id not in dag.nodes:
        raise HTTPException(status_code=404, detail="Step not found")
    step = dag.nodes[step_id]
    suggestions = CommandGenerator.generate_for_step(step)
    return {
        "session_id": session_id,
        "step_id": step_id,
        "commands": suggestions,
        "pacing_mode": session.pacing_mode,
    }


@router.post("/session/{session_id}/timer/start")
async def start_timer(session_id: str):
    session, dag = _get_or_404(session_id)
    if not session.current_step_id:
        raise HTTPException(status_code=400, detail="No active step. Call /next first.")
    step = dag.nodes[session.current_step_id]
    session.timer = TimerState(
        active_step_id=session.current_step_id,
        started_at=time.time(),
        elapsed_before_pause=0.0,
        status=TimerStatus.RUNNING,
        target_minutes=float(step.estimated_minutes),
    )
    session.updated_at = time.time()
    return {"session_id": session_id, "timer": session.timer.dict()}


@router.post("/session/{session_id}/timer/pause")
async def pause_timer(session_id: str):
    session, _ = _get_or_404(session_id)
    if session.timer.status != TimerStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Timer is not running")
    session.timer.elapsed_before_pause += time.time() - session.timer.started_at
    session.timer.status = TimerStatus.PAUSED
    session.timer.started_at = None
    session.updated_at = time.time()
    return {"session_id": session_id, "timer": session.timer.dict()}


@router.post("/session/{session_id}/timer/resume")
async def resume_timer(session_id: str):
    session, _ = _get_or_404(session_id)
    if session.timer.status != TimerStatus.PAUSED:
        raise HTTPException(status_code=400, detail="Timer is not paused")
    session.timer.status = TimerStatus.RUNNING
    session.timer.started_at = time.time()
    session.updated_at = time.time()
    return {"session_id": session_id, "timer": session.timer.dict()}


@router.post("/session/{session_id}/timer/stop")
async def stop_timer(session_id: str):
    session, _ = _get_or_404(session_id)
    if session.timer.status == TimerStatus.RUNNING:
        session.timer.elapsed_before_pause += time.time() - session.timer.started_at
    session.timer.status = TimerStatus.STOPPED
    session.timer.started_at = None
    session.updated_at = time.time()
    return {"session_id": session_id, "timer": session.timer.dict()}


@router.get("/session/{session_id}/timer")
async def get_timer(session_id: str):
    session, _ = _get_or_404(session_id)
    return {"session_id": session_id, "timer": session.timer.dict()}
