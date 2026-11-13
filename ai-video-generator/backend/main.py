import os

from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from worker import celery_app, generate_news_video

app = FastAPI(title="News AI Video Generator API", version="0.1.0")

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3005").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class VideoRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=20_000)
    aspect_ratio: str = Field(default="16:9", pattern=r"^(16:9|9:16)$")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/videos/generate", status_code=202)
def trigger_video_generation(req: VideoRequest):
    task = generate_news_video.delay(req.title, req.content, req.aspect_ratio)
    return {"task_id": task.id, "status": "queued"}


@app.get("/api/v1/videos/status/{task_id}")
def get_video_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    state = task_result.state

    if state == "PENDING":
        return {
            "task_id": task_id,
            "state": state,
            "progress": 0,
            "step": "Đang chờ trong hàng đợi...",
        }
    if state in {"STARTED", "PROCESSING"}:
        info = task_result.info if isinstance(task_result.info, dict) else {}
        return {
            "task_id": task_id,
            "state": "PROCESSING",
            "progress": info.get("progress", 0),
            "step": info.get("step", "Đang xử lý..."),
        }
    if state == "SUCCESS":
        return {"task_id": task_id, "state": state, "result": task_result.result}
    if state == "FAILURE":
        return {
            "task_id": task_id,
            "state": state,
            "error": str(task_result.result),
        }

    return {"task_id": task_id, "state": state, "progress": 0}
