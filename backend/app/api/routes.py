# -*- coding: utf-8 -*-
"""Upload, convert, publish, and query conversion jobs."""

import json
import re
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import settings
from app.models.schemas import ConvertResponse
from app.services import conversion
from app.services import geoserver_client as gs

router = APIRouter(prefix="/api", tags=["convert"])

SUPPORTED_EXTENSIONS = {
    ".dwg": "dwg",
    ".dxf": "dxf",
    ".kml": "kml",
    ".zip": "shp_zip",
}

_jobs: dict[str, dict] = {}


def _job_dir(job_id: str) -> Path:
    return settings.work_dir / "jobs" / job_id


def _job_metadata_path(job_dir: Path) -> Path:
    return job_dir / "job.json"


def _find_job_artifact(job_dir: Path, pattern: str) -> Path | None:
    matches = sorted(job_dir.glob(pattern))
    return matches[0] if matches else None


def _first_supported_source(job_dir: Path) -> Path | None:
    for ext in SUPPORTED_EXTENSIONS:
        path = _find_job_artifact(job_dir, f"*{ext}")
        if path:
            return path
    return None


def _safe_layer_token(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return token[:40] or "layer"


def _layer_name_for(job_id: str, native_layer_name: str, index: int) -> str:
    if index == 0:
        return f"layer_{job_id}"
    return f"layer_{job_id}_{index}_{_safe_layer_token(native_layer_name)}"


def _persist_job(job_id: str) -> None:
    job = _jobs.get(job_id)
    if not job:
        return

    job_dir = _job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    metadata = dict(job)
    metadata["job_id"] = job_id
    _job_metadata_path(job_dir).write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _load_job(job_id: str) -> dict | None:
    if job_id in _jobs:
        return _jobs[job_id]

    job_dir = _job_dir(job_id)
    meta_path = _job_metadata_path(job_dir)
    if meta_path.exists():
        try:
            job = json.loads(meta_path.read_text(encoding="utf-8"))
            _jobs[job_id] = job
            return job
        except Exception:
            pass

    if not job_dir.exists():
        return None

    source_path = _first_supported_source(job_dir)
    gpkg_path = _find_job_artifact(job_dir, "*.gpkg")
    dxf_path = _find_job_artifact(job_dir, "*.dxf")
    if not source_path:
        return None

    source_format = SUPPORTED_EXTENSIONS.get(source_path.suffix.lower())
    layers = None
    primary_layer_name = None
    primary_bbox = None
    if gpkg_path and gpkg_path.exists():
        native_layers = conversion.get_gpkg_feature_layers(gpkg_path)
        layers = []
        for index, native_layer_name in enumerate(native_layers):
            layer_name = _layer_name_for(job_id, native_layer_name, index)
            ok_bbox, bbox = conversion.get_gpkg_bbox(gpkg_path, native_layer_name)
            layer_info = {
                "layer_name": layer_name,
                "native_layer_name": native_layer_name,
                "mvt_url": gs.get_mvt_url(layer_name),
                "raster_url": gs.get_raster_url_v2(layer_name),
                "bbox": bbox if ok_bbox else None,
            }
            layers.append(layer_info)
            if index == 0:
                primary_layer_name = layer_name
                primary_bbox = layer_info["bbox"]

    job = {
        "status": "done" if gpkg_path and gpkg_path.exists() else "error",
        "progress": 100 if gpkg_path and gpkg_path.exists() else 0,
        "message": "Loaded from disk",
        "original_filename": source_path.name,
        "source_format": source_format,
        "source_path": str(source_path),
        "dxf_path": str(dxf_path) if dxf_path else None,
        "gpkg_path": str(gpkg_path) if gpkg_path else None,
        "layer_name": primary_layer_name,
        "layers": layers,
        "mvt_url": gs.get_mvt_url(primary_layer_name) if primary_layer_name else None,
        "raster_url": gs.get_raster_url_v2(primary_layer_name) if primary_layer_name else None,
        "wmts_url": gs.get_wmts_capabilities_url() if primary_layer_name else None,
        "bbox": primary_bbox,
    }
    _jobs[job_id] = job
    _persist_job(job_id)
    return job


def _job_response(job_id: str) -> ConvertResponse:
    job = _load_job(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")

    return ConvertResponse(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress", 0),
        message=job.get("message"),
        dxf_path=job.get("dxf_path"),
        gpkg_path=job.get("gpkg_path"),
        source_format=job.get("source_format"),
        source_path=job.get("source_path"),
        layer_name=job.get("layer_name"),
        layers=job.get("layers"),
        mvt_url=job.get("mvt_url"),
        raster_url=job.get("raster_url"),
        wmts_url=job.get("wmts_url"),
        bbox=job.get("bbox"),
    )


def _update_job(job_id: str, **values) -> None:
    if job_id not in _jobs:
        return
    _jobs[job_id].update(values)
    _persist_job(job_id)


def _convert_source_to_gpkg(source_format: str, source_path: Path, job_dir: Path, progress_callback=None):
    converters = {
        "dwg": conversion.convert_dwg_to_gpkg,
        "dxf": conversion.convert_dxf_to_gpkg,
        "kml": conversion.convert_kml_to_gpkg,
        "shp_zip": conversion.convert_shp_zip_to_gpkg,
    }
    return converters[source_format](source_path, job_dir, progress_callback=progress_callback)


def process_conversion_task(job_id: str, source_path: Path, job_dir: Path, original_filename: str, source_format: str):
    """Background conversion and GeoServer publishing."""

    def update_progress(percent: int, msg: str):
        _update_job(job_id, progress=percent, message=msg)

    try:
        ok, gpkg_path, err = _convert_source_to_gpkg(source_format, source_path, job_dir, progress_callback=update_progress)
        if not ok or not gpkg_path:
            _update_job(job_id, status="error", message=err, progress=0)
            return

        dxf_path = _find_job_artifact(job_dir, "*.dxf")
        _update_job(
            job_id,
            dxf_path=str(dxf_path) if dxf_path else None,
            gpkg_path=str(gpkg_path),
            status="publishing",
            message="正在发布到 GeoServer",
            progress=95,
        )

        native_layers = conversion.get_gpkg_feature_layers(gpkg_path)
        if not native_layers:
            _update_job(job_id, status="error", message="GeoPackage 中没有可发布的要素图层", progress=0)
            return

        ok_ws, ws_err = gs.ensure_workspace()
        if not ok_ws:
            _update_job(job_id, status="error", message=f"GeoServer 不可用: {ws_err}", progress=0)
            return

        layer_specs = [
            {
                "layer_name": _layer_name_for(job_id, native_layer_name, index),
                "native_layer_name": native_layer_name,
            }
            for index, native_layer_name in enumerate(native_layers)
        ]
        ok_pub, published_layers, pub_err = gs.publish_gpkg_layers(gpkg_path, f"job_{job_id}", layer_specs)
        if not ok_pub:
            _update_job(job_id, status="error", message=f"GeoServer 发布失败: {pub_err}", progress=0)
            return

        primary_layer = published_layers[0]
        primary_bbox = primary_layer.get("bbox")
        if not primary_bbox:
            ok_bbox, bbox = conversion.get_gpkg_bbox(gpkg_path, primary_layer["native_layer_name"])
            primary_bbox = bbox if ok_bbox else None

        _update_job(
            job_id,
            status="done",
            message="转换并发布完成",
            progress=100,
            layer_name=primary_layer["layer_name"],
            layers=published_layers,
            mvt_url=primary_layer.get("mvt_url"),
            raster_url=primary_layer.get("raster_url"),
            wmts_url=gs.get_wmts_capabilities_url(),
            bbox=primary_bbox,
        )
    except Exception as e:
        _update_job(job_id, status="error", message=f"服务器错误: {e}", progress=0)


@router.get("/jobs", response_model=list[dict])
async def list_jobs():
    """List all uploaded jobs."""
    jobs_list = []
    jobs_dir = settings.work_dir / "jobs"
    if not jobs_dir.exists():
        return []

    for job_dir in jobs_dir.iterdir():
        if not job_dir.is_dir():
            continue
        job_id = job_dir.name
        job = _load_job(job_id)
        source_path = _first_supported_source(job_dir)
        if not job or not source_path:
            continue
        jobs_list.append(
            {
                "job_id": job_id,
                "filename": job.get("original_filename", source_path.name),
                "status": job.get("status", "error"),
                "progress": job.get("progress", 0),
                "message": job.get("message", ""),
                "created_at": job_dir.stat().st_mtime,
            }
        )

    jobs_list.sort(key=lambda x: x["created_at"], reverse=True)
    return jobs_list


@router.post("/convert", response_model=ConvertResponse)
def upload_and_convert(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload a supported file, convert it to GeoPackage, and publish it to GeoServer."""
    if not file.filename:
        raise HTTPException(400, "请选择要上传的文件")

    suffix = Path(file.filename).suffix.lower()
    source_format = SUPPORTED_EXTENSIONS.get(suffix)
    if not source_format:
        raise HTTPException(400, "仅支持 DWG / DXF / SHP(zip) / KML 文件")

    job_id = uuid.uuid4().hex
    job_dir = _job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    source_path = job_dir / file.filename

    try:
        with source_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        _jobs[job_id] = {"status": "error", "message": str(e), "progress": 0}
        _persist_job(job_id)
        return _job_response(job_id)

    start_message = {
        "dwg": "正在转换 DWG → DXF → GeoPackage",
        "dxf": "正在转换 DXF → GeoPackage",
        "kml": "正在转换 KML → GeoPackage",
        "shp_zip": "正在解压 SHP(zip) → GeoPackage",
    }[source_format]

    _jobs[job_id] = {
        "status": "converting",
        "message": start_message,
        "progress": 0,
        "original_filename": file.filename,
        "source_format": source_format,
        "source_path": str(source_path),
        "dxf_path": None,
        "gpkg_path": None,
        "layer_name": None,
        "layers": None,
        "mvt_url": None,
        "raster_url": None,
        "wmts_url": None,
        "bbox": None,
    }
    _persist_job(job_id)

    if background_tasks:
        background_tasks.add_task(process_conversion_task, job_id, source_path, job_dir, file.filename, source_format)
    else:
        process_conversion_task(job_id, source_path, job_dir, file.filename, source_format)

    return _job_response(job_id)


@router.get("/convert/{job_id}", response_model=ConvertResponse)
async def get_convert_status(job_id: str):
    return _job_response(job_id)


@router.get("/status/{job_id}", response_model=ConvertResponse)
async def get_status(job_id: str):
    return _job_response(job_id)


@router.get("/layers/{job_id}", response_model=list[dict])
async def get_job_layers(job_id: str):
    gpkg_path = None
    job = _load_job(job_id)
    if job and job.get("gpkg_path"):
        gpkg_path = Path(job["gpkg_path"])

    if not gpkg_path:
        gpkg_path = _find_job_artifact(_job_dir(job_id), "*.gpkg")

    if not gpkg_path or not gpkg_path.exists():
        raise HTTPException(404, "GeoPackage file not found")

    return conversion.get_gpkg_layers(gpkg_path)


@router.get("/convert/{job_id}/gpkg")
async def download_gpkg(job_id: str):
    gpkg_path = None
    job = _load_job(job_id)
    if job and job.get("gpkg_path"):
        gpkg_path = Path(job["gpkg_path"])

    if not gpkg_path:
        gpkg_path = _find_job_artifact(_job_dir(job_id), "*.gpkg")

    if not gpkg_path or not gpkg_path.exists():
        raise HTTPException(404, "GPKG 文件不存在")

    return FileResponse(gpkg_path, filename=gpkg_path.name, media_type="application/geopackage+sqlite3")
