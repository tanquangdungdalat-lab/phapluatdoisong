import os

from celery import Celery

from services.comfyui_client import ComfyUIClient
from services.storage import VideoStorage

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery("video_worker", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(
    task_track_started=True,
    result_expires=60 * 60 * 24,
    broker_connection_retry_on_startup=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

comfyui = ComfyUIClient()
storage = VideoStorage()


@celery_app.task(bind=True, name="generate_news_video")
def generate_news_video(self, title: str, content: str, aspect_ratio: str = "16:9"):
    if aspect_ratio not in {"16:9", "9:16"}:
        raise ValueError("Unsupported aspect ratio. Use 16:9 or 9:16.")
    if not title.strip() or not content.strip():
        raise ValueError("Title and content are required.")
    if not comfyui.is_configured():
        raise RuntimeError(
            "Real video rendering is not configured. Set COMFYUI_URL and provide "
            "the API-format workflow file at COMFYUI_WORKFLOW_PATH."
        )

    self.update_state(state="PROCESSING", meta={"step": "Đang chuẩn bị workflow ComfyUI...", "progress": 10})

    def report(step: str, progress: int) -> None:
        self.update_state(state="PROCESSING", meta={"step": step, "progress": progress})

    outputs = comfyui.render(title, content, aspect_ratio, report)
    video_outputs = [item for item in outputs if str(item.get("filename", "")).lower().endswith((".mp4", ".webm", ".mov", ".mkv"))]
    if not video_outputs:
        raise RuntimeError(
            "Workflow completed but produced no video output. Configure a video output node "
            "(for example VHS_VideoCombine) in the ComfyUI API workflow."
        )

    report("Đang tải video từ ComfyUI và lưu vào MinIO/S3...", 95)
    video_bytes, filename = comfyui.download_output(video_outputs[0])
    video_url = storage.save_video(title, filename, video_bytes)

    return {
        "status": "completed",
        "progress": 100,
        "title": title,
        "aspect_ratio": aspect_ratio,
        "video_url": video_url,
        "demo": False,
    }
