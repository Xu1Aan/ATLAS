<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  Connection,
  Document,
  FolderOpened,
  Headset,
  Link,
  Lock,
  QuestionFilled,
  RefreshRight,
  Share,
  User,
  View,
  Hide,
} from '@element-plus/icons-vue'
import { login } from '../composables/useAuth'
import GitHubLink from '../components/layout/GitHubLink.vue'
import { PROJECT_META } from '../meta'

const router = useRouter()
const formRef = ref<FormInstance>()
const showPassword = ref(false)
const captchaCode = ref('')
const rememberMe = ref(true)

const form = reactive({
  username: '',
  password: '',
  captcha: '',
})

const features = [
  { icon: Document, title: '图纸切片发布', desc: '高效切片，快速发布' },
  { icon: Connection, title: 'GeoServer 自动发布', desc: '集成 GeoServer，一键发布' },
  { icon: FolderOpened, title: '多源 CAD/GIS 数据接入', desc: '支持 DWG/DXF/SHP/KML 等' },
  { icon: Share, title: 'MVT / WMTS 服务输出', desc: '标准服务输出，灵活集成' },
]

const CAPTCHA_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

const generateCaptcha = () => {
  let code = ''
  for (let i = 0; i < 4; i += 1) {
    code += CAPTCHA_CHARS[Math.floor(Math.random() * CAPTCHA_CHARS.length)]
  }
  captchaCode.value = code
  form.captcha = ''
}

const validateCaptcha = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (!value) {
    callback(new Error('请输入验证码'))
    return
  }
  if (value.toUpperCase() !== captchaCode.value) {
    callback(new Error('验证码不正确'))
    return
  }
  callback()
}

const rules: FormRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  captcha: [{ validator: validateCaptcha, trigger: 'blur' }],
}

const onSubmit = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  if (login(form.username.trim(), form.password, rememberMe.value)) {
    ElMessage.success('登录成功')
    router.push('/')
    return
  }

  ElMessage.error('账号或密码错误')
  generateCaptcha()
}

const onForgotPassword = () => {
  ElMessage.info(`请联系管理员：${PROJECT_META.email}`)
}

const onSso = () => {
  ElMessage.info('单点登录暂未接入')
}

const onHelp = () => {
  ElMessage.info('帮助文档筹备中')
}

onMounted(() => {
  generateCaptcha()
})
</script>

<template>
  <div class="login-page">
    <header class="login-topbar">
      <GitHubLink variant="text" />
      <span class="topbar-divider" />
      <span class="topbar-link">简体中文</span>
      <span class="topbar-divider" />
      <button type="button" class="topbar-link" @click="onHelp">
        <el-icon><QuestionFilled /></el-icon>
        帮助中心
      </button>
    </header>

    <main class="login-main">
      <section class="brand-panel">
        <div class="brand-header">
          <div class="brand-logo-wrap">
            <img src="/logo.png" alt="ATLAS" class="brand-logo" />
          </div>
          <div class="brand-text">
            <h1 class="brand-title">ATLAS</h1>
            <p class="brand-subtitle">空间数据治理与服务发布平台</p>
          </div>
        </div>

        <p class="brand-desc">
          连接多源 CAD/GIS 数据，统一治理，标准发布，高效构建企业级空间数据服务体系。
        </p>

        <div class="feature-grid">
          <div v-for="item in features" :key="item.title" class="feature-card">
            <div class="feature-icon">
              <el-icon :size="20"><component :is="item.icon" /></el-icon>
            </div>
            <div>
              <div class="feature-title">{{ item.title }}</div>
              <div class="feature-desc">{{ item.desc }}</div>
            </div>
          </div>
        </div>
      </section>

      <section class="form-panel">
        <div class="login-card">
          <div class="login-card-header">
            <h2>欢迎登录</h2>
            <p>登录后进入空间数据治理工作台</p>
          </div>

          <el-form ref="formRef" :model="form" :rules="rules" size="large" @submit.prevent="onSubmit">
            <el-form-item prop="username">
              <el-input v-model="form.username" placeholder="请输入账号" :prefix-icon="User" />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请输入密码"
                :prefix-icon="Lock"
                @keyup.enter="onSubmit"
              >
                <template #suffix>
                  <el-icon class="password-toggle" @click="showPassword = !showPassword">
                    <View v-if="showPassword" />
                    <Hide v-else />
                  </el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item prop="captcha">
              <div class="captcha-row">
                <el-input
                  v-model="form.captcha"
                  placeholder="请输入验证码"
                  maxlength="4"
                  class="captcha-input"
                  @keyup.enter="onSubmit"
                />
                <div class="captcha-display" aria-label="验证码">{{ captchaCode }}</div>
                <el-button :icon="RefreshRight" circle @click="generateCaptcha" />
              </div>
            </el-form-item>

            <div class="form-options">
              <el-checkbox v-model="rememberMe">记住我</el-checkbox>
              <button type="button" class="link-btn" @click="onForgotPassword">忘记密码?</button>
            </div>

            <el-button type="primary" class="submit-btn" native-type="submit">登录系统</el-button>
            <el-button plain class="sso-btn" :icon="Link" @click="onSso">单点登录 (SSO)</el-button>
          </el-form>

          <div class="login-card-footer">
            <a :href="`mailto:${PROJECT_META.email}`" class="contact-link">
              <el-icon><Headset /></el-icon>
              联系管理员
            </a>
          </div>
        </div>
      </section>
    </main>

    <footer class="login-footer">
      <span>{{ PROJECT_META.author }}</span>
      <a :href="`mailto:${PROJECT_META.email}`">{{ PROJECT_META.email }}</a>
      <span class="footer-divider" />
      <span class="footer-hint">建议使用 Chrome 110+ / Edge 110+ / Firefox 110+</span>
    </footer>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background:
    linear-gradient(rgba(255, 255, 255, 0.75), rgba(255, 255, 255, 0.75)),
    url('/background.png') center / cover no-repeat;
}

.login-topbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  padding: 16px 32px 0;
}

.topbar-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: transparent;
  color: #606266;
  font-size: 14px;
  cursor: pointer;
  padding: 0;
}

.topbar-link:hover {
  color: var(--app-primary);
}

.topbar-divider,
.footer-divider {
  width: 1px;
  height: 14px;
  background: var(--app-border);
}

.login-main {
  flex: 1;
  display: grid;
  grid-template-columns: minmax(320px, 1.1fr) minmax(340px, 0.9fr);
  gap: 48px;
  align-items: center;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 32px;
}

.brand-panel {
  padding-right: 16px;
}

.brand-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 24px;
}

.brand-logo-wrap {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 112px;
  height: 112px;
  padding: 12px;
  border-radius: 16px;
  background: var(--app-card-bg);
  border: 1px solid var(--app-border);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.brand-logo {
  width: 88px;
  height: 88px;
  object-fit: contain;
}

.brand-text {
  min-width: 0;
}

.brand-title {
  margin: 0;
  font-size: 40px;
  font-weight: 600;
  color: var(--app-primary);
  line-height: 1.15;
  letter-spacing: 0.02em;
}

.brand-subtitle {
  margin: 8px 0 0;
  font-size: 17px;
  color: #606266;
  line-height: 1.5;
}

.brand-desc {
  margin: 0 0 24px;
  max-width: 520px;
  font-size: 15px;
  line-height: 1.75;
  color: #606266;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.feature-card {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px 16px;
  border-radius: 8px;
  background: var(--app-card-bg);
  border: 1px solid var(--app-border);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.feature-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--app-primary);
  background: #e6f4ff;
  flex-shrink: 0;
}

.feature-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.feature-desc {
  font-size: 13px;
  color: var(--app-text-secondary);
  line-height: 1.5;
}

.form-panel {
  display: flex;
  justify-content: center;
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 28px;
  border-radius: 8px;
  background: var(--app-card-bg);
  border: 1px solid var(--app-border);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.login-card-header h2 {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 600;
  color: #303133;
}

.login-card-header p {
  margin: 0 0 20px;
  color: var(--app-text-secondary);
  font-size: 14px;
}

.captcha-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.captcha-input {
  flex: 1;
}

.captcha-display {
  min-width: 88px;
  height: 40px;
  padding: 0 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  background: #f5f7fa;
  border: 1px solid var(--app-border);
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 3px;
  color: #303133;
  user-select: none;
}

.password-toggle {
  cursor: pointer;
  color: var(--app-text-secondary);
}

.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.link-btn {
  border: none;
  background: transparent;
  color: var(--app-primary);
  cursor: pointer;
  font-size: 14px;
  padding: 0;
}

.submit-btn,
.sso-btn {
  width: 100%;
  margin-left: 0;
}

.submit-btn {
  margin-bottom: 10px;
}

.login-card-footer {
  margin-top: 16px;
  text-align: center;
}

.contact-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--app-text-secondary);
  text-decoration: none;
  font-size: 14px;
}

.contact-link:hover {
  color: var(--app-primary);
}

.login-footer {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 10px 16px;
  font-size: 12px;
  color: var(--app-text-secondary);
  border-top: 1px solid var(--app-border);
  background: var(--app-card-bg);
}

.login-footer a {
  color: var(--app-text-secondary);
  text-decoration: none;
}

.login-footer a:hover {
  color: var(--app-primary);
}

.footer-hint {
  color: var(--app-text-secondary);
}

@media (max-width: 960px) {
  .login-main {
    grid-template-columns: 1fr;
    gap: 24px;
    padding: 16px 20px 24px;
  }

  .brand-panel {
    padding-right: 0;
  }

  .brand-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .brand-logo-wrap {
    width: 96px;
    height: 96px;
    padding: 10px;
  }

  .brand-logo {
    width: 76px;
    height: 76px;
  }

  .brand-title {
    font-size: 32px;
  }

  .brand-subtitle {
    font-size: 15px;
  }

  .feature-grid {
    grid-template-columns: 1fr;
  }

  .login-footer {
    flex-direction: column;
    gap: 6px;
  }

  .footer-divider {
    display: none;
  }
}
</style>
