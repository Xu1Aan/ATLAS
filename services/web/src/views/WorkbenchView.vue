<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import AppHeader from '../components/layout/AppHeader.vue'
import TaskToolbar from '../components/layout/TaskToolbar.vue'
import TaskStatusCards from '../components/layout/TaskStatusCards.vue'
import LayerSidebar from '../components/map/LayerSidebar.vue'
import Map from '../components/Map.vue'
import { API_BASE } from '../config'
import { useLayerControl } from '../composables/useLayerControl'
import { PROJECT_META } from '../meta'
import type { ConvertResult, Job, MapMode } from '../types'

const result = ref<ConvertResult | null>(null)
const error = ref<string | null>(null)
const jobs = ref<Job[]>([])
const selectedJobId = ref('')
const mapMode = ref<MapMode>('vector')
const mapRef = ref<InstanceType<typeof Map> | null>(null)

const {
  sidebarLayers,
  selectedLayers,
  layerSearch,
  sidebarCollapsed,
  toggleLayer,
  toggleAllLayers
} = useLayerControl(result)

const publishedAt = computed(() => {
  if (!selectedJobId.value) return null
  const job = jobs.value.find(item => item.job_id === selectedJobId.value)
  return job?.created_at ?? null
})

const fetchJobs = async () => {
  try {
    const res = await fetch(`${API_BASE}/jobs`)
    if (res.ok) {
      jobs.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to fetch jobs', e)
  }
}

const loadJob = async (jobId: string) => {
  if (!jobId) {
    result.value = null
    selectedJobId.value = ''
    return
  }

  try {
    const res = await fetch(`${API_BASE}/convert/${jobId}`)
    if (res.ok) {
      result.value = await res.json()
      error.value = null
      selectedJobId.value = jobId
    } else {
      error.value = '加载任务失败'
    }
  } catch (e) {
    error.value = `加载任务出错：${e}`
  }
}

const onConvert = (res: ConvertResult) => {
  error.value = null
  result.value = res
  fetchJobs()
  if (res.job_id) {
    selectedJobId.value = res.job_id
  }
}

const onError = (msg: string) => {
  if (!msg) {
    error.value = null
    return
  }
  error.value = msg
}

const onSelectJob = (jobId: string) => {
  loadJob(jobId)
}

watch(sidebarCollapsed, () => {
  mapRef.value?.resizeMap()
})

onMounted(() => {
  fetchJobs()
})
</script>

<template>
  <AppHeader />

  <div v-if="error" class="app-error">{{ error }}</div>

  <div class="app-body">
    <LayerSidebar
      :layers="sidebarLayers"
      :selected-layers="selectedLayers"
      :collapsed="sidebarCollapsed"
      :search="layerSearch"
      :map-mode="mapMode"
      @toggle-collapse="sidebarCollapsed = !sidebarCollapsed"
      @toggle-layer="toggleLayer"
      @toggle-all="toggleAllLayers"
      @update:search="layerSearch = $event"
    />

    <div class="main-column">
      <TaskToolbar
        :api-base="API_BASE"
        :jobs="jobs"
        :selected-job-id="selectedJobId"
        @convert="onConvert"
        @error="onError"
        @select-job="onSelectJob"
      />

      <TaskStatusCards
        :result="result"
        :layer-count="sidebarLayers.length"
        :published-at="publishedAt"
      />

      <Map
        ref="mapRef"
        :result="result"
        :selected-layers="selectedLayers"
        :map-mode="mapMode"
        @update:map-mode="mapMode = $event"
      />

      <div v-if="result && !result.mvt_url && result.status === 'done'" class="app-hint">
        转换完成，但 GeoServer 暂未返回 MVT 地址。
        <a :href="`${API_BASE}/convert/${result.job_id}/gpkg`" download>下载 GPKG</a>
        后可在 QGIS 等工具中查看，或在 GeoServer 配置完成后重新发布。
      </div>
    </div>
  </div>

  <footer class="app-footer">
    <span>{{ PROJECT_META.author }}</span>
    <a :href="`mailto:${PROJECT_META.email}`">{{ PROJECT_META.email }}</a>
  </footer>
</template>

<style scoped>
.app-body {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.main-column {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}
</style>
