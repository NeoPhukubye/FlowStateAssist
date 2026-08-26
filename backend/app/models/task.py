from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"

class CognitiveLoad(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class MicroAction(BaseModel):
    id: str
    title: str
    description: str
    estimated_minutes: int = 5
    cognitive_load: CognitiveLoad
    command: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = Field(default_factory=list)

class TaskDAG(BaseModel):
    id: str
    goal: str
    nodes: Dict[str, MicroAction]
    entry_nodes: List[str]
