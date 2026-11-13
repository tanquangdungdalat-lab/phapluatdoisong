# AI Video Generator Module

Standalone video generation module for the news site. It does not modify the existing Flask application.

## Services and access

- Web UI: <http://localhost:3005>
- FastAPI / Swagger: <http://localhost:8005> / <http://localhost:8005/docs>
- MinIO Console: <http://localhost:9001>
- MinIO S3 endpoint: <http://localhost:9000>
- PostgreSQL: host port `5433` (internal service name `postgres:5432`)
- Redis: host port `6380` (internal service name `redis:6379`)

## Requirements

Install Docker Engine and Docker Compose plugin. For real rendering, run ComfyUI on an NVIDIA GPU host, install a compatible video-generation workflow/model and make its HTTP API reachable from Docker worker.

## Configure and start

```bash
cd ai-video-generator
cp .env.example .env
```

Edit `.env` and replace both placeholder passwords with long, unique random values. Do not commit `.env`. Then start:

```bash
docker compose up --build -d
docker compose ps
```

Open the UI at <http://localhost:3005>, API docs at <http://localhost:8005/docs>, and MinIO console at <http://localhost:9001>. Log in to MinIO using the values in `.env`; the `ai-videos` bucket is created automatically. The local sample credentials shown in `.env.example` are placeholders and must be replaced.

Stop services with `docker compose down`. To remove all local data as well, use `docker compose down -v` (this permanently deletes Postgres, Redis, and MinIO data).

## Enable real ComfyUI rendering

1. Start ComfyUI on the GPU machine with its HTTP server enabled (normally port `8188`).
2. In `.env`, set `COMFYUI_URL` to an address reachable from the worker. On Docker Desktop, `http://host.docker.internal:8188` is typically suitable. Linux Compose maps `host.docker.internal` to the host gateway. If ComfyUI is on another machine, use its reachable private IP/hostname instead.
3. In ComfyUI, construct and test a prompt-to-video workflow compatible with the installed model and video nodes. Export it using **Save (API Format)** and save the exported JSON as `workflows/news-video-api.json`.
4. In that API-format workflow, set the prompt input to `{{PROMPT}}` (or use `{{TITLE}}` / `{{CONTENT}}`), width and height inputs to `{{WIDTH}}` and `{{HEIGHT}}`, and optionally seed to `{{SEED}}`. Ensure the workflow includes an output node that emits a video file such as MP4/WebM/MOV/MKV. The illustrative JSON in `workflows/README-workflow-template.json` is not a ready Wan/Hunyuan workflow; use the API JSON exported by your installed ComfyUI nodes/model.
5. Restart/rebuild the worker after adding the workflow: `docker compose up --build -d worker`.

The task fails clearly if ComfyUI or the workflow file is missing; there is no misleading demo video fallback. Rendered video output is downloaded from ComfyUI and uploaded to the MinIO bucket. The API result includes a presigned URL valid for 24 hours.

For access from another computer, set `S3_PUBLIC_ENDPOINT_URL` to an address that browser can reach, e.g. `http://<server-ip>:9000`; configure DNS/HTTPS and secure MinIO with a reverse proxy before public deployment. Do not expose MinIO or its console directly to the Internet.

## API

- `POST /api/v1/videos/generate`: `{ "title": "...", "content": "...", "aspect_ratio": "16:9" }`
- `GET /api/v1/videos/status/{task_id}`
- `GET /health`

Only `16:9` and `9:16` aspect ratios are accepted. Title length is limited to 200 characters and content to 20,000 characters.

## Data and production limitations

PostgreSQL and MinIO are provisioned by Compose; current task state/results are managed by Celery/Redis and PostgreSQL is not yet used by the API for history. Add database migrations and access control before relying on it for application data. This deployment also needs HTTPS, API authentication/authorization, rate limiting, backup/retention policies, monitoring, and GPU/model-specific performance testing before public production use.

`DATABASE_URL` is passed to the backend for future persistence integration. MinIO uses the root credentials for the local MVP; production should use a scoped service account and secret manager.
