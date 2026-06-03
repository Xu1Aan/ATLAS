<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowDown, Bell, QuestionFilled } from '@element-plus/icons-vue'
import GitHubLink from './GitHubLink.vue'
import { clearAuth, getCurrentUser } from '../../composables/useAuth'

const router = useRouter()
const username = computed(() => getCurrentUser() ?? 'admin')
const avatarText = computed(() => username.value.slice(0, 2).toUpperCase())

const onLogout = () => {
  clearAuth()
  router.push('/login')
}
</script>

<template>
  <header class="app-header">
    <div class="brand">
      <img src="/logo.png" alt="ATLAS" class="brand-logo" />
      <div class="brand-text">
        <h1 class="app-title">ATLAS</h1>
        <p class="brand-tagline">空间数据治理与服务发布平台</p>
      </div>
    </div>

    <div class="header-actions">
      <el-tooltip content="GitHub 仓库" placement="bottom">
        <GitHubLink variant="icon" />
      </el-tooltip>
      <el-tooltip content="帮助" placement="bottom">
        <el-button circle :icon="QuestionFilled" />
      </el-tooltip>
      <el-tooltip content="通知" placement="bottom">
        <el-button circle :icon="Bell" />
      </el-tooltip>
      <el-dropdown trigger="click">
        <div class="user-entry">
          <el-avatar :size="32" class="user-avatar">{{ avatarText }}</el-avatar>
          <span class="user-name">{{ username }}</span>
          <el-icon><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item disabled>个人中心</el-dropdown-item>
            <el-dropdown-item @click="onLogout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid var(--app-border);
  flex-shrink: 0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-logo {
  width: 40px;
  height: 40px;
  object-fit: contain;
}

.brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.app-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  line-height: 1.2;
}

.brand-tagline {
  margin: 0;
  font-size: 12px;
  color: var(--app-text-secondary);
  line-height: 1.2;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 6px;
  cursor: pointer;
}

.user-entry:hover {
  background: #f5f7fa;
}

.user-avatar {
  background: var(--app-primary);
  font-size: 13px;
}

.user-name {
  font-size: 14px;
  color: #303133;
}
</style>
