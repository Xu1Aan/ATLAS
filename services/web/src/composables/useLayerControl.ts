import { ref, watch, type Ref } from 'vue'
import { API_BASE } from '../config'
import type { ConvertResult } from '../types'
import {
  buildSidebarLayers,
  type LayerListItem
} from '../components/map/layerUtils'

export function useLayerControl(result: Ref<ConvertResult | null>) {
  const sidebarLayers = ref<LayerListItem[]>([])
  const selectedLayers = ref<Set<string>>(new Set())
  const layerSearch = ref('')
  const sidebarCollapsed = ref(false)

  const loadSidebarLayers = async (convertResult: ConvertResult) => {
    if (!convertResult.job_id) {
      sidebarLayers.value = []
      selectedLayers.value = new Set()
      return
    }

    try {
      const response = await fetch(`${API_BASE}/layers/${convertResult.job_id}`)
      const data = response.ok ? await response.json() : []
      sidebarLayers.value = buildSidebarLayers(convertResult, Array.isArray(data) ? data : [])
      selectedLayers.value = new Set(sidebarLayers.value.map(layer => layer.name))
    } catch (error) {
      console.error('Fetch layers error:', error)
      sidebarLayers.value = buildSidebarLayers(convertResult)
      selectedLayers.value = new Set(sidebarLayers.value.map(layer => layer.name))
    }
  }

  const toggleLayer = (layerName: string) => {
    const next = new Set(selectedLayers.value)
    if (next.has(layerName)) {
      next.delete(layerName)
    } else {
      next.add(layerName)
    }
    selectedLayers.value = next
  }

  const toggleAllLayers = (checked: boolean) => {
    selectedLayers.value = checked
      ? new Set(sidebarLayers.value.map(layer => layer.name))
      : new Set()
  }

  const resetLayers = () => {
    sidebarLayers.value = []
    selectedLayers.value = new Set()
    layerSearch.value = ''
  }

  watch(result, async newVal => {
    if (!newVal) {
      resetLayers()
      return
    }
    await loadSidebarLayers(newVal)
  })

  return {
    sidebarLayers,
    selectedLayers,
    layerSearch,
    sidebarCollapsed,
    loadSidebarLayers,
    toggleLayer,
    toggleAllLayers,
    resetLayers
  }
}
