# FlowState Assist — Executive Dysfunction Decomposer & Micro-Step Pacer

An interactive developer copilot designed for knowledge workers dealing with ADHD, traumatic brain injury (TBI), or chronic fatigue. It ingests massive issue tickets, PR diffs, or architecture specs and programmatically splits them into 5-minute executable micro-actions with dynamic cognitive-load estimates.

## Features

- **AI Task Decomposition** - Breaks down tickets, PR diffs, and architecture specs into actionable micro-actions via IBM Granite
- **Dynamic Pacing Modes** - Adjusts task complexity based on user state: *In Focus* (up to 10 min, mixed load) or *Overwhelmed* (max 5 min, low cognitive load only)
- **DAG Orchestration** - Manages task dependencies, topological ordering, and cycle detection
- **Built-in Timer** - Tracks time spent on each step with start/pause/stop controls to combat time blindness
- **Command Suggestions** - Auto-generates shell commands and files needed for the immediate step so the user never has to context-switch across tools

## Tech Stack

- **Backend:** FastAPI (Python 3.10+)
- **AI Core:** IBM Granite 3 8B Instruct
- **Frontend:** Vanilla JS SPA served via FastAPI static files
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
      index.html            # Single-page frontend (task input, timer, step viewer)
    tests/                  # pytest suite
    requirements.txt
  scripts/
    run_server.sh           # Dev server launcher
```

## Frontend

The frontend is a single-page application (`backend/static/index.html`) served directly by FastAPI. It provides:

- **Task Input** - Textarea for pasting tickets, PR diffs, or architecture specs
- **Pacing Toggle** - Switch between *In Focus* and *Overwhelmed* modes
- **Step Viewer** - Displays the current micro-action with title, time estimate, cognitive load, and generated commands
- **Timer Controls** - Start, pause, and stop a session timer
- **Completion Flow** - Mark steps done and automatically load the next available action

No separate build step or frontend framework is required.

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
