# -*- coding: utf-8 -*-
# 维护者: 徐岸 <toxuan1998@qq.com>
"""ATLAS API entrypoint."""
import logging
import shutil
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.meta import (
    AUTHOR_EMAIL,
    AUTHOR_NAME,
    MAINTAINER,
    PROJECT_NAME,
    maintainer_contact,
)

logger = logging.getLogger("atlas.api")

_API_DESCRIPTION = (
    "Convert CAD/GIS sources to GeoPackage and publish map services via GeoServer.\n\n"
    f"Maintainer: {maintainer_contact()}"
)


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
    logger.info("maintainer=%s", maintainer_contact())
    logger.info("work_dir=%s", settings.work_dir)
    logger.info("geoserver_url=%s", settings.geoserver_url)
    logger.info("geoserver_public_url=%s", settings.geoserver_public_url)
    logger.info("minio_endpoint=%s", settings.minio_endpoint)
    logger.info("minio_secure=%s", settings.minio_secure)
    logger.info("minio_path_style=%s", settings.minio_path_style)
    logger.info(
        "minio_credentials_configured access_key=%s secret_key=%s",
        bool(settings.minio_access_key),
        bool(settings.minio_secret_key),
    )
    _log_dependency_status()
    yield


app = FastAPI(
    title=f"{PROJECT_NAME} Conversion API",
    description=_API_DESCRIPTION,
    contact={
        "name": AUTHOR_NAME,
        "email": AUTHOR_EMAIL,
    },
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
    return {
        "service": "atlas",
        "maintainer": MAINTAINER,
        "docs": "/docs",
    }


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/actuator/health")
async def actuator_health():
    return {"status": "UP"}


@app.get("/actuator/health/liveness")
async def actuator_liveness():
    return {"status": "UP"}


@app.get("/actuator/health/readiness")
async def actuator_readiness():
    return {"status": "UP"}
