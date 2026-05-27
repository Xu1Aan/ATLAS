<template>
  <div class="uploader-shell">
    <div class="mode-switch">
      <button type="button" class="mode-btn" :class="{ active: mode === 'local' }" @click="mode = 'local'">
        本地上传
      </button>
      <button type="button" class="mode-btn" :class="{ active: mode === 'minio' }" @click="mode = 'minio'">
        MinIO 导入
      </button>
    </div>

    <form v-if="mode === 'local'" class="uploader-form" @submit.prevent="onSubmitLocal">
      <label class="uploader-label-btn" :title="file ? file.name : '点击选择文件'">
        <span class="filename-span">{{ file ? file.name : '选择 DWG / DXF / SHP(zip) / KML' }}</span>
        <input
          type="file"
          accept=".dwg,.dxf,.kml,.zip"
          :disabled="loading"
          class="uploader-input"
          @change="onFileChange"
        />
      </label>
      <button type="submit" :disabled="loading || !file" class="uploader-submit-btn">
        {{ loading ? '处理中...' : '上传转换' }}
      </button>
    </form>

    <form v-else class="minio-form" @submit.prevent="onSubmitMinio">
      <input v-model.trim="minioBucket" :disabled="loading" class="minio-input" placeholder="Bucket 名称" />
      <input v-model.trim="minioObjectKey" :disabled="loading" class="minio-input minio-key" placeholder="Object Key，例如 folder/test.dwg" />
      <input v-model.trim="minioFilename" :disabled="loading" class="minio-input" placeholder="文件名（可选）" />
      <button type="submit" :disabled="loading || !minioBucket || !minioObjectKey" class="uploader-submit-btn">
        {{ loading ? '处理中...' : '导入转换' }}
      </button>
    </form>
  </div>

  <div v-if="loading" class="modal-overlay">
    <div class="modal-content" role="dialog" aria-modal="true" aria-labelledby="upload-progress-title">
      <h3 id="upload-progress-title">正在切片处理中...</h3>

      <div class="progress-wrapper">
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" :style="{ width: progress + '%' }"></div>
        </div>
        <div class="progress-text">{{ progress }}% - {{ progressMsg }}</div>
      </div>

      <div v-if="showDetails" class="logs-container">
        <div v-for="(log, idx) in logs" :key="idx" class="log-item">
          {{ log }}
        </div>
      </div>

      <div class="modal-footer">
        <button type="button" class="detail-btn" @click="showDetails = !showDetails">
          {{ showDetails ? '收起详情' : '查看详情' }}
        </button>
        <button type="button" class="cancel-btn" @click="cancelUpload">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
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

const minioBucket = ref('')
const minioObjectKey = ref('')
const minioFilename = ref('')

const allowedExtensions = ['.dwg', '.dxf', '.kml', '.zip']

const onFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  file.value = target.files?.[0] ?? null
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
  const isSupported = allowedExtensions.some((ext) => lowerName.endsWith(ext))
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
  const isSupported = allowedExtensions.some((ext) => effectiveName.endsWith(ext))
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
      headers: {
        'Content-Type': 'application/json'
      },
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

<style scoped>
.uploader-shell {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 520px;
}

.mode-switch {
  display: flex;
  gap: 8px;
}

.mode-btn {
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #334155;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 13px;
  cursor: pointer;
}

.mode-btn.active {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}

.uploader-form,
.minio-form {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 10px;
}

.uploader-label-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  cursor: pointer;
  background-color: #fff;
  min-width: 240px;
  max-width: 360px;
  height: 40px;
  box-sizing: border-box;
  transition: all 0.2s ease;
}

.uploader-label-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.filename-span {
  font-size: 14px;
  color: #334155;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.uploader-input {
  display: none;
}

.minio-input {
  height: 40px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  padding: 0 12px;
  font-size: 14px;
  min-width: 140px;
}

.minio-key {
  min-width: 280px;
}

.uploader-submit-btn {
  padding: 0 16px;
  height: 40px;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  white-space: nowrap;
}

.uploader-submit-btn:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
}

.uploader-submit-btn:hover:not(:disabled) {
  background-color: #2563eb;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.42);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  width: min(560px, calc(100vw - 32px));
  max-height: min(78vh, 720px);
  overflow: auto;
  background: #ffffff;
  border-radius: 16px;
  padding: 22px;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.28);
  border: 1px solid rgba(148, 163, 184, 0.22);
}

.modal-content h3 {
  margin: 0;
  font-size: 20px;
  color: #0f172a;
}

.progress-wrapper {
  margin-top: 16px;
}

.progress-bar-bg {
  width: 100%;
  height: 10px;
  border-radius: 999px;
  background: #e2e8f0;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #2563eb, #0ea5e9);
  transition: width 0.2s ease;
}

.progress-text {
  margin-top: 10px;
  font-size: 14px;
  color: #475569;
}

.logs-container {
  margin-top: 16px;
  max-height: 220px;
  overflow: auto;
  padding: 12px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.log-item {
  font-size: 13px;
  color: #334155;
  line-height: 1.6;
}

.modal-footer {
  margin-top: 18px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.detail-btn,
.cancel-btn {
  padding: 9px 14px;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn {
  color: #b91c1c;
  border-color: #fecaca;
  background: #fff5f5;
}
</style>
