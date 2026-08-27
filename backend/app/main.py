from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routes import tasks, sessions

app = FastAPI(title="FlowState Assist API")

app.include_router(tasks.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")

app.mount("/static", StaticFiles(directory="backend/static"), name="static")


@app.get("/")
async def root():
    return FileResponse("backend/static/index.html")
