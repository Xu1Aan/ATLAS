# -*- coding: utf-8 -*-
# 维护者: 徐岸 <toxuan1998@qq.com>

"""ATLAS runtime settings."""
from pathlib import Path
from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict

_API_DIR = Path(__file__).resolve().parent.parent
_ROOT_DIR = _API_DIR.parent.parent


def _resolve_env_files() -> tuple[str, ...]:
    files: list[Path] = []
    root_env = _ROOT_DIR / ".env"
    if root_env.exists():
        files.append(root_env)
    local_env = _API_DIR / ".env"
    if local_env.exists():
        files.append(local_env)
    return tuple(str(path) for path in files)


class Settings(BaseSettings):
    """Runtime settings."""

    work_dir: Path = Path("./data")
    dwg2dxf_cmd: str = "dwg2dxf"
    ogr2ogr_cmd: str = "ogr2ogr"
    target_srs: str = "EPSG:4326"
    gauss_kruger_zone: int | None = None
    enable_gauss_kruger_transform: bool = True
    geoserver_url: str = "http://geoserver:8080/geoserver"
    geoserver_user: str = "admin"
    geoserver_password: str = "geoserver"
    geoserver_workspace: str = "atlas"
    geoserver_public_url: str = "http://localhost:18081/geoserver"
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_secure: bool | None = None
    minio_region: str | None = None
    minio_path_style: bool = True

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=_resolve_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def model_post_init(self, __context) -> None:
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
