from app.models.session import SessionState
from app.models.task import TaskDAG

active_sessions: dict[str, SessionState] = {}
session_dags: dict[str, TaskDAG] = {}
