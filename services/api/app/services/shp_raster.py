# -*- coding: utf-8 -*-
# 维护者: 徐岸 <toxuan1998@qq.com>

"""SHP/SHP-ZIP raster tile publishing (isolated from KML/CAD raster code)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

import httpx

from app.config import settings
from app.services.geoserver_client import (
    _auth_headers,
    _build_raster_wmts_url,
    _get_featuretype_attribute_names,
    _get_gpkg_layer_columns,
    _recalculate_featuretype_attributes,
    _rest,
    _update_gwc_layer_styles,
    _upsert_workspace_style,
)

SHP_RASTER_STYLE_NAME = "shp_raster_style"
SHP_LABEL_FIELD_CANDIDATES = (
    "NAME",
    "Name",
    "name",
    "LABEL",
    "Label",
    "label",
    "MC",
    "名称",
    "FID",
    "ID",
    "id",
)

SHP_RASTER_SLD_BASE = """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0"
    xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd"
    xmlns="http://www.opengis.net/sld"
    xmlns:ogc="http://www.opengis.net/ogc"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <NamedLayer>
    <Name>shp_raster_style</Name>
    <UserStyle>
      <Title>SHP Raster Style</Title>
      <FeatureTypeStyle>
        <Rule>
          <Name>Polygon</Name>
          <Filter>
            <Or>
              <PropertyIsEqualTo>
                <Function name="geometryType"><PropertyName>geom</PropertyName></Function>
                <Literal>Polygon</Literal>
              </PropertyIsEqualTo>
              <PropertyIsEqualTo>
                <Function name="geometryType"><PropertyName>geom</PropertyName></Function>
                <Literal>MultiPolygon</Literal>
              </PropertyIsEqualTo>
            </Or>
          </Filter>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">#2e7d32</CssParameter>
              <CssParameter name="fill-opacity">0.3</CssParameter>
            </Fill>
            <Stroke>
              <CssParameter name="stroke">#1b5e20</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Line</Name>
          <Filter>
            <Or>
              <PropertyIsEqualTo>
                <Function name="geometryType"><PropertyName>geom</PropertyName></Function>
                <Literal>LineString</Literal>
              </PropertyIsEqualTo>
              <PropertyIsEqualTo>
                <Function name="geometryType"><PropertyName>geom</PropertyName></Function>
                <Literal>MultiLineString</Literal>
              </PropertyIsEqualTo>
            </Or>
          </Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#6a1b9a</CssParameter>
              <CssParameter name="stroke-width">2</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Point</Name>
          <Filter>
            <Or>
              <PropertyIsEqualTo>
                <Function name="geometryType"><PropertyName>geom</PropertyName></Function>
                <Literal>Point</Literal>
              </PropertyIsEqualTo>
              <PropertyIsEqualTo>
                <Function name="geometryType"><PropertyName>geom</PropertyName></Function>
                <Literal>MultiPoint</Literal>
              </PropertyIsEqualTo>
            </Or>
          </Filter>
          <PointSymbolizer>
            <Graphic>
              <Mark>
                <WellKnownName>circle</WellKnownName>
                <Fill><CssParameter name="fill">#f57c00</CssParameter></Fill>
                <Stroke>
                  <CssParameter name="stroke">#ffffff</CssParameter>
                  <CssParameter name="stroke-width">0.5</CssParameter>
                </Stroke>
              </Mark>
              <Size>8</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
"""


def _labeled_style_name(layer_name: str) -> str:
    token = "".join(ch if ch.isalnum() else "_" for ch in layer_name).strip("_")
    return f"shp_lbl_{token}"[:80]


def build_shp_labeled_raster_sld(label_field: str, style_name: str) -> str:
    field_xml = escape(label_field)
    style_xml = escape(style_name)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0"
    xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd"
    xmlns="http://www.opengis.net/sld"
    xmlns:ogc="http://www.opengis.net/ogc"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <NamedLayer>
    <Name>{style_xml}</Name>
    <UserStyle>
      <Title>SHP Labeled Raster</Title>
      <FeatureTypeStyle>
        <Rule>
          <Name>Polygon</Name>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">#2e7d32</CssParameter>
              <CssParameter name="fill-opacity">0.3</CssParameter>
            </Fill>
            <Stroke>
              <CssParameter name="stroke">#1b5e20</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Line</Name>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#6a1b9a</CssParameter>
              <CssParameter name="stroke-width">2</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Point</Name>
          <PointSymbolizer>
            <Graphic>
              <Mark>
                <WellKnownName>circle</WellKnownName>
                <Fill><CssParameter name="fill">#f57c00</CssParameter></Fill>
              </Mark>
              <Size>8</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
        <Rule>
          <Name>Label</Name>
          <Filter>
            <PropertyIsNotEqualTo>
              <PropertyName>{field_xml}</PropertyName>
              <Literal></Literal>
            </PropertyIsNotEqualTo>
          </Filter>
          <TextSymbolizer uom="http://www.opengeospatial.org/se/units/metre">
            <Label><PropertyName>{field_xml}</PropertyName></Label>
            <Font>
              <CssParameter name="font-family">Microsoft YaHei, SimSun, Arial, sans-serif</CssParameter>
              <CssParameter name="font-size">2.5</CssParameter>
            </Font>
            <Fill><CssParameter name="fill">#212121</CssParameter></Fill>
            <VendorOption name="maxDisplacement">200</VendorOption>
            <VendorOption name="partials">true</VendorOption>
          </TextSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
"""


@dataclass
class ShpRasterPlan:
    raster_url: str | None
    raster_enabled: bool
    raster_style: str | None
    raster_message: str | None
    shp_raster_labeled: bool = False
    shp_label_field: str | None = None
    shp_wmts_style: str = SHP_RASTER_STYLE_NAME
    fatal_error: str | None = None


def get_shp_raster_style_compatibility(gpkg_path: Path, table_name: str) -> tuple[bool, list[str]]:
    columns = _get_gpkg_layer_columns(gpkg_path, table_name)
    if not columns:
        return False, ["table"]
    if not (columns & {"geom", "GEOMETRY", "geometry"}):
        return False, ["geom"]
    return True, []


def pick_shp_label_field(gpkg_columns: set[str], geoserver_attributes: set[str]) -> str | None:
    shared = gpkg_columns & geoserver_attributes
    for candidate in SHP_LABEL_FIELD_CANDIDATES:
        if candidate in shared:
            return candidate
    return None


def ensure_shp_raster_style() -> tuple[bool, str]:
    return _upsert_workspace_style(SHP_RASTER_STYLE_NAME, SHP_RASTER_SLD_BASE)


def ensure_shp_labeled_style(layer_name: str, label_field: str) -> tuple[bool, str, str]:
    style_name = _labeled_style_name(layer_name)
    sld_body = build_shp_labeled_raster_sld(label_field, style_name)
    ok, msg = _upsert_workspace_style(style_name, sld_body)
    return ok, msg, style_name


def get_shp_raster_url(layer_name: str, wmts_style: str = SHP_RASTER_STYLE_NAME) -> str:
    return _build_raster_wmts_url(layer_name, wmts_style)


def resolve_shp_raster_url(
    layer_name: str,
    *,
    shp_raster_labeled: bool = False,
    shp_wmts_style: str = SHP_RASTER_STYLE_NAME,
) -> str | None:
    if shp_raster_labeled and shp_wmts_style != SHP_RASTER_STYLE_NAME:
        return get_shp_raster_url(layer_name, wmts_style=shp_wmts_style)
    return get_shp_raster_url(layer_name)


def add_shp_raster_styles_to_layer(
    layer_name: str,
    *,
    labeled_style_name: str | None = None,
) -> tuple[bool, str]:
    ws = settings.geoserver_workspace
    base = settings.geoserver_url.rstrip("/")

    ok, msg = ensure_shp_raster_style()
    if not ok:
        return False, msg

    style_entries = [
        {"name": "dwg_generic_style", "workspace": ws},
        {"name": SHP_RASTER_STYLE_NAME, "workspace": ws},
    ]
    if labeled_style_name:
        style_entries.append({"name": labeled_style_name, "workspace": ws})

    layer_url = f"{base}/rest/workspaces/{ws}/layers/{layer_name}.json"
    with httpx.Client(timeout=30.0) as client:
        headers = {**_auth_headers(), "Content-Type": "application/json"}
        body = {"layer": {"styles": {"style": style_entries}}}
        response = client.put(layer_url, headers=headers, json=body)
        if response.status_code != 200:
            return False, f"Update SHP layer styles failed: {response.status_code} {response.text[:200]}"

    _update_gwc_layer_styles(layer_name, SHP_RASTER_STYLE_NAME)
    if labeled_style_name:
        _update_gwc_layer_styles(layer_name, labeled_style_name)
    return True, ""


def publish_shp_layer_raster(
    client: httpx.Client,
    ws: str,
    store_name: str,
    layer_name: str,
    native_name: str,
    headers: dict,
    gpkg_path: Path,
    *,
    shp_style_ready: bool,
) -> tuple[ShpRasterPlan, bool]:
    """Publish raster tiles for one SHP feature layer."""
    ok, missing = get_shp_raster_style_compatibility(gpkg_path, native_name)
    if not ok:
        return (
            ShpRasterPlan(
                raster_url=None,
                raster_enabled=False,
                raster_style=None,
                raster_message="未启用 SHP 栅格样式，缺少: " + ", ".join(missing),
            ),
            shp_style_ready,
        )

    _recalculate_featuretype_attributes(client, ws, store_name, layer_name, headers)
    gs_attributes = _get_featuretype_attribute_names(client, ws, store_name, layer_name, headers)
    gpkg_columns = _get_gpkg_layer_columns(gpkg_path, native_name)
    label_field = pick_shp_label_field(gpkg_columns, gs_attributes)

    labeled_style_name = None
    wmts_style = SHP_RASTER_STYLE_NAME
    if label_field:
        ok_lbl, msg_lbl, labeled_style_name = ensure_shp_labeled_style(layer_name, label_field)
        if not ok_lbl:
            return (
                ShpRasterPlan(
                    raster_url=None,
                    raster_enabled=False,
                    raster_style=None,
                    fatal_error=f"SHP 标注栅格样式失败: {msg_lbl}",
                ),
                shp_style_ready,
            )
        wmts_style = labeled_style_name

    if not shp_style_ready:
        ok_base, msg_base = ensure_shp_raster_style()
        if not ok_base:
            return (
                ShpRasterPlan(
                    raster_url=None,
                    raster_enabled=False,
                    raster_style=None,
                    fatal_error=f"SHP 栅格样式失败: {msg_base}",
                ),
                shp_style_ready,
            )
        shp_style_ready = True

    ok_attach, msg_attach = add_shp_raster_styles_to_layer(
        layer_name,
        labeled_style_name=labeled_style_name,
    )
    if not ok_attach:
        return (
            ShpRasterPlan(
                raster_url=None,
                raster_enabled=False,
                raster_style=None,
                fatal_error=f"挂载 SHP 栅格样式失败: {msg_attach}",
            ),
            shp_style_ready,
        )

    use_labeled = labeled_style_name is not None
    return (
        ShpRasterPlan(
            raster_url=get_shp_raster_url(layer_name, wmts_style=wmts_style),
            raster_enabled=True,
            raster_style="shp_labeled" if use_labeled else "shp",
            raster_message=None,
            shp_raster_labeled=use_labeled,
            shp_label_field=label_field,
            shp_wmts_style=wmts_style,
        ),
        shp_style_ready,
    )
