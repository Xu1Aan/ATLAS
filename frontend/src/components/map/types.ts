import type { ConvertResult, PublishedLayer } from '../../types'

export type LayerListKind = 'cad-layer' | 'published-layer'

export type LayerListItem = {
  name: string
  color: string
  kind: LayerListKind
}

export type MapMode = 'vector' | 'raster'

export const isCadFormat = (sourceFormat?: string) => sourceFormat === 'dwg' || sourceFormat === 'dxf'

export const getCadSourceLayers = (result: ConvertResult) => {
  return Array.from(new Set([
    'entities',
    result.layer_name
  ].filter((value): value is string => Boolean(value))))
}

export const getPublishedLayerDisplayName = (layer: PublishedLayer) => {
  return layer.native_layer_name || layer.layer_name
}

export const getGisSourceLayerCandidates = (result: ConvertResult | null, layer: PublishedLayer) => {
  if (!result) return []
  return Array.from(new Set([
    layer.layer_name,
    layer.native_layer_name,
    result.layer_name
  ].filter((value): value is string => Boolean(value))))
}

export const getGisPublishedLayers = (result: ConvertResult | null): PublishedLayer[] => {
  if (!result) return []
  if (result.layers?.length) {
    return result.layers
  }
  if (result.layer_name) {
    return [{
      layer_name: result.layer_name,
      native_layer_name: result.layer_name,
      mvt_url: result.mvt_url,
      raster_url: result.raster_url,
      bbox: result.bbox
    }]
  }
  return []
}

export const devLog = (...args: unknown[]) => {
  if (import.meta.env.DEV) {
    console.log('[map]', ...args)
  }
}
