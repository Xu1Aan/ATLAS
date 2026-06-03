<script setup lang="ts">
import { computed } from 'vue'
import { DArrowLeft, MoreFilled, Search, Setting } from '@element-plus/icons-vue'
import type { LayerListItem } from './types'

const props = defineProps<{
  layers: LayerListItem[]
  selectedLayers: Set<string>
  collapsed: boolean
  search: string
  mapMode: 'vector' | 'raster'
}>()

const emit = defineEmits<{
  (e: 'toggle-collapse'): void
  (e: 'toggle-layer', name: string): void
  (e: 'toggle-all', checked: boolean): void
  (e: 'update:search', value: string): void
}>()

const filteredLayers = computed(() => {
  const keyword = props.search.trim().toLowerCase()
  if (!keyword) return props.layers
  return props.layers.filter(layer => layer.name.toLowerCase().includes(keyword))
})

const allSelected = computed(() =>
  props.layers.length > 0 && props.selectedLayers.size === props.layers.length
)

const isIndeterminate = computed(() =>
  props.selectedLayers.size > 0 && props.selectedLayers.size < props.layers.length
)

const onSearchInput = (value: string) => {
  emit('update:search', value)
}
</script>

<template>
  <aside class="layer-sidebar" :class="{ 'is-collapsed': collapsed }">
    <div v-if="collapsed" class="collapsed-bar">
      <el-button text :icon="DArrowLeft" title="展开图层控制" @click="emit('toggle-collapse')" />
    </div>

    <template v-else>
      <div class="sidebar-header">
        <span class="sidebar-title">图层控制</span>
        <el-button text :icon="DArrowLeft" title="收起" @click="emit('toggle-collapse')" />
      </div>

      <div class="sidebar-search">
        <el-input
          :model-value="search"
          placeholder="搜索图层名称"
          clearable
          :prefix-icon="Search"
          @update:model-value="onSearchInput"
        />
      </div>

      <div v-if="layers.length > 0 && mapMode === 'vector'" class="sidebar-select-all">
        <el-checkbox
          :model-value="allSelected"
          :indeterminate="isIndeterminate"
          @change="(val: boolean) => emit('toggle-all', val)"
        >
          全选
        </el-checkbox>
        <span class="selected-count">已选 {{ selectedLayers.size }} / {{ layers.length }}</span>
      </div>

      <div class="sidebar-list-wrap">
        <el-empty
          v-if="layers.length === 0"
          description="暂无图层，请先上传并转换文件"
          :image-size="64"
        />
        <el-empty
          v-else-if="mapMode !== 'vector'"
          description="栅格模式下图层控制不可用"
          :image-size="64"
        />
        <el-scrollbar v-else>
          <div class="layer-list">
            <div
              v-for="layer in filteredLayers"
              :key="layer.name"
              class="layer-item"
            >
              <el-checkbox
                :model-value="selectedLayers.has(layer.name)"
                @change="() => emit('toggle-layer', layer.name)"
              />
              <span class="layer-dot" :style="{ backgroundColor: layer.color }" />
              <span class="layer-name" :title="layer.name">{{ layer.name }}</span>
              <el-dropdown trigger="click" @click.stop>
                <el-button text :icon="MoreFilled" class="layer-menu-btn" />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="emit('toggle-layer', layer.name)">
                      {{ selectedLayers.has(layer.name) ? '隐藏图层' : '显示图层' }}
                    </el-dropdown-item>
                    <el-dropdown-item disabled>图层属性</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
            <div v-if="filteredLayers.length === 0 && search" class="no-match">
              未找到匹配图层
            </div>
          </div>
        </el-scrollbar>
      </div>

      <div class="sidebar-footer">
        <span>共 {{ layers.length }} 个图层</span>
        <el-button text :icon="Setting" title="设置" />
      </div>
    </template>
  </aside>
</template>

<style scoped>
.layer-sidebar {
  width: 280px;
  background: #fff;
  border-right: 1px solid var(--app-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.3s ease;
  overflow: hidden;
}

.layer-sidebar.is-collapsed {
  width: 48px;
}

.collapsed-bar {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 12px;
  height: 100%;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 12px 8px;
  border-bottom: 1px solid var(--app-border);
}

.sidebar-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.sidebar-search {
  padding: 10px 12px;
}

.sidebar-select-all {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px 8px;
  font-size: 13px;
}

.selected-count {
  color: var(--app-text-secondary);
  font-size: 12px;
}

.sidebar-list-wrap {
  flex: 1;
  min-height: 0;
  padding: 0 4px;
}

.layer-list {
  padding: 4px 8px 12px;
}

.layer-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 4px;
  border-radius: 6px;
}

.layer-item:hover {
  background: #f5f7fa;
}

.layer-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.layer-name {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.layer-menu-btn {
  flex-shrink: 0;
  padding: 4px;
}

.no-match {
  padding: 16px;
  text-align: center;
  color: var(--app-text-secondary);
  font-size: 13px;
}

.sidebar-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-top: 1px solid var(--app-border);
  font-size: 12px;
  color: var(--app-text-secondary);
}
</style>
