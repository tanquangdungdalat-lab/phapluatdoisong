from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote

import requests


class ComfyUIClient:
    """ComfyUI client that runs a user-exported API workflow template."""

    def __init__(self) -> None:
        self.base_url = os.getenv("COMFYUI_URL", "").rstrip("/")
        self.workflow_path = os.getenv("COMFYUI_WORKFLOW_PATH", "/app/workflows/news-video-api.json")
        self.timeout_seconds = int(os.getenv("COMFYUI_TIMEOUT_SECONDS", "1800"))
        self.poll_seconds = float(os.getenv("COMFYUI_POLL_SECONDS", "3"))

    def is_configured(self) -> bool:
        return bool(self.base_url and Path(self.workflow_path).is_file())

    @staticmethod
    def _render_template(value: Any, replacements: dict[str, Any]) -> Any:
        if isinstance(value, dict):
            return {key: ComfyUIClient._render_template(item, replacements) for key, item in value.items()}
        if isinstance(value, list):
            return [ComfyUIClient._render_template(item, replacements) for item in value]
        if isinstance(value, str):
            if value in replacements:
                return replacements[value]
            for marker, replacement in replacements.items():
                if isinstance(replacement, str):
                    value = value.replace(marker, replacement)
            return value
        return value

    def load_workflow(self, title: str, content: str, aspect_ratio: str) -> dict[str, Any]:
        path = Path(self.workflow_path)
        if not path.is_file():
            raise RuntimeError(
                f"ComfyUI workflow not found: {path}. Export an API workflow and mount it into the worker."
            )
        try:
            workflow = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Could not read ComfyUI workflow JSON: {exc}") from exc
        if not isinstance(workflow, dict) or not workflow:
            raise RuntimeError("ComfyUI API workflow must be a non-empty JSON object.")

        width, height = (1280, 720) if aspect_ratio == "16:9" else (720, 1280)
        prompt = f"{title}. {content[:4000]}"
        return self._render_template(
            workflow,
            {
                "{{PROMPT}}": prompt,
                "{{TITLE}}": title,
                "{{CONTENT}}": content[:4000],
                "{{WIDTH}}": width,
                "{{HEIGHT}}": height,
                "{{SEED}}": int.from_bytes(os.urandom(4), "big"),
            },
        )

    def queue_prompt(self, workflow: dict[str, Any]) -> str:
        if not self.base_url:
            raise RuntimeError("COMFYUI_URL is not configured.")
        response = requests.post(f"{self.base_url}/prompt", json={"prompt": workflow}, timeout=30)
        response.raise_for_status()
        prompt_id = response.json().get("prompt_id")
        if not prompt_id:
            raise RuntimeError("ComfyUI did not return prompt_id.")
        return str(prompt_id)

    def _history(self, prompt_id: str) -> dict[str, Any]:
        response = requests.get(f"{self.base_url}/history/{quote(prompt_id)}", timeout=30)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            return {}
        return payload.get(prompt_id) or payload

    def _outputs(self, entry: dict[str, Any]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for output in (entry.get("outputs") or {}).values():
            if not isinstance(output, dict):
                continue
            for key in ("videos", "gifs", "images"):
                files = output.get(key) or []
                if isinstance(files, list):
                    results.extend(item for item in files if isinstance(item, dict) and item.get("filename"))
        return results

    def render(self, title: str, content: str, aspect_ratio: str, progress: Callable[[str, int], None]) -> list[dict[str, Any]]:
        workflow = self.load_workflow(title, content, aspect_ratio)
        prompt_id = self.queue_prompt(workflow)
        deadline = time.monotonic() + self.timeout_seconds

        while time.monotonic() < deadline:
            entry = self._history(prompt_id)
            status = entry.get("status") or {}
            status_str = str(status.get("status_str", "")).lower() if isinstance(status, dict) else ""
            if status_str in {"error", "failed"} or entry.get("exception_message"):
                raise RuntimeError(f"ComfyUI render failed: {entry.get('exception_message') or status}")

            outputs = self._outputs(entry)
            if outputs:
                progress("Đã render xong, đang lưu video...", 90)
                return outputs

            progress("ComfyUI đang render video...", 55)
            time.sleep(self.poll_seconds)

        raise TimeoutError(f"ComfyUI render timed out after {self.timeout_seconds} seconds (prompt {prompt_id}).")

    def download_output(self, output: dict[str, Any]) -> tuple[bytes, str]:
        response = requests.get(
            f"{self.base_url}/view",
            params={
                "filename": output["filename"],
                "subfolder": output.get("subfolder", ""),
                "type": output.get("type", "output"),
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.content, str(output["filename"])


__all__ = ["ComfyUIClient"]
