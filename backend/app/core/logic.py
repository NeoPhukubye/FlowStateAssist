from typing import List, Dict, Set, Optional
from app.models.task import TaskDAG, MicroAction, TaskStatus, CognitiveLoad
from app.models.session import PacingMode

class DAGManager:
    def __init__(self, dag: TaskDAG):
        self.dag = dag

    def get_available_tasks(self) -> List[MicroAction]:
        available = []
        completed_ids: Set[str] = {
            tid for tid, t in self.dag.nodes.items() if t.status == TaskStatus.COMPLETED
        }
        for task_id, task in self.dag.nodes.items():
            if task.status != TaskStatus.PENDING:
                continue
            if all(dep in completed_ids for dep in task.dependencies):
                available.append(task)
        return available

    def update_task_status(self, task_id: str, status: TaskStatus):
        if task_id in self.dag.nodes:
            self.dag.nodes[task_id].status = status
        else:
            raise ValueError(f"Task {task_id} not found in DAG")

    def is_goal_reached(self) -> bool:
        return all(t.status == TaskStatus.COMPLETED for t in self.dag.nodes.values())

    def get_next_step(self, pacing_mode: PacingMode = PacingMode.IN_FOCUS) -> Optional[MicroAction]:
        available = self.get_available_tasks()
        if not available:
            return None
        preferred_load = (
            CognitiveLoad.LOW
            if pacing_mode == PacingMode.OVERWHELMED
            else CognitiveLoad.MEDIUM
        )
        for task in available:
            if task.cognitive_load == preferred_load:
                return task
        return available[0]

    def mark_completed(self, task_id: str):
        self.update_task_status(task_id, TaskStatus.COMPLETED)

    def topological_order(self) -> List[str]:
        in_degree: Dict[str, int] = {tid: 0 for tid in self.dag.nodes}
        adj: Dict[str, List[str]] = {tid: [] for tid in self.dag.nodes}
        for tid, node in self.dag.nodes.items():
            for dep in node.dependencies:
                adj[dep].append(tid)
                in_degree[tid] += 1
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        order = []
        while queue:
            tid = queue.pop(0)
            order.append(tid)
            for neighbor in adj[tid]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        if len(order) != len(self.dag.nodes):
            raise ValueError("Cycle detected in DAG")
        return order


class PacingEngine:
    @staticmethod
    def adjust_task(task: MicroAction, mode: PacingMode) -> MicroAction:
        if mode == PacingMode.OVERWHELMED:
            new_minutes = max(1, min(task.estimated_minutes, 5))
            new_load = CognitiveLoad.LOW
        else:
            new_minutes = min(task.estimated_minutes, 10)
            new_load = task.cognitive_load
        return task.copy(update={"estimated_minutes": new_minutes, "cognitive_load": new_load})

    @staticmethod
    def adjust_dag(dag: TaskDAG, mode: PacingMode) -> TaskDAG:
        new_nodes = {tid: PacingEngine.adjust_task(node, mode) for tid, node in dag.nodes.items()}
        return dag.copy(update={"nodes": new_nodes})


class CommandGenerator:
    @staticmethod
    def generate_for_step(step: MicroAction) -> List[dict]:
        suggestions = []
        if step.command:
            suggestions.append({
                "command": step.command,
                "cwd": ".",
                "explanation": step.description,
                "creates_files": step.file_operations,
                "opens_ports": [],
                "risk_level": "low",
            })
        if not suggestions:
            suggestions.append({
                "command": f"echo 'Starting: {step.title} - {step.description}'",
                "cwd": ".",
                "explanation": "No automated command available for this step. Proceed manually.",
                "creates_files": step.file_operations,
                "opens_ports": [],
                "risk_level": "low",
            })
        return suggestions
