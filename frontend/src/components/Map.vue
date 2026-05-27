<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { ConvertResult } from '../types'
import { API_BASE } from '../config'
import LayerSidebar from './map/LayerSidebar.vue'
import { CAD_FILL_PREFIX, CAD_LINE_PREFIX, CAD_TEXT_PREFIX, renderCadVectorLayers, setCadCandidateVisibility, updateCadLayerFilters } from './map/cadRenderer'
import { GIS_FILL_PREFIX, GIS_LINE_PREFIX, GIS_POINT_PREFIX, GIS_TEXT_PREFIX, renderGisVectorLayers, setGisCandidateVisibility, updateGisLayerVisibility } from './map/gisRenderer'
import { devLog, getCadSourceLayers, getGisPublishedLayers, getGisSourceLayerCandidates, getPublishedLayerDisplayName, isCadFormat, type LayerListItem, type MapMode } from './map/types'
import { clearMapArtifacts, createMapInstance, destroyMapInstance, fitToBounds, RASTER_LAYER_ID, RASTER_SOURCE_ID, VECTOR_SOURCE_ID } from './map/useMapInstance'

const props = defineProps<{
  result: ConvertResult | null
}>()

const mapContainer = ref<HTMLElement | null>(null)
const map = ref<any>(null)
const mapLoaded = ref(false)
const sidebarLayers = ref<LayerListItem[]>([])
const selectedLayers = ref<Set<string>>(new Set())
const isLayerListCollapsed = ref(false)
const mouseCoords = ref<[number, number] | null>(null)
const overlayMessage = ref('请先上传数据文件')
const mapMode = ref<MapMode>('vector')

const clearRenderedLayers = () => {
  clearMapArtifacts(map.value, [
    CAD_FILL_PREFIX,
    CAD_LINE_PREFIX,
    CAD_TEXT_PREFIX,
    GIS_FILL_PREFIX,
    GIS_LINE_PREFIX,
    GIS_POINT_PREFIX,
    GIS_TEXT_PREFIX
  ])
}

const buildSidebarLayers = (result: ConvertResult, fetchedLayers: any[] = []): LayerListItem[] => {
  if (isCadFormat(result.source_format)) {
    return fetchedLayers.map((item: any) => ({
      name: item.name,
      color: item.color || '#9ca3af',
      kind: 'cad-layer'
    }))
  }

  const published = getGisPublishedLayers(result)
  if (published.length > 0) {
    return published.map(layer => ({
      name: getPublishedLayerDisplayName(layer),
      color: '#2563eb',
      kind: 'published-layer'
    }))
  }

  return fetchedLayers.map((item: any) => ({
    name: item.name,
    color: item.color || '#2563eb',
    kind: 'published-layer'
  }))
}

const updateMapControls = () => {
  const mapInstance = map.value
  const result = props.result
  if (!mapInstance || !result || !mapLoaded.value || mapMode.value !== 'vector') return

  if (isCadFormat(result.source_format)) {
    updateCadLayerFilters(mapInstance, selectedLayers.value)
  } else {
    updateGisLayerVisibility(mapInstance, result, selectedLayers.value)
  }
}

const renderRasterLayer = () => {
  const mapInstance = map.value
  const result = props.result
  if (!mapInstance || !result || !mapLoaded.value) return

  if (!result.raster_url) {
    overlayMessage.value = result.message || '栅格切片暂不可用'
    return
  }

  let rasterUrl = result.raster_url
  if (rasterUrl.startsWith('/')) {
    rasterUrl = window.location.origin + rasterUrl
  }

  mapInstance.addSource(RASTER_SOURCE_ID, {
    type: 'raster',
    tiles: [rasterUrl],
    tileSize: 256,
    scheme: 'xyz'
  })

  mapInstance.addLayer({
    id: RASTER_LAYER_ID,
    type: 'raster',
    source: RASTER_SOURCE_ID,
    paint: {
      'raster-opacity': 1
    }
  })

  overlayMessage.value = ''
}

const inspectCadSourceLayers = () => {
  const mapInstance = map.value
  const result = props.result
  if (!mapInstance || !result || !isCadFormat(result.source_format)) return

  const candidates = getCadSourceLayers(result)
  const activeIndexes = new Set<number>()
  let hasLayerProperty = false

  candidates.forEach((sourceLayer, index) => {
    const features = mapInstance.querySourceFeatures(VECTOR_SOURCE_ID, { sourceLayer }) || []
    if (features.length > 0) {
      activeIndexes.add(index)
      if (features.some((feature: any) => feature?.properties?.Layer || feature?.properties?.layer)) {
        hasLayerProperty = true
      }
    }
  })

  if (activeIndexes.size > 0) {
    setCadCandidateVisibility(mapInstance, activeIndexes)
  }

  devLog('cad source inspection', {
    candidates,
    activeIndexes: Array.from(activeIndexes),
    hasLayerProperty
  })

  if (!hasLayerProperty && sidebarLayers.value.length > 0) {
    overlayMessage.value = '当前 CAD 矢量切片缺少 Layer 属性，图层控制不可用'
  }
}

const inspectGisSourceLayers = () => {
  const mapInstance = map.value
  const result = props.result
  if (!mapInstance || !result || isCadFormat(result.source_format)) return

  const publishedLayers = getGisPublishedLayers(result)
  const activeCandidates = new Map<number, Set<number>>()
  let hasAnyFeature = false

  publishedLayers.forEach((layer, layerIndex) => {
    const activeIndexes = new Set<number>()
    getGisSourceLayerCandidates(result, layer).forEach((sourceLayer, candidateIndex) => {
      const features = mapInstance.querySourceFeatures(VECTOR_SOURCE_ID, { sourceLayer }) || []
      if (features.length > 0) {
        activeIndexes.add(candidateIndex)
        hasAnyFeature = true
      }
    })
    activeCandidates.set(layerIndex, activeIndexes)
  })

  setGisCandidateVisibility(mapInstance, result, activeCandidates)

  devLog('gis source inspection', {
    publishedLayers,
    activeCandidates: Array.from(activeCandidates.entries()).map(([layerIndex, indexes]) => ({
      layerIndex,
      indexes: Array.from(indexes)
    }))
  })

  if (!hasAnyFeature) {
    overlayMessage.value = '矢量切片已发布，但当前未探测到可显示的要素'
  }
}

const inspectVectorLayers = () => {
  const mapInstance = map.value
  const result = props.result
  if (!mapInstance || !result || !mapLoaded.value || mapMode.value !== 'vector') return
  if (!mapInstance.getSource(VECTOR_SOURCE_ID)) return

  const runInspection = () => {
    if (!map.value || !props.result || mapMode.value !== 'vector') return
    if (isCadFormat(props.result.source_format)) {
      inspectCadSourceLayers()
    } else {
      inspectGisSourceLayers()
    }
    updateMapControls()
  }

  if (mapInstance.isSourceLoaded(VECTOR_SOURCE_ID)) {
    runInspection()
    return
  }

  let attempts = 0
  const maxAttempts = 12
  const timer = window.setInterval(() => {
    attempts += 1
    if (!map.value || !map.value.getSource(VECTOR_SOURCE_ID)) {
      window.clearInterval(timer)
      return
    }
    if (map.value.isSourceLoaded(VECTOR_SOURCE_ID) || attempts >= maxAttempts) {
      window.clearInterval(timer)
      runInspection()
    }
  }, 300)
}

const renderMapLayers = () => {
  const mapInstance = map.value
  const result = props.result
  if (!mapInstance || !result || !mapLoaded.value) return

  clearRenderedLayers()

  if (mapMode.value === 'raster') {
    renderRasterLayer()
    return
  }

  if (!result.mvt_url) {
    overlayMessage.value = result.message || '矢量切片暂不可用'
    return
  }

  devLog('render', {
    sourceFormat: result.source_format,
    layerName: result.layer_name,
    publishedLayers: result.layers?.map(layer => ({
      layerName: layer.layer_name,
      nativeLayerName: layer.native_layer_name
    }))
  })

  if (isCadFormat(result.source_format)) {
    renderCadVectorLayers(mapInstance, result)
  } else {
    renderGisVectorLayers(mapInstance, result)
  }

  overlayMessage.value = ''
  inspectVectorLayers()
}

const toggleMode = () => {
  mapMode.value = mapMode.value === 'vector' ? 'raster' : 'vector'
  renderMapLayers()
}

const resetView = () => {
  fitToBounds(map.value, props.result?.bbox)
}

const toggleLayer = (layerName: string) => {
  const next = new Set(selectedLayers.value)
  if (next.has(layerName)) {
    next.delete(layerName)
  } else {
    next.add(layerName)
  }
  selectedLayers.value = next
  updateMapControls()
}

const toggleAllLayers = (event: Event) => {
  const checked = (event.target as HTMLInputElement).checked
  selectedLayers.value = checked ? new Set(sidebarLayers.value.map(layer => layer.name)) : new Set()
  updateMapControls()
}

const loadSidebarLayers = async (result: ConvertResult) => {
  if (!result.job_id) {
    sidebarLayers.value = []
    selectedLayers.value = new Set()
    return
  }

  try {
    const response = await fetch(`${API_BASE}/layers/${result.job_id}`)
    const data = response.ok ? await response.json() : []
    sidebarLayers.value = buildSidebarLayers(result, Array.isArray(data) ? data : [])
    selectedLayers.value = new Set(sidebarLayers.value.map(layer => layer.name))
    devLog('sidebar layers', sidebarLayers.value)
  } catch (error) {
    console.error('Fetch layers error:', error)
    sidebarLayers.value = buildSidebarLayers(result)
    selectedLayers.value = new Set(sidebarLayers.value.map(layer => layer.name))
  }
}

watch(isLayerListCollapsed, () => {
  setTimeout(() => map.value?.resize(), 350)
})

watch(() => props.result, async newVal => {
  if (!map.value) return

  if (!newVal) {
    overlayMessage.value = '请先上传数据文件'
    sidebarLayers.value = []
    selectedLayers.value = new Set()
    clearRenderedLayers()
    return
  }

  if (newVal.status === 'error') {
    overlayMessage.value = newVal.message || '转换或发布失败'
  } else if (newVal.status !== 'done') {
    overlayMessage.value = newVal.message || '正在处理数据...'
  }

  await loadSidebarLayers(newVal)
  fitToBounds(map.value, newVal.bbox)
  renderMapLayers()
})

onMounted(() => {
  if (!mapContainer.value) return

  map.value = createMapInstance(mapContainer.value)
  map.value.addControl(new maplibregl.NavigationControl())
  map.value.on('load', () => {
    mapLoaded.value = true
    if (props.result) {
      fitToBounds(map.value, props.result.bbox)
      renderMapLayers()
    }
  })

  map.value.on('mousemove', (event: any) => {
    mouseCoords.value = [event.lngLat.lng, event.lngLat.lat]
  })

  map.value.on('mouseleave', () => {
    mouseCoords.value = null
  })
})

onUnmounted(() => {
  destroyMapInstance(map.value)
  map.value = null
  mapLoaded.value = false
})
</script>

<template>
  <div class="map-wrapper">
    <LayerSidebar
      v-if="sidebarLayers.length > 0 && mapMode === 'vector'"
      :layers="sidebarLayers"
      :selected-layers="selectedLayers"
      :collapsed="isLayerListCollapsed"
      @toggle-collapse="isLayerListCollapsed = !isLayerListCollapsed"
      @toggle-layer="toggleLayer"
      @toggle-all="toggleAllLayers"
    />

    <div ref="mapContainer" class="map-container">
      <div v-if="overlayMessage" class="map-overlay">
        {{ overlayMessage }}
      </div>
      <button v-if="result" class="mode-toggle-btn" @click="toggleMode">
        切换为{{ mapMode === 'vector' ? '栅格切片（图片）' : '矢量切片（交互）' }}
      </button>
      <button v-if="result" class="reset-btn" @click="resetView">
        重置视角
      </button>
      <div v-if="mouseCoords" class="coords-display">
        经度：{{ mouseCoords[0].toFixed(6) }}，纬度：{{ mouseCoords[1].toFixed(6) }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.map-wrapper {
  display: flex;
  width: 100%;
  height: 100%;
  overflow: hidden;
  position: relative;
}

.map-container {
  flex: 1;
  height: 100%;
  background:
    radial-gradient(circle at top left, rgba(148, 163, 184, 0.18), transparent 28%),
    linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
  position: relative;
}

.map-overlay {
  position: absolute;
  inset: 0;
  z-index: 9;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  text-align: center;
  color: #334155;
  font-size: 16px;
  font-weight: 500;
  background: rgba(248, 250, 252, 0.72);
  backdrop-filter: blur(2px);
  pointer-events: none;
}

.mode-toggle-btn {
  position: absolute;
  top: 10px;
  right: 60px;
  z-index: 10;
  background-color: rgba(30, 41, 59, 0.8);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.mode-toggle-btn:hover {
  background-color: rgba(30, 41, 59, 1);
}

.reset-btn {
  position: absolute;
  bottom: 40px;
  right: 10px;
  z-index: 10;
  background-color: #3b82f6;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: background-color 0.2s;
}

.reset-btn:hover {
  background-color: #2563eb;
}

.coords-display {
  position: absolute;
  bottom: 10px;
  left: 10px;
  z-index: 10;
  background-color: rgba(30, 41, 59, 0.85);
  color: #e5e7eb;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
  pointer-events: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
</style>
