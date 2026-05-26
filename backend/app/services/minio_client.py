# -*- coding: utf-8 -*-
"""Helpers for downloading source files from MinIO."""

import re
from pathlib import Path

from minio import Minio

from app.config import settings


def _build_client() -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=bool(settings.minio_secure),
    )


def safe_filename(name: str) -> str:
    cleaned = Path(name).name.strip()
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned)
    return cleaned or "source"


def download_object(bucket_name: str, object_name: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    client = _build_client()
    client.fget_object(bucket_name, object_name, str(destination))
