from typing import List, Dict, Set
from app.models.task import TaskDAG, MicroAction, TaskStatus

class DAGManager:
    def __init__(self, dag: TaskDAG):
        self.dag = dag

    def get_available_tasks(self) -> List[MicroAction]:
        """
        Returns tasks that are PENDING and have all dependencies COMPLETED.
        """
        available = []
        for task_id, task in self.dag.nodes.items():
            if task.status != TaskStatus.PENDING:
                continue
            
            all_deps_completed = True
            for dep_id in task.dependencies:
                dep_task = self.dag.nodes.get(dep_id)
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    all_deps_completed = False
                    break
            
            if all_deps_completed:
                available.append(task)
        
        return available

    def update_task_status(self, task_id: str, status: TaskStatus):
        if task_id in self.dag.nodes:
            self.dag.nodes[task_id].status = status
        else:
            raise ValueError(f"Task {task_id} not found in DAG")

    def is_goal_reached(self) -> bool:
        """
        In a simple model, goal is reached if all nodes are COMPLETED.
        In a more complex one, we might look at specific sink nodes.
        """
        return all(task.status == TaskStatus.COMPLETED for task in self.dag.nodes.values())
