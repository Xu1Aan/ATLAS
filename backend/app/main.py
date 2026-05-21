# -*- coding: utf-8 -*-
"""Application entrypoint."""
import logging
import shutil
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings

logger = logging.getLogger("dwg2mvt")


def _log_dependency_status() -> None:
    """Log external command availability on startup."""
    for label, command in (
        ("dwg2dxf", settings.dwg2dxf_cmd),
        ("ogr2ogr", settings.ogr2ogr_cmd),
    ):
        resolved = shutil.which(command)
        if resolved:
            logger.info("%s available at %s", label, resolved)
        else:
            logger.warning("%s not found on PATH; configured value=%s", label, command)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logging.basicConfig(level=logging.INFO)
    logger.info("work_dir=%s", settings.work_dir)
    logger.info("geoserver_url=%s", settings.geoserver_url)
    logger.info("geoserver_public_url=%s", settings.geoserver_public_url)
    _log_dependency_status()
    yield


app = FastAPI(
    title="DWG Conversion API",
    description="Upload DWG, convert it to GeoPackage, and publish it to GeoServer.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/")
async def root():
    return {"service": "dwg-to-tiles", "docs": "/docs"}


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
