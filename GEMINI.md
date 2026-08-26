# FlowState Assist: Project Conventions

## Overview
FlowState Assist is a developer copilot designed to mitigate executive dysfunction by decomposing complex tasks into 5-minute micro-actions.

## Tech Stack
- **Backend:** FastAPI (Python 3.10+)
- **AI Core:** IBM Granite (via local/remote API)
- **State Management:** Directed Acyclic Graphs (DAGs) for task dependencies.

## Architecture
- `backend/app/main.py`: Entry point for the FastAPI application.
- `backend/app/models/`: Pydantic models for request/response validation and internal state.
- `backend/app/routes/`: API endpoint definitions.
- `backend/app/core/`: Business logic, including DAG traversal and AI interaction.

## Development Workflow
- Always include Pydantic models for API contracts.
- Use async/await for I/O bound operations.
- Ensure 5-minute granularity for micro-actions.
