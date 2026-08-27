import json
import re
import time
import uuid
from typing import Optional
import httpx
from app.models.task import TaskDAG, MicroAction, CognitiveLoad, TaskStatus
from app.models.session import PacingMode

class GraniteService:
    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        self.api_key = api_key
        self.endpoint = endpoint or "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
        self.model_id = "ibm/granite-3-8b-instruct"

    async def parse_task_to_dag(self, description: str, pacing_mode: PacingMode = PacingMode.IN_FOCUS) -> TaskDAG:
        if not self.api_key:
            return self._mock_parse(description, pacing_mode)

        prompt = self._build_prompt(description, pacing_mode)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model_id": self.model_id,
                    "input": prompt,
                    "parameters": {"max_new_tokens": 1024, "temperature": 0.2}
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            text = data.get("results", [{}])[0].get("generated_text", "")
            return self._parse_granite_output(text, description, pacing_mode)

    def _build_prompt(self, description: str, pacing_mode: PacingMode) -> str:
        pacing_note = (
            "Each micro-action should take 5 minutes or less. Cognitive load should be low."
            if pacing_mode == PacingMode.OVERWHELMED
            else "Micro-actions can be up to 10 minutes. Mix low and medium cognitive loads."
        )
        return f"""You are an expert developer assistant. Decompose the following task into a DAG of 5-minute micro-actions.

Task: {description}

Rules:
- Output valid JSON only.
- Each node is a micro-action with: id, title, description, estimated_minutes (1-10), cognitive_load (low/medium/high), command (optional shell command), dependencies (array of ids), file_operations (array of file paths).
- Dependencies must form a directed acyclic graph.
- {pacing_note}
- Provide entry_nodes (nodes with no dependencies).

JSON Schema:
{{
  "id": "string",
  "goal": "string",
  "nodes": {{
    "step_id": {{
      "id": "step_id",
      "title": "string",
      "description": "string",
      "estimated_minutes": 5,
      "cognitive_load": "low",
      "command": "optional string",
      "dependencies": [],
      "file_operations": []
    }}
  }},
  "entry_nodes": ["step_id"]
}}
"""

    def _parse_granite_output(self, text: str, goal: str, pacing_mode: PacingMode) -> TaskDAG:
        cleaned = re.sub(r"```json\n?|```", "", text).strip()
        try:
            data = json.loads(cleaned)
            nodes = {}
            for nid, node in data.get("nodes", {}).items():
                node.setdefault("status", "pending")
                node["cognitive_load"] = node.get("cognitive_load", "low")
                nodes[nid] = MicroAction(**node)
            return TaskDAG(
                id=data.get("id", str(uuid.uuid4())),
                goal=data.get("goal", goal),
                nodes=nodes,
                entry_nodes=data.get("entry_nodes", list(nodes.keys())),
            )
        except Exception:
            return self._mock_parse(goal, pacing_mode)

    def _mock_parse(self, description: str, pacing_mode: PacingMode) -> TaskDAG:
        desc_lower = description.lower()
        goal = description
        nodes = {}
        entry_nodes = []

        if any(k in desc_lower for k in ["git", "repo", "repository"]):
            nodes["init_repo"] = MicroAction(
                id="init_repo", title="Initialize Git Repository",
                description="Run git init and create initial .gitignore.",
                estimated_minutes=3 if pacing_mode == PacingMode.OVERWHELMED else 5,
                cognitive_load=CognitiveLoad.LOW,
                command="git init && echo '__pycache__/\n*.pyc\n.env\nnode_modules/' > .gitignore",
                file_operations=[".gitignore"],
            )
            entry_nodes.append("init_repo")

        if any(k in desc_lower for k in ["pr", "pull request", "review"]):
            nodes["fetch_pr"] = MicroAction(
                id="fetch_pr", title="Fetch PR Diff",
                description="Fetch the pull request diff locally.",
                estimated_minutes=3 if pacing_mode == PacingMode.OVERWHELMED else 5,
                cognitive_load=CognitiveLoad.MEDIUM,
                command="gh pr diff $PR_NUMBER > /tmp/pr_diff.diff",
                dependencies=["init_repo"] if "init_repo" in nodes else [],
                file_operations=["/tmp/pr_diff.diff"],
            )
            if "init_repo" not in nodes:
                entry_nodes.append("fetch_pr")
            nodes["scan_diff"] = MicroAction(
                id="scan_diff", title="Scan Diff for Hotspots",
                description="Run grep/awk to locate changed files and complexity.",
                estimated_minutes=4 if pacing_mode == PacingMode.OVERWHELMED else 7,
                cognitive_load=CognitiveLoad.MEDIUM,
                command="grep -E '^diff --git' /tmp/pr_diff.diff | awk '{print $4}' | sed 's#^b/##'",
                dependencies=["fetch_pr"],
            )
            nodes["run_tests"] = MicroAction(
                id="run_tests", title="Run Affected Tests",
                description="Execute test suite for changed modules.",
                estimated_minutes=5 if pacing_mode == PacingMode.OVERWHELMED else 8,
                cognitive_load=CognitiveLoad.LOW,
                command="pytest $(grep -E '^diff --git' /tmp/pr_diff.diff | awk '{print $4}' | sed 's#^b/##' | grep '\.py$' | xargs -I{} dirname {} | sort -u)",
                dependencies=["scan_diff"],
            )
            nodes["leave_review"] = MicroAction(
                id="leave_review", title="Leave Review Comment",
                description="Post a structured review comment on the PR.",
                estimated_minutes=3 if pacing_mode == PacingMode.OVERWHELMED else 5,
                cognitive_load=CognitiveLoad.LOW,
                command='gh pr comment $PR_NUMBER --body "$(cat /tmp/review_notes.md)"',
                dependencies=["run_tests"],
                file_operations=["/tmp/review_notes.md"],
            )

        if any(k in desc_lower for k in ["docker", "container", "compose"]):
            nodes["docker_build"] = MicroAction(
                id="docker_build", title="Build Docker Image",
                description="Build the container image.",
                estimated_minutes=4 if pacing_mode == PacingMode.OVERWHELMED else 7,
                cognitive_load=CognitiveLoad.MEDIUM,
                command="docker build -t myapp:latest .",
            )
            entry_nodes.append("docker_build")
            nodes["docker_run"] = MicroAction(
                id="docker_run", title="Run Container",
                description="Start the container in detached mode.",
                estimated_minutes=2 if pacing_mode == PacingMode.OVERWHELMED else 3,
                cognitive_load=CognitiveLoad.LOW,
                command="docker run -d -p 8000:8000 --name myapp_container myapp:latest",
                dependencies=["docker_build"],
                opens_ports=[8000],
            )
            nodes["docker_logs"] = MicroAction(
                id="docker_logs", title="Check Logs",
                description="Tail container logs for startup errors.",
                estimated_minutes=2 if pacing_mode == PacingMode.OVERWHELMED else 3,
                cognitive_load=CognitiveLoad.LOW,
                command="docker logs -f myapp_container",
                dependencies=["docker_run"],
            )

        if not nodes:
            nodes["start"] = MicroAction(
                id="start", title="Break Down Task Manually",
                description="No specific pattern recognized. Start by listing subtasks.",
                estimated_minutes=5,
                cognitive_load=CognitiveLoad.LOW,
                command="echo 'Create a todo list for: " + description.replace("'", "'\\''") + "'",
            )
            entry_nodes.append("start")

        dag_id = f"dag-{int(time.time())}"
        return TaskDAG(id=dag_id, goal=goal, nodes=nodes, entry_nodes=entry_nodes)
