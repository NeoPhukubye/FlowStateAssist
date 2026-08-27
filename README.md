# FlowState Assist

A developer copilot that mitigates executive dysfunction by decomposing complex tasks into 5-minute micro-actions using IBM Granite AI and DAG-based task orchestration.

## Features

- **AI Task Decomposition** - Breaks down tickets, PR diffs, and architecture specs into actionable micro-actions via IBM Granite
- **Pacing Modes** - Adjusts task complexity dynamically: *In Focus* (up to 10 min, mixed load) or *Overwhelmed* (max 5 min, low cognitive load only)
- **DAG Orchestration** - Manages task dependencies, topological ordering, and cycle detection
- **Built-in Timer** - Tracks time spent on each step with start/pause/stop controls
- **Command Suggestions** - Auto-generates shell commands and file operations for each step

## Tech Stack

- **Backend:** FastAPI (Python 3.10+)
- **AI:** IBM Granite 3 8B Instruct
- **State:** Pydantic models with in-memory session storage

## Project Structure

```
FlowStateAssist/
  backend/
    app/
      main.py               # FastAPI entry point
      models/               # Pydantic models (task, session)
      routes/               # API routers (tasks, sessions)
      core/                 # Business logic (DAG, AI, pacing)
    static/
      index.html            # Single-page frontend
    tests/                  # pytest suite
    requirements.txt
  scripts/
    run_server.sh           # Dev server launcher
```

## Getting Started

### Prerequisites

- Python 3.10+
- IBM Cloud API key (optional; falls back to mock mode if omitted)

### Install & Run

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Set IBM API key (optional)
export IBM_API_KEY="your-key"

# Run server
cd ..
bash scripts/run_server.sh
```

Open `http://localhost:8000`.

### Run Tests

```bash
cd backend
pytest
```

## API Reference

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/decompose` | Decompose a task description into a DAG |

### Sessions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/session/{id}/mode` | Update pacing mode |
| `GET` | `/api/v1/session/{id}/next` | Get next available step |
| `POST` | `/api/v1/session/{id}/step/{id}/complete` | Mark step complete |
| `GET` | `/api/v1/session/{id}/step/{id}/commands` | Get step command suggestions |
| `POST` | `/api/v1/session/{id}/timer/start` | Start step timer |
| `POST` | `/api/v1/session/{id}/timer/pause` | Pause timer |
| `POST` | `/api/v1/session/{id}/timer/resume` | Resume timer |
| `POST` | `/api/v1/session/{id}/timer/stop` | Stop timer |
| `GET` | `/api/v1/session/{id}/timer` | Get timer state |
