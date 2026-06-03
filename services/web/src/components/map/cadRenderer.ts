import type maplibregl from 'maplibre-gl'
import type { ConvertResult } from '../../types'
import { VECTOR_SOURCE_ID } from './useMapInstance'
import { getCadSourceLayers } from './types'

export const CAD_FILL_PREFIX = 'cad-fill'
export const CAD_LINE_PREFIX = 'cad-line'
export const CAD_TEXT_PREFIX = 'cad-text'

const buildCadSelectionFilter = (selectedLayers: Set<string>) => {
  const selected = Array.from(selectedLayers)
  if (selected.length === 0) {
    return ['all', ['==', 'Layer', '__never__'], ['==', 'layer', '__never__']]
  }
  return ['any', ['in', 'Layer', ...selected], ['in', 'layer', ...selected]]
}

const combineCadFilter = (baseFilter: any, selectedLayers: Set<string>) => {
  const selectionFilter = buildCadSelectionFilter(selectedLayers)
  return ['all', baseFilter, selectionFilter]
}

export const renderCadVectorLayers = (map: maplibregl.Map, result: ConvertResult) => {
  let mvtUrl = result.mvt_url || ''
  if (mvtUrl.startsWith('/')) {
    mvtUrl = window.location.origin + mvtUrl
  }

  map.addSource(VECTOR_SOURCE_ID, {
    type: 'vector',
    tiles: [mvtUrl],
    scheme: 'xyz'
  })

  getCadSourceLayers(result).forEach((sourceLayer, index) => {
    const suffix = `-${index}`

    map.addLayer({
      id: `${CAD_FILL_PREFIX}${suffix}`,
      type: 'fill',
      source: VECTOR_SOURCE_ID,
      'source-layer': sourceLayer,
      filter: ['==', '$type', 'Polygon'],
      paint: {
        'fill-color': ['coalesce', ['get', 'fill_color'], 'rgba(0,0,0,0)'],
        'fill-opacity': 0.55,
        'fill-outline-color': ['coalesce', ['get', 'line_color'], '#475569']
      }
    })

    map.addLayer({
      id: `${CAD_LINE_PREFIX}${suffix}`,
      type: 'line',
      source: VECTOR_SOURCE_ID,
      'source-layer': sourceLayer,
      filter: ['in', '$type', 'LineString', 'Polygon'],
      paint: {
        'line-color': ['coalesce', ['get', 'line_color'], '#1f2937'],
        'line-width': [
          'case',
          ['has', 'line_width'],
          ['max', ['/', ['to-number', ['get', 'line_width']], 25], 1],
          1.2
        ]
      }
    })

    map.addLayer({
      id: `${CAD_TEXT_PREFIX}${suffix}`,
      type: 'symbol',
      source: VECTOR_SOURCE_ID,
      'source-layer': sourceLayer,
      layout: {
        'text-field': ['coalesce', ['get', 'Text'], ['get', 'text_content']],
        'text-size': ['coalesce', ['to-number', ['get', 'text_size']], 12],
        'text-rotate': ['coalesce', ['get', 'text_angle'], ['get', 'rotation'], 0],
        'text-allow-overlap': false,
        'text-ignore-placement': false,
        'text-rotation-alignment': 'map',
        'text-font': ['Open Sans Regular', 'Arial Unicode MS Regular']
      },
      paint: {
        'text-color': ['coalesce', ['get', 'text_color'], ['get', 'line_color'], '#111827'],
        'text-halo-color': '#ffffff',
        'text-halo-width': 1
      },
      filter: ['any', ['has', 'Text'], ['has', 'text_content']]
    })
  })
}

export const getCadLayerIds = (map: maplibregl.Map) => {
  return (map.getStyle()?.layers || []).map((layer: any) => layer.id as string)
}

export const setCadCandidateVisibility = (map: maplibregl.Map, activeIndexes: Set<number>) => {
  getCadLayerIds(map).forEach((id: string) => {
    const match = id.match(/-(\d+)$/)
    if (!match) return
    const idx = Number(match[1])
    if (!Number.isFinite(idx)) return
    if (
      id.startsWith(CAD_FILL_PREFIX) ||
      id.startsWith(CAD_LINE_PREFIX) ||
      id.startsWith(CAD_TEXT_PREFIX)
    ) {
      map.setLayoutProperty(id, 'visibility', activeIndexes.has(idx) ? 'visible' : 'none')
    }
  })
}

export const updateCadLayerFilters = (map: maplibregl.Map, selectedLayers: Set<string>) => {
  const layerIds = getCadLayerIds(map)

  layerIds
    .filter((id: string) => id.startsWith(CAD_FILL_PREFIX))
    .forEach((id: string) => {
      if (map.getLayer(id)) {
        map.setFilter(id, combineCadFilter(['==', '$type', 'Polygon'], selectedLayers) as any)
      }
    })

  layerIds
    .filter((id: string) => id.startsWith(CAD_LINE_PREFIX))
    .forEach((id: string) => {
      if (map.getLayer(id)) {
        map.setFilter(id, combineCadFilter(['in', '$type', 'LineString', 'Polygon'], selectedLayers) as any)
      }
    })

  layerIds
    .filter((id: string) => id.startsWith(CAD_TEXT_PREFIX))
    .forEach((id: string) => {
      if (map.getLayer(id)) {
        map.setFilter(
          id,
          combineCadFilter(['any', ['has', 'Text'], ['has', 'text_content']], selectedLayers) as any
        )
      }
    })
}
