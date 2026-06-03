# -*- coding: utf-8 -*-
# 维护者: 徐岸 <toxuan1998@qq.com>

"""API request/response schemas."""

from pydantic import BaseModel, Field


class PublishedLayer(BaseModel):
    """Published GeoServer layer metadata."""

    layer_name: str = Field(..., description="GeoServer layer name")
    native_layer_name: str = Field(..., description="Native feature layer name in GeoPackage")
    mvt_url: str | None = Field(None, description="MVT vector tile URL")
    raster_url: str | None = Field(None, description="Raster tile URL")
    bbox: list[float] | None = Field(None, description="Layer bbox [minx, miny, maxx, maxy]")


class ConvertResponse(BaseModel):
    """Conversion job response."""

    job_id: str = Field(..., description="Job ID")
    status: str = Field(..., description="pending | converting | publishing | done | error")
    progress: int = Field(0, description="Progress 0-100")
    message: str | None = Field(None, description="Status or error message")
    dxf_path: str | None = None
    gpkg_path: str | None = None
    source_format: str | None = None
    source_path: str | None = None
    layer_name: str | None = None
    layers: list[PublishedLayer] | None = None
    mvt_url: str | None = Field(None, description="MVT vector tile URL")
    raster_url: str | None = Field(None, description="XYZ raster tile URL")
    wmts_url: str | None = Field(None, description="WMTS Capabilities URL")
    bbox: list[float] | None = Field(None, description="Layer bbox [minx, miny, maxx, maxy] EPSG:4326")


class MinioConvertRequest(BaseModel):
    """Request body for converting a source file stored in MinIO."""

    bucket_name: str = Field("atlas-data", description="MinIO bucket name")
    object_name: str = Field(..., description="MinIO object key")
    filename: str | None = Field(None, description="Optional local filename override")
