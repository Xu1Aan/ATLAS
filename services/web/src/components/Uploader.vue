<script setup lang="ts">
import { ref } from 'vue'
import { FolderOpened, Upload } from '@element-plus/icons-vue'
import type { ConvertResult, MinioConvertRequest } from '../types'

const props = defineProps<{
  apiBase: string
}>()

const emit = defineEmits<{
  (e: 'convert', res: ConvertResult): void
  (e: 'error', msg: string): void
}>()

const mode = ref<'local' | 'minio'>('local')
const loading = ref(false)
const progress = ref(0)
const progressMsg = ref('')
const file = ref<File | null>(null)
const showDetails = ref(false)
const logs = ref<string[]>([])
const currentJobId = ref<string | null>(null)
const xhr = ref<XMLHttpRequest | null>(null)

const minioBucket = ref('atlas-data')
const minioObjectKey = ref('')
const minioFilename = ref('')

const allowedExtensions = ['.dwg', '.dxf', '.kml', '.zip']

const onFileChange = (uploadFile: { raw?: File } | undefined) => {
  file.value = uploadFile?.raw ?? null
}

const addLog = (msg: string) => {
  if (!msg) return
  const last = logs.value[logs.value.length - 1]
  if (last !== msg) {
    logs.value.push(msg)
  }
}

const resetState = () => {
  loading.value = false
  currentJobId.value = null
  progress.value = 0
  progressMsg.value = ''
  logs.value = []
}

const cancelUpload = () => {
  if (xhr.value) {
    xhr.value.abort()
    xhr.value = null
  }
  resetState()
  emit('error', '已取消请求')
}

const pollStatus = async (jobId: string) => {
  if (!loading.value) return

  const poll = async () => {
    if (!loading.value || currentJobId.value !== jobId) return

    try {
      const r = await fetch(`${props.apiBase}/status/${jobId}`)
      if (!r.ok) {
        if (loading.value) setTimeout(poll, 2000)
        return
      }

      const res = await r.json() as ConvertResult
      progress.value = res.progress || 0
      progressMsg.value = res.message || ''
      addLog(res.message || '')

      if (res.status === 'done') {
        loading.value = false
        emit('convert', res)
        return
      }

      if (res.status === 'error') {
        loading.value = false
        emit('error', res.message || '转换失败')
        return
      }

      setTimeout(poll, 1000)
    } catch (err) {
      console.error(err)
      if (loading.value) setTimeout(poll, 2000)
    }
  }

  poll()
}

const beginLoading = (initialLog: string, initialProgress: string) => {
  loading.value = true
  progress.value = 0
  progressMsg.value = initialProgress
  logs.value = [initialLog]
  showDetails.value = false
  emit('error', '')
}

const handleAcceptedResponse = (res: ConvertResult, nextMessage: string) => {
  if (res.status === 'error') {
    resetState()
    emit('error', res.message || '转换失败')
    return
  }

  addLog(nextMessage)
  progress.value = 0
  progressMsg.value = '等待后台转换...'
  currentJobId.value = res.job_id
  pollStatus(res.job_id)
}

const onSubmitLocal = async () => {
  const lowerName = file.value?.name.toLowerCase() || ''
  const isSupported = allowedExtensions.some(ext => lowerName.endsWith(ext))
  if (!file.value || !isSupported) {
    emit('error', '请选择 DWG / DXF / SHP(zip) / KML 文件')
    return
  }

  beginLoading('开始上传本地文件...', '正在上传...')

  try {
    const form = new FormData()
    form.append('file', file.value)

    const req = new XMLHttpRequest()
    xhr.value = req
    req.open('POST', `${props.apiBase}/convert`)

    req.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 100)
        progress.value = percent
        progressMsg.value = `正在上传... ${percent}%`
      }
    }

    req.onload = () => {
      xhr.value = null
      if (req.status >= 200 && req.status < 300) {
        try {
          const res = JSON.parse(req.responseText) as ConvertResult
          handleAcceptedResponse(res, '上传完成，等待服务端处理...')
        } catch {
          resetState()
          emit('error', '响应解析失败')
        }
      } else {
        resetState()
        let msg = `请求失败 ${req.status}`
        try {
          const err = JSON.parse(req.responseText)
          msg = err.detail?.msg || err.detail || err.message || msg
        } catch {}
        emit('error', msg)
      }
    }

    req.onerror = () => {
      xhr.value = null
      resetState()
      emit('error', '网络错误')
    }

    req.onabort = () => {
      xhr.value = null
    }

    req.send(form)
  } catch (err) {
    resetState()
    emit('error', err instanceof Error ? err.message : '未知错误')
  }
}

const onSubmitMinio = async () => {
  const effectiveName = (minioFilename.value || minioObjectKey.value.split('/').pop() || '').toLowerCase()
  const isSupported = allowedExtensions.some(ext => effectiveName.endsWith(ext))
  if (!minioBucket.value || !minioObjectKey.value || !isSupported) {
    emit('error', '请填写 bucket、object key，并确保对象是 DWG / DXF / SHP(zip) / KML')
    return
  }

  beginLoading('开始请求 MinIO 导入...', '等待 MinIO 下载...')

  const payload: MinioConvertRequest = {
    bucket_name: minioBucket.value,
    object_name: minioObjectKey.value,
    filename: minioFilename.value || undefined
  }

  try {
    const res = await fetch(`${props.apiBase}/convert/minio`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (!res.ok) {
      resetState()
      let msg = `请求失败 ${res.status}`
      try {
        const err = await res.json()
        msg = err.detail?.msg || err.detail || err.message || msg
      } catch {}
      emit('error', msg)
      return
    }

    const body = await res.json() as ConvertResult
    handleAcceptedResponse(body, 'MinIO 请求已接收，等待服务端下载并转换...')
  } catch (err) {
    resetState()
    emit('error', err instanceof Error ? err.message : '未知错误')
  }
}
</script>

<template>
  <div class="uploader-root">
    <el-row :gutter="16" align="middle">
      <el-col :xs="24" :sm="24" :md="8" :lg="7">
        <div class="toolbar-section">
          <span class="section-label">上传方式</span>
          <el-radio-group v-model="mode" size="default" class="mode-group">
            <el-radio-button value="local">本地上传</el-radio-button>
            <el-radio-button value="minio">MinIO 导入</el-radio-button>
          </el-radio-group>
        </div>
      </el-col>

      <el-col :xs="24" :sm="24" :md="10" :lg="10">
        <div class="toolbar-section">
          <span class="section-label">选择文件</span>
          <div v-if="mode === 'local'" class="upload-row">
            <el-upload
              :auto-upload="false"
              :show-file-list="false"
              accept=".dwg,.dxf,.kml,.zip"
              :disabled="loading"
              class="file-picker"
              @change="onFileChange"
            >
              <template #trigger>
                <el-input
                  readonly
                  :model-value="file?.name || ''"
                  placeholder="选择 DWG / DXF / SHP(zip) / KML 文件"
                  :prefix-icon="FolderOpened"
                />
              </template>
            </el-upload>
            <el-button type="primary" :icon="Upload" :disabled="loading || !file" @click="onSubmitLocal">
              {{ loading ? '处理中...' : '上传转换' }}
            </el-button>
          </div>
          <div v-else class="minio-row">
            <el-input v-model.trim="minioBucket" :disabled="loading" placeholder="Bucket 名称" />
            <el-input v-model.trim="minioObjectKey" :disabled="loading" placeholder="Object Key" />
            <el-input v-model.trim="minioFilename" :disabled="loading" placeholder="文件名（可选）" />
            <el-button type="primary" :icon="Upload" :disabled="loading || !minioBucket || !minioObjectKey" @click="onSubmitMinio">
              {{ loading ? '处理中...' : '导入转换' }}
            </el-button>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="24" :md="6" :lg="7">
        <slot name="history" />
      </el-col>
    </el-row>

    <el-dialog
      v-model="loading"
      title="正在切片处理中..."
      width="560px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
      align-center
    >
      <el-progress :percentage="progress" :stroke-width="10" />
      <p class="progress-text">{{ progress }}% - {{ progressMsg }}</p>

      <el-collapse v-if="showDetails" class="logs-collapse">
        <el-collapse-item title="处理日志" name="logs">
          <div class="logs-container">
            <div v-for="(log, idx) in logs" :key="idx" class="log-item">{{ log }}</div>
          </div>
        </el-collapse-item>
      </el-collapse>

      <template #footer>
        <el-button @click="showDetails = !showDetails">
          {{ showDetails ? '收起详情' : '查看详情' }}
        </el-button>
        <el-button type="danger" plain @click="cancelUpload">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.uploader-root {
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid var(--app-border);
  flex-shrink: 0;
}

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

.mode-group {
  width: fit-content;
}

.upload-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.file-picker {
  flex: 1;
  min-width: 0;
}

.file-picker :deep(.el-upload) {
  width: 100%;
}

.minio-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.progress-text {
  margin: 12px 0 0;
  font-size: 14px;
  color: #606266;
}

.logs-collapse {
  margin-top: 12px;
}

.logs-container {
  max-height: 220px;
  overflow: auto;
}

.log-item {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}
</style>
