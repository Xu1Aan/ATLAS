export interface PublishedLayer {
  layer_name: string
  native_layer_name: string
  mvt_url?: string
  raster_url?: string
  bbox?: number[]
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
