from __future__ import annotations

import os
import re
from uuid import uuid4

import boto3
from botocore.client import Config


class VideoStorage:
    """Uploads generated video files to S3-compatible storage such as MinIO or R2."""

    def __init__(self) -> None:
        self.endpoint = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")
        self.public_endpoint = os.getenv("S3_PUBLIC_ENDPOINT_URL", self.endpoint)
        self.bucket = os.getenv("S3_BUCKET", "ai-videos")
        self.access_key = os.getenv("S3_ACCESS_KEY", "")
        self.secret_key = os.getenv("S3_SECRET_KEY", "")
        self.region = os.getenv("S3_REGION", "us-east-1")

    def _client(self, endpoint: str):
        return boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def save_video(self, title: str, filename: str, payload: bytes) -> str:
        if not self.access_key or not self.secret_key:
            raise RuntimeError("S3_ACCESS_KEY and S3_SECRET_KEY must be configured.")
        safe_title = re.sub(r"[^a-zA-Z0-9_-]+", "-", title).strip("-")[:50] or "video"
        extension = os.path.splitext(filename)[1] or ".mp4"
        key = f"generated/{safe_title}-{uuid4().hex}{extension}"
        self._client(self.endpoint).put_object(
            Bucket=self.bucket,
            Key=key,
            Body=payload,
            ContentType="video/mp4",
        )
        public_client = self._client(self.public_endpoint)
        return public_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=60 * 60 * 24,
        )


__all__ = ["VideoStorage"]
