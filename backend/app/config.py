# -*- coding: utf-8 -*-
"""Application settings for local and container deployments."""
import os
from pathlib import Path
from urllib.parse import urlparse

from pydantic_settings import BaseSettings

_BACKEND_DIR = Path(__file__).resolve().parent.parent


def _resolve_env_files() -> tuple[str, ...]:
    app_env = os.getenv("APP_ENV", "").strip().lower()
    files: list[Path] = []
    if app_env in {"pro", "prod", "production"}:
        files.append(_BACKEND_DIR / ".env.pro")
    elif app_env in {"dev", "development"}:
        files.append(_BACKEND_DIR / ".env.dev")
    local_env = _BACKEND_DIR / ".env"
    if local_env.exists():
        files.append(local_env)
    if files:
        return tuple(str(path) for path in files)
    return (str(_BACKEND_DIR / ".env.dev"),)


class Settings(BaseSettings):
    """Runtime settings."""

    work_dir: Path = Path("./data")
    dwg2dxf_cmd: str = "dwg2dxf"
    ogr2ogr_cmd: str = "ogr2ogr"
    target_srs: str = "EPSG:4326"
    gauss_kruger_zone: int | None = None
    enable_gauss_kruger_transform: bool = True
    geoserver_url: str = "http://10.20.124.71:18081/geoserver"
    geoserver_user: str = "admin"
    geoserver_password: str = "geoserver"
    geoserver_workspace: str = "dwg"
    geoserver_public_url: str = "http://10.20.124.50:30030/public/dwgconvert/geoserver"
    minio_endpoint: str = "http://10.20.124.73:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_secure: bool | None = None
    minio_region: str | None = None
    minio_path_style: bool = True

    class Config:
        env_prefix = "APP_"
        env_file = _resolve_env_files()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.work_dir = Path(self.work_dir).resolve()
        self.work_dir.mkdir(parents=True, exist_ok=True)
        parsed = urlparse(self.minio_endpoint)
        if parsed.scheme and parsed.netloc:
            if self.minio_secure is None:
                self.minio_secure = parsed.scheme == "https"
            self.minio_endpoint = parsed.netloc
        elif self.minio_secure is None:
            self.minio_secure = False
settings = Settings()
