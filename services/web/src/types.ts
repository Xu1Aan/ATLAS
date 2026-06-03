export interface PublishedLayer {
  layer_name: string
  native_layer_name: string
  mvt_url?: string
  raster_url?: string
  bbox?: number[]
}

export interface LayerListItem {
  name: string
  color?: string
  kind?: 'cad-layer' | 'published-layer'
}

export interface ConvertResult {
  job_id: string
  status: string
  progress?: number
  message?: string
  dxf_path?: string
  gpkg_path?: string
  source_format?: string
  source_path?: string
  layer_name?: string
  layers?: PublishedLayer[]
  mvt_url?: string
  raster_url?: string
  wmts_url?: string
  bbox?: number[]
}

export interface Job {
  job_id: string
  filename: string
  status: string
  created_at: number
}

export interface MinioConvertRequest {
  bucket_name: string
  object_name: string
  filename?: string
}

export type MapMode = 'vector' | 'raster'
