<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { Aim } from '@element-plus/icons-vue'
import type { ConvertResult, MapMode } from '../types'
import { CAD_FILL_PREFIX, CAD_LINE_PREFIX, CAD_TEXT_PREFIX, renderCadVectorLayers, setCadCandidateVisibility, updateCadLayerFilters } from './map/cadRenderer'
import { GIS_FILL_PREFIX, GIS_LINE_PREFIX, GIS_POINT_PREFIX, GIS_TEXT_PREFIX, renderGisVectorLayers, setGisCandidateVisibility, updateGisLayerVisibility } from './map/gisRenderer'
import { devLog, getCadSourceLayers, getGisPublishedLayers, getGisSourceLayerCandidates, isCadFormat } from './map/types'
import { clearMapArtifacts, createMapInstance, destroyMapInstance, fitToBounds, RASTER_LAYER_ID, RASTER_SOURCE_ID, VECTOR_SOURCE_ID } from './map/useMapInstance'

const props = defineProps<{
  result: ConvertResult | null
  selectedLayers: Set<string>
  mapMode: MapMode
}>()

const emit = defineEmits<{
  (e: 'update:mapMode', mode: MapMode): void
}>()

const mapContainer = ref<HTMLElement | null>(null)
const map = ref<any>(null)
const mapLoaded = ref(false)
const mouseCoords = ref<[number, number] | null>(null)
const overlayMessage = ref('请先上传数据文件')

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

const updateMapControls = () => {
  const mapInstance = map.value
  const result = props.result
  if (!mapInstance || !result || !mapLoaded.value || props.mapMode !== 'vector') return

  if (isCadFormat(result.source_format)) {
    updateCadLayerFilters(mapInstance, props.selectedLayers)
  } else {
    updateGisLayerVisibility(mapInstance, result, props.selectedLayers)
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
    paint: { 'raster-opacity': 1 }
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

  if (!hasAnyFeature) {
    overlayMessage.value = '矢量切片已发布，但当前未探测到可显示的要素'
  }
}

const inspectVectorLayers = () => {
  const mapInstance = map.value
  const result = props.result
  if (!mapInstance || !result || !mapLoaded.value || props.mapMode !== 'vector') return
  if (!mapInstance.getSource(VECTOR_SOURCE_ID)) return

  const runInspection = () => {
    if (!map.value || !props.result || props.mapMode !== 'vector') return
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

  if (props.mapMode === 'raster') {
    renderRasterLayer()
    return
  }

  if (!result.mvt_url) {
    overlayMessage.value = result.message || '矢量切片暂不可用'
    return
  }

  if (isCadFormat(result.source_format)) {
    renderCadVectorLayers(mapInstance, result)
  } else {
    renderGisVectorLayers(mapInstance, result)
  }

  overlayMessage.value = ''
  inspectVectorLayers()
}

const setMapMode = (mode: MapMode) => {
  emit('update:mapMode', mode)
}

const resetView = () => {
  fitToBounds(map.value, props.result?.bbox)
}

const resizeMap = () => {
  setTimeout(() => map.value?.resize(), 350)
}

watch(() => props.selectedLayers, () => {
  updateMapControls()
}, { deep: true })

watch(() => props.mapMode, () => {
  renderMapLayers()
})

watch(() => props.result, newVal => {
  if (!map.value) return

  if (!newVal) {
    overlayMessage.value = '请先上传数据文件'
    clearRenderedLayers()
    return
  }

  if (newVal.status === 'error') {
    overlayMessage.value = newVal.message || '转换或发布失败'
  } else if (newVal.status !== 'done') {
    overlayMessage.value = newVal.message || '正在处理数据...'
  }

  fitToBounds(map.value, newVal.bbox)
  renderMapLayers()
})

defineExpose({ resizeMap })

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
  <div class="map-panel">
    <div ref="mapContainer" class="map-container">
      <div v-if="overlayMessage" class="map-overlay">
        {{ overlayMessage }}
      </div>

      <div v-if="result" class="map-controls-top">
        <el-button-group>
          <el-button
            size="small"
            :type="mapMode === 'vector' ? 'primary' : 'default'"
            @click="setMapMode('vector')"
          >
            矢量
          </el-button>
          <el-button
            size="small"
            :type="mapMode === 'raster' ? 'primary' : 'default'"
            @click="setMapMode('raster')"
          >
            栅格
          </el-button>
        </el-button-group>
      </div>

      <el-button
        v-if="result"
        class="reset-btn"
        type="primary"
        size="small"
        :icon="Aim"
        @click="resetView"
      >
        重置视角
      </el-button>

      <div v-if="mouseCoords" class="coords-display">
        经度: {{ mouseCoords[0].toFixed(6) }}, 纬度: {{ mouseCoords[1].toFixed(6) }}
      </div>

      <div class="map-attribution">
        © 基于 MapLibre GL JS 渲染引擎
        <a href="https://maplibre.org/" target="_blank" rel="noopener noreferrer">MapLibre</a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.map-panel {
  flex: 1;
  min-height: 0;
  padding: 0 16px 16px;
  background: var(--app-bg);
}

.map-container {
  width: 100%;
  height: 100%;
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--app-border);
  overflow: hidden;
  position: relative;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
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
  color: #606266;
  font-size: 15px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(2px);
  pointer-events: none;
}

.map-controls-top {
  position: absolute;
  top: 12px;
  right: 52px;
  z-index: 10;
}

.reset-btn {
  position: absolute;
  bottom: 36px;
  right: 12px;
  z-index: 10;
}

.coords-display {
  position: absolute;
  bottom: 12px;
  left: 12px;
  z-index: 10;
  background: rgba(48, 49, 51, 0.85);
  color: #fff;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-family: Consolas, Monaco, monospace;
  pointer-events: none;
}

.map-attribution {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  font-size: 11px;
  color: #909399;
  pointer-events: auto;
}

.map-attribution a {
  color: var(--app-primary);
  text-decoration: none;
}

.map-attribution a:hover {
  text-decoration: underline;
}
</style>
