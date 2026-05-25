# -*- coding: utf-8 -*-
"""Application settings for local and container deployments."""
from pathlib import Path

from pydantic_settings import BaseSettings


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
    geoserver_public_url: str = "http://10.20.124.71:18081/geoserver"

    class Config:
        env_prefix = "APP_"
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.work_dir = Path(self.work_dir).resolve()
        self.work_dir.mkdir(parents=True, exist_ok=True)
settings = Settings()
