from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

class PacingMode(str, Enum):
    OVERWHELMED = "overwhelmed"
    IN_FOCUS = "in_focus"

class TimerStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"

class TimerState(BaseModel):
    active_step_id: Optional[str] = None
    started_at: Optional[float] = None
    elapsed_before_pause: float = 0.0
    status: TimerStatus = TimerStatus.IDLE
    target_minutes: float = 5.0

class CommandSuggestion(BaseModel):
    command: str
    cwd: str
    explanation: str
    creates_files: List[str] = Field(default_factory=list)
    opens_ports: List[int] = Field(default_factory=list)
    risk_level: str = "low"

class SessionState(BaseModel):
    id: str
    user_id: Optional[str] = None
    dag_id: str
    current_step_id: Optional[str] = None
    pacing_mode: PacingMode = PacingMode.IN_FOCUS
    timer: TimerState = Field(default_factory=TimerState)
    created_at: float
    updated_at: float

class FeedbackRequest(BaseModel):
    session_id: str
    mode: PacingMode

class CompleteStepRequest(BaseModel):
    session_id: str
    step_id: str
