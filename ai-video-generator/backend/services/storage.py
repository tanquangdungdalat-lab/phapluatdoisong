from __future__ import annotations

import os
from pathlib import Path


class LocalVideoStorage:
    """Local file storage used when ComfyUI exposes a filesystem-backed output."""

    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or os.getenv("VIDEO_OUTPUT_DIR", "/tmp/ai-video-output"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, filename: str, payload: bytes) -> str:
        destination = self.base_dir / filename
        destination.write_bytes(payload)
        return str(destination)
