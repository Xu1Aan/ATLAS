<script setup lang="ts">
import Uploader from '../Uploader.vue'
import type { ConvertResult, Job } from '../../types'

defineProps<{
  apiBase: string
  jobs: Job[]
  selectedJobId: string
}>()

const emit = defineEmits<{
  (e: 'convert', res: ConvertResult): void
  (e: 'error', msg: string): void
  (e: 'select-job', jobId: string): void
}>()
</script>

<template>
  <Uploader
    :api-base="apiBase"
    @convert="emit('convert', $event)"
    @error="emit('error', $event)"
  >
    <template #history>
      <div class="toolbar-section">
        <span class="section-label">历史任务</span>
        <el-select
          :model-value="selectedJobId"
          placeholder="选择历史任务..."
          filterable
          clearable
          class="job-select"
          @update:model-value="emit('select-job', $event || '')"
        >
          <el-option
            v-for="job in jobs"
            :key="job.job_id"
            :value="job.job_id"
            :label="`${job.filename} (${new Date(job.created_at * 1000).toLocaleString()})`"
          />
        </el-select>
      </div>
    </template>
  </Uploader>
</template>

<style scoped>
.toolbar-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 64px;
}

.section-label {
  font-size: 13px;
  color: var(--app-text-secondary);
  font-weight: 500;
}

.job-select {
  width: 100%;
}
</style>
