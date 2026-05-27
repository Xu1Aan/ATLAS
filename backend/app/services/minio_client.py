# -*- coding: utf-8 -*-
"""Helpers for downloading source files from MinIO."""

import re
from pathlib import Path

from minio import Minio
from minio.error import S3Error

from app.config import settings


def _build_client() -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=bool(settings.minio_secure),
        region=settings.minio_region,
    )


def _ensure_configured() -> None:
    if not settings.minio_endpoint:
        raise RuntimeError("MinIO endpoint 未配置")
    if not settings.minio_access_key or not settings.minio_secret_key:
        raise RuntimeError("MinIO 凭证未配置")


def safe_filename(name: str) -> str:
    cleaned = Path(name).name.strip()
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned)
    return cleaned or "source"


def download_object(bucket_name: str, object_name: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    _ensure_configured()
    client = _build_client()
    try:
        client.fget_object(bucket_name, object_name, str(destination))
    except S3Error as exc:
        if exc.code == "NoSuchBucket":
            raise RuntimeError(f"MinIO bucket 不存在: {bucket_name}") from exc
        if exc.code == "NoSuchKey":
            raise RuntimeError(f"MinIO 对象不存在: {object_name}") from exc
        if exc.code in {"InvalidAccessKeyId", "SignatureDoesNotMatch", "AccessDenied"}:
            raise RuntimeError("MinIO 凭证无效或无权限访问对象") from exc
        raise RuntimeError(f"MinIO 下载失败: {exc.code}") from exc
