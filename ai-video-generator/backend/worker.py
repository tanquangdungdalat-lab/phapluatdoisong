import os
import time

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery("video_worker", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(
    task_track_started=True,
    result_expires=60 * 60 * 24,
    broker_connection_retry_on_startup=True,
)


@celery_app.task(bind=True, name="generate_news_video")
def generate_news_video(self, title: str, content: str, aspect_ratio: str = "16:9"):
    """Demonstration task. Replace the simulated stages with a real video provider."""
    self.update_state(
        state="PROCESSING",
        meta={"step": "Đang phân tích nội dung bài báo...", "progress": 20},
    )
    time.sleep(3)

    self.update_state(
        state="PROCESSING",
        meta={"step": "Đang tạo video demo...", "progress": 60},
    )
    time.sleep(5)

    # Demo output only. This URL is not generated from the submitted article.
    sample_video = (
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
    )
    return {
        "status": "completed",
        "progress": 100,
        "title": title,
        "aspect_ratio": aspect_ratio,
        "video_url": sample_video,
        "demo": True,
    }
