from fastapi import FastAPI
from app.routes import tasks

app = FastAPI(title="FlowState Assist API")

app.include_router(tasks.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to FlowState Assist API"}
