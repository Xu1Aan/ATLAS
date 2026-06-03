import type maplibregl from 'maplibre-gl'
import type { ConvertResult } from '../../types'
import { VECTOR_SOURCE_ID } from './useMapInstance'
import { getGisPublishedLayers, getGisSourceLayerCandidates, getPublishedLayerDisplayName } from './types'

export const GIS_FILL_PREFIX = 'gis-fill'
export const GIS_LINE_PREFIX = 'gis-line'
export const GIS_POINT_PREFIX = 'gis-point'
export const GIS_TEXT_PREFIX = 'gis-text'

export const renderGisVectorLayers = (map: maplibregl.Map, result: ConvertResult) => {
  let mvtUrl = result.mvt_url || ''
  if (mvtUrl.startsWith('/')) {
    mvtUrl = window.location.origin + mvtUrl
  }

  const publishedLayers = getGisPublishedLayers(result)
  map.addSource(VECTOR_SOURCE_ID, {
    type: 'vector',
    tiles: [mvtUrl],
    scheme: 'xyz'
  })

  publishedLayers.forEach((layer, index) => {
    getGisSourceLayerCandidates(result, layer).forEach((sourceLayer, candidateIndex) => {
      const suffix = `${index}-${candidateIndex}`

      map.addLayer({
        id: `${GIS_FILL_PREFIX}-${suffix}`,
        type: 'fill',
        source: VECTOR_SOURCE_ID,
        'source-layer': sourceLayer,
        filter: ['==', '$type', 'Polygon'],
        paint: {
          'fill-color': '#60a5fa',
          'fill-opacity': 0.35,
          'fill-outline-color': '#2563eb'
        }
      })

      map.addLayer({
        id: `${GIS_LINE_PREFIX}-${suffix}`,
        type: 'line',
        source: VECTOR_SOURCE_ID,
        'source-layer': sourceLayer,
        filter: ['in', '$type', 'LineString', 'Polygon'],
        paint: {
          'line-color': '#2563eb',
          'line-width': 2
        }
      })

      map.addLayer({
        id: `${GIS_POINT_PREFIX}-${suffix}`,
        type: 'circle',
        source: VECTOR_SOURCE_ID,
        'source-layer': sourceLayer,
        filter: ['==', '$type', 'Point'],
        paint: {
          'circle-radius': 5,
          'circle-color': '#ef4444',
          'circle-stroke-color': '#ffffff',
          'circle-stroke-width': 1.5
        }
      })

      map.addLayer({
        id: `${GIS_TEXT_PREFIX}-${suffix}`,
        type: 'symbol',
        source: VECTOR_SOURCE_ID,
        'source-layer': sourceLayer,
        layout: {
          'text-field': ['coalesce', ['get', 'name'], ['get', 'Name'], ['get', 'text_content'], ['get', 'Text']],
          'text-size': 12,
          'text-offset': [0, 1.2],
          'text-anchor': 'top',
          'text-font': ['Open Sans Regular', 'Arial Unicode MS Regular']
        },
        paint: {
          'text-color': '#111827',
          'text-halo-color': '#ffffff',
          'text-halo-width': 1
        },
        filter: ['any', ['has', 'name'], ['has', 'Name'], ['has', 'text_content'], ['has', 'Text']]
      })
    })
  })
}

export const setGisCandidateVisibility = (
  map: maplibregl.Map,
  result: ConvertResult | null,
  activeCandidates: Map<number, Set<number>>
) => {
  const publishedLayers = getGisPublishedLayers(result)
  publishedLayers.forEach((layer, index) => {
    const active = activeCandidates.get(index) ?? new Set<number>()
    getGisSourceLayerCandidates(result, layer).forEach((_, candidateIndex) => {
      const visibility = active.size === 0 || active.has(candidateIndex) ? 'visible' : 'none'
      ;[
        `${GIS_FILL_PREFIX}-${index}-${candidateIndex}`,
        `${GIS_LINE_PREFIX}-${index}-${candidateIndex}`,
        `${GIS_POINT_PREFIX}-${index}-${candidateIndex}`,
        `${GIS_TEXT_PREFIX}-${index}-${candidateIndex}`
      ].forEach((id: string) => {
        if (map.getLayer(id)) {
          map.setLayoutProperty(id, 'visibility', visibility)
        }
      })
    })
  })
}

export const updateGisLayerVisibility = (
  map: maplibregl.Map,
  result: ConvertResult | null,
  selectedLayers: Set<string>
) => {
  const publishedLayers = getGisPublishedLayers(result)
  publishedLayers.forEach((layer, index) => {
    const visible = selectedLayers.has(getPublishedLayerDisplayName(layer))
    const visibility = visible ? 'visible' : 'none'
    getGisSourceLayerCandidates(result, layer).forEach((_, candidateIndex) => {
      ;[
        `${GIS_FILL_PREFIX}-${index}-${candidateIndex}`,
        `${GIS_LINE_PREFIX}-${index}-${candidateIndex}`,
        `${GIS_POINT_PREFIX}-${index}-${candidateIndex}`,
        `${GIS_TEXT_PREFIX}-${index}-${candidateIndex}`
      ].forEach((id: string) => {
        if (map.getLayer(id)) {
          map.setLayoutProperty(id, 'visibility', visibility)
        }
      })
    })
  })
}
