<script setup lang="ts">
import { computed } from 'vue'
import {
  Clock,
  Collection,
  Document,
  Platform,
  Location,
  SuccessFilled
} from '@element-plus/icons-vue'
import type { ConvertResult } from '../../types'

const props = defineProps<{
  result: ConvertResult | null
  layerCount: number
  publishedAt: number | null
}>()

const formatLabels: Record<string, string> = {
  dwg: 'DWG',
  dxf: 'DXF',
  kml: 'KML',
  shp_zip: 'SHP'
}

const statusLabel = computed(() => {
  if (!props.result) return '—'
  const map: Record<string, string> = {
    done: '转换完成',
    error: '转换失败',
    pending: '等待中',
    converting: '转换中',
    publishing: '发布中'
  }
  return map[props.result.status] || props.result.status
})

const statusType = computed(() => {
  if (!props.result) return 'info'
  if (props.result.status === 'done') return 'success'
  if (props.result.status === 'error') return 'danger'
  return 'warning'
})

const fileType = computed(() => {
  if (!props.result?.source_format) return '—'
  return formatLabels[props.result.source_format] || props.result.source_format.toUpperCase()
})

const layerCountDisplay = computed(() => {
  if (!props.result) return '—'
  const count = props.layerCount || props.result.layers?.length || 0
  return `${count} 个图层`
})

const publishedTime = computed(() => {
  if (!props.publishedAt) return '—'
  return new Date(props.publishedAt * 1000).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).replace(/\//g, '-')
})

const cards = computed(() => [
  { key: 'type', label: '文件类型', value: fileType.value, icon: Document },
  { key: 'status', label: '任务状态', value: statusLabel.value, icon: SuccessFilled, tag: statusType.value },
  { key: 'target', label: '发布目标', value: props.result ? 'GeoServer' : '—', icon: Platform },
  { key: 'crs', label: '坐标系', value: props.result ? 'EPSG:4326' : '—', icon: Location },
  { key: 'layers', label: '图层数量', value: layerCountDisplay.value, icon: Collection },
  { key: 'time', label: '发布时间', value: publishedTime.value, icon: Clock }
])
</script>

<template>
  <div class="status-cards">
    <el-row :gutter="12">
      <el-col v-for="card in cards" :key="card.key" :xs="12" :sm="8" :md="4">
        <el-card shadow="never" class="status-card">
          <div class="card-inner">
            <el-icon class="card-icon" :size="20">
              <component :is="card.icon" />
            </el-icon>
            <div class="card-body">
              <span class="card-label">{{ card.label }}</span>
              <el-tag v-if="card.tag" :type="card.tag as any" size="small" effect="light">
                {{ card.value }}
              </el-tag>
              <span v-else class="card-value" :title="String(card.value)">{{ card.value }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.status-cards {
  padding: 12px 16px;
  background: var(--app-bg);
  flex-shrink: 0;
}

.status-card {
  border: 1px solid var(--app-border);
  border-radius: 8px;
  margin-bottom: 0;
}

.status-card :deep(.el-card__body) {
  padding: 12px 14px;
}

.card-inner {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.card-icon {
  color: var(--app-primary);
  flex-shrink: 0;
  margin-top: 2px;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.card-label {
  font-size: 12px;
  color: var(--app-text-secondary);
}

.card-value {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
