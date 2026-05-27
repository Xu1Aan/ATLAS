<script setup lang="ts">
import type { LayerListItem } from './types'

defineProps<{
  layers: LayerListItem[]
  selectedLayers: Set<string>
  collapsed: boolean
}>()

const emit = defineEmits<{
  (e: 'toggle-collapse'): void
  (e: 'toggle-layer', name: string): void
  (e: 'toggle-all', event: Event): void
}>()
</script>

<template>
  <div class="sidebar" :class="{ 'is-collapsed': collapsed }">
    <div class="sidebar-toggle" :title="collapsed ? '展开图层列表' : '收起图层列表'" @click="emit('toggle-collapse')">
      {{ collapsed ? '▶' : '◀' }}
    </div>
    <div v-show="!collapsed" class="sidebar-content">
      <div class="sidebar-header">
        <h3>图层列表</h3>
        <label class="select-all">
          <input type="checkbox" :checked="selectedLayers.size === layers.length" @change="emit('toggle-all', $event)" />
          全选
        </label>
      </div>
      <div class="layer-list">
        <label v-for="layer in layers" :key="layer.name" class="layer-item">
          <input type="checkbox" :checked="selectedLayers.has(layer.name)" @change="emit('toggle-layer', layer.name)" />
          <span class="layer-color-box" :style="{ backgroundColor: layer.color }"></span>
          <span class="layer-name" :title="layer.name">{{ layer.name }}</span>
        </label>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  width: 240px;
  background: #3b4453;
  border-right: 1px solid #2d3239;
  display: flex;
  flex-direction: row;
  z-index: 10;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.2);
  transition: width 0.3s ease;
}

.sidebar.is-collapsed {
  width: 24px;
}

.sidebar-toggle {
  width: 24px;
  height: 100%;
  background: #23272e;
  color: #9ca3af;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-right: 1px solid #1f2937;
  font-size: 10px;
  flex-shrink: 0;
}

.sidebar-toggle:hover {
  background: #374151;
  color: #fff;
}

.sidebar-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
  height: 100%;
}

.sidebar-header {
  padding: 10px 15px;
  border-bottom: 1px solid #2d3239;
  background: #2e3440;
}

.sidebar-header h3 {
  margin: 0 0 8px 0;
  font-size: 1rem;
  color: #e5e7eb;
}

.select-all {
  font-size: 0.85rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #9ca3af;
}

.layer-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.layer-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  cursor: pointer;
  font-size: 0.9rem;
  color: #d1d5db;
}

.layer-item:hover {
  color: #fff;
}

.layer-color-box {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.layer-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
