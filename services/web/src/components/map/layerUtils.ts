import type { ConvertResult } from '../../types'
import {
  getPublishedLayerDisplayName,
  isCadFormat,
  type LayerListItem
} from './types'

export function buildSidebarLayers(result: ConvertResult, fetchedLayers: any[] = []): LayerListItem[] {
  if (isCadFormat(result.source_format)) {
    return fetchedLayers.map((item: any) => ({
      name: item.name,
      color: item.color || '#9ca3af',
      kind: 'cad-layer' as const
    }))
  }

  const published = result.layers || []
  if (published.length > 0) {
    return published.map(layer => ({
      name: getPublishedLayerDisplayName(layer),
      color: '#2563eb',
      kind: 'published-layer' as const
    }))
  }

  return fetchedLayers.map((item: any) => ({
    name: item.name,
    color: item.color || '#2563eb',
    kind: 'published-layer' as const
  }))
}

export type { LayerListItem }
