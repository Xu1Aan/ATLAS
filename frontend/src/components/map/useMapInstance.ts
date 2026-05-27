import maplibregl from 'maplibre-gl'

export const VECTOR_SOURCE_ID = 'vector-source'
export const RASTER_SOURCE_ID = 'raster-source'
export const RASTER_LAYER_ID = 'feature-raster'

export const createMapInstance = (container: HTMLElement) => {
  return new maplibregl.Map({
    container,
    style: {
      version: 8,
      glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
      sources: {},
      layers: [
        {
          id: 'background',
          type: 'background',
          paint: {
            'background-color': '#eef2f7'
          }
        }
      ]
    },
    localIdeographFontFamily: "'SimSun', 'SimHei', 'sans-serif'"
  })
}

export const destroyMapInstance = (map: maplibregl.Map | null) => {
  map?.remove()
}

export const fitToBounds = (map: maplibregl.Map | null, bbox?: number[]) => {
  if (!map || !bbox || bbox.length !== 4) return
  const [minX, minY, maxX, maxY] = bbox
  const isValid = (n: number) => Number.isFinite(n) && Math.abs(n) < 1e20
  const isValidLat = (n: number) => n >= -90 && n <= 90

  if (isValid(minX) && isValid(minY) && isValid(maxX) && isValid(maxY) && isValidLat(minY) && isValidLat(maxY)) {
    map.fitBounds(bbox as [number, number, number, number], { padding: 50, animate: false })
  }
}

export const getLayerIdsByPrefixes = (map: maplibregl.Map | null, prefixes: string[]) => {
  if (!map) return []
  return (map.getStyle()?.layers || [])
    .map((layer: any) => layer.id as string)
    .filter((id: string) => prefixes.some(prefix => id.startsWith(prefix)) || id === RASTER_LAYER_ID)
}

export const clearMapArtifacts = (map: maplibregl.Map | null, prefixes: string[]) => {
  if (!map) return

  getLayerIdsByPrefixes(map, prefixes).forEach((id: string) => {
    if (map.getLayer(id)) {
      map.removeLayer(id)
    }
  })

  if (map.getSource(VECTOR_SOURCE_ID)) {
    map.removeSource(VECTOR_SOURCE_ID)
  }
  if (map.getSource(RASTER_SOURCE_ID)) {
    map.removeSource(RASTER_SOURCE_ID)
  }
}
