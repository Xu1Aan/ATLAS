# -*- coding: utf-8 -*-
# 维护者: 徐岸 <toxuan1998@qq.com>

"""Dispatch raster publishing by source format (CAD / KML / SHP)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import httpx

from app.services import geoserver_client as gs
from app.services import shp_raster


@dataclass
class LayerRasterOutcome:
    raster_url: str | None = None
    raster_enabled: bool = False
    raster_style: str | None = None
    raster_message: str | None = None
    missing_columns: list[str] = field(default_factory=list)
    kml_raster_styled: bool = False
    shp_raster_labeled: bool = False
    shp_label_field: str | None = None
    shp_wmts_style: str | None = None
    fatal_error: str | None = None


@dataclass
class RasterPublishState:
    cad_ready: bool = False
    kml_ready: bool = False
    shp_ready: bool = False


def sync_gwc_raster_styles(layer_name: str, outcome: LayerRasterOutcome) -> None:
    """Register raster WMTS styles on GWC after enable_gwc_mvt resets the layer config."""
    if not outcome.raster_enabled:
        return

    if outcome.raster_style == "dwg":
        gs._update_gwc_layer_styles(layer_name, "dwg_raster_style")
        return

    if outcome.raster_style in ("kml", "kml_styled"):
        gs._update_gwc_layer_styles(layer_name, "kml_raster_style")
        if outcome.kml_raster_styled:
            gs._update_gwc_layer_styles(layer_name, "kml_raster_styled")
        return

    if outcome.raster_style in ("shp", "shp_labeled"):
        gs._update_gwc_layer_styles(layer_name, shp_raster.SHP_RASTER_STYLE_NAME)
        if (
            outcome.shp_wmts_style
            and outcome.shp_wmts_style != shp_raster.SHP_RASTER_STYLE_NAME
        ):
            gs._update_gwc_layer_styles(layer_name, outcome.shp_wmts_style)


def resolve_layer_raster_url(
    gpkg_path: Path,
    native_layer_name: str,
    layer_name: str,
    source_format: str | None = None,
    *,
    kml_raster_styled: bool = False,
    shp_raster_labeled: bool = False,
    shp_wmts_style: str | None = None,
) -> str | None:
    cad_ok, _ = gs.get_raster_style_compatibility(gpkg_path, native_layer_name)
    if cad_ok:
        return gs.get_raster_url_v2(layer_name)

    if source_format == "kml":
        kml_ok, _ = gs.get_kml_raster_style_compatibility(gpkg_path, native_layer_name)
        if kml_ok:
            return gs.get_kml_raster_url(layer_name, styled=kml_raster_styled)

    if source_format == "shp_zip":
        shp_ok, _ = shp_raster.get_shp_raster_style_compatibility(gpkg_path, native_layer_name)
        if shp_ok:
            return shp_raster.resolve_shp_raster_url(
                layer_name,
                shp_raster_labeled=shp_raster_labeled,
                shp_wmts_style=shp_wmts_style or shp_raster.SHP_RASTER_STYLE_NAME,
            )
    return None


def setup_layer_raster(
    source_format: str | None,
    client: httpx.Client,
    ws: str,
    store_name: str,
    layer_name: str,
    native_name: str,
    headers: dict,
    gpkg_path: Path,
    state: RasterPublishState,
) -> LayerRasterOutcome:
    raster_enabled, missing_columns = gs.get_raster_style_compatibility(gpkg_path, native_name)
    if raster_enabled:
        if not state.cad_ready:
            ok_style, msg_style = gs.ensure_dwg_raster_style()
            if not ok_style:
                return LayerRasterOutcome(
                    fatal_error=f"Raster style creation failed: {msg_style}",
                    missing_columns=missing_columns,
                )
            state.cad_ready = True

        ok_attach, msg_attach = gs.add_raster_style_to_layer(layer_name)
        if not ok_attach:
            return LayerRasterOutcome(
                fatal_error=f"Attach raster style failed for {layer_name}: {msg_attach}",
                missing_columns=missing_columns,
            )
        return LayerRasterOutcome(
            raster_url=gs.get_raster_url_v2(layer_name),
            raster_enabled=True,
            raster_style="dwg",
            missing_columns=[],
        )

    if source_format == "kml":
        return _setup_kml_raster(
            client,
            ws,
            store_name,
            layer_name,
            native_name,
            headers,
            gpkg_path,
            state,
            missing_columns,
        )

    if source_format == "shp_zip":
        return _setup_shp_raster(
            client,
            ws,
            store_name,
            layer_name,
            native_name,
            headers,
            gpkg_path,
            state,
            missing_columns,
        )

    return LayerRasterOutcome(
        raster_message="未启用栅格样式，缺少字段: " + ", ".join(missing_columns),
        missing_columns=missing_columns,
    )


def _setup_kml_raster(
    client: httpx.Client,
    ws: str,
    store_name: str,
    layer_name: str,
    native_name: str,
    headers: dict,
    gpkg_path: Path,
    state: RasterPublishState,
    missing_columns: list[str],
) -> LayerRasterOutcome:
    kml_ok, kml_missing = gs.get_kml_raster_style_compatibility(gpkg_path, native_name)
    if not kml_ok:
        return LayerRasterOutcome(
            raster_message="未启用 KML 栅格样式，缺少: " + ", ".join(kml_missing),
            missing_columns=missing_columns,
        )

    gs._recalculate_featuretype_attributes(client, ws, store_name, layer_name, headers)
    gs_attributes = gs._get_featuretype_attribute_names(client, ws, store_name, layer_name, headers)
    use_styled = gs._kml_layer_use_styled_raster(gpkg_path, native_name, gs_attributes)

    if not state.kml_ready:
        ok_kml_style, msg_kml_style = gs.ensure_kml_raster_style()
        if not ok_kml_style:
            return LayerRasterOutcome(
                fatal_error=f"KML raster style creation failed: {msg_kml_style}",
                missing_columns=missing_columns,
            )
        state.kml_ready = True

    ok_kml_attach, msg_kml_attach = gs.add_kml_raster_style_to_layer(layer_name, use_styled=use_styled)
    if not ok_kml_attach:
        return LayerRasterOutcome(
            fatal_error=f"Attach KML raster style failed for {layer_name}: {msg_kml_attach}",
            missing_columns=missing_columns,
        )

    return LayerRasterOutcome(
        raster_url=gs.get_kml_raster_url(layer_name, styled=use_styled),
        raster_enabled=True,
        raster_style="kml_styled" if use_styled else "kml",
        missing_columns=[],
        kml_raster_styled=use_styled,
    )


def _setup_shp_raster(
    client: httpx.Client,
    ws: str,
    store_name: str,
    layer_name: str,
    native_name: str,
    headers: dict,
    gpkg_path: Path,
    state: RasterPublishState,
    missing_columns: list[str],
) -> LayerRasterOutcome:
    plan, state.shp_ready = shp_raster.publish_shp_layer_raster(
        client,
        ws,
        store_name,
        layer_name,
        native_name,
        headers,
        gpkg_path,
        shp_style_ready=state.shp_ready,
    )
    return LayerRasterOutcome(
        raster_url=plan.raster_url,
        raster_enabled=plan.raster_enabled,
        raster_style=plan.raster_style,
        raster_message=plan.raster_message,
        missing_columns=missing_columns if not plan.raster_enabled else [],
        shp_raster_labeled=plan.shp_raster_labeled,
        shp_label_field=plan.shp_label_field,
        shp_wmts_style=plan.shp_wmts_style,
        fatal_error=plan.fatal_error,
    )
